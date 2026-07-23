import unittest
from copy import deepcopy

from card_duel_engine.domain.enums import MatchStatus, MoveReason, Phase, TriggerKind, Zone
from card_duel_engine.domain.errors import IllegalAction
from card_duel_engine.domain.models import (
    CardDefinition, EffectDefinition, GameState, PlayerState, StackItem,
    TargetAllocation, ZoneTarget,
)
from card_duel_engine.engine.combat import CombatManager
from card_duel_engine.engine.commands import DeclareAttackers, GameCommand
from card_duel_engine.engine.stack import StackManager
from card_duel_engine.engine.zones import ZoneManager
from card_duel_engine.rules.config import RuleSet
from card_duel_engine import GameEngine


def minimal_state() -> GameState:
    return GameState(
        ruleset_id="base",
        ruleset_version="0.13.0",
        players={"A": PlayerState("A"), "B": PlayerState("B")},
        turn_order=("A", "B"),
        cards={},
        priority_player_id="A",
        phase=Phase.COMBAT,
        status=MatchStatus.RUNNING,
    )


class MinimalCombatContext:
    def __init__(self) -> None:
        self.state = minimal_state()

    def _require_running_state(self) -> GameState:
        return self.state

    def _is_ready_creature(self, card_id: str) -> bool: return False
    def _is_lord_creature(self, card_id: str) -> bool: return False
    def _is_creature(self, card_id: str) -> bool: return False
    def _current_strength(self, card_id: str) -> int: return 0
    def _deal_damage(self, card_id: str, amount: int, source_card_id: str | None = None) -> None: raise AssertionError
    def _deal_wounds(self, player_id: str, amount: int, source_card_id: str | None = None) -> None: raise AssertionError
    def _run_state_based_actions(self) -> None: raise AssertionError
    def _emit(self, event_type: str, player_id: str | None = None, card_id: str | None = None, payload: dict[str, object] | None = None) -> None: raise AssertionError


class MinimalStackContext:
    def __init__(self) -> None:
        self.state = minimal_state()
        self.events: list[str] = []

    def _require_running_state(self) -> GameState:
        return self.state

    def _next_player(self, player_id: str) -> str:
        return "B" if player_id == "A" else "A"

    def _definition(self, card_id: str) -> CardDefinition: raise AssertionError
    def _move_card(self, card_id: str, destination: Zone, destination_player: str, *, reason: MoveReason = MoveReason.RULE, allow_replacement: bool = True) -> Zone: raise AssertionError
    def _queue_triggered_abilities(self, source_card_id: str, trigger: TriggerKind) -> None: raise AssertionError
    def _run_state_based_actions(self) -> None: raise AssertionError
    def _apply_effect(self, effect: EffectDefinition, item: StackItem, selected_target_id: str | ZoneTarget | TargetAllocation | None = None) -> None: raise AssertionError
    def _emit(self, event_type: str, player_id: str | None = None, card_id: str | None = None, payload: dict[str, object] | None = None) -> None:
        self.events.append(event_type)


class MinimalZoneContext:
    def __init__(self) -> None:
        self.state = minimal_state()
        self.rules = RuleSet()
        self.events: list[str] = []

    def _require_state(self) -> GameState:
        return self.state

    def _require_running_state(self) -> GameState: return self.state
    def _definition(self, card_id: str) -> CardDefinition: raise AssertionError
    def _current_strength(self, card_id: str) -> int: raise AssertionError
    def _consume_replacement_replay_choice(self) -> int | None: return None
    def _execute_transaction(self, command: GameCommand, replay_choices: tuple[int, ...]) -> None: raise AssertionError
    def _emit(self, event_type: str, player_id: str | None = None, card_id: str | None = None, payload: dict[str, object] | None = None) -> None:
        self.events.append(event_type)


class IndependentManagerContextTests(unittest.TestCase):
    def test_replay_choices_are_consumed_in_order_and_exhaust_to_none(self):
        engine = GameEngine()
        engine._replacement_replay_choices = (2, 0)
        self.assertEqual(engine._consume_replacement_replay_choice(), 2)
        self.assertEqual(engine._consume_replacement_replay_choice(), 0)
        self.assertIsNone(engine._consume_replacement_replay_choice())
        self.assertEqual(engine._replacement_replay_cursor, 2)

    def test_combat_rejects_invalid_declaration_without_partial_mutation(self):
        context = MinimalCombatContext()
        before = deepcopy(context.state)
        with self.assertRaises(IllegalAction):
            CombatManager(context)._declare_attackers(DeclareAttackers("A", (), "B"))
        self.assertEqual(context.state, before)

    def test_stack_advances_priority_with_only_its_minimum_collaborators(self):
        context = MinimalStackContext()
        StackManager(context)._pass_priority("A")
        self.assertEqual(context.state.priority_player_id, "B")
        self.assertEqual(context.state.consecutive_passes, 1)
        self.assertEqual(context.events, ["PRIORITY_PASSED"])

    def test_zone_reports_exhausted_deck_without_mutating_zones(self):
        context = MinimalZoneContext()
        before = deepcopy(context.state.players["A"].zones)
        ZoneManager(context)._draw("A", 1)
        self.assertEqual(context.state.players["A"].zones, before)
        self.assertEqual(context.events, ["DRAW_FAILED"])


if __name__ == "__main__":
    unittest.main()
