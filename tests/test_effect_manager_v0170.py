from __future__ import annotations

from copy import deepcopy
import unittest

from card_duel_engine.catalog import CardCatalog
from card_duel_engine.domain.enums import CardKind, CardRank, EffectDuration, EffectKind, MatchStatus, Phase, TargetMode, Zone
from card_duel_engine.domain.errors import UnsupportedEffectError
from card_duel_engine.domain.models import AbilitySourceProfile, CardDefinition, CardInstance, EffectDefinition, GameState, PlayerState, StackItem, TargetAllocation, TextPatchDefinition, ZoneTarget
from card_duel_engine.engine.effects import EffectManager
from card_duel_engine import GameEngine


def engine_with_battlefield() -> tuple[GameEngine, StackItem, str]:
    source = CardDefinition("source", "Source", CardKind.ARTIFACT, 0)
    target = CardDefinition("target", "Target", CardKind.CREATURE, 1, base_strength=3)
    engine = GameEngine(catalog=CardCatalog({"source": source, "target": target}))
    state = GameState(
        ruleset_id="base", ruleset_version="0.17.0",
        players={"A": PlayerState("A"), "B": PlayerState("B")}, turn_order=("A", "B"),
        cards={
            "source-i": CardInstance("source-i", "source", "A", "A", Zone.BATTLEFIELD),
            "target-i": CardInstance("target-i", "target", "B", "B", Zone.BATTLEFIELD),
        }, priority_player_id="A", phase=Phase.EFFECTS,
        status=MatchStatus.RUNNING,
    )
    state.players["A"].zones[Zone.BATTLEFIELD].append("source-i")
    state.players["B"].zones[Zone.BATTLEFIELD].append("target-i")
    engine.state = state
    item = StackItem("stack-1", "A", "source-i", ()); return engine, item, "target-i"


