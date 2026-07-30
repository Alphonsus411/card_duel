import unittest

from card_duel_engine import GameEngine, RuleSet
from card_duel_engine.domain.enums import MatchStatus
from card_duel_engine.domain.errors import IllegalAction
from card_duel_engine.engine.commands import Concede

from fixtures import test_deck


class EndConditionTests(unittest.TestCase):
    def test_legal_actions_distinguishes_non_running_statuses(self):
        engine = GameEngine()
        with self.assertRaises(RuntimeError):
            engine.legal_actions("A")

        engine.new_match(
            {"A": test_deck("A"), "B": test_deck("B")}, auto_start=False
        )
        with self.assertRaises(IllegalAction):
            engine.legal_actions("A")

        engine.state.status = MatchStatus.BLOCKED
        self.assertEqual(engine.legal_actions("A"), ())

    def test_wound_limit_finishes_match(self):
        engine = GameEngine(RuleSet(wound_limit=25))
        engine.new_match({"A": test_deck("A"), "B": test_deck("B")})
        engine.add_wounds("B", 25)
        self.assertIs(engine.state.status, MatchStatus.FINISHED)
        self.assertEqual(engine.state.winner_ids, ("A",))
        self.assertEqual(engine.legal_actions("A"), ())
        self.assertEqual(engine.legal_actions("B"), ())

    def test_concession_finishes_match(self):
        engine = GameEngine()
        engine.new_match({"A": test_deck("A"), "B": test_deck("B")})
        engine.execute(Concede("A"))
        self.assertIs(engine.state.status, MatchStatus.FINISHED)
        self.assertEqual(engine.state.winner_ids, ("B",))
        self.assertEqual(engine.legal_actions("A"), ())
        self.assertEqual(engine.legal_actions("B"), ())

    def test_multiplayer_concession_blocks_without_inventing_winners(self):
        engine = GameEngine()
        engine.new_match(
            {player_id: test_deck(player_id) for player_id in ("A", "B", "C")}
        )

        engine.execute(Concede("B"))

        self.assertIs(engine.state.status, MatchStatus.BLOCKED)
        self.assertTrue(engine.state.players["B"].conceded)
        self.assertEqual(engine.state.winner_ids, ())
        self.assertEqual(engine.state.event_log[-1].event_type, "MULTIPLAYER_END_UNDEFINED")
        self.assertEqual(
            engine.state.event_log[-1].payload,
            {"affected_player_ids": ("B",), "cause": "concession"},
        )

    def test_multiplayer_wound_limit_blocks_without_inventing_winners(self):
        engine = GameEngine(RuleSet(wound_limit=25))
        engine.new_match(
            {player_id: test_deck(player_id) for player_id in ("A", "B", "C")}
        )

        engine.add_wounds("C", 25)

        self.assertIs(engine.state.status, MatchStatus.BLOCKED)
        self.assertEqual(engine.state.winner_ids, ())
        self.assertEqual(engine.state.event_log[-1].event_type, "MULTIPLAYER_END_UNDEFINED")
        self.assertEqual(
            engine.state.event_log[-1].payload,
            {"affected_player_ids": ("C",), "cause": "wound_limit"},
        )
