from __future__ import annotations

from dataclasses import dataclass

from ..domain.models import TargetAllocation, ZoneTarget


@dataclass(frozen=True)
class GameCommand:
    player_id: str


@dataclass(frozen=True)
class AdvancePhase(GameCommand):
    pass


@dataclass(frozen=True)
class DiscardCards(GameCommand):
    card_ids: tuple[str, ...]


@dataclass(frozen=True)
class TransmutePermanent(GameCommand):
    card_id: str


@dataclass(frozen=True)
class Concede(GameCommand):
    pass


@dataclass(frozen=True)
class PlayCard(GameCommand):
    card_id: str
    chosen_player_ids: tuple[str, ...] = ()
    chosen_card_ids: tuple[str, ...] = ()
    chosen_zone_targets: tuple[ZoneTarget, ...] = ()
    allocations: tuple[TargetAllocation, ...] = ()
    cost_option_index: int | None = None
    discard_card_ids: tuple[str, ...] = ()
    sacrifice_card_ids: tuple[str, ...] = ()
    x_value: int | None = None


@dataclass(frozen=True)
class PassPriority(GameCommand):
    pass


@dataclass(frozen=True)
class DeclareAttackers(GameCommand):
    attacker_ids: tuple[str, ...]
    defending_player_id: str


@dataclass(frozen=True)
class DeclareBlockers(GameCommand):
    assignments: tuple[tuple[str, tuple[str, ...]], ...] = ()


@dataclass(frozen=True)
class ResolveCombat(GameCommand):
    pass


@dataclass(frozen=True)
class ActivateAbility(GameCommand):
    source_card_id: str
    ability_id: str
    chosen_player_ids: tuple[str, ...] = ()
    chosen_card_ids: tuple[str, ...] = ()
    discard_card_ids: tuple[str, ...] = ()
    sacrifice_card_ids: tuple[str, ...] = ()
    chosen_zone_targets: tuple[ZoneTarget, ...] = ()
    allocations: tuple[TargetAllocation, ...] = ()
    x_value: int | None = None


@dataclass(frozen=True)
class EquipCard(GameCommand):
    equipment_id: str
    creature_id: str


@dataclass(frozen=True)
class DrainSteps(GameCommand):
    amount: int


@dataclass(frozen=True)
class DeclareChallenge(GameCommand):
    challenger_id: str
    challenged_id: str
    defending_player_id: str


@dataclass(frozen=True)
class OrderTriggeredAbilities(GameCommand):
    resolution_order: tuple[str, ...]


@dataclass(frozen=True)
class ChooseTriggeredTargets(GameCommand):
    item_id: str
    chosen_player_ids: tuple[str, ...] = ()
    chosen_card_ids: tuple[str, ...] = ()
    chosen_zone_targets: tuple[ZoneTarget, ...] = ()
    allocations: tuple[TargetAllocation, ...] = ()


@dataclass(frozen=True)
class ResolveSearchChoice(GameCommand):
    selected_card_ids: tuple[str, ...]


@dataclass(frozen=True)
class SetReplacementOrder(GameCommand):
    card_id: str
    ordered_indices: tuple[int, ...]


@dataclass(frozen=True)
class ResolveMoveReplacement(GameCommand):
    replacement_index: int
