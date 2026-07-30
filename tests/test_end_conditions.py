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
