from __future__ import annotations

import random
from dataclasses import replace
from typing import Protocol
from ..domain.enums import CardKind, ControllerScope, MatchStatus, MoveReason, TriggerKind, Zone
from ..domain.errors import IllegalAction, InvariantViolation
from ..domain.models import CardDefinition, GameState, MoveReplacementDefinition, PendingMoveReplacement
from ..rules.config import RuleSet
from .commands import GameCommand, ResolveMoveReplacement, SetReplacementOrder


class MoveReplacementChoiceRequired(Exception):
    def __init__(
        self,
        chooser_id: str,
        card_id: str,
        reason: MoveReason,
        candidate_indices: tuple[int, ...],
        candidate_destinations: tuple[Zone, ...],
    ) -> None:
        self.chooser_id = chooser_id
        self.card_id = card_id
        self.reason = reason
        self.candidate_indices = candidate_indices
        self.candidate_destinations = candidate_destinations


class ZoneContext(Protocol):
    """Estado y servicios mínimos requeridos para movimientos y sustituciones."""

    rules: RuleSet
    def _require_state(self) -> GameState: ...
    def _require_running_state(self) -> GameState: ...
    def _definition(self, card_id: str) -> CardDefinition: ...
    def _current_strength(self, card_id: str) -> int: ...
    def _consume_replacement_replay_choice(self) -> int | None: ...
    def _execute_transaction(self, command: GameCommand, replay_choices: tuple[int, ...]) -> None: ...
    def _emit(self, event_type: str, player_id: str | None = None, card_id: str | None = None, payload: dict[str, object] | None = None) -> None: ...


