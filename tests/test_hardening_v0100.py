import hashlib
import json
import random
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from card_duel_engine import GameEngine
from card_duel_engine.content import CollectionManifest, dump_manifest, load_manifest
from card_duel_engine.domain import (
    CardDefinition,
    CardKind,
    CompositeCost,
    CostComponent,
    CostMetric,
    CostTerm,
    DynamicCostDefinition,
    MatchStatus,
    TextPatchDefinition,
    XCostDefinition,
)
from card_duel_engine.engine import Concede
from card_duel_engine.persistence import (
    dump_replay,
    dump_snapshot,
    load_snapshot,
    replay_from_log,
    state_digest,
)
from card_duel_engine.persistence.codec import canonical_json
from card_duel_engine.rules.resolvers import (
    apply_text_patch,
    resolve_dynamic_cost,
    resolve_x_cost,
)
from card_duel_engine.storage import (
    InMemoryMatchStore,
    SQLiteMatchStore,
    VersionConflict,
)

from fixtures import test_deck


def checksum(body):
    return hashlib.sha256(canonical_json(body).encode("utf-8")).hexdigest()


class HardeningV0100Tests(unittest.TestCase):
    def make_engine(self, seed=100):
        engine = GameEngine()
        engine.new_match(
            {"A": test_deck(f"HA{seed}", 12), "B": test_deck(f"HB{seed}", 12)},
            seed=seed,
        )
        return engine

    def test_snapshot_and_replay_schema_one_migrate_to_schema_two(self):
        engine = self.make_engine()

        snapshot = json.loads(dump_snapshot(engine))
        snapshot["body"]["schema_version"] = "1"
        snapshot["body"].pop("state_digest")
        snapshot["sha256"] = checksum(snapshot["body"])
        restored = load_snapshot(snapshot)
        self.assertEqual(state_digest(restored), state_digest(engine))

        replay = json.loads(dump_replay(engine))
        replay["body"]["schema_version"] = "1"
        replay["body"].pop("command_count")
        replay["sha256"] = checksum(replay["body"])
        replayed = replay_from_log(replay)
        self.assertEqual(state_digest(replayed), state_digest(engine))

    def test_manifest_schema_one_migrates_with_safe_defaults(self):
        card = CardDefinition(
            "MIGRATE-1",
            "Migrable",
            CardKind.CREATURE,
            1,
            base_strength=1,
            set_id="migration-set",
        )
        current = CollectionManifest(
            "migration-set",
            "Migración",
            1,
            "0.9.0",
            (card,),
            metadata={"author": "tests"},
            dependencies=("base-set",),
        )
        legacy = json.loads(dump_manifest(current))
        legacy["schema_version"] = "1"
        legacy.pop("metadata")
        legacy.pop("dependencies")
        migrated = load_manifest(legacy, engine_version="0.10.0")
        self.assertEqual(migrated.metadata, {})
        self.assertEqual(migrated.dependencies, ())
        self.assertEqual(migrated.cards, (card,))

    def test_pure_cost_resolvers_obey_bounds_for_generated_formulas(self):
        engine = self.make_engine(101)
        rng = random.Random(101)
        player = engine.state.players["A"]
        for _ in range(200):
            player.wounds = rng.randrange(0, 40)
            multiplier = rng.randrange(-3, 4)
            minimum = rng.randrange(0, 5)
            maximum = rng.randrange(minimum, minimum + 20)
            formula = DynamicCostDefinition(
                CostComponent.STEPS,
                (CostTerm(CostMetric.OWN_WOUNDS, multiplier),),
                base=CompositeCost(steps=2),
                offset=rng.randrange(-10, 11),
                minimum=minimum,
                maximum=maximum,
            )
            resolved = resolve_dynamic_cost(formula, engine.state, "A")
            self.assertGreaterEqual(resolved.steps, 2 + minimum)
            self.assertLessEqual(resolved.steps, 2 + maximum)

            x_max = rng.randrange(1, 30)
            x_value = rng.randrange(0, x_max + 1)
            x_cost = XCostDefinition(
                CostComponent.WOUNDS, multiplier=2, maximum=x_max
            )
            self.assertEqual(resolve_x_cost(x_cost, x_value).wounds, x_value * 2)

    def test_text_resolver_never_mutates_the_catalog_definition(self):
        original = CardDefinition(
            "PURE-TEXT",
            "Original",
            CardKind.CREATURE,
            2,
            base_strength=2,
            keywords=frozenset({"A"}),
        )
        patched = apply_text_patch(
            original,
            TextPatchDefinition(
                grant_keywords=frozenset({"B"}),
                remove_keywords=frozenset({"A"}),
            ),
        )
        self.assertEqual(original.keywords, frozenset({"A"}))
        self.assertEqual(patched.keywords, frozenset({"B"}))
        self.assertIsNot(original, patched)

    def test_generated_command_sequences_preserve_invariants_and_replay(self):
        for seed in range(20):
            engine = self.make_engine(2000 + seed)
            rng = random.Random(seed)
            for step in range(80):
                state = engine.state
                if state.status is not MatchStatus.RUNNING:
                    break
                combat = state.combat
                if combat is not None and not combat.blockers_declared and not state.stack:
                    player_id = combat.defending_player_id
                elif state.phase_priority_complete and not state.stack:
                    player_id = state.active_player_id
                else:
                    player_id = state.priority_player_id
                candidates = tuple(
                    action
                    for action in engine.legal_actions(player_id)
                    if not isinstance(action, Concede)
                )
                self.assertTrue(candidates)
                engine.execute(rng.choice(candidates))
                engine.validate_invariants()
                if step % 17 == 0:
                    restored = load_snapshot(dump_snapshot(engine, indent=None))
                    self.assertEqual(state_digest(restored), state_digest(engine))
            replayed = replay_from_log(dump_replay(engine, indent=None))
            self.assertEqual(state_digest(replayed), state_digest(engine))

    def test_in_memory_store_uses_optimistic_versions_and_isolation(self):
        store = InMemoryMatchStore()
        engine = self.make_engine(102)
        self.assertEqual(store.create("match-1", engine), 1)
        first = store.load("match-1")
        second = store.load("match-1")
        first.engine.add_wounds("A", 1)
        self.assertEqual(store.save("match-1", first.engine, expected_version=1), 2)
        second.engine.add_wounds("A", 2)
        with self.assertRaises(VersionConflict):
            store.save("match-1", second.engine, expected_version=1)
        stored = store.load("match-1")
        self.assertEqual(stored.version, 2)
        self.assertEqual(stored.engine.state.players["A"].wounds, 1)

    def test_sqlite_store_allows_only_one_concurrent_compare_and_swap(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "matches.sqlite3"
            SQLiteMatchStore(path).create("shared", self.make_engine(103))
            workers = 8
            barrier = threading.Barrier(workers)

            def attempt(index):
                store = SQLiteMatchStore(path)
                record = store.load("shared")
                record.engine.add_wounds("A", index + 1)
                barrier.wait()
                try:
                    store.save(
                        "shared", record.engine, expected_version=record.version
                    )
                    return "saved"
                except VersionConflict:
                    return "conflict"

            with ThreadPoolExecutor(max_workers=workers) as executor:
                results = list(executor.map(attempt, range(workers)))
            self.assertEqual(results.count("saved"), 1)
            self.assertEqual(results.count("conflict"), workers - 1)
            final = SQLiteMatchStore(path).load("shared")
            self.assertEqual(final.version, 2)
            self.assertGreaterEqual(final.engine.state.players["A"].wounds, 1)
            self.assertLessEqual(final.engine.state.players["A"].wounds, workers)


if __name__ == "__main__":
    unittest.main()
