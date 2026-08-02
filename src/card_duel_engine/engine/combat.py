from __future__ import annotations

from collections.abc import Iterator
from itertools import combinations, islice, permutations, product
from typing import Protocol
from ..domain.enums import Keyword, LordDomain, Phase, Zone
from ..domain.errors import IllegalAction
from ..domain.models import CombatState, GameState
from .commands import (
    DeclareAttackers,
    DeclareBlockers,
    DeclareChallenge,
    GameCommand,
    ResolveCombat,
)


class CombatContext(Protocol):
    """Operaciones del coordinador que necesita exclusivamente el combate."""

    def _require_running_state(self) -> GameState: ...
    def _is_ready_creature(self, card_id: str) -> bool: ...
    def _is_lord_creature(self, card_id: str) -> bool: ...
    def _lord_domain(self, card_id: str) -> LordDomain | None: ...
    def _effective_keywords(self, card_id: str) -> frozenset[str | Keyword]: ...
    @property
    def _legacy_019_replay(self) -> bool: ...
    def _is_creature(self, card_id: str) -> bool: ...
    @property
    def _combat_action_enumeration_limit(self) -> int: ...
    def _current_strength(self, card_id: str) -> int: ...
    def _deal_damage(self, card_id: str, amount: int, source_card_id: str | None = None) -> None: ...
    def _deal_wounds(self, player_id: str, amount: int, source_card_id: str | None = None) -> None: ...
    def _run_state_based_actions(self) -> None: ...
    def _emit(self, event_type: str, player_id: str | None = None, card_id: str | None = None, payload: dict[str, object] | None = None) -> None: ...


