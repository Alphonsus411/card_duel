from __future__ import annotations

from itertools import combinations, islice, permutations
from typing import Protocol

from ..domain.enums import CardKind, MatchStatus, Phase, Zone
from ..domain.errors import IllegalAction
from ..domain.models import CardDefinition, GameState, MoveReplacementDefinition, StackItem
from ..rules.config import RuleSet
from .commands import (
    ActivateAbility,
    AdvancePhase,
    ChooseTriggeredTargets,
    Concede,
    DeclareAttackers,
    DeclareBlockers,
    DeclareChallenge,
    DiscardCards,
    DrainSteps,
    EquipCard,
    GameCommand,
    OrderTriggeredAbilities,
    PassPriority,
    PlayCard,
    ResolveCombat,
    ResolveMoveReplacement,
    ResolveSearchChoice,
    SetReplacementOrder,
    TransmutePermanent,
)


class CombatActionEnumerator(Protocol):
    """Acceso mínimo y tipado a la enumeración propia del combate."""

    def legal_actions(self, player_id: str) -> tuple[GameCommand, ...]: ...


class LegalActionContext(Protocol):
    """Consultas de solo lectura necesarias para enumerar acciones legales."""

    rules: RuleSet

    def _require_state(self) -> GameState: ...
    def _require_running_state(self) -> GameState: ...
    def _definition(self, card_id: str) -> CardDefinition: ...
    def _replacement_definitions(
        self, definition: CardDefinition
    ) -> tuple[MoveReplacementDefinition, ...]: ...
    def _trigger_target_commands(
        self, player_id: str, item: StackItem
    ) -> list[ChooseTriggeredTargets]: ...
    def _legal_plays(self, player_id: str) -> list[PlayCard]: ...
    def _legal_ability_activations(
        self, player_id: str, source_card_id: str
    ) -> list[ActivateAbility]: ...
    def _is_creature(self, card_id: str) -> bool: ...
    @property
    def _legacy_019(self) -> bool: ...
    @property
    def _combat_action_enumerator(self) -> CombatActionEnumerator: ...


class LegalActionEnumerator:
    """Enumera comandos disponibles sin validar ni ejecutar ninguno."""

    def __init__(self, context: LegalActionContext) -> None:
        self._context = context

    def legal_actions(self, player_id: str) -> tuple[GameCommand, ...]:
        context = self._context
        state = context._require_state()
        if state.status in (MatchStatus.FINISHED, MatchStatus.BLOCKED):
            return ()
        if state.status is not MatchStatus.RUNNING:
            raise IllegalAction("La partida no está en ejecución")
        if player_id not in state.players:
            return ()
        actions: list[GameCommand] = []
        player = state.players[player_id]

        if state.pending_move_replacement:
            pending = state.pending_move_replacement
            if player_id != pending.chooser_id:
                return (Concede(player_id),)
            return tuple(
                ResolveMoveReplacement(player_id, index)
                for index in pending.candidate_indices
            ) + (Concede(player_id),)

        if state.pending_search:
            search = state.pending_search
            if player_id != search.chooser_id:
                return (Concede(player_id),)
            actions.extend(
                ResolveSearchChoice(player_id, tuple(selection))
                for count in range(search.minimum, search.maximum + 1)
                for selection in islice(
                    combinations(search.eligible_card_ids, count),
                    context.rules.legal_action_enumeration_limit,
                )
            )
            actions.append(Concede(player_id))
            return tuple(actions[: context.rules.legal_action_enumeration_limit + 1])

        if state.pending_triggers:
            if player_id != state.priority_player_id:
                return (Concede(player_id),)
            unlocked = next(
                (item for item in state.pending_triggers if not item.targets_locked),
                None,
            )
            if unlocked is not None:
                actions.extend(context._trigger_target_commands(player_id, unlocked))
                actions.append(Concede(player_id))
                return tuple(actions)
            item_ids = tuple(item.item_id for item in state.pending_triggers)
            actions.extend(
                OrderTriggeredAbilities(player_id, tuple(order))
                for order in islice(
                    permutations(item_ids),
                    context.rules.legal_action_enumeration_limit,
                )
            )
            actions.append(Concede(player_id))
            return tuple(actions)

        if state.phase in {Phase.EFFECTS, Phase.COMBAT}:
            actions.extend(context._combat_action_enumerator.legal_actions(player_id))

        if player_id == state.priority_player_id:
            actions.extend(context._legal_plays(player_id))
            if (
                player_id == state.active_player_id
                and (context._legacy_019 or state.phase is Phase.EFFECTS)
                and player.drainage_used_turn_serial != state.turn_serial
            ):
                actions.extend(DrainSteps(player_id, amount) for amount in range(1, 6))
            for card_id in player.zones[Zone.BATTLEFIELD]:
                definition = context._definition(card_id)
                replacements = context._replacement_definitions(definition)
                if definition.player_orders_replacements and len(replacements) > 1:
                    actions.extend(
                        SetReplacementOrder(player_id, card_id, tuple(order))
                        for order in islice(
                            permutations(range(len(replacements))),
                            context.rules.legal_action_enumeration_limit,
                        )
                        if tuple(order) != state.cards[card_id].replacement_order
                    )
                if definition.transmutable:
                    actions.append(TransmutePermanent(player_id, card_id))
                actions.extend(context._legal_ability_activations(player_id, card_id))
                if definition.kind is CardKind.EQUIPMENT:
                    for creature_id in player.zones[Zone.BATTLEFIELD]:
                        if context._is_creature(creature_id):
                            if player.steps >= definition.cost:
                                actions.append(EquipCard(player_id, card_id, creature_id))
            actions.append(PassPriority(player_id))

        if (
            player_id == state.active_player_id
            and state.phase_priority_complete
            and not state.stack
        ):
            if state.phase is Phase.DISCARD:
                excess = max(0, len(player.zones[Zone.HAND]) - context.rules.hand_limit)
                if excess:
                    actions.extend(
                        DiscardCards(player_id, tuple(card_ids))
                        for card_ids in combinations(player.zones[Zone.HAND], excess)
                    )
                else:
                    actions.append(AdvancePhase(player_id))
            elif not (state.phase is Phase.COMBAT and state.combat and not state.combat.resolved):
                actions.append(AdvancePhase(player_id))

        actions.append(Concede(player_id))
        command_order = {
            DiscardCards: 0,
            DeclareBlockers: 0,
            ResolveCombat: 0,
            DeclareAttackers: 1,
            DeclareChallenge: 1,
            AdvancePhase: 2,
            PlayCard: 10,
            ActivateAbility: 11,
            DrainSteps: 11,
            EquipCard: 12,
            TransmutePermanent: 20,
            PassPriority: 90,
            SetReplacementOrder: 95,
            Concede: 100,
        }
        return tuple(sorted(actions, key=lambda action: command_order[type(action)]))
