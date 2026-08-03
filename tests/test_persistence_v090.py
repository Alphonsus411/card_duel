import hashlib
import json
import unittest

from card_duel_engine import EngineSemantics, GameEngine, RuleSet
from card_duel_engine.catalog import CardCatalog
from card_duel_engine.content import (
    CollectionManifest,
    dump_manifest,
    load_manifest,
    register_manifest,
)
from card_duel_engine.domain import (
    CardDefinition,
    CardFilter,
    CardKind,
    EffectDefinition,
    EffectKind,
    MoveReplacementDefinition,
    TargetMode,
    Zone,
    ZoneTarget,
)
from card_duel_engine.domain.errors import IllegalAction, InvariantViolation
from card_duel_engine.domain.models import StackItem
from card_duel_engine.engine import (
    PassPriority,
    PlayCard,
    ResolveMoveReplacement,
)
from card_duel_engine.persistence import (
    dump_replay,
    dump_snapshot,
    load_snapshot,
    replay_from_log,
    state_digest,
)
from card_duel_engine.persistence.codec import canonical_json

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


def recalculate_snapshot_fingerprints(envelope):
    body = envelope["body"]
    body["state_digest"] = hashlib.sha256(
        canonical_json(body["state"]).encode("utf-8")
    ).hexdigest()
    envelope["sha256"] = hashlib.sha256(
        canonical_json(body).encode("utf-8")
    ).hexdigest()


