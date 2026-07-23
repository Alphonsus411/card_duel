from __future__ import annotations

import random
from typing import Any
from ..domain.enums import EffectKind, MoveReason, TargetMode, TriggerKind, Zone
from ..domain.errors import IllegalAction
from ..domain.models import PendingSearch, StackItem, ZoneTarget
from .commands import ResolveSearchChoice


class _EngineComponent:
    """Componente ligado a un motor; GameState sigue siendo la única autoridad."""
    def __init__(self, engine: Any) -> None:
        object.__setattr__(self, "_engine", engine)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._engine, name)

    def __setattr__(self, name: str, value: Any) -> None:
        setattr(self._engine, name, value)


class StackManager(_EngineComponent):
    def _pass_priority(self, player_id: str) -> None:
        state = self._require_running_state()
        if player_id != state.priority_player_id:
            raise IllegalAction("El jugador no posee prioridad")
        state.consecutive_passes += 1
        self._emit("PRIORITY_PASSED", player_id)
        if state.consecutive_passes < len(state.turn_order):
            state.priority_player_id = self._next_player(player_id)
            return

        state.consecutive_passes = 0
        if state.stack:
            self._resolve_top_stack()
            state.phase_priority_complete = False
        else:
            state.phase_priority_complete = True
            self._emit("PRIORITY_WINDOW_CLOSED", state.active_player_id)
        if not state.pending_triggers and state.pending_search is None:
            state.priority_player_id = state.active_player_id

    def _resolve_top_stack(self) -> None:
        state = self._require_running_state()
        item = state.stack.pop()
        self._continue_stack_resolution(item, 0)

    def _continue_stack_resolution(self, item: StackItem, start_index: int) -> None:
        state = self._require_running_state()
        for effect_index in range(start_index, len(item.effects)):
            effect = item.effects[effect_index]
            if effect.kind is EffectKind.SEARCH_ZONE:
                if len(item.chosen_zone_targets) != 1:
                    self._emit(
                        "EFFECT_FIZZLED",
                        item.controller_id,
                        item.source_card_id,
                        {"reason": "search_requires_one_zone"},
                    )
                    continue
                zone_target = item.chosen_zone_targets[0]
                eligible = tuple(
                    card_id
                    for card_id in state.players[zone_target.player_id].zones[
                        zone_target.zone
                    ]
                    if effect.search_filter is None
                    or effect.search_filter.matches(self._definition(card_id))
                )
                maximum = min(effect.selection_maximum, len(eligible))
                if maximum < effect.selection_minimum:
                    self._emit(
                        "SEARCH_FAILED",
                        item.controller_id,
                        item.source_card_id,
                        {"reason": "not_enough_eligible_cards"},
                    )
                    if effect.shuffle_after_search:
                        self._shuffle_zone(zone_target)
                    continue
                state.pending_search = PendingSearch(
                    stack_item=item,
                    next_effect_index=effect_index + 1,
                    chooser_id=item.controller_id,
                    zone_target=zone_target,
                    eligible_card_ids=eligible,
                    minimum=effect.selection_minimum,
                    maximum=maximum,
                    destination_zone=effect.destination_zone,
                    shuffle_after=effect.shuffle_after_search,
                    reveal_selection=effect.reveal_search_selection,
                )
                state.priority_player_id = item.controller_id
                self._emit(
                    "SEARCH_CHOICE_REQUESTED",
                    item.controller_id,
                    item.source_card_id,
                    {"minimum": effect.selection_minimum, "maximum": maximum},
                )
                return
            targets: tuple[object, ...]
            if effect.target is TargetMode.CHOSEN_PLAYER:
                targets = item.chosen_player_ids
            elif effect.target is TargetMode.CHOSEN_PERMANENT:
                targets = item.chosen_card_ids
            elif effect.target is TargetMode.CHOSEN_ZONE:
                targets = item.chosen_zone_targets
            elif effect.target is TargetMode.CHOSEN_ENTITY:
                targets = item.allocations
            else:
                targets = (None,)
            for target_id in targets:
                self._apply_effect(effect, item, target_id)
        if item.destination_on_resolve is not None:
            instance = state.cards[item.source_card_id]
            destination_player = (
                item.controller_id
                if item.destination_on_resolve is Zone.BATTLEFIELD
                else instance.owner_id
            )
            self._move_card(item.source_card_id, item.destination_on_resolve, destination_player)
            if item.destination_on_resolve is Zone.BATTLEFIELD:
                self._queue_triggered_abilities(
                    item.source_card_id, TriggerKind.ON_ENTER_BATTLEFIELD
                )
        self._run_state_based_actions()
        self._emit(
            "STACK_ITEM_RESOLVED",
            item.controller_id,
            item.source_card_id,
            {"remaining": len(state.stack)},
        )

    def _resolve_search_choice(self, command: ResolveSearchChoice) -> None:
        state = self._require_running_state()
        search = state.pending_search
        if search is None or command.player_id != search.chooser_id:
            raise IllegalAction("No existe una búsqueda propia pendiente")
        if len(command.selected_card_ids) != len(set(command.selected_card_ids)):
            raise IllegalAction("Una carta no puede elegirse dos veces")
        if not search.minimum <= len(command.selected_card_ids) <= search.maximum:
            raise IllegalAction("El número de cartas elegidas no es válido")
        if any(card_id not in search.eligible_card_ids for card_id in command.selected_card_ids):
            raise IllegalAction("La búsqueda contiene una carta no elegible")
        source_zone = state.players[search.zone_target.player_id].zones[
            search.zone_target.zone
        ]
        if any(card_id not in source_zone for card_id in command.selected_card_ids):
            raise IllegalAction("La zona cambió y una carta elegida ya no está disponible")
        for card_id in command.selected_card_ids:
            self._move_card(
                card_id,
                search.destination_zone,
                search.zone_target.player_id,
                reason=MoveReason.RULE,
            )
        if search.shuffle_after:
            self._shuffle_zone(search.zone_target)
        state.pending_search = None
        self._emit(
            "SEARCH_COMPLETED",
            command.player_id,
            search.stack_item.source_card_id,
            (
                {"selected_card_ids": command.selected_card_ids}
                if search.reveal_selection
                else {"selected_count": len(command.selected_card_ids)}
            ),
        )
        self._continue_stack_resolution(search.stack_item, search.next_effect_index)
        if state.pending_search is None and not state.pending_triggers:
            state.priority_player_id = state.active_player_id
            state.phase_priority_complete = False

    def _shuffle_zone(self, target: ZoneTarget) -> None:
        state = self._require_running_state()
        cards = state.players[target.player_id].zones[target.zone]
        random.Random(
            state.random_seed + state.turn_serial * 10_000 + len(state.event_log)
        ).shuffle(cards)
        self._emit(
            "ZONE_SHUFFLED",
            target.player_id,
            payload={"zone": target.zone.name, "count": len(cards)},
        )
