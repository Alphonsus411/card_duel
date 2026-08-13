from __future__ import annotations

from typing import Protocol

from ..domain.models import (
    CardDefinition,
    CompositeCost,
    DynamicCostDefinition,
    EffectDefinition,
    GameState,
    XCostDefinition,
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

    def _option_effect_amount(
        self, effect: EffectDefinition, x_value: int
    ) -> int: ...


class ActionOptionResolver:
    """Resuelve opciones mediante un contexto autoritativo y explícito."""

    def __init__(self, context: ActionOptionContext) -> None:
        self._context = context
