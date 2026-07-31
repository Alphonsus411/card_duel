import unittest

from card_duel_engine import GameEngine
from card_duel_engine.domain.enums import CardKind, Phase, Zone
from card_duel_engine.domain.models import CardDefinition
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
    def _engine_with_small_blocker(self, seed: int) -> tuple[GameEngine, str, str]:
        small_blocker = CardDefinition(
            card_id="SMALL-BLOCKER",
            name="Bloqueador pequeño",
            kind=CardKind.CREATURE,
            cost=2,
            base_strength=2,
            set_id="test-fixtures",
        )
        engine = GameEngine()
        engine.new_match(
            {
                "A": test_deck("A"),
                "B": [small_blocker, *test_deck("B")],
            },
            seed=seed,
        )
        attacker = force_zone(engine, "A-001", "A", Zone.BATTLEFIELD)
        blocker = force_zone(engine, small_blocker.card_id, "B", Zone.BATTLEFIELD)
        advance_to(engine, Phase.COMBAT)
        close_priority(engine)
        engine.execute(DeclareAttackers("A", (attacker,), "B"))
        engine.execute(DeclareBlockers("B", ((attacker, (blocker,)),)))
        close_priority(engine)
        engine.execute(ResolveCombat("A"))
        return engine, attacker, blocker

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

    def test_nonlethal_combat_damage_remains_until_end_of_turn_cleanup(self):
        engine, attacker, blocker = self._engine_with_small_blocker(seed=11)

        self.assertIn(blocker, engine.state.players["B"].zones[Zone.DISCARD])
        self.assertIn(attacker, engine.state.players["A"].zones[Zone.BATTLEFIELD])
        self.assertEqual(engine.state.cards[attacker].damage, 2)

        active_player = engine.state.active_player_id
        while engine.state.active_player_id == active_player:
            if not engine.state.phase_priority_complete:
                close_priority(engine)
            engine.execute(AdvancePhase(active_player))

        self.assertEqual(engine.state.cards[attacker].damage, 0)

    def test_postcombat_damage_accumulates_and_becomes_lethal(self):
        engine, attacker, _ = self._engine_with_small_blocker(seed=12)

        self.assertEqual(engine.state.cards[attacker].damage, 2)
        engine._deal_damage(attacker, 3)
        self.assertEqual(engine.state.cards[attacker].damage, 5)
        engine._run_state_based_actions()

        self.assertIn(attacker, engine.state.players["A"].zones[Zone.DISCARD])

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
