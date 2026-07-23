import unittest

from card_duel_engine import GameEngine, RuleSet
from card_duel_engine.domain.enums import Phase, Zone
from card_duel_engine.domain.errors import IllegalAction
from card_duel_engine.engine.commands import AdvancePhase, DiscardCards, PassPriority

from fixtures import test_deck


def make_engine() -> GameEngine:
    engine = GameEngine(RuleSet())
    engine.new_match({"A": test_deck("A"), "B": test_deck("B")}, seed=7)
    return engine


def close_priority(engine: GameEngine) -> None:
    for _ in engine.state.turn_order:
        engine.execute(PassPriority(engine.state.priority_player_id))


def advance(engine: GameEngine, player_id: str) -> None:
    close_priority(engine)
    engine.execute(AdvancePhase(player_id))


class SetupAndPhaseTests(unittest.TestCase):
    def test_match_deals_six_and_draws_for_first_turn(self):
        engine = make_engine()
        self.assertEqual(len(engine.state.players["A"].zones[Zone.HAND]), 7)
        self.assertEqual(len(engine.state.players["B"].zones[Zone.HAND]), 6)
        self.assertIs(engine.state.phase, Phase.DRAW)

    def test_mulligan_reduces_hand_before_match_starts(self):
        engine = GameEngine(RuleSet())
        engine.new_match(
            {"A": test_deck("A"), "B": test_deck("B")},
            seed=7,
            auto_start=False,
        )
        engine.mulligan("A")
        self.assertEqual(len(engine.state.players["A"].zones[Zone.HAND]), 5)
        engine.start_match()
        self.assertEqual(len(engine.state.players["A"].zones[Zone.HAND]), 6)

    def test_phase_sequence_and_maintenance_income(self):
        engine = make_engine()
        advance(engine, "A")
        self.assertIs(engine.state.phase, Phase.MAINTENANCE)
        self.assertEqual(engine.state.players["A"].steps, 5)
        expected = [Phase.EFFECTS, Phase.COMBAT, Phase.LEGENDARY, Phase.DISCARD]
        for phase in expected:
            advance(engine, "A")
            self.assertIs(engine.state.phase, phase)

    def test_passive_player_cannot_advance_phase(self):
        engine = make_engine()
        close_priority(engine)
        with self.assertRaisesRegex(IllegalAction, "jugador activo"):
            engine.execute(AdvancePhase("B"))

    def test_discard_must_restore_hand_limit_before_turn_changes(self):
        engine = make_engine()
        for _ in range(5):
            advance(engine, "A")
        self.assertIs(engine.state.phase, Phase.DISCARD)
        close_priority(engine)
        with self.assertRaisesRegex(IllegalAction, "descartarse"):
            engine.execute(AdvancePhase("A"))
        hand = engine.state.players["A"].zones[Zone.HAND]
        engine.execute(DiscardCards("A", tuple(hand[:1])))
        # Descartar no reabre la ventana; ya se cerró antes de ajustar la mano.
        engine.execute(AdvancePhase("A"))
        self.assertEqual(engine.state.active_player_id, "B")
        self.assertIs(engine.state.phase, Phase.DRAW)