class CombatManager:
    def __init__(self, context: CombatContext) -> None:
        self._context = context

    @property
    def _legacy_019_replay(self) -> bool:
        """Mantiene compatibles los contextos mínimos externos del gestor."""
        return getattr(self._context, "_legacy_019_replay", False)

    def legal_actions(self, player_id: str) -> tuple[GameCommand, ...]:
        """Construye solo las acciones propias del combate, en orden estable."""
        state = self._context._require_running_state()
        if state.phase not in {Phase.EFFECTS, Phase.COMBAT} or player_id not in state.players:
            return ()

        actions: list[GameCommand] = []
        combat = state.combat
        if combat is not None:
            if player_id == combat.defending_player_id and not combat.blockers_declared:
                actions.extend(
                    islice(
                        self._blocker_declarations(player_id, combat),
                        self._context._combat_action_enumeration_limit,
                    )
                )
            if (
                player_id == combat.attacking_player_id
                and combat.blockers_declared
                and not combat.resolved
                and not state.stack
                and state.phase_priority_complete
            ):
                actions.append(ResolveCombat(player_id))

        if (
            state.phase is Phase.COMBAT
            and not self._challenge_used_this_turn(player_id)
            and player_id == state.active_player_id
            and state.phase_priority_complete
            and not state.stack
            and combat is None
        ):
            player = state.players[player_id]
            ready = tuple(
                card_id
                for card_id in player.zones[Zone.BATTLEFIELD]
                if self._context._is_ready_creature(card_id)
            )
            if ready:
                defenders = tuple(
                    defender for defender in state.turn_order if defender != player_id
                )
                actions.extend(
                    DeclareAttackers(player_id, tuple(attackers), defender)
                    for attackers, defender in islice(
                        (
                            (attackers, defender)
                            for size in range(1, len(ready) + 1)
                            for attackers in combinations(ready, size)
                            for defender in defenders
                        ),
                        self._context._combat_action_enumeration_limit,
                    )
                )
        if (
            state.phase is Phase.EFFECTS
            and player_id == state.active_player_id
            and state.phase_priority_complete
            and not state.stack
            and combat is None
            and not self._challenge_used_this_turn(player_id)
            and not self._normal_combat_used_this_turn(player_id)
        ):
            for challenger_id in state.players[player_id].zones[Zone.BATTLEFIELD]:
                if self._can_initiate_challenge(challenger_id):
                    for defender_id in state.turn_order:
                        if defender_id == player_id:
                            continue
                        for challenged_id in state.players[defender_id].zones[
                            Zone.BATTLEFIELD
                        ]:
                            if self._context._is_creature(challenged_id):
                                actions.append(
                                    DeclareChallenge(
                                        player_id,
                                        challenger_id,
                                        challenged_id,
                                        defender_id,
                                    )
                                )
        return tuple(actions)

    def _challenge_used_this_turn(self, player_id: str) -> bool:
        """Consulta el registro ya persistido, sin añadir campos a v1/v2."""
        state = self._context._require_running_state()
        return any(
            event.event_type == "CHALLENGE_DECLARED"
            and event.player_id == player_id
            and event.payload.get("turn_serial") == state.turn_serial
            for event in state.event_log
        )

    def _can_initiate_challenge(self, card_id: str) -> bool:
        """Decide la aptitud del desafiante desde su identidad y estado efectivos."""
        if not (
            self._context._is_ready_creature(card_id)
            and self._context._is_lord_creature(card_id)
        ):
            return False
        if self._legacy_019_replay:
            return True
        if self._context._lord_domain(card_id) is LordDomain.REALMS:
            return True
        return Keyword.CAN_CHALLENGE in self._context._effective_keywords(card_id)

    def _normal_combat_used_this_turn(self, player_id: str) -> bool:
        state = self._context._require_running_state()
        return any(
            event.event_type == "ATTACKERS_DECLARED"
            and event.player_id == player_id
            and event.payload.get("turn_serial") == state.turn_serial
            for event in state.event_log
        )

    def _blocker_declarations(
        self, player_id: str, combat: CombatState
    ) -> Iterator[DeclareBlockers]:
        """Enumera bloqueos legales conservando el orden de cada grupo."""
        state = self._context._require_running_state()
        blockers = tuple(
            card_id
            for card_id in state.players[combat.defending_player_id].zones[Zone.BATTLEFIELD]
            if self._context._is_ready_creature(card_id)
        )

        yield DeclareBlockers(player_id)
        for blocker_count in range(1, len(blockers) + 1):
            for ordered_blockers in permutations(blockers, blocker_count):
                for destinations in product(combat.attackers, repeat=blocker_count):
                    assignments = tuple(
                        (
                            attacker_id,
                            tuple(
                                blocker_id
                                for blocker_id, destination in zip(
                                    ordered_blockers, destinations, strict=True
                                )
                                if destination == attacker_id
                            ),
                        )
                        for attacker_id in combat.attackers
                        if attacker_id in destinations
                    )
                    yield DeclareBlockers(player_id, assignments)

    def _declare_challenge(self, command: DeclareChallenge) -> None:
        state = self._context._require_running_state()
        expected_phase = Phase.COMBAT if self._legacy_019_replay else Phase.EFFECTS
        if command.player_id != state.active_player_id or state.phase is not expected_phase:
            raise IllegalAction("Desafío solo puede declararse en la Fase Activa propia")
        if not self._legacy_019_replay and self._challenge_used_this_turn(command.player_id):
            raise IllegalAction("Desafío solo puede declararse una vez por turno")
        if not self._legacy_019_replay and self._normal_combat_used_this_turn(command.player_id):
            raise IllegalAction("Desafío sustituye al combate normal de este turno")
        if state.stack or not state.phase_priority_complete or state.combat is not None:
            raise IllegalAction("Desafío sustituye a un combate todavía no declarado")
        if (
            command.defending_player_id == command.player_id
            or command.defending_player_id not in state.players
        ):
            raise IllegalAction("Jugador desafiado inválido")
        if command.challenger_id not in state.players[command.player_id].zones[Zone.BATTLEFIELD]:
            raise IllegalAction("El desafiante debe estar en el campo propio")
        if command.challenged_id not in state.players[command.defending_player_id].zones[
            Zone.BATTLEFIELD
        ]:
            raise IllegalAction("La criatura desafiada debe pertenecer al oponente indicado")
        if not self._can_initiate_challenge(command.challenger_id):
            raise IllegalAction(
                "Solo un Señor elegible, transformado y enderezado puede iniciar Desafío"
            )
        if not self._context._is_creature(command.challenged_id):
            raise IllegalAction("Desafío requiere otra criatura")
        state.combat = CombatState(
            attacking_player_id=command.player_id,
            defending_player_id=command.defending_player_id,
            attackers=(command.challenger_id,),
            blockers={command.challenger_id: (command.challenged_id,)},
            blockers_declared=True,
            is_challenge=True,
        )
        state.priority_player_id = command.defending_player_id
        state.phase_priority_complete = False
        state.consecutive_passes = 0
        payload: dict[str, object] = {
            "challenged_id": command.challenged_id,
            "defender": command.defending_player_id,
        }
        if not self._legacy_019_replay:
            payload["turn_serial"] = state.turn_serial
        self._context._emit(
            "CHALLENGE_DECLARED",
            command.player_id,
            command.challenger_id,
            payload,
        )

    def _declare_attackers(self, command: DeclareAttackers) -> None:
        state = self._context._require_running_state()
        if command.player_id != state.active_player_id or state.phase is not Phase.COMBAT:
            raise IllegalAction("Los atacantes solo se declaran durante el Combate propio")
        if self._challenge_used_this_turn(command.player_id):
            raise IllegalAction("El Desafío ya sustituyó al combate normal de este turno")
        if state.stack or not state.phase_priority_complete or state.combat is not None:
            raise IllegalAction("No puede declararse ahora un nuevo combate")
        if (
            command.defending_player_id == command.player_id
            or command.defending_player_id not in state.players
        ):
            raise IllegalAction("Defensor inválido")
        if not command.attacker_ids or len(set(command.attacker_ids)) != len(command.attacker_ids):
            raise IllegalAction("La declaración de atacantes no es válida")
        for card_id in command.attacker_ids:
            if card_id not in state.players[command.player_id].zones[Zone.BATTLEFIELD]:
                raise IllegalAction("Atacante fuera del campo propio")
            if not self._context._is_ready_creature(card_id):
                raise IllegalAction("Solo una criatura enderezada puede atacar")
        for card_id in command.attacker_ids:
            state.cards[card_id].exhausted = True
        state.combat = CombatState(
            attacking_player_id=command.player_id,
            defending_player_id=command.defending_player_id,
            attackers=command.attacker_ids,
        )
        state.priority_player_id = command.defending_player_id
        state.phase_priority_complete = False
        state.consecutive_passes = 0
        payload: dict[str, object] = {
            "attackers": command.attacker_ids,
            "defender": command.defending_player_id,
        }
        if not self._legacy_019_replay:
            payload["turn_serial"] = state.turn_serial
        self._context._emit(
            "ATTACKERS_DECLARED",
            command.player_id,
            payload=payload,
        )

    def _declare_blockers(self, command: DeclareBlockers) -> None:
        state = self._context._require_running_state()
        combat = state.combat
        if state.phase is not Phase.COMBAT or combat is None or combat.blockers_declared:
            raise IllegalAction("No hay una declaración de bloqueadores pendiente")
        if command.player_id != combat.defending_player_id or state.stack:
            raise IllegalAction("Solo el defensor puede declarar bloqueadores")
        assignments = dict(command.assignments)
        if len(assignments) != len(command.assignments):
            raise IllegalAction("Un atacante aparece duplicado en los bloqueos")
        if set(assignments) - set(combat.attackers):
            raise IllegalAction("Se ha asignado un atacante inexistente")
        used: list[str] = []
        for blocker_ids in assignments.values():
            used.extend(blocker_ids)
        if len(used) != len(set(used)):
            raise IllegalAction("Una criatura no puede bloquear a dos atacantes")
        defender = state.players[combat.defending_player_id]
        for blocker_id in used:
            if blocker_id not in defender.zones[Zone.BATTLEFIELD] or not self._context._is_ready_creature(blocker_id):
                raise IllegalAction("Solo una criatura enderezada propia puede bloquear")
        for blocker_id in used:
            state.cards[blocker_id].exhausted = True
        combat.blockers = {attacker: tuple(blockers) for attacker, blockers in assignments.items()}
        combat.blockers_declared = True
        state.priority_player_id = combat.attacking_player_id
        state.phase_priority_complete = False
        state.consecutive_passes = 0
        self._context._emit("BLOCKERS_DECLARED", command.player_id, payload={"assignments": assignments})

    def _resolve_combat(self, player_id: str) -> None:
        state = self._context._require_running_state()
        combat = state.combat
        if combat is None or player_id != combat.attacking_player_id:
            raise IllegalAction("No existe un combate propio pendiente")
        if not combat.blockers_declared or combat.resolved or state.stack:
            raise IllegalAction("El combate todavía no puede resolverse")
        if not state.phase_priority_complete:
            raise IllegalAction("Debe cerrarse la ventana de respuestas del combate")

        for attacker_id in combat.attackers:
            if attacker_id not in state.cards or state.cards[attacker_id].zone is not Zone.BATTLEFIELD:
                continue
            attack_strength = self._context._current_strength(attacker_id)
            blocker_ids = [
                blocker_id
                for blocker_id in combat.blockers.get(attacker_id, ())
                if state.cards[blocker_id].zone is Zone.BATTLEFIELD
            ]
            if combat.is_challenge:
                if blocker_ids:
                    challenged_id = blocker_ids[0]
                    self._context._deal_damage(challenged_id, attack_strength, attacker_id)
                    self._context._deal_damage(
                        attacker_id,
                        self._context._current_strength(challenged_id),
                        challenged_id,
                    )
                continue
            if not blocker_ids:
                self._context._deal_wounds(combat.defending_player_id, attack_strength, attacker_id)
                self._context._emit(
                    "COMBAT_WOUNDS",
                    combat.attacking_player_id,
                    attacker_id,
                    {"target": combat.defending_player_id, "amount": attack_strength},
                )
                continue

            remaining = attack_strength
            for blocker_id in blocker_ids:
                if remaining <= 0:
                    break
                assigned = min(remaining, self._context._current_strength(blocker_id))
                self._context._deal_damage(blocker_id, assigned, attacker_id)
                remaining -= assigned
            self._context._deal_damage(
                attacker_id,
                sum(self._context._current_strength(blocker_id) for blocker_id in blocker_ids),
            )
            if remaining > 0:
                self._context._deal_wounds(combat.defending_player_id, remaining, attacker_id)
                self._context._emit(
                    "COMBAT_WOUNDS",
                    combat.attacking_player_id,
                    attacker_id,
                    {"target": combat.defending_player_id, "amount": remaining},
                )

        self._context._run_state_based_actions()
        combat.resolved = True
        state.phase_priority_complete = True
        self._context._emit("COMBAT_RESOLVED", combat.attacking_player_id)
