import unittest

from card_duel_engine import GameEngine, RuleSet
from card_duel_engine.domain import (
    AbilityDefinition,
    CardDefinition,
    CardFilter,
    CardKind,
    CompositeCost,
    EffectDefinition,
    EffectDuration,
    EffectKind,
    MoveReplacementDefinition,
    TargetMode,
    Zone,
    ZoneTarget,
)
from card_duel_engine.domain.errors import IllegalAction, PaymentError
from card_duel_engine.engine import (
    ActivateAbility,
    PassPriority,
    PlayCard,
    ResolveSearchChoice,
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


class ExtensibilityV060Tests(unittest.TestCase):
    def make_engine(self, a_specials=(), b_specials=(), seed=60):
        engine = GameEngine(RuleSet())
        engine.new_match(
            {
                "A": [*a_specials, *test_deck("A6", 14)],
                "B": [*b_specials, *test_deck("B6", 14)],
            },
            seed=seed,
        )
        return engine

    def test_hidden_search_pauses_resolution_and_only_chooser_sees_candidates(self):
        prize = CardDefinition("PRIZE", "Objetivo", CardKind.CREATURE, 2, base_strength=2)
        searcher = CardDefinition(
            "SEARCHER",
            "Búsqueda privada",
            CardKind.QUICK_RESOURCE,
            0,
            permanent=False,
            transmutable=False,
            effects=(
                EffectDefinition(
                    EffectKind.SEARCH_ZONE,
                    0,
                    TargetMode.CHOSEN_ZONE,
                    destination_zone=Zone.HAND,
                    search_filter=CardFilter(definition_ids=frozenset({"PRIZE"})),
                    reveal_search_selection=False,
                ),
            ),
        )
        engine = self.make_engine((searcher, prize))
        spell = force_zone(engine, "SEARCHER", "A", Zone.HAND)
        selected = force_zone(engine, "PRIZE", "A", Zone.DECK)
        engine.execute(
            PlayCard(
                "A",
                spell,
                chosen_zone_targets=(ZoneTarget("A", Zone.DECK),),
            )
        )
        resolve_one(engine)

        self.assertIsNotNone(engine.state.pending_search)
        self.assertEqual(engine.observe("A").searchable_card_ids, (selected,))
        self.assertEqual(engine.observe("B").searchable_card_ids, ())
        with self.assertRaises(IllegalAction):
            engine.execute(ResolveSearchChoice("B", (selected,)))

        engine.execute(ResolveSearchChoice("A", (selected,)))
        self.assertIn(selected, engine.state.players["A"].zones[Zone.HAND])
        self.assertIsNone(engine.state.pending_search)
        completion = next(
            event
            for event in reversed(engine.state.event_log)
            if event.event_type == "SEARCH_COMPLETED"
        )
        self.assertEqual(completion.payload, {"selected_count": 1})
        self.assertTrue(
            any(event.event_type == "ZONE_SHUFFLED" for event in engine.state.event_log)
        )

    def test_explicit_shuffle_is_deterministic_for_the_same_seed(self):
        shuffle = CardDefinition(
            "SHUFFLE",
            "Barajar",
            CardKind.QUICK_RESOURCE,
            0,
            permanent=False,
            transmutable=False,
            effects=(
                EffectDefinition(
                    EffectKind.SHUFFLE_ZONE,
                    0,
                    TargetMode.CHOSEN_ZONE,
                ),
            ),
        )
        orders = []
        for _ in range(2):
            engine = self.make_engine((shuffle,), seed=601)
            spell = force_zone(engine, "SHUFFLE", "A", Zone.HAND)
            engine.execute(
                PlayCard(
                    "A",
                    spell,
                    chosen_zone_targets=(ZoneTarget("A", Zone.DECK),),
                )
            )
            resolve_one(engine)
            orders.append(tuple(engine.state.players["A"].zones[Zone.DECK]))
        self.assertEqual(orders[0], orders[1])

    def test_temporary_control_moves_the_permanent_and_restores_it(self):
        seize = CardDefinition(
            "SEIZE",
            "Tomar control",
            CardKind.QUICK_RESOURCE,
            0,
            permanent=False,
            transmutable=False,
            effects=(
                EffectDefinition(
                    EffectKind.CHANGE_CONTROL,
                    0,
                    TargetMode.CHOSEN_PERMANENT,
                    duration=EffectDuration.END_OF_TURN,
                ),
            ),
        )
        victim = CardDefinition("VICTIM", "Objetivo", CardKind.CREATURE, 4, base_strength=4)
        engine = self.make_engine((seize,), (victim,))
        spell = force_zone(engine, "SEIZE", "A", Zone.HAND)
        target = force_zone(engine, "VICTIM", "B", Zone.BATTLEFIELD)
        engine.execute(PlayCard("A", spell, chosen_card_ids=(target,)))
        resolve_one(engine)
        self.assertIn(target, engine.state.players["A"].zones[Zone.BATTLEFIELD])
        self.assertEqual(engine.state.cards[target].controller_id, "A")

        engine._cleanup_end_of_turn()
        engine.validate_invariants()
        self.assertIn(target, engine.state.players["B"].zones[Zone.BATTLEFIELD])
        self.assertEqual(engine.state.cards[target].controller_id, "B")

    def test_copy_and_full_transformation_restore_at_end_of_turn(self):
        mimic = CardDefinition(
            "MIMIC",
            "Mímico",
            CardKind.CREATURE,
            1,
            base_strength=1,
            abilities=(
                AbilityDefinition(
                    "copy",
                    (
                        EffectDefinition(
                            EffectKind.COPY_DEFINITION,
                            0,
                            TargetMode.CHOSEN_PERMANENT,
                            duration=EffectDuration.END_OF_TURN,
                        ),
                    ),
                ),
            ),
        )
        giant = CardDefinition("GIANT6", "Gigante", CardKind.CREATURE, 9, base_strength=9)
        form = CardDefinition("FORM6", "Forma", CardKind.CREATURE, 7, base_strength=7)
        transform = CardDefinition(
            "TRANSFORM6",
            "Transformar",
            CardKind.QUICK_RESOURCE,
            0,
            permanent=False,
            transmutable=False,
            effects=(
                EffectDefinition(
                    EffectKind.TRANSFORM_DEFINITION,
                    0,
                    TargetMode.CHOSEN_PERMANENT,
                    duration=EffectDuration.END_OF_TURN,
                    transform_definition_id="FORM6",
                ),
            ),
        )
        engine = self.make_engine((mimic, transform, form), (giant,))
        source = force_zone(engine, "MIMIC", "A", Zone.BATTLEFIELD)
        giant_id = force_zone(engine, "GIANT6", "B", Zone.BATTLEFIELD)
        form_id = force_zone(engine, "FORM6", "A", Zone.EXILE)
        engine.execute(ActivateAbility("A", source, "copy", chosen_card_ids=(giant_id,)))
        resolve_one(engine)
        self.assertEqual(engine._definition(source).card_id, "GIANT6")
        self.assertEqual(engine._current_strength(source), 9)

        engine.state.priority_player_id = "A"
        spell = force_zone(engine, "TRANSFORM6", "A", Zone.HAND)
        engine.execute(PlayCard("A", spell, chosen_card_ids=(giant_id,)))
        resolve_one(engine)
        self.assertEqual(engine._definition(giant_id).card_id, "FORM6")
        self.assertEqual(engine._current_strength(giant_id), 7)
        self.assertIn(form_id, engine.state.players["A"].zones[Zone.EXILE])

        engine._cleanup_end_of_turn()
        self.assertEqual(engine._definition(source).card_id, "MIMIC")
        self.assertEqual(engine._definition(giant_id).card_id, "GIANT6")

    def test_alternative_cost_can_pay_wounds_and_mill_atomically(self):
        alternate = CardDefinition(
            "ALTERNATE",
            "Coste alternativo",
            CardKind.QUICK_RESOURCE,
            50,
            permanent=False,
            transmutable=False,
            alternative_costs=(CompositeCost(wounds=3, mill_count=2),),
        )
        engine = self.make_engine((alternate,))
        card_id = force_zone(engine, "ALTERNATE", "A", Zone.HAND)
        engine.state.players["A"].steps = 0
        deck_before = len(engine.state.players["A"].zones[Zone.DECK])
        discard_before = len(engine.state.players["A"].zones[Zone.DISCARD])
        engine.execute(PlayCard("A", card_id, cost_option_index=0))
        self.assertEqual(engine.state.players["A"].wounds, 3)
        self.assertEqual(len(engine.state.players["A"].zones[Zone.DECK]), deck_before - 2)
        self.assertEqual(
            len(engine.state.players["A"].zones[Zone.DISCARD]), discard_before + 2
        )

        impossible = CardDefinition(
            "IMPOSSIBLE",
            "Coste imposible",
            CardKind.QUICK_RESOURCE,
            50,
            permanent=False,
            transmutable=False,
            alternative_costs=(CompositeCost(mill_count=999),),
        )
        other = self.make_engine((impossible,))
        impossible_id = force_zone(other, "IMPOSSIBLE", "A", Zone.HAND)
        before = tuple(other.state.players["A"].zones[Zone.HAND])
        with self.assertRaises(PaymentError):
            other.execute(PlayCard("A", impossible_id, cost_option_index=0))
        self.assertEqual(tuple(other.state.players["A"].zones[Zone.HAND]), before)

    def test_multiple_move_replacements_use_highest_priority(self):
        resilient = CardDefinition(
            "RESILIENT6",
            "Resiliente",
            CardKind.CREATURE,
            5,
            base_strength=5,
            move_replacements=(
                MoveReplacementDefinition(Zone.HAND, priority=10),
                MoveReplacementDefinition(Zone.EXILE, priority=50),
            ),
        )
        destroy = CardDefinition(
            "DESTROY6",
            "Destruir",
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
        engine = self.make_engine((destroy,), (resilient,))
        spell = force_zone(engine, "DESTROY6", "A", Zone.HAND)
        target = force_zone(engine, "RESILIENT6", "B", Zone.BATTLEFIELD)
        engine.execute(PlayCard("A", spell, chosen_card_ids=(target,)))
        resolve_one(engine)
        self.assertIn(target, engine.state.players["B"].zones[Zone.EXILE])
        replacement_event = next(
            event
            for event in reversed(engine.state.event_log)
            if event.event_type == "MOVE_REPLACED" and event.card_id == target
        )
        self.assertEqual(replacement_event.payload["destination"], "EXILE")


if __name__ == "__main__":
    unittest.main()
