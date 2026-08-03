import unittest

from card_duel_engine import GameEngine, RuleSet
from card_duel_engine.domain.enums import CardKind, EffectKind, Phase, TargetMode, Zone
from card_duel_engine.domain.errors import PaymentError
from card_duel_engine.domain.models import AbilityDefinition, CardDefinition, CompositeCost, EffectDefinition
from card_duel_engine.engine.commands import ActivateAbility, AdvancePhase, PassPriority, PlayCard

from fixtures import quick_damage_fixture, test_deck


def force_zone(engine: GameEngine, definition_id: str, player_id: str, zone: Zone) -> str:
    card_id = next(
        instance_id
        for instance_id, instance in engine.state.cards.items()
        if instance.definition_id == definition_id and instance.owner_id == player_id
    )
    instance = engine.state.cards[card_id]
    for owner in engine.state.players.values():
        for cards in owner.zones.values():
            if card_id in cards:
                cards.remove(card_id)
    if card_id in engine.state.resolution:
        engine.state.resolution.remove(card_id)
    engine.state.players[player_id].zones[zone].append(card_id)
    instance.zone = zone
    instance.controller_id = player_id
    return card_id


class StackAndPriorityTests(unittest.TestCase):
    def make_engine(self) -> tuple[GameEngine, str, str]:
        a_quick = quick_damage_fixture("A-QUICK")
        b_quick = quick_damage_fixture("B-QUICK")
        engine = GameEngine(RuleSet())
        engine.new_match(
            {
                "A": [a_quick, *test_deck("A", 8)],
                "B": [b_quick, *test_deck("B", 8)],
            },
            seed=4,
        )
        a_id = force_zone(engine, "A-QUICK", "A", Zone.HAND)
        b_id = force_zone(engine, "B-QUICK", "B", Zone.HAND)
        engine.state.players["A"].steps = 10
        engine.state.players["B"].steps = 10
        engine.validate_invariants()
        return engine, a_id, b_id

    def test_responses_resolve_last_in_first_out(self):
        engine, a_id, b_id = self.make_engine()
        engine.execute(PlayCard("A", a_id, ("B",)))
        engine.execute(PlayCard("B", b_id, ("A",)))
        self.assertEqual(len(engine.state.stack), 2)

        engine.execute(PassPriority("A"))
        engine.execute(PassPriority("B"))
        self.assertEqual(engine.state.players["A"].wounds, 5)
        self.assertEqual(engine.state.players["B"].wounds, 0)
        self.assertIn(b_id, engine.state.players["B"].zones[Zone.DISCARD])

        engine.execute(PassPriority("A"))
        engine.execute(PassPriority("B"))
        self.assertEqual(engine.state.players["B"].wounds, 5)
        self.assertIn(a_id, engine.state.players["A"].zones[Zone.DISCARD])

    def test_payment_is_atomic(self):
        engine, a_id, _ = self.make_engine()
        engine.state.players["A"].steps = 4
        with self.assertRaises(PaymentError):
            engine.execute(PlayCard("A", a_id, ("B",)))
        self.assertEqual(engine.state.players["A"].steps, 4)
        self.assertIn(a_id, engine.state.players["A"].zones[Zone.HAND])
        self.assertFalse(engine.state.stack)

    def test_generic_creature_resolves_from_hand_to_battlefield(self):
        engine = GameEngine(RuleSet())
        engine.new_match({"A": test_deck("A"), "B": test_deck("B")}, seed=5)
        creature_id = force_zone(engine, "A-001", "A", Zone.HAND)
        while engine.state.phase is not Phase.EFFECTS:
            engine.execute(PassPriority(engine.state.priority_player_id))
            engine.execute(PassPriority(engine.state.priority_player_id))
            engine.execute(AdvancePhase("A"))
        engine.state.players["A"].steps = 5
        engine.execute(PlayCard("A", creature_id))
        engine.execute(PassPriority("B"))
        engine.execute(PassPriority("A"))
        self.assertIn(creature_id, engine.state.players["A"].zones[Zone.BATTLEFIELD])
        self.assertEqual(engine.state.players["A"].steps, 0)

    def test_self_sacrificing_ability_never_blocks_priority_in_ten_runs(self):
        """Regresión: resolver no debe volver a validar la presencia de la fuente."""

        for run in range(10):
            with self.subTest(run=run):
                source = CardDefinition(
                    f"SOURCE-{run}",
                    "Fuente sacrificable",
                    CardKind.CREATURE,
                    0,
                    base_strength=2,
                    abilities=(AbilityDefinition(
                        "last_shot",
                        (EffectDefinition(
                            EffectKind.DEAL_DAMAGE,
                            1,
                            TargetMode.CHOSEN_PERMANENT,
                        ),),
                        cost=CompositeCost(sacrifice_count=1),
                    ),),
                )
                engine = GameEngine(RuleSet())
                engine.new_match(
                    {
                        "A": [source, *test_deck(f"SSA{run}", 11)],
                        "B": test_deck(f"SSB{run}", 12),
                    },
                    seed=100 + run,
                )
                source_id = force_zone(engine, source.card_id, "A", Zone.BATTLEFIELD)
                target_id = force_zone(engine, f"SSB{run}-000", "B", Zone.BATTLEFIELD)
                engine.state.priority_player_id = "A"
                engine.execute(ActivateAbility(
                    "A",
                    source_id,
                    "last_shot",
                    chosen_card_ids=(target_id,),
                    sacrifice_card_ids=(source_id,),
                ))
                profile = engine.state.stack[-1].ability_source_profile
                self.assertIsNotNone(profile)
                self.assertTrue(profile.was_effective_creature)
                self.assertTrue(profile.was_on_battlefield)
                engine.execute(PassPriority("B"))
                engine.execute(PassPriority("A"))
                self.assertEqual(engine.state.cards[target_id].damage, 1)
                self.assertFalse(engine.state.stack)
                self.assertEqual(engine.state.priority_player_id, engine.state.active_player_id)
