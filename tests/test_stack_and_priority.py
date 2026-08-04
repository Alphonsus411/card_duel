import unittest

from card_duel_engine import GameEngine, RuleSet
from card_duel_engine.domain.enums import CardKind, CardRank, EffectKind, LordDomain, Phase, TargetMode, TriggerKind, Zone
from card_duel_engine.domain.errors import IllegalAction, PaymentError
from card_duel_engine.domain.models import AbilityDefinition, AbilitySourceProfile, CardDefinition, CompositeCost, EffectDefinition, StackItem
from card_duel_engine.engine.commands import ActivateAbility, AdvancePhase, PassPriority, PlayCard
from card_duel_engine.persistence.snapshot import dump_snapshot, load_snapshot

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
    def make_ability_source_engine(self) -> tuple[GameEngine, dict[str, str]]:
        activated = AbilityDefinition("pulse", ())
        triggered = AbilityDefinition(
            "arrival", (), trigger=TriggerKind.ON_ENTER_BATTLEFIELD
        )
        definitions = (
            CardDefinition(
                "permanent", "Permanente", CardKind.CREATURE, 0,
                base_strength=2, abilities=(activated,),
            ),
            CardDefinition(
                "other-permanent", "Permanente ajeno", CardKind.CREATURE, 0,
                base_strength=2, abilities=(activated,),
            ),
            CardDefinition(
                "non-permanent", "No permanente", CardKind.EVENT, 0,
                permanent=False, abilities=(activated,),
            ),
            CardDefinition(
                "triggered", "Disparada", CardKind.CREATURE, 0,
                base_strength=2, abilities=(triggered,),
            ),
        )
        engine = GameEngine(RuleSet())
        engine.new_match({
            "A": [definitions[0], definitions[2], definitions[3], *test_deck("ASA", 9)],
            "B": [definitions[1], *test_deck("ASB", 11)],
        }, seed=91)
        ids = {
            "permanent": force_zone(engine, "permanent", "A", Zone.BATTLEFIELD),
            "other": force_zone(engine, "other-permanent", "B", Zone.BATTLEFIELD),
            "non_permanent": force_zone(engine, "non-permanent", "A", Zone.BATTLEFIELD),
            "triggered": force_zone(engine, "triggered", "A", Zone.BATTLEFIELD),
        }
        engine.state.priority_player_id = "A"
        return engine, ids

    def transform_source(self, engine: GameEngine, source_id: str, definition_id: str) -> None:
        engine._effects.apply(
            EffectDefinition(
                EffectKind.TRANSFORM_DEFINITION, 1,
                TargetMode.CHOSEN_PERMANENT,
                transform_definition_id=definition_id,
            ),
            StackItem("transform-test", "A", source_id, ()),
            source_id,
        )

    def test_normal_permanent_is_an_activatable_source(self):
        engine, ids = self.make_ability_source_engine()

        actions = engine._legal_ability_activations("A", ids["permanent"])

        self.assertEqual([action.ability_id for action in actions], ["pulse"])
        engine.execute(actions[0])

    def test_source_transformed_to_non_permanent_cannot_activate(self):
        engine, ids = self.make_ability_source_engine()
        self.transform_source(engine, ids["permanent"], "non-permanent")

        self.assertEqual(engine._legal_ability_activations("A", ids["permanent"]), [])
        with self.assertRaises(IllegalAction):
            engine.execute(ActivateAbility("A", ids["permanent"], "pulse"))

    def test_source_outside_battlefield_cannot_activate(self):
        engine, ids = self.make_ability_source_engine()
        source_id = ids["permanent"]
        force_zone(engine, "permanent", "A", Zone.HAND)

        self.assertEqual(engine._legal_ability_activations("A", source_id), [])
        with self.assertRaises(IllegalAction):
            engine.execute(ActivateAbility("A", source_id, "pulse"))

    def test_opponents_source_cannot_activate(self):
        engine, ids = self.make_ability_source_engine()

        self.assertEqual(engine._legal_ability_activations("A", ids["other"]), [])
        with self.assertRaises(IllegalAction):
            engine.execute(ActivateAbility("A", ids["other"], "pulse"))

    def test_triggered_ability_is_not_announced_as_activated(self):
        engine, ids = self.make_ability_source_engine()

        self.assertTrue(engine._ability_source_can_activate("A", ids["triggered"]))
        self.assertEqual(engine._legal_ability_activations("A", ids["triggered"]), [])
        with self.assertRaises(IllegalAction):
            engine.execute(ActivateAbility("A", ids["triggered"], "arrival"))

    def test_source_transformed_from_non_permanent_to_permanent_can_activate(self):
        engine, ids = self.make_ability_source_engine()
        self.transform_source(engine, ids["non_permanent"], "permanent")

        actions = engine._legal_ability_activations("A", ids["non_permanent"])

        self.assertEqual([action.ability_id for action in actions], ["pulse"])
        engine.execute(actions[0])

    def test_every_announced_ability_activation_executes_from_independent_snapshot(self):
        engine, ids = self.make_ability_source_engine()
        self.transform_source(engine, ids["non_permanent"], "permanent")
        snapshot = dump_snapshot(engine, indent=None)
        announced = tuple(
            action for action in engine.legal_actions("A")
            if isinstance(action, ActivateAbility)
        )
        self.assertTrue(announced)

        for action in announced:
            with self.subTest(action=action):
                restored = load_snapshot(snapshot)
                try:
                    restored.execute(action)
                except IllegalAction as exc:
                    self.fail(f"Una activación anunciada fue ilegal: {exc}")

    def test_source_profile_freezes_copied_and_transformed_effective_definition(self):
        ability = AbilityDefinition("pulse", ())
        artifact = CardDefinition("artifact", "Artefacto", CardKind.ARTIFACT, 0)
        event = CardDefinition(
            "event", "Evento", CardKind.EVENT, 0,
            permanent=False, abilities=(ability,),
        )
        quick = CardDefinition(
            "quick", "Recurso Rápido", CardKind.QUICK_RESOURCE, 0,
            permanent=False, abilities=(ability,),
        )
        lord = CardDefinition(
            "lord", "Señor", CardKind.LORD, 0,
            lord_domain=LordDomain.REALMS, abilities=(ability,),
        )
        creature = CardDefinition(
            "creature", "Criatura", CardKind.CREATURE, 0,
            base_strength=2, abilities=(ability,),
        )
        engine = GameEngine(RuleSet())
        engine.new_match(
            {
                "A": [artifact, event, quick, lord, creature, *test_deck("PA", 7)],
                "B": test_deck("PB", 12),
            }, seed=88,
        )
        source_id = force_zone(engine, "artifact", "A", Zone.BATTLEFIELD)
        target_id = force_zone(engine, "event", "A", Zone.BATTLEFIELD)
        item = StackItem("copy", "A", source_id, ())

        engine._effects.apply(
            EffectDefinition(EffectKind.COPY_DEFINITION, 1, TargetMode.CHOSEN_PERMANENT),
            item, target_id,
        )
        copied = engine._ability_source_profile(source_id)
        self.assertIs(copied.effective_kind, CardKind.EVENT)
        self.assertFalse(copied.was_permanent)

        engine._effects.apply(
            EffectDefinition(
                EffectKind.TRANSFORM_DEFINITION, 1, TargetMode.CHOSEN_PERMANENT,
                transform_definition_id="quick",
            ), item, source_id,
        )
        transformed = engine._ability_source_profile(source_id)
        self.assertIs(transformed.effective_kind, CardKind.QUICK_RESOURCE)
        self.assertFalse(transformed.was_permanent)

        lord_id = force_zone(engine, "lord", "A", Zone.BATTLEFIELD)
        engine._effects.apply(
            EffectDefinition(
                EffectKind.TRANSFORM_DEFINITION, 1, TargetMode.CHOSEN_PERMANENT,
                transform_definition_id="creature",
            ), StackItem("transform", "A", lord_id, ()), lord_id,
        )
        converted_lord = engine._ability_source_profile(lord_id)
        self.assertIs(converted_lord.effective_kind, CardKind.CREATURE)
        self.assertTrue(converted_lord.was_effective_creature)

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

    def test_uncertain_missing_source_fizzles_and_priority_keeps_advancing(self):
        engine, _, _ = self.make_engine()
        target_id = force_zone(engine, "B-000", "B", Zone.BATTLEFIELD)
        target = engine.catalog.get("B-000")
        engine.catalog._cards["B-000"] = CardDefinition(
            target.card_id, target.name, target.kind, target.cost,
            rank=CardRank.DIVINE, base_strength=target.base_strength,
        )
        engine.state.stack.append(StackItem(
            "legacy-missing", "A", "missing-source",
            (EffectDefinition(EffectKind.DEAL_DAMAGE, 1, TargetMode.CHOSEN_PERMANENT),),
            chosen_card_ids=(target_id,), ability_id="old",
            ability_source_profile=AbilitySourceProfile(
                "missing-source", CardKind.EVENT, True, True, False,
                nature_is_certain=False,
            ),
        ))
        engine.state.priority_player_id = "B"
        engine.execute(PassPriority("B"))
        engine.execute(PassPriority("A"))
        self.assertFalse(engine.state.stack)
        self.assertEqual(engine.state.cards[target_id].damage, 0)
        self.assertEqual(engine.state.event_log[-1].event_type, "STACK_ITEM_RESOLVED")
        self.assertEqual(engine.state.priority_player_id, engine.state.active_player_id)
