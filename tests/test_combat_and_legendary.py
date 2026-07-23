import unittest

from card_duel_engine import GameEngine
from card_duel_engine.domain.enums import Phase, Zone
from card_duel_engine.engine.commands import (
    AdvancePhase,
    DeclareAttackers,
    DeclareBlockers,
    PassPriority,
    ResolveCombat,
)

from fixtures import legendary_fixture, test_deck
from test_stack_and_priority import force_zone


def close_priority(engine: GameEngine) -> None:
    for _ in engine.state.turn_order:
        engine.execute(PassPriority(engine.state.priority_player_id))


def advance_to(engine: GameEngine, phase: Phase) -> None:
    while engine.state.phase is not phase:
        close_priority(engine)
        engine.execute(AdvancePhase(engine.state.active_player_id))


class CombatAndLegendaryTests(unittest.TestCase):
    def test_equal_creatures_destroy_each_other_in_combat(self):
        engine = GameEngine()
        engine.new_match({"A": test_deck("A"), "B": test_deck("B")}, seed=8)
        attacker = force_zone(engine, "A-001", "A", Zone.BATTLEFIELD)
        blocker = force_zone(engine, "B-001", "B", Zone.BATTLEFIELD)
        advance_to(engine, Phase.COMBAT)
        close_priority(engine)

        engine.execute(DeclareAttackers("A", (attacker,), "B"))
        engine.execute(DeclareBlockers("B", ((attacker, (blocker,)),)))
        close_priority(engine)
        engine.execute(ResolveCombat("A"))

        self.assertIn(attacker, engine.state.players["A"].zones[Zone.DISCARD])
        self.assertIn(blocker, engine.state.players["B"].zones[Zone.DISCARD])
        self.assertEqual(engine.state.players["B"].wounds, 0)

    def test_unblocked_creature_inflicts_its_strength(self):
        engine = GameEngine()
        engine.new_match({"A": test_deck("A"), "B": test_deck("B")}, seed=9)
        attacker = force_zone(engine, "A-001", "A", Zone.BATTLEFIELD)
        advance_to(engine, Phase.COMBAT)
        close_priority(engine)
        engine.execute(DeclareAttackers("A", (attacker,), "B"))
        engine.execute(DeclareBlockers("B"))
        close_priority(engine)
        engine.execute(ResolveCombat("A"))
        self.assertEqual(engine.state.players["B"].wounds, 5)

    def test_legendary_permanent_queues_its_phase_effect(self):
        legend = legendary_fixture()
        engine = GameEngine()
        engine.new_match(
            {"A": [legend, *test_deck("A")], "B": test_deck("B")},
            seed=10,
        )
        legend_id = force_zone(engine, legend.card_id, "A", Zone.BATTLEFIELD)
        advance_to(engine, Phase.LEGENDARY)
        self.assertEqual(len(engine.state.stack), 1)
        self.assertEqual(engine.state.stack[-1].source_card_id, legend_id)
        before = engine.state.players["A"].steps
        close_priority(engine)
        self.assertEqual(engine.state.players["A"].steps, before + 3)
