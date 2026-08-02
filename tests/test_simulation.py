import unittest

from card_duel_engine import GameEngine
from card_duel_engine.domain.enums import MatchStatus, Phase, Zone
from card_duel_engine.engine.commands import (
    AdvancePhase,
    DeclareAttackers,
    DeclareBlockers,
    PassPriority,
)
from card_duel_engine.simulation import (
    PhaseProgressAgent,
    SimulationStopReason,
    run_headless,
)

from fixtures import test_deck
from test_stack_and_priority import force_zone


class SimulationTests(unittest.TestCase):
    def test_legal_action_only_agent_can_choose_a_nonempty_block(self):
        class BlockingAgent(PhaseProgressAgent):
            chose_nonempty_block = False

            def choose_action(self, request):
                for action in request.legal_actions:
                    if isinstance(action, DeclareBlockers) and action.assignments:
                        self.chose_nonempty_block = True
                        return action
                return super().choose_action(request)

        engine = GameEngine()
        engine.new_match({"A": test_deck("A"), "B": test_deck("B")}, seed=12)
        attacker = force_zone(engine, "A-001", "A", Zone.BATTLEFIELD)
        blocker = force_zone(engine, "B-001", "B", Zone.BATTLEFIELD)
        while engine.state.phase is not Phase.COMBAT:
            for _ in engine.state.turn_order:
                engine.execute(PassPriority(engine.state.priority_player_id))
            engine.execute(AdvancePhase("A"))
        for _ in engine.state.turn_order:
            engine.execute(PassPriority(engine.state.priority_player_id))
        engine.execute(DeclareAttackers("A", (attacker,), "B"))
        blocking_agent = BlockingAgent()

        run_headless(
            engine,
            {"A": PhaseProgressAgent(), "B": blocking_agent},
            max_commands=1,
        )

        self.assertTrue(blocking_agent.chose_nonempty_block)
        self.assertEqual(engine.state.combat.blockers, {attacker: (blocker,)})

    def test_headless_runner_rejects_an_uninitialized_engine(self):
        with self.assertRaisesRegex(
            ValueError, "No se puede simular un motor sin una partida iniciada"
        ):
            run_headless(GameEngine(), {})

    def test_headless_runner_rejects_a_nonpositive_command_limit(self):
        engine = GameEngine()
        engine.new_match({"A": test_deck("A"), "B": test_deck("B")}, seed=11)

        for max_commands in (0, -1):
            with self.subTest(max_commands=max_commands):
                with self.assertRaisesRegex(
                    ValueError, "max_commands debe ser un entero positivo"
                ):
                    run_headless(engine, {}, max_commands=max_commands)

    def test_headless_runner_advances_without_an_interface(self):
        engine = GameEngine()
        engine.new_match({"A": test_deck("A"), "B": test_deck("B")}, seed=11)
        report = run_headless(
            engine,
            {"A": PhaseProgressAgent(), "B": PhaseProgressAgent()},
            max_commands=80,
        )
        self.assertEqual(report.commands_executed, 80)
        self.assertIs(report.stop_reason, SimulationStopReason.COMMAND_LIMIT_REACHED)
        self.assertIs(report.status, MatchStatus.RUNNING)
        self.assertIs(engine.state.status, MatchStatus.RUNNING)
        self.assertNotIn(
            "ALL_PHASES_SUPPRESSED",
            (event.event_type for event in engine.state.event_log),
        )
        self.assertNotIn(
            "MULTIPLAYER_END_UNDEFINED",
            (event.event_type for event in engine.state.event_log),
        )
        self.assertGreaterEqual(report.turn_reached, 2)
        self.assertGreater(report.event_count, 15)
