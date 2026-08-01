from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from ..catalog import CardCatalogReader
from ..domain.enums import EffectDuration, EffectKind, MoveReason, TargetMode, Zone
from ..domain.errors import UnsupportedEffectError
from ..domain.models import (
    AppliedTextPatch,
    CardDefinition,
    ControlChange,
    EffectDefinition,
    GameState,
    PhaseSuppression,
    PlayerState,
    StackItem,
    TargetAllocation,
    TextPatchDefinition,
    TimedModifier,
    ZoneTarget,
)


class EffectContext(Protocol):
    """Operaciones autoritativas que necesita la resolución de efectos."""

    catalog: CardCatalogReader

    def _require_running_state(self) -> GameState: ...
    def _effect_amount(self, effect: EffectDefinition, x_value: int) -> int: ...
    def _definition(self, card_id: str) -> CardDefinition: ...
    def _card_can_be_targeted(self, source: CardDefinition, target_id: str, from_ability: bool) -> bool: ...
    def _draw(self, player_id: str, amount: int) -> None: ...
    def _deal_wounds(self, player_id: str, amount: int, source_card_id: str | None = None) -> None: ...
    def _deal_damage(self, card_id: str, amount: int, source_card_id: str | None = None, *, allows_regeneration: bool = True) -> None: ...
    def _destroy_permanent(self, card_id: str, reason: MoveReason, *, allows_regeneration: bool = True) -> bool: ...
    def _move_card(self, card_id: str, destination: Zone, destination_player: str, *, reason: MoveReason = MoveReason.RULE, allow_replacement: bool = True) -> Zone: ...
    def _shuffle_zone(self, target: ZoneTarget) -> None: ...
    def _set_controller(self, card_id: str, controller_id: str) -> None: ...
    def _apply_text_patch_to_definition(self, definition: CardDefinition, patch: TextPatchDefinition) -> CardDefinition: ...
    def _emit(self, event_type: str, player_id: str | None = None, card_id: str | None = None, payload: dict[str, object] | None = None) -> None: ...


EffectHandler = Callable[[EffectDefinition, StackItem, str, PlayerState | None, ZoneTarget | None], None]


