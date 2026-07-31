from __future__ import annotations

from typing import Protocol
from ..domain.enums import Phase, Zone
from ..domain.errors import IllegalAction
from ..domain.models import CombatState, GameState
from .commands import DeclareAttackers, DeclareBlockers, DeclareChallenge


class CombatContext(Protocol):
    """Operaciones del coordinador que necesita exclusivamente el combate."""

    def _require_running_state(self) -> GameState: ...
    def _is_ready_creature(self, card_id: str) -> bool: ...
    def _is_lord_creature(self, card_id: str) -> bool: ...
    def _is_creature(self, card_id: str) -> bool: ...
    def _current_strength(self, card_id: str) -> int: ...
    def _deal_damage(self, card_id: str, amount: int, source_card_id: str | None = None) -> None: ...
    def _deal_wounds(self, player_id: str, amount: int, source_card_id: str | None = None) -> None: ...
    def _run_state_based_actions(self) -> None: ...
    def _emit(self, event_type: str, player_id: str | None = None, card_id: str | None = None, payload: dict[str, object] | None = None) -> None: ...


class CombatManager:
    def __init__(self, context: CombatContext) -> None:
        self._context = context

    def _declare_challenge(self, command: DeclareChallenge) -> None:
        state = self._context._require_running_state()
        if command.player_id != state.active_player_id or state.phase is not Phase.COMBAT:
            raise IllegalAction("Desafío solo puede declararse en la Fase de Combate propia")
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
        if not self._context._is_ready_creature(
            command.challenger_id
        ) or not self._context._is_lord_creature(command.challenger_id):
            raise IllegalAction("Solo un Señor criatura enderezado puede iniciar Desafío")
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
        self._context._emit(
            "CHALLENGE_DECLARED",
            command.player_id,
            command.challenger_id,
            {"challenged_id": command.challenged_id, "defender": command.defending_player_id},
        )

    def _declare_attackers(self, command: DeclareAttackers) -> None:
        state = self._context._require_running_state()
        if command.player_id != state.active_player_id or state.phase is not Phase.COMBAT:
            raise IllegalAction("Los atacantes solo se declaran durante el Combate propio")
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
        self._context._emit(
            "ATTACKERS_DECLARED",
            command.player_id,
            payload={"attackers": command.attacker_ids, "defender": command.defending_player_id},
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
