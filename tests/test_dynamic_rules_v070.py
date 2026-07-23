import unittest

from card_duel_engine import GameEngine, RuleSet
from card_duel_engine.domain import (
    AbilityDefinition,
    CardDefinition,
    CardKind,
    CompositeCost,
    CostComponent,
    CostMetric,
    CostTerm,
    DynamicCostDefinition,
    EffectDefinition,
    EffectDuration,
    EffectKind,
    MoveReplacementDefinition,
    TargetMode,
    TextPatchDefinition,
    Zone,
)
from card_duel_engine.domain.errors import IllegalAction, PaymentError
from card_duel_engine.engine import (
    ActivateAbility,
    PassPriority,
    PlayCard,
    SetReplacementOrder,
)

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


class DynamicRulesV070Tests(unittest.TestCase):
    def make_engine(self, a_specials=(), b_specials=()):
        engine = GameEngine(RuleSet())
        engine.new_match(
            {
                "A": [*a_specials, *test_deck("A7", 16)],
                "B": [*b_specials, *test_deck("B7", 16)],
            },
            seed=70,
        )
        return engine

    def test_card_cost_is_calculated_from_current_board_state(self):
        scalable = CardDefinition(
            "SCALABLE7",
            "Coste de oposición",
            CardKind.QUICK_RESOURCE,
            99,
            permanent=False,
            transmutable=False,
            dynamic_cost=DynamicCostDefinition(
                component=CostComponent.STEPS,
                terms=(CostTerm(CostMetric.OPPONENT_BATTLEFIELD_SIZE, 2),),
                offset=1,
                maximum=9,
            ),
        )
        foes = (
            CardDefinition("FOE7A", "Rival A", CardKind.CREATURE, 1, base_strength=1),
            CardDefinition("FOE7B", "Rival B", CardKind.CREATURE, 1, base_strength=1),
        )
        engine = self.make_engine((scalable,), foes)
        card_id = force_zone(engine, "SCALABLE7", "A", Zone.HAND)
        force_zone(engine, "FOE7A", "B", Zone.BATTLEFIELD)
        force_zone(engine, "FOE7B", "B", Zone.BATTLEFIELD)
        engine.state.players["A"].steps = 5

        engine.execute(PlayCard("A", card_id))
        self.assertEqual(engine.state.players["A"].steps, 0)
        played = next(
            event
            for event in reversed(engine.state.event_log)
            if event.event_type == "CARD_PLAYED"
        )
        self.assertEqual(played.payload["printed_cost"], 99)
        self.assertEqual(played.payload["paid_cost"]["steps"], 5)

    def test_dynamic_alternative_and_dynamic_ability_cost_are_atomic(self):
        alternate = CardDefinition(
            "DYNAMIC_ALT7",
            "Alternativa dinámica",
            CardKind.QUICK_RESOURCE,
            50,
            permanent=False,
            transmutable=False,
            alternative_costs=(CompositeCost(wounds=20),),
            dynamic_alternative_costs=(
                DynamicCostDefinition(
                    component=CostComponent.WOUNDS,
                    terms=(CostTerm(CostMetric.OWN_HAND_SIZE),),
                    maximum=6,
                ),
            ),
        )
        engine = self.make_engine((alternate,))
        card_id = force_zone(engine, "DYNAMIC_ALT7", "A", Zone.HAND)
        expected = len(engine.state.players["A"].zones[Zone.HAND])
        engine.execute(PlayCard("A", card_id, cost_option_index=1))
        self.assertEqual(engine.state.players["A"].wounds, min(6, expected))

        ability_card = CardDefinition(
            "DYNAMIC_ABILITY7",
            "Habilidad dinámica",
            CardKind.CREATURE,
            1,
            base_strength=3,
            abilities=(
                AbilityDefinition(
                    "variable",
                    (),
                    dynamic_cost=DynamicCostDefinition(
                        component=CostComponent.STEPS,
                        terms=(CostTerm(CostMetric.OWN_WOUNDS),),
                        base=CompositeCost(exhaust_source=True),
                    ),
                ),
            ),
        )
        engine2 = self.make_engine((ability_card,))
        source = force_zone(engine2, "DYNAMIC_ABILITY7", "A", Zone.BATTLEFIELD)
        engine2.state.players["A"].wounds = 3
        engine2.state.players["A"].steps = 2
        with self.assertRaises(PaymentError):
            engine2.execute(ActivateAbility("A", source, "variable"))
        self.assertFalse(engine2.state.cards[source].exhausted)
        self.assertEqual(engine2.state.players["A"].steps, 2)

        engine2.state.players["A"].steps = 3
        engine2.execute(ActivateAbility("A", source, "variable"))
        self.assertTrue(engine2.state.cards[source].exhausted)
        self.assertEqual(engine2.state.players["A"].steps, 0)

    def test_player_order_overrides_automatic_replacement_priority(self):
        chooser = CardDefinition(
            "CHOOSER7",
            "Elige su destino",
            CardKind.CREATURE,
            4,
            base_strength=4,
            move_replacements=(
                MoveReplacementDefinition(Zone.HAND, priority=100),
                MoveReplacementDefinition(Zone.EXILE, priority=0),
            ),
            player_orders_replacements=True,
        )
        destroy = CardDefinition(
            "DESTROY7",
            "Destruir propio",
            CardKind.QUICK_RESOURCE,
            0,
            permanent=False,
            transmutable=False,
            effects=(
                EffectDefinition(
                    EffectKind.DESTROY,
                    0,
                    TargetMode.CHOSEN_PERMANENT,
                ),
            ),
        )
        engine = self.make_engine((chooser, destroy))
        target = force_zone(engine, "CHOOSER7", "A", Zone.BATTLEFIELD)
        spell = force_zone(engine, "DESTROY7", "A", Zone.HAND)
        orders = [
            action
            for action in engine.legal_actions("A")
            if isinstance(action, SetReplacementOrder) and action.card_id == target
        ]
        self.assertEqual({action.ordered_indices for action in orders}, {(0, 1), (1, 0)})
        with self.assertRaises(IllegalAction):
            engine.execute(SetReplacementOrder("A", target, (1,)))

        engine.execute(SetReplacementOrder("A", target, (1, 0)))
        engine.execute(PlayCard("A", spell, chosen_card_ids=(target,)))
        resolve_one(engine)
        self.assertIn(target, engine.state.players["A"].zones[Zone.EXILE])

    def test_text_patch_changes_keywords_subtypes_abilities_and_transmutation(self):
        original_ability = AbilityDefinition("original", ())
        granted_ability = AbilityDefinition("granted", ())
        target_definition = CardDefinition(
            "PATCH_TARGET7",
            "Texto mutable",
            CardKind.CREATURE,
            3,
            base_strength=3,
            subtypes=frozenset({"HUMANO"}),
            abilities=(original_ability,),
        )
        editor = CardDefinition(
            "EDITOR7",
            "Editar texto",
            CardKind.QUICK_RESOURCE,
            0,
            permanent=False,
            transmutable=False,
            effects=(
                EffectDefinition(
                    EffectKind.MODIFY_TEXT,
                    0,
                    TargetMode.CHOSEN_PERMANENT,
                    duration=EffectDuration.END_OF_TURN,
                    text_patch=TextPatchDefinition(
                        grant_keywords=frozenset({"INDESTRUCTIBLE"}),
                        grant_subtypes=frozenset({"MÍSTICO"}),
                        remove_subtypes=frozenset({"HUMANO"}),
                        add_abilities=(granted_ability,),
                        remove_ability_ids=frozenset({"original"}),
                        set_transmutable=False,
                    ),
                ),
            ),
        )
        engine = self.make_engine((editor, target_definition))
        target = force_zone(engine, "PATCH_TARGET7", "A", Zone.BATTLEFIELD)
        spell = force_zone(engine, "EDITOR7", "A", Zone.HAND)
        engine.execute(PlayCard("A", spell, chosen_card_ids=(target,)))
        resolve_one(engine)

        effective = engine._definition(target)
        self.assertIn("INDESTRUCTIBLE", effective.keywords)
        self.assertEqual(effective.subtypes, frozenset({"MÍSTICO"}))
        self.assertEqual(tuple(item.ability_id for item in effective.abilities), ("granted",))
        self.assertFalse(effective.transmutable)

        engine._cleanup_end_of_turn()
        restored = engine._definition(target)
        self.assertNotIn("INDESTRUCTIBLE", restored.keywords)
        self.assertEqual(restored.subtypes, frozenset({"HUMANO"}))
        self.assertEqual(tuple(item.ability_id for item in restored.abilities), ("original",))
        self.assertTrue(restored.transmutable)


if __name__ == "__main__":
    unittest.main()
