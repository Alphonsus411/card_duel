import unittest

from card_duel_engine import GameEngine
from card_duel_engine.domain.enums import MatchStatus
from card_duel_engine.simulation import PhaseProgressAgent, run_headless

from fixtures import test_deck


class SimulationTests(unittest.TestCase):
    def test_headless_runner_advances_without_an_interface(self):
        engine = GameEngine()
        engine.new_match({"A": test_deck("A"), "B": test_deck("B")}, seed=11)
        report = run_headless(
            engine,
            {"A": PhaseProgressAgent(), "B": PhaseProgressAgent()},
            max_commands=80,
        )
        self.assertEqual(report.commands_executed, 80)
        self.assertIn(report.status, {MatchStatus.BLOCKED, MatchStatus.FINISHED})
        self.assertGreaterEqual(report.turn_reached, 2)
        self.assertGreater(report.event_count, 15)
