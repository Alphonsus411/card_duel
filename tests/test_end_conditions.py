import unittest

from card_duel_engine import GameEngine, RuleSet
from card_duel_engine.domain.enums import MatchStatus
from card_duel_engine.engine.commands import Concede

from fixtures import test_deck


class EndConditionTests(unittest.TestCase):
    def test_wound_limit_finishes_match(self):
        engine = GameEngine(RuleSet(wound_limit=25))
        engine.new_match({"A": test_deck("A"), "B": test_deck("B")})
        engine.add_wounds("B", 25)
        self.assertIs(engine.state.status, MatchStatus.FINISHED)
        self.assertEqual(engine.state.winner_ids, ("A",))

    def test_concession_finishes_match(self):
        engine = GameEngine()
        engine.new_match({"A": test_deck("A"), "B": test_deck("B")})
        engine.execute(Concede("A"))
        self.assertIs(engine.state.status, MatchStatus.FINISHED)
        self.assertEqual(engine.state.winner_ids, ("B",))