class EffectManagerTests(unittest.TestCase):
    def test_resolution_uses_captured_source_profile_for_divine_targeting(self):
        for effective_creature, expected_damage in ((True, 0), (False, 1)):
            with self.subTest(effective_creature=effective_creature):
                engine, _, target = engine_with_battlefield()
                state = engine._require_running_state()
                divine = engine.catalog.get("target")
                engine.catalog._cards["target"] = CardDefinition(
                    divine.card_id, divine.name, divine.kind, divine.cost,
                    rank=CardRank.DIVINE, base_strength=divine.base_strength,
                )
                state.players["A"].zones[Zone.BATTLEFIELD].remove("source-i")
                state.players["A"].zones[Zone.DISCARD].append("source-i")
                state.cards["source-i"].zone = Zone.DISCARD
                profile = AbilitySourceProfile(
                    "source-i", CardKind.ARTIFACT, effective_creature, True, True
                )
                item = StackItem(
                    "stack-profile", "A", "source-i", (), ability_id="ability",
                    ability_source_profile=profile,
                )
                EffectManager(engine).apply(
                    EffectDefinition(EffectKind.DEAL_DAMAGE, 1, TargetMode.CHOSEN_PERMANENT),
                    item,
                    target,
                )
                self.assertEqual(state.cards[target].damage, expected_damage)
                if effective_creature:
                    self.assertEqual(state.event_log[-1].event_type, "EFFECT_FIZZLED")

    def test_acquired_ability_immunity_is_a_normal_fizzle(self):
        engine, _, target = engine_with_battlefield()
        state = engine._require_running_state()
        state.players["A"].zones[Zone.BATTLEFIELD].remove("source-i")
        state.players["A"].zones[Zone.DISCARD].append("source-i")
        state.cards["source-i"].zone = Zone.DISCARD
        definition = engine.catalog.get("target")
        engine.catalog._cards["target"] = CardDefinition(
            definition.card_id, definition.name, definition.kind, definition.cost,
            base_strength=definition.base_strength,
            keywords=frozenset({"IMMUNE_ABILITIES"}),
        )
        item = StackItem(
            "stack-immune", "A", "source-i", (), ability_id="ability",
            ability_source_profile=AbilitySourceProfile(
                "source-i", CardKind.ARTIFACT, False, True, True
            ),
        )
        EffectManager(engine).apply(
            EffectDefinition(EffectKind.DEAL_DAMAGE, 1, TargetMode.CHOSEN_PERMANENT),
            item,
            target,
        )
        self.assertEqual(state.cards[target].damage, 0)
        self.assertEqual(state.event_log[-1].payload["reason"], "immune")
    def test_closed_registry_contains_every_effect_kind(self):
        engine, _, _ = engine_with_battlefield()
        self.assertEqual(engine._effects.supported_kinds, frozenset(EffectKind))

    def test_player_and_permanent_handlers_apply_without_owning_state(self):
        engine, item, target = engine_with_battlefield(); manager = EffectManager(engine)
        state = engine._require_running_state(); state.players["A"].wounds = 4
        manager.apply(EffectDefinition(EffectKind.HEAL_WOUNDS, 2), item)
        manager.apply(EffectDefinition(EffectKind.GAIN_STEPS, 3), item)
        manager.apply(EffectDefinition(EffectKind.PREVENT_WOUNDS, 1), item)
        for kind in (EffectKind.TAP, EffectKind.UNTAP, EffectKind.PREVENT_DAMAGE, EffectKind.ADD_REGENERATION):
            manager.apply(EffectDefinition(kind, 1, TargetMode.CHOSEN_PERMANENT), item, target)
        self.assertEqual(state.players["A"].wounds, 2)
        self.assertEqual(state.players["A"].steps, 3)
        self.assertEqual(state.cards[target].damage_prevention, 1)
        self.assertIs(manager._context, engine)

    def test_invalid_target_is_atomic_and_diagnostic(self):
        engine, item, _ = engine_with_battlefield(); before = deepcopy(engine.state)
        EffectManager(engine).apply(
            EffectDefinition(EffectKind.TAP, 1, TargetMode.CHOSEN_PERMANENT), item, "missing"
        )
        assert engine.state is not None and before is not None
        self.assertEqual(engine.state.players, before.players)
        self.assertEqual(engine.state.cards, before.cards)
        self.assertEqual(engine.state.event_log[-1].event_type, "EFFECT_FIZZLED")
        self.assertEqual(engine.state.event_log[-1].payload["reason"], "invalid_target")

    def test_missing_registered_handler_raises_domain_error_without_mutation(self):
        engine, item, _ = engine_with_battlefield(); manager = EffectManager(engine)
        manager._handlers.pop(EffectKind.GAIN_STEPS); before = deepcopy(engine.state)
        with self.assertRaises(UnsupportedEffectError):
            manager.apply(EffectDefinition(EffectKind.GAIN_STEPS, 1), item)
        self.assertEqual(engine.state, before)

    def test_remaining_handlers_and_resolution_branches(self):
        engine, item, target = engine_with_battlefield(); manager = EffectManager(engine)
        state = engine._require_running_state()
        manager.apply(EffectDefinition(EffectKind.DEAL_WOUNDS, 2), item)
        manager.apply(EffectDefinition(EffectKind.DEAL_DAMAGE, 1, TargetMode.CHOSEN_PERMANENT), item, target)
        manager.apply(EffectDefinition(EffectKind.MODIFY_STRENGTH, -1, TargetMode.CHOSEN_PERMANENT, EffectDuration.END_OF_TURN), item, target)
        manager.apply(EffectDefinition(EffectKind.BECOME_CREATURE, 1, TargetMode.CHOSEN_PERMANENT, EffectDuration.END_OF_TURN), item, target)
        manager.apply(EffectDefinition(EffectKind.CHANGE_CONTROL, 1, TargetMode.CHOSEN_PERMANENT, EffectDuration.END_OF_TURN), item, target)
        manager.apply(EffectDefinition(EffectKind.COPY_DEFINITION, 1, TargetMode.CHOSEN_PERMANENT), item, target)
        manager.apply(EffectDefinition(EffectKind.TRANSFORM_DEFINITION, 1, TargetMode.CHOSEN_PERMANENT, transform_definition_id="missing"), item, target)
        manager.apply(EffectDefinition(EffectKind.MODIFY_TEXT, 1, TargetMode.CHOSEN_PERMANENT, text_patch=TextPatchDefinition(grant_keywords=frozenset({"FLYING"}))), item, target)
        manager.apply(EffectDefinition(EffectKind.SKIP_PHASE, 1, phase=Phase.DRAW, duration=EffectDuration.NEXT_OCCURRENCE), item)
        manager.apply(EffectDefinition(EffectKind.DEAL_HARM, 2, TargetMode.CHOSEN_ENTITY, distributed=True), item, TargetAllocation("A", 2))
        self.assertTrue(state.timed_modifiers and state.control_changes and state.text_patches)
        self.assertTrue(state.phase_suppressions)

    def test_zone_handlers_use_the_exact_selected_zone(self):
        engine, item, _ = engine_with_battlefield(); state = engine._require_running_state()
        card = CardInstance("deck-i", "target", "A", "A", Zone.DECK)
        state.cards[card.instance_id] = card; state.players["A"].zones[Zone.DECK].append(card.instance_id)
        zone_target = ZoneTarget("A", Zone.DECK)
        item = StackItem("stack-zone", "A", "source-i", (), chosen_zone_targets=(zone_target,))
        EffectManager(engine).apply(EffectDefinition(EffectKind.MOVE_CARDS, 1, TargetMode.CHOSEN_ZONE, destination_zone=Zone.HAND), item, zone_target)
        self.assertIn(card.instance_id, state.players["A"].zones[Zone.HAND])
        EffectManager(engine).apply(EffectDefinition(EffectKind.SHUFFLE_ZONE, 0, TargetMode.CHOSEN_ZONE), item, zone_target)
        EffectManager(engine).apply(EffectDefinition(EffectKind.SEARCH_ZONE, 0, TargetMode.CHOSEN_ZONE, destination_zone=Zone.HAND, selection_minimum=0), item, zone_target)

    def test_malformed_runtime_targets_fizzle_before_mutation(self):
        engine, item, _ = engine_with_battlefield(); manager = EffectManager(engine)
        effects = (
            EffectDefinition(EffectKind.MOVE_CARDS, 1, TargetMode.CHOSEN_ZONE, destination_zone=Zone.HAND),
            EffectDefinition(EffectKind.DEAL_HARM, 1, TargetMode.CHOSEN_ENTITY, distributed=True),
            EffectDefinition(EffectKind.GAIN_STEPS, 1, TargetMode.CHOSEN_PLAYER),
        )
        for effect in effects: manager.apply(effect, item, None)
        self.assertEqual([event.payload["reason"] for event in engine._require_running_state().event_log], ["invalid_target"] * 3)

    def test_direct_damage_draw_destroy_and_invalid_allocated_target(self):
        engine, item, target = engine_with_battlefield(); manager = EffectManager(engine)
        state = engine._require_running_state()
        state.cards["deck-i"] = CardInstance("deck-i", "target", "A", "A", Zone.DECK)
        state.players["A"].zones[Zone.DECK].append("deck-i")
        manager.apply(EffectDefinition(EffectKind.DRAW_CARDS, 1), item)
        manager.apply(EffectDefinition(EffectKind.DEAL_HARM, 1, TargetMode.CHOSEN_ENTITY, distributed=True), item, TargetAllocation("missing", 1))
        manager.apply(EffectDefinition(EffectKind.DESTROY, 1, TargetMode.CHOSEN_PERMANENT), item, target)
        self.assertIn("deck-i", state.players["A"].zones[Zone.HAND])
        self.assertIn(target, state.players["B"].zones[Zone.DISCARD])


if __name__ == "__main__": unittest.main()
