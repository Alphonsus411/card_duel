import unittest

from card_duel_engine.catalog import CardCatalog
from card_duel_engine.domain.enums import CardKind, CardRank, CostComponent, CostMetric, EffectKind, LordDomain, Phase, TargetMode, TriggerKind, Zone
from card_duel_engine.domain.models import (
    AbilityDefinition, CardDefinition, CardFilter, CompositeCost, ContinuousEffectDefinition,
    CostTerm, DynamicCostDefinition, EffectDefinition, EffectPatchDefinition,
    MoveReplacementDefinition, TargetAllocation, TextPatchDefinition, XCostDefinition,
)
from card_duel_engine.rules.config import RuleSet


class DomainValidationTests(unittest.TestCase):
    def assert_invalid(self, constructor, *args, **kwargs):
        with self.assertRaises(ValueError): constructor(*args, **kwargs)

    def test_cost_and_patch_definitions_reject_ambiguous_or_impossible_data(self):
        self.assert_invalid(CompositeCost, steps=-1)
        self.assert_invalid(DynamicCostDefinition, CostComponent.STEPS, ())
        term = CostTerm(CostMetric.OWN_STEPS)
        self.assert_invalid(DynamicCostDefinition, CostComponent.STEPS, (term,), minimum=-1)
        self.assert_invalid(DynamicCostDefinition, CostComponent.STEPS, (term,), minimum=2, maximum=1)
        self.assert_invalid(XCostDefinition, CostComponent.STEPS, multiplier=0)
        self.assert_invalid(XCostDefinition, CostComponent.STEPS, minimum=-1)
        self.assert_invalid(EffectPatchDefinition, -1)
        self.assert_invalid(EffectPatchDefinition, 0, ability_id="a", legendary=True)
        self.assert_invalid(TextPatchDefinition, grant_keywords=frozenset({"X"}), remove_keywords=frozenset({"X"}))
        self.assert_invalid(TextPatchDefinition, grant_subtypes=frozenset({"X"}), remove_subtypes=frozenset({"X"}))
        ability = AbilityDefinition("a", ())
        self.assert_invalid(TextPatchDefinition, add_abilities=(ability, ability))

    def test_effect_schema_rejects_every_invalid_target_and_payload_shape(self):
        invalid = [
            (EffectKind.DEAL_WOUNDS, -1, {}),
            (EffectKind.DEAL_WOUNDS, 1, {"x_multiplier": -1}),
            (EffectKind.DEAL_WOUNDS, 1, {"minimum_targets": -1}),
            (EffectKind.DEAL_WOUNDS, 1, {"target": TargetMode.SOURCE}),
            (EffectKind.TAP, 1, {"target": TargetMode.SELF}),
            (EffectKind.MOVE_CARDS, 1, {"target": TargetMode.SELF}),
            (EffectKind.DEAL_HARM, 1, {"target": TargetMode.SELF}),
            (EffectKind.DEAL_HARM, 1, {"target": TargetMode.CHOSEN_ENTITY}),
            (EffectKind.DEAL_HARM, 0, {"target": TargetMode.CHOSEN_ENTITY, "distributed": True}),
            (EffectKind.MOVE_CARDS, 1, {"target": TargetMode.CHOSEN_ZONE}),
            (EffectKind.MOVE_CARDS, 0, {"target": TargetMode.CHOSEN_ZONE, "destination_zone": Zone.HAND}),
            (EffectKind.SEARCH_ZONE, 1, {"target": TargetMode.CHOSEN_ZONE}),
            (EffectKind.SEARCH_ZONE, 1, {"target": TargetMode.CHOSEN_ZONE, "destination_zone": Zone.HAND, "selection_minimum": 2, "selection_maximum": 1}),
            (EffectKind.TRANSFORM_DEFINITION, 1, {"target": TargetMode.SOURCE}),
            (EffectKind.MODIFY_TEXT, 1, {"target": TargetMode.SOURCE}),
            (EffectKind.TAP, 1, {"target": TargetMode.SOURCE, "text_patch": TextPatchDefinition()}),
            (EffectKind.SKIP_PHASE, 1, {}),
            (EffectKind.DEAL_WOUNDS, 1, {"distributed": True}),
        ]
        for kind, amount, kwargs in invalid:
            with self.subTest(kind=kind, kwargs=kwargs): self.assert_invalid(EffectDefinition, kind, amount, **kwargs)

    def test_ability_card_and_replacement_invariants(self):
        self.assert_invalid(TargetAllocation, "x", 0)
        self.assert_invalid(MoveReplacementDefinition, Zone.VOID)
        self.assert_invalid(ContinuousEffectDefinition, grant_keywords=frozenset({"X"}), remove_keywords=frozenset({"X"}))
        self.assert_invalid(AbilityDefinition, "", ())
        fixed = CompositeCost(steps=1); dynamic = DynamicCostDefinition(CostComponent.STEPS, (CostTerm(CostMetric.OWN_STEPS),))
        xcost = XCostDefinition(CostComponent.STEPS)
        self.assert_invalid(AbilityDefinition, "a", (), cost=fixed, trigger=TriggerKind.ON_TRANSMUTED)
        self.assert_invalid(AbilityDefinition, "a", (), cost=fixed, dynamic_cost=dynamic)
        self.assert_invalid(AbilityDefinition, "a", (), cost=fixed, x_cost=xcost)
        self.assert_invalid(CardDefinition, "x", "X", CardKind.ARTIFACT, -1)
        self.assert_invalid(CardDefinition, "x", "X", CardKind.CREATURE, 1)
        self.assert_invalid(CardDefinition, "x", "X", CardKind.LORD, 1)
        self.assert_invalid(CardDefinition, "x", "X", CardKind.ARTIFACT, 1, alternative_costs=(CompositeCost(strength=1),))
        self.assert_invalid(CardDefinition, "x", "X", CardKind.ARTIFACT, 1, player_orders_replacements=True)
        replacement = MoveReplacementDefinition(Zone.HAND)
        self.assert_invalid(CardDefinition, "x", "X", CardKind.ARTIFACT, 1, move_replacement=replacement, player_orders_replacements=True, deferred_replacement_choice=True)
        self.assert_invalid(CardDefinition, "x", "X", CardKind.ARTIFACT, 1, move_replacement=replacement, deferred_replacement_choice=True)
        self.assert_invalid(CardDefinition, "x", "X", CardKind.ARTIFACT, 1, dynamic_cost=dynamic, x_cost=xcost)
        strength_dynamic = DynamicCostDefinition(CostComponent.STRENGTH, (CostTerm(CostMetric.OWN_STEPS),))
        self.assert_invalid(CardDefinition, "x", "X", CardKind.ARTIFACT, 1, dynamic_cost=strength_dynamic)
        strength_x = XCostDefinition(CostComponent.STRENGTH)
        self.assert_invalid(CardDefinition, "x", "X", CardKind.ARTIFACT, 1, x_cost=strength_x)
        harm = EffectDefinition(EffectKind.DEAL_HARM, 1, TargetMode.CHOSEN_ENTITY, distributed=True)
        self.assert_invalid(CardDefinition, "x", "X", CardKind.ARTIFACT, 1, effects=(harm, harm))
        self.assert_invalid(CardDefinition, "x", "X", CardKind.ARTIFACT, 1, legendary_effects=(harm, harm))
        duplicate = AbilityDefinition("same", ())
        self.assert_invalid(CardDefinition, "x", "X", CardKind.ARTIFACT, 1, abilities=(duplicate, duplicate))
        distributed_ability = AbilityDefinition("harm", (harm, harm))
        self.assert_invalid(CardDefinition, "x", "X", CardKind.ARTIFACT, 1, abilities=(distributed_ability,))
        lord = CardDefinition("lord", "Lord", CardKind.LORD, 1, lord_domain=LordDomain.ABYSS)
        self.assertEqual(lord.lord_domain, LordDomain.ABYSS)

    def test_filters_catalog_and_ruleset_reject_non_matching_or_invalid_inputs(self):
        card = CardDefinition("card", "Card", CardKind.ARTIFACT, 1, subtypes=frozenset({"A"}))
        self.assertFalse(CardFilter(kinds=frozenset({CardKind.CREATURE})).matches(card))
        self.assertFalse(CardFilter(ranks=frozenset({CardRank.DIVINE})).matches(card))
        self.assertFalse(CardFilter(subtypes=frozenset({"B"})).matches(card))
        self.assertFalse(CardFilter(definition_ids=frozenset({"other"})).matches(card))
        with self.assertRaises(KeyError): CardCatalog().get("missing")
        for kwargs in (
            {"initial_hand_size": 0}, {"hand_limit": 0}, {"wound_limit": 0},
            {"steps_per_maintenance": -1}, {"legal_action_enumeration_limit": 0},
            {"minimum_players": 1}, {"phase_sequence": (Phase.DRAW, Phase.DRAW)},
            {"phase_sequence": (Phase.DRAW, Phase.DISCARD)},
        ):
            with self.subTest(kwargs=kwargs): self.assert_invalid(RuleSet, **kwargs)


if __name__ == "__main__": unittest.main()