class PersistenceV090Tests(unittest.TestCase):
    def test_snapshot_serializes_and_restores_current_semantics_for_019_rules(self):
        engine = GameEngine(RuleSet(version="0.19.0"))
        engine.new_match({"A": test_deck("CA"), "B": test_deck("CB")}, seed=907)

        document = json.loads(dump_snapshot(engine))
        self.assertEqual(document["body"]["schema_version"], "2")
        self.assertEqual(document["body"]["engine_semantics"], "CURRENT")
        self.assertIs(load_snapshot(document).semantics, EngineSemantics.CURRENT)

    def test_snapshot_restores_legacy_019_semantics(self):
        engine = GameEngine(RuleSet(version="0.19.0"))
        engine.new_match({"A": test_deck("LA"), "B": test_deck("LB")}, seed=908)
        document = json.loads(dump_snapshot(engine))
        document["body"]["engine_semantics"] = "LEGACY_019"
        recalculate_snapshot_fingerprints(document)

        restored = load_snapshot(document)

        self.assertIs(restored.semantics, EngineSemantics.LEGACY_019)
        self.assertEqual(
            json.loads(dump_snapshot(restored))["body"]["engine_semantics"],
            "LEGACY_019",
        )

    def test_snapshot_without_semantics_defaults_to_current(self):
        engine = GameEngine(RuleSet(version="0.19.0"))
        engine.new_match({"A": test_deck("MA"), "B": test_deck("MB")}, seed=911)
        document = json.loads(dump_snapshot(engine))
        del document["body"]["engine_semantics"]
        recalculate_snapshot_fingerprints(document)

        self.assertIs(load_snapshot(document).semantics, EngineSemantics.CURRENT)

    def test_snapshot_rejects_invalid_semantics_fields_and_version_pair(self):
        engine = GameEngine(RuleSet(version="0.20.9"))
        engine.new_match({"A": test_deck("VA"), "B": test_deck("VB")}, seed=912)
        baseline = json.loads(dump_snapshot(engine))
        cases = ((17, "cadena"), ("FUTURE", "desconocida"), ("LEGACY_019", "0.19.0"))
        for value, message in cases:
            with self.subTest(value=value):
                document = json.loads(json.dumps(baseline))
                document["body"]["engine_semantics"] = value
                recalculate_snapshot_fingerprints(document)
                with self.assertRaisesRegex(ValueError, message):
                    load_snapshot(document)

    def test_snapshot_v2_roundtrip_preserves_ability_source_profile_and_counters(self):
        engine = GameEngine(RuleSet())
        engine.new_match({"A": test_deck("PA"), "B": test_deck("PB")}, seed=909)
        source = force_zone(engine, "PA-000", "A", Zone.BATTLEFIELD)
        target = force_zone(engine, "PB-000", "B", Zone.BATTLEFIELD)
        engine.state.stack.append(StackItem(
            "stack-profile", "A", source,
            (EffectDefinition(EffectKind.DEAL_DAMAGE, 1, TargetMode.CHOSEN_PERMANENT),),
            chosen_card_ids=(target,), ability_id="captured",
            ability_source_profile=engine._ability_source_profile(source),
        ))
        before = (
            state_digest(engine),
            tuple(engine.state.event_log),
            tuple(engine.state.command_history),
            engine._next_instance,
            engine._next_stack_item,
        )
        payload = dump_snapshot(engine)
        restored = load_snapshot(payload)
        after = (
            state_digest(restored),
            tuple(restored.state.event_log),
            tuple(restored.state.command_history),
            restored._next_instance,
            restored._next_stack_item,
        )
        self.assertEqual(after, before)
        self.assertEqual(
            restored.state.stack[-1].ability_source_profile,
            engine.state.stack[-1].ability_source_profile,
        )

    def test_old_v2_stack_item_derives_profile_for_present_and_moved_source(self):
        engine = GameEngine(RuleSet())
        engine.new_match({"A": test_deck("OA"), "B": test_deck("OB")}, seed=910)
        source = force_zone(engine, "OA-000", "A", Zone.BATTLEFIELD)
        engine.state.stack.append(StackItem(
            "legacy-stack", "A", source, (), ability_id="legacy"
        ))
        envelope = json.loads(dump_snapshot(engine))

        def remove_profile(value):
            if isinstance(value, dict):
                if value.get("$type") == "StackItem":
                    value["fields"].pop("ability_source_profile")
                for child in value.values():
                    remove_profile(child)
            elif isinstance(value, list):
                for child in value:
                    remove_profile(child)

        remove_profile(envelope["body"]["state"])
        recalculate_snapshot_fingerprints(envelope)
        restored = load_snapshot(envelope)
        self.assertIsNotNone(restored.state.stack[-1].ability_source_profile)

        engine._move_card(source, Zone.DISCARD, "A")
        envelope = json.loads(dump_snapshot(engine))
        remove_profile(envelope["body"]["state"])
        recalculate_snapshot_fingerprints(envelope)
        restored = load_snapshot(envelope)
        profile = restored.state.stack[-1].ability_source_profile
        self.assertIsNotNone(profile)
        self.assertFalse(profile.was_on_battlefield)
        self.assertTrue(profile.was_effective_creature)
        self.assertFalse(profile.nature_is_certain)
        roundtrip = load_snapshot(dump_snapshot(restored))
        self.assertEqual(roundtrip.state.stack[-1].ability_source_profile, profile)

    def make_pending_search_snapshot(self):
        prize = CardDefinition(
            "SNAP_SEARCH_PRIZE", "Objetivo", CardKind.CREATURE, 2, base_strength=2
        )
        searcher = CardDefinition(
            "SNAP_SEARCHER",
            "Búsqueda persistida",
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
                    search_filter=CardFilter(
                        definition_ids=frozenset({"SNAP_SEARCH_PRIZE"})
                    ),
                ),
            ),
        )
        engine = GameEngine()
        engine.new_match(
            {
                "A": [searcher, prize, *test_deck("PSA", 12)],
                "B": test_deck("PSB", 14),
            },
            seed=903,
        )
        spell = force_zone(engine, "SNAP_SEARCHER", "A", Zone.HAND)
        force_zone(engine, "SNAP_SEARCH_PRIZE", "A", Zone.DECK)
        engine.execute(
            PlayCard(
                "A", spell, chosen_zone_targets=(ZoneTarget("A", Zone.DECK),)
            )
        )
        engine.execute(PassPriority("B"))
        engine.execute(PassPriority("A"))
        self.assertIsNotNone(engine.state.pending_search)
        return json.loads(dump_snapshot(engine))

    def test_snapshot_restores_a_pending_replacement_and_continues_identically(self):
        resilient = CardDefinition(
            "SNAP_RESILIENT",
            "Resiliente persistente",
            CardKind.CREATURE,
            3,
            base_strength=3,
            move_replacements=(
                MoveReplacementDefinition(Zone.HAND),
                MoveReplacementDefinition(Zone.EXILE),
            ),
            deferred_replacement_choice=True,
        )
        destroy = CardDefinition(
            "SNAP_DESTROY",
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
        engine = GameEngine(RuleSet())
        engine.new_match(
            {
                "B": [resilient, *test_deck("SB", 14)],
                "A": [destroy, *test_deck("SA", 14)],
            },
            seed=90,
        )
        target = force_zone(engine, "SNAP_RESILIENT", "B", Zone.BATTLEFIELD)
        spell = force_zone(engine, "SNAP_DESTROY", "A", Zone.HAND)
        engine.state.priority_player_id = "A"
        engine.execute(PlayCard("A", spell, chosen_card_ids=(target,)))
        engine.execute(PassPriority("B"))
        engine.execute(PassPriority("A"))
        self.assertIsNotNone(engine.state.pending_move_replacement)

        payload = dump_snapshot(engine)
        restored = load_snapshot(payload)
        self.assertEqual(state_digest(restored), state_digest(engine))
        self.assertEqual(restored.state.turn_order, ("B", "A"))
        self.assertEqual(restored.state.pending_move_replacement.card_id, target)

        choice = ResolveMoveReplacement("B", 1)
        engine.execute(choice)
        restored.execute(choice)
        self.assertEqual(state_digest(restored), state_digest(engine))
        self.assertIn(target, restored.state.players["B"].zones[Zone.EXILE])

    def test_failed_replacement_choice_remains_persistable_and_resolvable(self):
        resilient = CardDefinition(
            "SNAP_FAILED_CHOICE",
            "Elección recuperable",
            CardKind.CREATURE,
            3,
            base_strength=3,
            move_replacements=(
                MoveReplacementDefinition(Zone.HAND),
                MoveReplacementDefinition(Zone.EXILE),
            ),
            deferred_replacement_choice=True,
        )
        destroy = CardDefinition(
            "SNAP_FAILED_DESTROY",
            "Destrucción recuperable",
            CardKind.QUICK_RESOURCE,
            0,
            permanent=False,
            transmutable=False,
            effects=(
                EffectDefinition(EffectKind.DESTROY, 0, TargetMode.CHOSEN_PERMANENT),
            ),
        )
        engine = GameEngine()
        engine.new_match(
            {
                "A": [destroy, *test_deck("SFA", 14)],
                "B": [resilient, *test_deck("SFB", 14)],
            },
            seed=905,
        )
        spell = force_zone(engine, "SNAP_FAILED_DESTROY", "A", Zone.HAND)
        target = force_zone(engine, "SNAP_FAILED_CHOICE", "B", Zone.BATTLEFIELD)
        engine.execute(PlayCard("A", spell, chosen_card_ids=(target,)))
        engine.execute(PassPriority("B"))
        engine.execute(PassPriority("A"))

        snapshot_before = dump_snapshot(engine, indent=None)
        history_before = tuple(engine.state.command_history)
        events_before = tuple(engine.state.event_log)
        check_wound_limits = engine._check_wound_limits

        def fail_after_replacement():
            raise RuntimeError("fallo persistible simulado")

        engine._check_wound_limits = fail_after_replacement
        try:
            with self.assertRaisesRegex(RuntimeError, "fallo persistible simulado"):
                engine.execute(ResolveMoveReplacement("B", 1))
        finally:
            engine._check_wound_limits = check_wound_limits

        self.assertEqual(dump_snapshot(engine, indent=None), snapshot_before)
        self.assertEqual(tuple(engine.state.command_history), history_before)
        self.assertEqual(tuple(engine.state.event_log), events_before)

        restored = load_snapshot(dump_snapshot(engine))
        self.assertIsNotNone(restored.state.pending_move_replacement)
        restored.execute(ResolveMoveReplacement("B", 1))

        self.assertIsNone(restored.state.pending_move_replacement)
        self.assertIn(target, restored.state.players["B"].zones[Zone.EXILE])
        self.assertEqual(len(restored.state.command_history), len(history_before) + 1)
        self.assertEqual(
            sum(
                event.event_type == "MOVE_REPLACEMENT_CHOSEN"
                for event in restored.state.event_log
            ),
            1,
        )
        self.assertEqual(
            sum(
                event.event_type == "MOVE_REPLACEMENT_CHOICE_REQUESTED"
                for event in restored.state.event_log
            ),
            1,
        )

    def test_snapshot_rejects_tampering(self):
        engine = GameEngine()
        engine.new_match({"A": test_deck("TA"), "B": test_deck("TB")}, seed=9)
        envelope = json.loads(dump_snapshot(engine))
        envelope["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "huella"):
            load_snapshot(envelope)

    def test_snapshot_rejects_pending_search_with_unknown_chooser(self):
        envelope = self.make_pending_search_snapshot()
        pending_search = envelope["body"]["state"]["fields"]["pending_search"]
        pending_search["fields"]["chooser_id"] = "DESCONOCIDO"
        recalculate_snapshot_fingerprints(envelope)

        with self.assertRaisesRegex(
            InvariantViolation, "Búsqueda asignada a un jugador inexistente"
        ):
            load_snapshot(envelope)

    def test_snapshot_rejects_pending_search_with_unknown_zone_owner(self):
        envelope = self.make_pending_search_snapshot()
        pending_search = envelope["body"]["state"]["fields"]["pending_search"]
        pending_search["fields"]["zone_target"]["fields"][
            "player_id"
        ] = "DESCONOCIDO"
        recalculate_snapshot_fingerprints(envelope)

        with self.assertRaisesRegex(
            InvariantViolation, "Búsqueda dirigida a un jugador inexistente"
        ):
            load_snapshot(envelope)

    def test_command_log_replays_to_the_exact_final_digest(self):
        ping = CardDefinition(
            "REPLAY_PING",
            "Pulso",
            CardKind.QUICK_RESOURCE,
            0,
            permanent=False,
            transmutable=False,
            effects=(
                EffectDefinition(
                    EffectKind.DEAL_WOUNDS,
                    2,
                    TargetMode.CHOSEN_PLAYER,
                ),
            ),
            set_id="replay-test",
        )
        engine = GameEngine()
        engine.new_match(
            {"Z": [ping] * 12, "A": [ping] * 12}, seed=901
        )
        card_id = engine.state.players["Z"].zones[Zone.HAND][0]
        engine.execute(PlayCard("Z", card_id, chosen_player_ids=("A",)))
        engine.execute(PassPriority("A"))
        engine.execute(PassPriority("Z"))
        expected = state_digest(engine)

        replayed = replay_from_log(dump_replay(engine))
        self.assertEqual(state_digest(replayed), expected)
        self.assertEqual(replayed.state.turn_order, ("Z", "A"))
        self.assertEqual(replayed.state.players["A"].wounds, 2)
        self.assertEqual(len(replayed.state.command_history), 3)

    def test_replay_restores_chained_deferred_replacement_choices(self):
        replacement_pair = (
            MoveReplacementDefinition(Zone.HAND),
            MoveReplacementDefinition(Zone.EXILE),
        )
        first = CardDefinition(
            "REPLAY_DEFERRED_A",
            "Primer destino diferido",
            CardKind.QUICK_RESOURCE,
            0,
            base_strength=3,
            move_replacements=replacement_pair,
            deferred_replacement_choice=True,
        )
        second = CardDefinition(
            "REPLAY_DEFERRED_B",
            "Segundo destino diferido",
            CardKind.QUICK_RESOURCE,
            0,
            base_strength=3,
            move_replacements=replacement_pair,
            deferred_replacement_choice=True,
        )
        destroy = CardDefinition(
            "REPLAY_DOUBLE_DESTROY",
            "Destrucción doble reproducible",
            CardKind.QUICK_RESOURCE,
            0,
            permanent=False,
            transmutable=False,
            effects=(
                EffectDefinition(
                    EffectKind.DESTROY,
                    0,
                    TargetMode.CHOSEN_PERMANENT,
                    minimum_targets=2,
                    maximum_targets=2,
                ),
            ),
        )
        engine = GameEngine()
        engine.new_match(
            {
                "B": [first] * 7 + [second] * 7,
                "A": [destroy] * 14,
            },
            seed=904,
        )
        target_a = next(
            card_id
            for card_id in engine.state.players["B"].zones[Zone.HAND]
            if engine.state.cards[card_id].definition_id == "REPLAY_DEFERRED_A"
        )
        target_b = next(
            card_id
            for card_id in engine.state.players["B"].zones[Zone.HAND]
            if engine.state.cards[card_id].definition_id == "REPLAY_DEFERRED_B"
        )
        spell = engine.state.players["A"].zones[Zone.HAND][0]
        setup_commands = (
            PlayCard("B", target_a),
            PassPriority("A"),
            PassPriority("B"),
            PlayCard("B", target_b),
            PassPriority("A"),
            PassPriority("B"),
            PassPriority("B"),
        )
        for command in setup_commands:
            engine.execute(command)

        play_destroy = PlayCard(
            "A", spell, chosen_card_ids=(target_a, target_b)
        )
        engine.execute(play_destroy)
        engine.execute(PassPriority("B"))
        original_command = PassPriority("A")
        engine.execute(original_command)
        self.assertIsNotNone(engine.state.pending_move_replacement)
        self.assertEqual(engine.state.pending_move_replacement.card_id, target_a)
        history_before_rejection = tuple(engine.state.command_history)
        with self.assertRaises(IllegalAction):
            engine.execute(ResolveMoveReplacement("A", 0))
        self.assertEqual(tuple(engine.state.command_history), history_before_rejection)

        first_choice = ResolveMoveReplacement("B", 0)
        engine.execute(first_choice)
        self.assertIsNotNone(engine.state.pending_move_replacement)
        self.assertEqual(engine.state.pending_move_replacement.card_id, target_b)
        self.assertEqual(engine.state.pending_move_replacement.replay_choices, (0,))

        second_choice = ResolveMoveReplacement("B", 1)
        engine.execute(second_choice)
        self.assertIsNone(engine.state.pending_move_replacement)
        self.assertIn(target_a, engine.state.players["B"].zones[Zone.HAND])
        self.assertIn(target_b, engine.state.players["B"].zones[Zone.EXILE])

        expected_history = (
            *setup_commands,
            play_destroy,
            PassPriority("B"),
            original_command,
            first_choice,
            second_choice,
        )
        self.assertEqual(tuple(engine.state.command_history), expected_history)
        replay_document = json.loads(dump_replay(engine))
        self.assertEqual(
            replay_document["body"]["command_count"], len(expected_history)
        )

        replayed = replay_from_log(replay_document)
        self.assertEqual(state_digest(replayed), state_digest(engine))
        self.assertEqual(
            replayed.state.players["A"].zones, engine.state.players["A"].zones
        )
        self.assertEqual(
            replayed.state.players["B"].zones, engine.state.players["B"].zones
        )
        self.assertIsNone(replayed.state.pending_move_replacement)
        self.assertEqual(tuple(replayed.state.command_history), expected_history)

    def test_setup_mulligans_are_part_of_replay(self):
        engine = GameEngine()
        engine.new_match(
            {"A": test_deck("MA"), "B": test_deck("MB")},
            seed=902,
            auto_start=False,
        )
        engine.mulligan("B")
        engine.start_match()
        replayed = replay_from_log(dump_replay(engine))
        self.assertEqual(state_digest(replayed), state_digest(engine))
        self.assertEqual(replayed.state.players["B"].mulligans_taken, 1)

    def test_collection_manifest_round_trip_and_atomic_registration(self):
        card = CardDefinition(
            "COLL-001",
            "Carta externa",
            CardKind.CREATURE,
            4,
            base_strength=4,
            set_id="new-dawn",
        )
        manifest = CollectionManifest(
            collection_id="new-dawn",
            name="Nuevo Amanecer",
            revision=1,
            engine_min_version="0.9.0",
            cards=(card,),
        )
        restored = load_manifest(dump_manifest(manifest), engine_version="0.9.0")
        self.assertEqual(restored, manifest)
        catalog = CardCatalog()
        register_manifest(catalog, restored)
        self.assertEqual(catalog.get("COLL-001"), card)
        with self.assertRaisesRegex(ValueError, "colisiona"):
            register_manifest(catalog, restored)
        self.assertEqual(len(catalog), 1)

    def test_collection_manifest_rejects_incompatible_or_malformed_content(self):
        card = CardDefinition(
            "WRONG-SET",
            "Incorrecta",
            CardKind.CREATURE,
            1,
            base_strength=1,
            set_id="other",
        )
        with self.assertRaisesRegex(ValueError, "pertenecer"):
            CollectionManifest("expected", "Colección", 1, "0.9.0", (card,))

        valid = CollectionManifest(
            "other", "Colección", 1, "9.0.0", (card,)
        )
        with self.assertRaisesRegex(ValueError, "requiere motor"):
            load_manifest(dump_manifest(valid), engine_version="0.9.0")

        malformed = json.loads(dump_manifest(valid))
        malformed["cards"][0]["$type"] = "ArbitraryPythonClass"
        with self.assertRaisesRegex(ValueError, "no autorizado"):
            load_manifest(malformed, engine_version="9.0.0")

        wrong_type = json.loads(dump_manifest(valid))
        wrong_type["cards"][0]["fields"]["cost"] = 1.5
        with self.assertRaisesRegex(ValueError, "Tipos de campo"):
            load_manifest(wrong_type, engine_version="9.0.0")


if __name__ == "__main__":
    unittest.main()
