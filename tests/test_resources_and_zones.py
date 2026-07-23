import unittest

from card_duel_engine import GameEngine, RuleSet
from card_duel_engine.domain.enums import Phase, Zone
from card_duel_engine.engine.commands import TransmutePermanent

from fixtures import test_deck


class ResourceAndZoneTests(unittest.TestCase):
    def test_transmutation_moves_permanent_and_gains_printed_cost(self):
        engine = GameEngine(RuleSet())
        engine.new_match({"A": test_deck("A"), "B": test_deck("B")}, seed=3)
        player = engine.state.players["A"]
        card_id = player.zones[Zone.HAND][0]
        player.zones[Zone.HAND].remove(card_id)
        player.zones[Zone.BATTLEFIELD].append(card_id)
        engine.state.cards[card_id].zone = Zone.BATTLEFIELD

        engine.execute(TransmutePermanent("A", card_id))

        self.assertIn(card_id, player.zones[Zone.DISCARD])
        self.assertEqual(player.steps, 5)
        self.assertEqual(engine.state.event_log[-1].event_type, "CARD_TRANSMUTED")

    def test_empty_deck_recycles_discard_when_drawing(self):
        rules = RuleSet(initial_hand_size=1)
        engine = GameEngine(rules)
        engine.new_match({"A": test_deck("A", 1), "B": test_deck("B", 1)}, seed=2)
        card_id = engine.state.players["A"].zones[Zone.HAND][0]
        engine.state.players["A"].zones[Zone.HAND].remove(card_id)
        engine.state.players["A"].zones[Zone.DISCARD].append(card_id)
        engine.state.cards[card_id].zone = Zone.DISCARD
        engine._enter_phase(Phase.DRAW)
        self.assertIn(card_id, engine.state.players["A"].zones[Zone.HAND])
