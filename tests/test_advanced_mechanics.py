import unittest

from card_duel_engine import GameEngine, RuleSet
from card_duel_engine.domain import (
    AbilityDefinition,
    CardDefinition,
    CardKind,
    CompositeCost,
    EffectDefinition,
    EffectKind,
    Phase,
    TargetMode,
    TriggerKind,
    Zone,
)
from card_duel_engine.domain.errors import PaymentError
from card_duel_engine.engine import ActivateAbility, EquipCard, PassPriority, PlayCard

from fixtures import test_deck


def force_zone(engine, definition_id, player_id, zone):
    card_id = next(
        card_id
        for card_id, instance in engine.state.cards.items()
        if instance.definition_id == definition_id and instance.owner_id == player_id
    )
    instance = engine.state.cards[card_id]
    for player in engine.state.players.values():
        for cards in player.zones.values():
            if card_id in cards:
                cards.remove(card_id)
    if card_id in engine.state.resolution:
        engine.state.resolution.remove(card_id)
    engine.state.players[player_id].zones[zone].append(card_id)
    instance.zone = zone
    instance.controller_id = player_id
    return card_id


def resolve_one(engine):
    engine.execute(PassPriority(engine.state.priority_player_id))
    engine.execute(PassPriority(engine.state.priority_player_id))


class AdvancedMechanicsTests(unittest.TestCase):
    def make_engine(self, *specials):
        engine = GameEngine(RuleSet())
        engine.new_match(
            {"A": [*specials, *test_deck("A", 10)], "B": test_deck("B", 10)},
            seed=31,
        )
        return engine

    def test_composite_activated_cost_is_atomic_and_resolves(self):
        source_def = CardDefinition(
            "SOURCE", "Fuente", CardKind.ARTIFACT, 2,
            abilities=(AbilityDefinition(
                "pulse",
                (EffectDefinition(EffectKind.DEAL_WOUNDS, 3, TargetMode.CHOSEN_PLAYER),),
                CompositeCost(steps=2, wounds=1, discard_count=1, exhaust_source=True),
                once_per_turn=True,
            ),),
        )
        fodder = CardDefinition("FODDER", "Descartable", CardKind.ARTIFACT, 0)
        engine = self.make_engine(source_def, fodder)
        source = force_zone(engine, "SOURCE", "A", Zone.BATTLEFIELD)
        discarded = force_zone(engine, "FODDER", "A", Zone.HAND)
        engine.state.players["A"].steps = 1
        command = ActivateAbility("A", source, "pulse", ("B",), (), (discarded,))

        with self.assertRaises(PaymentError):
            engine.execute(command)
        self.assertEqual(engine.state.players["A"].steps, 1)
        self.assertEqual(engine.state.players["A"].wounds, 0)
        self.assertFalse(engine.state.cards[source].exhausted)
        self.assertIn(discarded, engine.state.players["A"].zones[Zone.HAND])

        engine.state.players["A"].steps = 2
        engine.execute(command)
        self.assertEqual(engine.state.players["A"].wounds, 1)
        self.assertTrue(engine.state.cards[source].exhausted)
        self.assertIn(discarded, engine.state.players["A"].zones[Zone.DISCARD])
        resolve_one(engine)
        self.assertEqual(engine.state.players["B"].wounds, 3)

    def test_prevention_absorbs_wounds_and_damage(self):
        engine = self.make_engine()
        creature = force_zone(engine, "A-001", "A", Zone.BATTLEFIELD)
        engine.state.players["A"].wound_prevention = 2
        engine.state.cards[creature].damage_prevention = 2
        engine._deal_wounds("A", 5)
        engine._deal_damage(creature, 4)
        self.assertEqual(engine.state.players["A"].wounds, 3)
        self.assertEqual(engine.state.cards[creature].damage, 2)
        self.assertEqual(engine.state.players["A"].wound_prevention, 0)

    def test_indestructible_survives_destroy_and_lethal_damage(self):
        immortal = CardDefinition(
            "IMMORTAL", "Inmortal", CardKind.CREATURE, 1,
            base_strength=2, keywords=frozenset({"INDESTRUCTIBLE"}),
        )
        destroy = CardDefinition(
            "DESTROY", "Destruir", CardKind.QUICK_RESOURCE, 0,
            permanent=False, transmutable=False,
            effects=(EffectDefinition(
                EffectKind.DESTROY, 1, TargetMode.CHOSEN_PERMANENT
            ),),
        )
        engine = self.make_engine(immortal, destroy)
        card_id = force_zone(engine, "IMMORTAL", "A", Zone.BATTLEFIELD)
        destroy_id = force_zone(engine, "DESTROY", "A", Zone.HAND)
        engine.execute(PlayCard("A", destroy_id, (), (card_id,)))
        resolve_one(engine)
        self.assertIn(card_id, engine.state.players["A"].zones[Zone.BATTLEFIELD])
        engine._deal_damage(card_id, 99)
        engine._run_state_based_actions()
        self.assertIn(card_id, engine.state.players["A"].zones[Zone.BATTLEFIELD])

    def test_equipment_bonus_and_detachment(self):
        equipment = CardDefinition(
            "SWORD", "Espada", CardKind.EQUIPMENT, 2,
            equipment_strength_bonus=3,
        )
        engine = self.make_engine(equipment)
        sword = force_zone(engine, "SWORD", "A", Zone.BATTLEFIELD)
        creature = force_zone(engine, "A-001", "A", Zone.BATTLEFIELD)
        base = engine._current_strength(creature)
        engine.state.phase = Phase.EFFECTS
        engine.state.priority_player_id = "A"
        engine.state.players["A"].steps = 2
        engine.execute(EquipCard("A", sword, creature))
        self.assertEqual(engine._current_strength(creature), base + 3)
        engine._move_card(creature, Zone.DISCARD, "A")
        self.assertIsNone(engine.state.cards[sword].attached_to)
        self.assertIn(sword, engine.state.players["A"].zones[Zone.BATTLEFIELD])

    def test_end_of_turn_modifier_expires(self):
        engine = self.make_engine()
        creature = force_zone(engine, "A-001", "A", Zone.BATTLEFIELD)
        base = engine._current_strength(creature)
        from card_duel_engine.domain.models import TimedModifier
        engine.state.timed_modifiers.append(
            TimedModifier("temporary", creature, 4, engine.state.turn_serial)
        )
        self.assertEqual(engine._current_strength(creature), base + 4)
        engine._cleanup_end_of_turn()
        self.assertEqual(engine._current_strength(creature), base)

    def test_enter_battlefield_trigger_uses_the_stack(self):
        creature_def = CardDefinition(
            "HERALD", "Heraldo", CardKind.CREATURE, 1, base_strength=1,
            abilities=(AbilityDefinition(
                "arrival",
                (EffectDefinition(EffectKind.GAIN_STEPS, 2),),
                trigger=TriggerKind.ON_ENTER_BATTLEFIELD,
            ),),
        )
        engine = self.make_engine(creature_def)
        card_id = force_zone(engine, "HERALD", "A", Zone.HAND)
        engine.state.phase = Phase.EFFECTS
        engine.state.priority_player_id = "A"
        engine.state.players["A"].steps = 1
        engine.execute(PlayCard("A", card_id))
        resolve_one(engine)
        self.assertEqual(len(engine.state.stack), 1)
        resolve_one(engine)
        self.assertEqual(engine.state.players["A"].steps, 2)


if __name__ == "__main__":
    unittest.main()