class ZoneManager:
    def __init__(self, context: ZoneContext) -> None:
        self._context = context

    def _draw(self, player_id: str, amount: int) -> None:
        state = self._context._require_state()
        player = state.players[player_id]
        for _ in range(amount):
            if not player.zones[Zone.DECK]:
                if (
                    self._context.rules.recycle_discard
                    and not player.discard_recycling_blocked
                    and player.zones[Zone.DISCARD]
                ):
                    for card_id in tuple(player.zones[Zone.DISCARD]):
                        self._move_card(card_id, Zone.DECK, player_id)
                    random.Random(state.random_seed + state.turn_number).shuffle(
                        player.zones[Zone.DECK]
                    )
                    self._context._emit("DISCARD_RECYCLED", player_id)
                else:
                    self._context._emit("DRAW_FAILED", player_id)
                    return
            card_id = player.zones[Zone.DECK][-1]
            self._move_card(card_id, Zone.HAND, player_id)
            self._context._emit("CARD_DRAWN", player_id, card_id)

    @staticmethod
    def _replacement_definitions(
        definition: CardDefinition,
    ) -> tuple[MoveReplacementDefinition, ...]:
        return (
            *((definition.move_replacement,) if definition.move_replacement else ()),
            *definition.move_replacements,
        )

    def _set_replacement_order(self, command: SetReplacementOrder) -> None:
        state = self._context._require_running_state()
        if command.player_id != state.priority_player_id:
            raise IllegalAction("El jugador no posee prioridad")
        if command.card_id not in state.players[command.player_id].zones[Zone.BATTLEFIELD]:
            raise IllegalAction("Solo pueden ordenarse sustituciones de un permanente propio")
        definition = self._context._definition(command.card_id)
        replacements = self._replacement_definitions(definition)
        if not definition.player_orders_replacements or len(replacements) < 2:
            raise IllegalAction("La carta no admite ordenar sustituciones")
        expected = tuple(range(len(replacements)))
        if len(command.ordered_indices) != len(replacements) or set(
            command.ordered_indices
        ) != set(expected):
            raise IllegalAction("El orden de sustituciones no es una permutación completa")
        state.cards[command.card_id].replacement_order = command.ordered_indices
        self._context._emit(
            "REPLACEMENT_ORDER_SET",
            command.player_id,
            command.card_id,
            {"ordered_indices": command.ordered_indices},
        )

    def _ordered_replacements(self, card_id: str, definition: CardDefinition) -> tuple[MoveReplacementDefinition, ...]:
        replacements = self._replacement_definitions(definition)
        instance = self._context._require_state().cards[card_id]
        if (
            definition.player_orders_replacements
            and len(instance.replacement_order) == len(replacements)
            and set(instance.replacement_order) == set(range(len(replacements)))
        ):
            return tuple(replacements[index] for index in instance.replacement_order)
        return tuple(
            replacement
            for _, replacement in sorted(
                enumerate(replacements),
                key=lambda item: (-item[1].priority, item[0]),
            )
        )

    def _move_card(
        self,
        card_id: str,
        destination: Zone,
        destination_player: str,
        *,
        reason: MoveReason = MoveReason.RULE,
        allow_replacement: bool = True,
    ) -> Zone:
        state = self._context._require_state()
        instance = state.cards[card_id]
        definition = self._context._definition(card_id)
        all_replacements = self._replacement_definitions(definition)
        applicable = tuple(
            (index, item)
            for index, item in enumerate(all_replacements)
            if allow_replacement
            and instance.zone is Zone.BATTLEFIELD
            and destination is Zone.DISCARD
            and reason in item.applies_to
            and (
                item.minimum_strength_after is None
                or self._context._current_strength(card_id) + item.strength_delta
                >= item.minimum_strength_after
            )
        )
        replacement: MoveReplacementDefinition | None
        if definition.deferred_replacement_choice and len(applicable) > 1:
            selected_index = self._context._consume_replacement_replay_choice()
            if selected_index is not None:
                by_index = dict(applicable)
                if selected_index not in by_index:
                    raise InvariantViolation(
                        "La sustitución reproducida ya no resulta aplicable"
                    )
                replacement = by_index[selected_index]
            else:
                raise MoveReplacementChoiceRequired(
                    instance.controller_id,
                    card_id,
                    reason,
                    tuple(index for index, _ in applicable),
                    tuple(item.destination for _, item in applicable),
                )
        elif definition.player_orders_replacements:
            ordered = self._ordered_replacements(card_id, definition)
            replacement = next(
                (item for item in ordered if item in {entry[1] for entry in applicable}),
                None,
            )
        else:
            replacement = next(
                (
                    item
                    for item in self._ordered_replacements(card_id, definition)
                    if item in {entry[1] for entry in applicable}
                ),
                None,
            )
        if (
            allow_replacement
            and instance.zone is Zone.BATTLEFIELD
            and destination is Zone.DISCARD
            and replacement is not None
        ):
            after_strength = self._context._current_strength(card_id) + replacement.strength_delta
            if (
                replacement.minimum_strength_after is None
                or after_strength >= replacement.minimum_strength_after
            ):
                if replacement.destination is Zone.BATTLEFIELD:
                    instance.strength_modifier += replacement.strength_delta
                    instance.exhausted = replacement.enters_exhausted
                    if replacement.clear_damage:
                        instance.damage = 0
                    self._context._emit(
                        "MOVE_REPLACED",
                        instance.controller_id,
                        card_id,
                        {
                            "reason": reason.name,
                            "destination": Zone.BATTLEFIELD.name,
                        },
                    )
                    return Zone.BATTLEFIELD
                destination = replacement.destination
                destination_player = instance.owner_id
                self._context._emit(
                    "MOVE_REPLACED",
                    instance.controller_id,
                    card_id,
                    {"reason": reason.name, "destination": destination.name},
                )
        if instance.zone is Zone.BATTLEFIELD and destination is not Zone.BATTLEFIELD:
            for other in state.cards.values():
                if other.attached_to == card_id:
                    other.attached_to = None
                    if state.status is MatchStatus.RUNNING:
                        self._context._emit("EQUIPMENT_DETACHED", card_id=other.instance_id,
                                   payload={"former_target": card_id})
            state.timed_modifiers = [
                modifier
                for modifier in state.timed_modifiers
                if modifier.target_card_id != card_id
            ]
            state.text_patches = [
                patch for patch in state.text_patches if patch.target_card_id != card_id
            ]
        found = False
        for player in state.players.values():
            for zone_cards in player.zones.values():
                if card_id in zone_cards:
                    zone_cards.remove(card_id)
                    found = True
                    break
            if found:
                break
        if card_id in state.resolution:
            state.resolution.remove(card_id)
            found = True
        if card_id in state.void:
            state.void.remove(card_id)
            found = True
        if not found:
            raise InvariantViolation(f"La carta {card_id} no estaba en ninguna zona")

        instance.zone = destination
        if destination is Zone.RESOLUTION:
            state.resolution.append(card_id)
        elif destination is Zone.VOID:
            state.void.append(card_id)
        elif destination in state.players[destination_player].zones:
            state.players[destination_player].zones[destination].append(card_id)
        else:
            raise ValueError(f"Zona de destino no almacenable: {destination.name}")
        if destination is not Zone.BATTLEFIELD:
            instance.controller_id = instance.owner_id
            instance.attached_to = None
            instance.exhausted = False
            instance.damage = 0
            instance.strength_modifier = 0
            instance.damage_prevention = 0
            instance.activated_this_turn.clear()
            instance.transformed_as_creature = False
            instance.creature_form_expires_turn_serial = None
            instance.regeneration_shields = 0
            instance.regeneration_blocked_until_state_check = False
            instance.overridden_definition_id = None
            instance.definition_override_expires_turn_serial = None
            instance.replacement_order = ()
            state.control_changes = [
                change for change in state.control_changes if change.card_id != card_id
            ]
        return destination
