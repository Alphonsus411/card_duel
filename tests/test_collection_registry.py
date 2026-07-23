from __future__ import annotations

import random
import tempfile
from pathlib import Path
import unittest

from card_duel_engine import CollectionRegistry, GameEngine
from card_duel_engine.content import (CollectionManifest, dump_manifest, load_manifest,
                                      load_manifest_file, save_manifest_file)
from card_duel_engine.domain.enums import CardKind
from card_duel_engine.domain.models import CardDefinition


def manifest(name: str, dependencies=(), card_id: str | None = None, revision: int = 1):
    cards = () if card_id is None else (CardDefinition(card_id, card_id, CardKind.CREATURE, 0, base_strength=1, set_id=name),)
    return CollectionManifest(name, name, revision, "0.1.0", cards, dependencies=tuple(dependencies))


class Policy:
    def __init__(self, accept=True): self.accept = accept; self.calls = []
    def validate(self, item, canonical, digest):
        self.calls.append((item, canonical, digest))
        if not self.accept: raise ValueError("confianza rechazada")


class CollectionRegistryTests(unittest.TestCase):
    def test_unordered_branched_graph_has_deterministic_provenance(self):
        registry = CollectionRegistry()
        result = registry.register_batch([manifest("d", ("b", "c")), manifest("c", ("a",)), manifest("a"), manifest("b", ("a",))])
        self.assertEqual(tuple(result), ("a", "b", "c", "d"))
        self.assertEqual(registry.provenance("d").dependencies, ("b", "c"))
        with self.assertRaises(TypeError): registry.collections["x"] = result["a"]  # type: ignore[index]

    def test_missing_cycle_and_duplicate_ids_are_rejected_atomically(self):
        for batch, message in [([manifest("a", ("missing",), "a1")], "ausentes"),
                               ([manifest("a", ("b",)), manifest("b", ("a",))], "Ciclo"),
                               ([manifest("a"), manifest("a")], "duplicada")]:
            registry = CollectionRegistry()
            with self.assertRaisesRegex(ValueError, message): registry.register_batch(batch)
            self.assertEqual(len(registry.catalog), 0); self.assertEqual(dict(registry.collections), {})

    def test_collision_policy_and_batch_rollback(self):
        registry = CollectionRegistry(); registry.register(manifest("base", card_id="same"))
        with self.assertRaisesRegex(ValueError, "colisiona"):
            registry.register_batch([manifest("ok", card_id="new"), manifest("bad", card_id="same")])
        self.assertNotIn("new", registry.catalog); self.assertNotIn("ok", registry.collections)
        policy = Policy(False); rejected = CollectionRegistry(trust_policy=policy)
        with self.assertRaisesRegex(ValueError, "confianza"): rejected.register(manifest("x", card_id="x"))
        self.assertEqual(len(rejected.catalog), 0)

    def test_digest_is_canonical_and_trust_policy_receives_it(self):
        policy = Policy(); registry = CollectionRegistry(trust_policy=policy); item = manifest("a")
        provenance = registry.register(item)
        self.assertEqual(policy.calls[0][1], dump_manifest(item, indent=None).encode())
        self.assertEqual(policy.calls[0][2], provenance.manifest_sha256)
        self.assertEqual(len(provenance.manifest_sha256), 64)

    def test_revisions_and_tampering_are_rejected(self):
        registry = CollectionRegistry(); registry.register(manifest("a", revision=2))
        with self.assertRaisesRegex(ValueError, "inferior"): registry.register(manifest("a"))
        with self.assertRaisesRegex(ValueError, "alterado"): registry.register(manifest("a", dependencies=(), card_id="new", revision=2))
        with self.assertRaisesRegex(ValueError, "incompatible"): registry.register(manifest("a", revision=3))
        with self.assertRaisesRegex(ValueError, "ya registrada"): registry.register(manifest("a", revision=2))

    def test_manifest_canonical_file_bytes_and_validation(self):
        item = manifest("files", card_id="one")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "collection.json"
            self.assertEqual(save_manifest_file(item, path), path)
            self.assertEqual(load_manifest_file(path), item)
            self.assertEqual(load_manifest(path.read_bytes()), item)
        invalid = [
            ({"schema_version": "1"}, "compatible"),
            ({"collection_id": "", "name": "n"}, "identificador"),
            ({"collection_id": "x", "name": "",}, "identificador"),
            ({"revision": 0}, "positiva"),
            ({"revision": True}, "entero"),
            ({"engine_min_version": "bad"}, "semántica"),
            ({"metadata": {"x": 1}}, "metadatos"),
            ({"dependencies": ("d", "d")}, "duplicadas"),
            ({"dependencies": ("x",)}, "sí misma"),
        ]
        for changes, message in invalid:
            values = dict(collection_id="x", name="name", revision=1,
                          engine_min_version="0.1.0", cards=())
            values.update(changes)
            with self.assertRaisesRegex(ValueError, message): CollectionManifest(**values)
        raw = __import__("json").loads(dump_manifest(item)); raw["extra"] = True
        with self.assertRaisesRegex(ValueError, "estructura"): load_manifest(raw)

    def test_engine_accepts_registry_and_enforces_exact_definition(self):
        registry = CollectionRegistry(); item = manifest("set", card_id="card"); registry.register(item)
        engine = GameEngine(catalog=registry); self.assertIs(engine.catalog, registry.catalog)
        altered = CardDefinition("card", "altered", CardKind.CREATURE, 0, base_strength=1, set_id="set")
        with self.assertRaisesRegex(ValueError, "no coincide"):
            engine.new_match({"a": [item.cards[0]] * 6, "b": [altered] * 6})

    def test_seeded_small_dags(self):
        for seed in range(12):
            rng = random.Random(seed); nodes = [f"n{i}" for i in range(6)]
            batch = [manifest(node, tuple(prior for prior in nodes[:i] if rng.choice((True, False)))) for i, node in enumerate(nodes)]
            rng.shuffle(batch); result = CollectionRegistry().register_batch(batch)
            positions = {name: i for i, name in enumerate(result)}
            self.assertTrue(all(positions[dep] < positions[item.collection_id] for item in batch for dep in item.dependencies))


if __name__ == "__main__": unittest.main()
