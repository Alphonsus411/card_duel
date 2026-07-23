from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

from ..domain.enums import Phase
from ..engine.commands import GameCommand


@dataclass(frozen=True)
class PlayerObservation:
    player_id: str
    active_player_id: str
    phase: Phase
    own_hand: tuple[str, ...]
    own_steps: int
    own_wounds: int
    opponent_hand_sizes: dict[str, int]
    public_event_count: int
    own_battlefield: tuple[str, ...] = ()
    opponent_battlefields: dict[str, tuple[str, ...]] | None = None
    stack_size: int = 0
    stack_items: tuple[tuple[str, str | None, str], ...] = ()
    pending_triggers: tuple[tuple[str, str | None, str, bool], ...] = ()
    suppressed_phases: tuple[tuple[str, Phase], ...] = ()
    pending_search_item_id: str | None = None
    searchable_card_ids: tuple[str, ...] = ()
    replacement_orders: tuple[tuple[str, tuple[int, ...]], ...] = ()
    pending_replacement_card_id: str | None = None
    replacement_destinations: tuple[tuple[int, str], ...] = ()


@dataclass(frozen=True)
class DecisionRequest:
    observation: PlayerObservation
    legal_actions: Sequence[GameCommand]


class PlayerController(Protocol):
    def choose_action(self, request: DecisionRequest) -> GameCommand:
        """Devuelve una de las acciones legales propuestas por el motor."""
        ...
