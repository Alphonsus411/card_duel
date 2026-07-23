import json
import unittest

from card_duel_engine import GameEngine, RuleSet
from card_duel_engine.catalog import CardCatalog
from card_duel_engine.content import (
    CollectionManifest,
    dump_manifest,
    load_manifest,
    register_manifest,
)
from card_duel_engine.domain import (
    CardDefinition,
    CardKind,
    EffectDefinition,
    EffectKind,
    MoveReplacementDefinition,
    TargetMode,
    Zone,
)
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


class PersistenceV090Tests(unittest.TestCase):
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

    def test_snapshot_rejects_tampering(self):
        engine = GameEngine()
        engine.new_match({"A": test_deck("TA"), "B": test_deck("TB")}, seed=9)
        envelope = json.loads(dump_snapshot(engine))
        envelope["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "huella"):
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
