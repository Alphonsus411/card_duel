from __future__ import annotations

from collections.abc import Iterable, Iterator
from itertools import combinations, islice
from typing import Protocol

from ..domain.enums import TargetMode, Zone
from ..domain.models import (
    CardDefinition,
    CompositeCost,
    DynamicCostDefinition,
    EffectDefinition,
    GameState,
    TargetAllocation,
    XCostDefinition,
    ZoneTarget,
)


class ActionOptionContext(Protocol):
    """Consultas mínimas necesarias para resolver opciones de una acción."""

    @property
    def _option_state(self) -> GameState: ...

    @property
    def _option_enumeration_limit(self) -> int: ...

    def _option_resolve_dynamic_cost(
        self, definition: DynamicCostDefinition, player_id: str
    ) -> CompositeCost: ...

    def _option_resolve_x_cost(
        self, definition: XCostDefinition, x_value: int
    ) -> CompositeCost: ...

    def _option_card_can_be_targeted(
        self,
        source_definition: CardDefinition | None,
        target_card_id: str,
        from_ability: bool = False,
        source_card_id: str | None = None,
    ) -> bool: ...

    def _option_effect_amount(self, effect: EffectDefinition, x_value: int) -> int: ...


class ActionOptionResolver:
    """Resuelve opciones mediante un contexto autoritativo y explícito."""

    def __init__(self, context: ActionOptionContext) -> None:
        self._context = context

    def card_cost_options(
        self, definition: CardDefinition, player_id: str
    ) -> tuple[tuple[int | None, int | None, CompositeCost], ...]:
        result: list[tuple[int | None, int | None, CompositeCost]] = []
        if definition.x_cost is not None:
            result.extend(
                (
                    None,
                    x_value,
                    self._context._option_resolve_x_cost(definition.x_cost, x_value),
                )
                for x_value in islice(
                    range(definition.x_cost.minimum, definition.x_cost.maximum + 1),
                    self._context._option_enumeration_limit,
                )
            )
        else:
            normal = (
                self._context._option_resolve_dynamic_cost(
                    definition.dynamic_cost, player_id
                )
                if definition.dynamic_cost is not None
                else CompositeCost(steps=definition.cost)
            )
            result.append((None, None, normal))
        alternatives: list[CompositeCost] = [*definition.alternative_costs]
        alternatives.extend(
            self._context._option_resolve_dynamic_cost(item, player_id)
            for item in definition.dynamic_alternative_costs
        )
        result.extend((index, None, cost) for index, cost in enumerate(alternatives))
        first_x_index = len(alternatives)
        for offset, x_cost in enumerate(definition.x_alternative_costs):
            result.extend(
                (
                    first_x_index + offset,
                    x_value,
                    self._context._option_resolve_x_cost(x_cost, x_value),
                )
                for x_value in islice(
                    range(x_cost.minimum, x_cost.maximum + 1),
                    self._context._option_enumeration_limit,
                )
            )
        return tuple(result)

    def zone_target_selections(
        self, effects: tuple[EffectDefinition, ...]
    ) -> tuple[tuple[ZoneTarget, ...], ...]:
        state = self._context._option_state
        candidates = tuple(
            ZoneTarget(player_id, zone)
            for player_id, player in state.players.items()
            for zone in player.zones
        )
        targeted = tuple(
            effect for effect in effects if effect.target is TargetMode.CHOSEN_ZONE
        )
        if not targeted:
            return ((),)
        minimum = max(effect.minimum_targets for effect in targeted)
        maximum = min(effect.maximum_targets for effect in targeted)
        return tuple(
            islice(
                (
                    tuple(selection)
                    for count in range(minimum, min(maximum, len(candidates)) + 1)
                    for selection in combinations(candidates, count)
                ),
                self._context._option_enumeration_limit,
            )
        )

    def allocation_selections(
        self,
        effects: tuple[EffectDefinition, ...],
        source_definition: CardDefinition,
        *,
        from_ability: bool = False,
        source_card_id: str | None = None,
        x_value: int = 0,
    ) -> tuple[tuple[TargetAllocation, ...], ...]:
        state = self._context._option_state
        effect = next((item for item in effects if item.distributed), None)
        if effect is None:
            return ((),)
        candidates = [*state.turn_order]
        candidates.extend(
            card_id
            for player in state.players.values()
            for card_id in player.zones[Zone.BATTLEFIELD]
            if self._context._option_card_can_be_targeted(
                source_definition, card_id, from_ability, source_card_id
            )
        )
        results: list[tuple[TargetAllocation, ...]] = []
        for count in range(
            effect.minimum_targets, min(effect.maximum_targets, len(candidates)) + 1
        ):
            for selected in combinations(candidates, count):
                for amounts in self.positive_compositions(
                    self._context._option_effect_amount(effect, x_value), count
                ):
                    results.append(
                        tuple(
                            TargetAllocation(target_id, amount)
                            for target_id, amount in zip(selected, amounts, strict=True)
                        )
                    )
                    if len(results) >= self._context._option_enumeration_limit:
                        return tuple(results)
        return tuple(results)

    def positive_compositions(
        self, total: int, parts: int
    ) -> Iterator[tuple[int, ...]]:
        if parts == 1:
            if total >= 1:
                yield (total,)
            return
        for first in range(1, total - parts + 2):
            for rest in self.positive_compositions(total - first, parts - 1):
                yield (first, *rest)

    def target_selections(
        self,
        effects: tuple[EffectDefinition, ...],
        mode: TargetMode,
        candidates: Iterable[str],
    ) -> tuple[tuple[str, ...], ...]:
        targeted = tuple(effect for effect in effects if effect.target is mode)
        if not targeted:
            return ((),)
        minimum = max(effect.minimum_targets for effect in targeted)
        maximum = min(effect.maximum_targets for effect in targeted)
        pool = tuple(candidates)
        maximum = min(maximum, len(pool))
        return tuple(
            islice(
                (
                    tuple(selection)
                    for count in range(minimum, maximum + 1)
                    for selection in combinations(pool, count)
                ),
                self._context._option_enumeration_limit,
            )
        )