class EffectManager:
    """Resuelve el vocabulario cerrado de efectos sobre el contexto del motor."""

    def __init__(self, context: EffectContext) -> None:
        self._context = context
        self._handlers: dict[EffectKind, EffectHandler] = {
            EffectKind.DEAL_WOUNDS: self._deal_wounds,
            EffectKind.HEAL_WOUNDS: self._heal_wounds,
            EffectKind.GAIN_STEPS: self._gain_steps,
            EffectKind.DRAW_CARDS: self._draw_cards,
            EffectKind.DEAL_DAMAGE: self._deal_damage,
            EffectKind.MODIFY_STRENGTH: self._modify_strength,
            EffectKind.TAP: self._tap,
            EffectKind.UNTAP: self._untap,
            EffectKind.DESTROY: self._destroy,
            EffectKind.PREVENT_WOUNDS: self._prevent_wounds,
            EffectKind.PREVENT_DAMAGE: self._prevent_damage,
            EffectKind.BECOME_CREATURE: self._become_creature,
            EffectKind.DEAL_HARM: self._deal_harm,
            EffectKind.MOVE_CARDS: self._move_cards,
            EffectKind.ADD_REGENERATION: self._add_regeneration,
            EffectKind.SKIP_PHASE: self._skip_phase,
            EffectKind.SEARCH_ZONE: self._search_zone,
            EffectKind.SHUFFLE_ZONE: self._shuffle,
            EffectKind.CHANGE_CONTROL: self._change_control,
            EffectKind.COPY_DEFINITION: self._copy_definition,
            EffectKind.TRANSFORM_DEFINITION: self._transform_definition,
            EffectKind.MODIFY_TEXT: self._modify_text,
        }

    @property
    def supported_kinds(self) -> frozenset[EffectKind]:
        return frozenset(self._handlers)

    def apply(self, effect: EffectDefinition, item: StackItem, selected: str | ZoneTarget | TargetAllocation | None = None) -> None:
        state = self._context._require_running_state()
        amount = self._context._effect_amount(effect, item.x_value)
        if effect.target is TargetMode.CHOSEN_ZONE:
            if not isinstance(selected, ZoneTarget) or selected.player_id not in state.players:
                self._fizzle(item, selected, "invalid_target")
                return
            target_id, player, zone_target = selected.player_id, None, selected
        elif effect.target is TargetMode.CHOSEN_ENTITY:
            if not isinstance(selected, TargetAllocation):
                self._fizzle(item, selected, "invalid_target")
                return
            self._deal_allocated_harm(effect, item, selected)
            return
        elif effect.target in {TargetMode.SELF, TargetMode.CHOSEN_PLAYER}:
            candidate = item.controller_id if effect.target is TargetMode.SELF else selected
            if not isinstance(candidate, str) or candidate not in state.players:
                self._fizzle(item, selected, "invalid_target")
                return
            target_id, player, zone_target = candidate, state.players[candidate], None
        else:
            candidate = item.source_card_id if effect.target is TargetMode.SOURCE else selected
            if not isinstance(candidate, str) or candidate not in state.cards or state.cards[candidate].zone is not Zone.BATTLEFIELD:
                self._fizzle(item, selected, "invalid_target")
                return
            target_id, zone_target = candidate, None
            if effect.target is TargetMode.CHOSEN_PERMANENT and not self._context._card_can_be_targeted(
                self._context._definition(item.source_card_id), target_id, item.ability_id is not None
            ):
                self._fizzle(item, target_id, "immune")
                return
            player = None
        handler = self._handlers.get(effect.kind)
        if handler is None:
            raise UnsupportedEffectError(f"Efecto no soportado: {effect.kind!r}")
        # Los gestores mutan el único GameState propiedad del contexto; no guardan estado.
        handler(effect, item, target_id, player, zone_target)

    def _fizzle(self, item: StackItem, target: object, reason: str) -> None:
        payload: dict[str, object] = {"reason": reason}
        if isinstance(target, str):
            payload["target"] = target
        self._context._emit("EFFECT_FIZZLED", item.controller_id, item.source_card_id, payload)

    def _deal_allocated_harm(self, effect: EffectDefinition, item: StackItem, allocation: TargetAllocation) -> None:
        state = self._context._require_running_state()
        target_id = allocation.target_id
        if target_id in state.players:
            self._context._deal_wounds(target_id, allocation.amount, item.source_card_id)
        elif target_id not in state.cards or state.cards[target_id].zone is not Zone.BATTLEFIELD:
            self._fizzle(item, target_id, "invalid_target")
        elif not self._context._card_can_be_targeted(self._context._definition(item.source_card_id), target_id, item.ability_id is not None):
            self._fizzle(item, target_id, "immune")
        else:
            self._context._deal_damage(target_id, allocation.amount, item.source_card_id, allows_regeneration=effect.allows_regeneration)

    def _deal_wounds(self, effect: EffectDefinition, item: StackItem, target: str, player: PlayerState | None, zone_target: ZoneTarget | None) -> None:
        self._context._deal_wounds(target, self._context._effect_amount(effect, item.x_value), item.source_card_id)

    def _heal_wounds(self, effect: EffectDefinition, item: StackItem, target: str, player: PlayerState | None, zone_target: ZoneTarget | None) -> None:
        assert player is not None
        actual = min(player.wounds, self._context._effect_amount(effect, item.x_value))
        player.wounds -= actual
        self._context._emit("WOUNDS_HEALED", target, payload={"amount": actual})

    def _gain_steps(self, effect: EffectDefinition, item: StackItem, target: str, player: PlayerState | None, zone_target: ZoneTarget | None) -> None:
        assert player is not None
        amount = self._context._effect_amount(effect, item.x_value)
        player.steps += amount
        self._context._emit("STEPS_GAINED", target, payload={"amount": amount})

    def _draw_cards(self, effect: EffectDefinition, item: StackItem, target: str, player: PlayerState | None, zone_target: ZoneTarget | None) -> None:
        self._context._draw(target, self._context._effect_amount(effect, item.x_value))

    def _prevent_wounds(self, effect: EffectDefinition, item: StackItem, target: str, player: PlayerState | None, zone_target: ZoneTarget | None) -> None:
        assert player is not None
        amount = self._context._effect_amount(effect, item.x_value)
        player.wound_prevention += amount
        self._context._emit("WOUND_PREVENTION_ADDED", target, payload={"amount": amount})

    def _deal_damage(self, effect: EffectDefinition, item: StackItem, target: str, player: PlayerState | None, zone_target: ZoneTarget | None) -> None:
        self._context._deal_damage(target, self._context._effect_amount(effect, item.x_value), item.source_card_id, allows_regeneration=effect.allows_regeneration)

    def _prevent_damage(self, effect: EffectDefinition, item: StackItem, target: str, player: PlayerState | None, zone_target: ZoneTarget | None) -> None:
        amount = self._context._effect_amount(effect, item.x_value)
        self._context._require_running_state().cards[target].damage_prevention += amount
        self._context._emit("DAMAGE_PREVENTION_ADDED", card_id=target, payload={"amount": amount})

    def _add_regeneration(self, effect: EffectDefinition, item: StackItem, target: str, player: PlayerState | None, zone_target: ZoneTarget | None) -> None:
        amount = self._context._effect_amount(effect, item.x_value)
        self._context._require_running_state().cards[target].regeneration_shields += amount
        self._context._emit("REGENERATION_ADDED", card_id=target, payload={"amount": amount})

    def _modify_strength(self, effect: EffectDefinition, item: StackItem, target: str, player: PlayerState | None, zone_target: ZoneTarget | None) -> None:
        state = self._context._require_running_state()
        amount = self._context._effect_amount(effect, item.x_value)
        if effect.duration is EffectDuration.END_OF_TURN:
            state.timed_modifiers.append(TimedModifier(f"modifier-{len(state.event_log) + 1:06d}", target, amount, state.turn_serial))
        else:
            state.cards[target].strength_modifier += amount
        self._context._emit("STRENGTH_MODIFIED", card_id=target, payload={"amount": amount, "duration": effect.duration.name})

    def _tap(self, effect: EffectDefinition, item: StackItem, target: str, player: PlayerState | None, zone_target: ZoneTarget | None) -> None:
        self._context._require_running_state().cards[target].exhausted = True
        self._context._emit("PERMANENT_TAPPED", card_id=target)

    def _untap(self, effect: EffectDefinition, item: StackItem, target: str, player: PlayerState | None, zone_target: ZoneTarget | None) -> None:
        self._context._require_running_state().cards[target].exhausted = False
        self._context._emit("PERMANENT_UNTAPPED", card_id=target)

    def _destroy(self, effect: EffectDefinition, item: StackItem, target: str, player: PlayerState | None, zone_target: ZoneTarget | None) -> None:
        self._context._destroy_permanent(target, MoveReason.DESTROY, allows_regeneration=effect.allows_regeneration)

    def _become_creature(self, effect: EffectDefinition, item: StackItem, target: str, player: PlayerState | None, zone_target: ZoneTarget | None) -> None:
        state = self._context._require_running_state(); instance = state.cards[target]
        instance.transformed_as_creature = True
        instance.creature_form_expires_turn_serial = state.turn_serial if effect.duration is EffectDuration.END_OF_TURN else None
        self._context._emit("PERMANENT_BECAME_CREATURE", card_id=target, payload={"duration": effect.duration.name})

    def _change_control(self, effect: EffectDefinition, item: StackItem, target: str, player: PlayerState | None, zone_target: ZoneTarget | None) -> None:
        state = self._context._require_running_state(); previous = state.cards[target].controller_id
        self._context._set_controller(target, item.controller_id)
        if effect.duration is EffectDuration.END_OF_TURN:
            state.control_changes.append(ControlChange(target, previous, state.turn_serial))
        self._context._emit("CONTROL_CHANGED", item.controller_id, target, {"previous_controller": previous, "duration": effect.duration.name})

    def _copy_definition(self, effect: EffectDefinition, item: StackItem, target: str, player: PlayerState | None, zone_target: ZoneTarget | None) -> None:
        state = self._context._require_running_state(); source = state.cards[item.source_card_id]
        source.overridden_definition_id = self._context._definition(target).card_id
        source.replacement_order = ()
        source.definition_override_expires_turn_serial = state.turn_serial if effect.duration is EffectDuration.END_OF_TURN else None
        self._context._emit("DEFINITION_COPIED", item.controller_id, item.source_card_id, {"copied_from": target, "duration": effect.duration.name})

    def _transform_definition(self, effect: EffectDefinition, item: StackItem, target: str, player: PlayerState | None, zone_target: ZoneTarget | None) -> None:
        assert effect.transform_definition_id is not None
        if effect.transform_definition_id not in self._context.catalog:
            self._context._emit("EFFECT_FIZZLED", item.controller_id, item.source_card_id, {"reason": "unknown_transform_definition"}); return
        state = self._context._require_running_state(); instance = state.cards[target]
        instance.overridden_definition_id = effect.transform_definition_id; instance.replacement_order = ()
        instance.definition_override_expires_turn_serial = state.turn_serial if effect.duration is EffectDuration.END_OF_TURN else None
        self._context._emit("PERMANENT_TRANSFORMED", item.controller_id, target, {"definition_id": effect.transform_definition_id, "duration": effect.duration.name})

    def _modify_text(self, effect: EffectDefinition, item: StackItem, target: str, player: PlayerState | None, zone_target: ZoneTarget | None) -> None:
        assert effect.text_patch is not None
        try:
            self._context._apply_text_patch_to_definition(self._context._definition(target), effect.text_patch)
        except (IndexError, ValueError):
            self._context._emit("EFFECT_FIZZLED", item.controller_id, item.source_card_id, {"target": target, "reason": "invalid_text_patch"}); return
        state = self._context._require_running_state()
        state.text_patches.append(AppliedTextPatch(f"text-patch-{len(state.event_log) + 1:06d}", target, effect.text_patch, state.turn_serial if effect.duration is EffectDuration.END_OF_TURN else None))
        self._context._emit("CARD_TEXT_MODIFIED", item.controller_id, target, {"duration": effect.duration.name})

    def _skip_phase(self, effect: EffectDefinition, item: StackItem, target: str, player: PlayerState | None, zone_target: ZoneTarget | None) -> None:
        assert player is not None and effect.phase is not None
        state = self._context._require_running_state()
        state.phase_suppressions.append(PhaseSuppression(target, effect.phase, state.turn_serial if effect.duration is EffectDuration.END_OF_TURN else None, 1 if effect.duration is EffectDuration.NEXT_OCCURRENCE else None))
        self._context._emit("PHASE_SUPPRESSION_ADDED", target, payload={"phase": effect.phase.name, "duration": effect.duration.name})

    def _move_cards(self, effect: EffectDefinition, item: StackItem, target: str, player: PlayerState | None, zone_target: ZoneTarget | None) -> None:
        assert effect.destination_zone is not None
        state = self._context._require_running_state(); assert zone_target is not None
        moved = tuple(state.players[target].zones[zone_target.zone][-self._context._effect_amount(effect, item.x_value):])
        for card_id in moved:
            self._context._move_card(card_id, effect.destination_zone, target, reason=MoveReason.RULE)
        self._context._emit("ZONE_CARDS_MOVED", item.controller_id, item.source_card_id, {"target_player": target, "source_zone": zone_target.zone.name, "destination_zone": effect.destination_zone.name, "count": len(moved)})

    def _shuffle(self, effect: EffectDefinition, item: StackItem, target: str, player: PlayerState | None, zone_target: ZoneTarget | None) -> None:
        assert zone_target is not None
        self._context._shuffle_zone(zone_target)

    def _search_zone(self, effect: EffectDefinition, item: StackItem, target: str, player: PlayerState | None, zone_target: ZoneTarget | None) -> None:
        # StackManager pausa y reanuda las búsquedas; este handler completa el registro.
        return

    def _deal_harm(self, effect: EffectDefinition, item: StackItem, target: str, player: PlayerState | None, zone_target: ZoneTarget | None) -> None:
        raise UnsupportedEffectError("DEAL_HARM requiere TargetAllocation")
