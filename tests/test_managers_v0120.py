import unittest
from copy import deepcopy

from card_duel_engine import GameEngine
from card_duel_engine.domain.enums import Phase, Zone
from card_duel_engine.domain.errors import IllegalAction
from card_duel_engine.engine.combat import CombatManager
from card_duel_engine.engine.commands import DeclareAttackers, DeclareBlockers, PassPriority, ResolveSearchChoice
from card_duel_engine.engine.stack import StackManager
from card_duel_engine.engine.zones import ZoneManager
from fixtures import test_deck


class ManagerContractsV0120Tests(unittest.TestCase):
    def setUp(self):
        self.engine = GameEngine()
        self.engine.new_match({"A": test_deck("A"), "B": test_deck("B")}, seed=12)

    def test_managers_receive_an_explicit_context(self):
        self.assertIsInstance(self.engine._combat, CombatManager)
        self.assertIsInstance(self.engine._stack, StackManager)
        self.assertIsInstance(self.engine._zones, ZoneManager)
        self.assertIs(self.engine._combat._context, self.engine)
        self.assertIs(self.engine._stack._context, self.engine)
        self.assertIs(self.engine._zones._context, self.engine)

    def test_direct_combat_declaration_and_resolution(self):
        state = self.engine.state
        attacker = state.players["A"].zones[Zone.HAND][0]
        self.engine._zones._move_card(attacker, Zone.BATTLEFIELD, "A")
        state.phase = Phase.COMBAT
        state.phase_priority_complete = True
        self.engine._combat._declare_attackers(DeclareAttackers("A", (attacker,), "B"))
        self.engine._combat._declare_blockers(DeclareBlockers("B", ()))
        state.phase_priority_complete = True
        wounds = state.players["B"].wounds
        self.engine._combat._resolve_combat("A")
        self.assertTrue(state.combat.resolved)
        self.assertGreater(state.players["B"].wounds, wounds)

    def test_direct_discard_and_exile_movements(self):
        card_id = self.engine.state.players["A"].zones[Zone.HAND][0]
        self.assertEqual(self.engine._zones._move_card(card_id, Zone.DISCARD, "A"), Zone.DISCARD)
        self.assertIn(card_id, self.engine.state.players["A"].zones[Zone.DISCARD])
        self.assertEqual(self.engine._zones._move_card(card_id, Zone.VOID, "A"), Zone.VOID)
        self.assertIn(card_id, self.engine.state.void)

    def test_illegal_combat_declaration_preserves_state(self):
        before = deepcopy(self.engine.state)
        attacker = self.engine.state.players["A"].zones[Zone.HAND][0]
        with self.assertRaises(IllegalAction):
            self.engine._combat._declare_attackers(DeclareAttackers("A", (attacker,), "B"))
        self.assertEqual(self.engine.state, before)

    def test_illegal_priority_and_search_choices_preserve_state(self):
        before = deepcopy(self.engine.state)
        with self.assertRaises(IllegalAction):
            self.engine._stack._pass_priority("B")
        self.assertEqual(self.engine.state, before)
        with self.assertRaises(IllegalAction):
            self.engine._stack._resolve_search_choice(ResolveSearchChoice("A", ()))
        self.assertEqual(self.engine.state, before)

    def test_illegal_zone_command_preserves_state(self):
        before = deepcopy(self.engine.state)
        missing = "card-that-does-not-exist"
        with self.assertRaises(KeyError):
            self.engine._zones._move_card(missing, Zone.VOID, "A")
        self.assertEqual(self.engine.state, before)


if __name__ == "__main__":
    unittest.main()
