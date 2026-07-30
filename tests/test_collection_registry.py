from __future__ import annotations

import random
import hashlib
import hmac
from dataclasses import replace
import tempfile
from pathlib import Path
import unittest

from card_duel_engine import CollectionRegistry, GameEngine
from card_duel_engine.content import (
    CollectionManifest, CollectionSignatureEnvelope, CollectionTrustPolicy,
    PermissiveCollectionTrustPolicy, TrustedKey, dump_manifest, load_manifest,
    load_manifest_file, load_signature_envelope, save_manifest_file,
)
from card_duel_engine.domain.enums import CardKind
from card_duel_engine.domain.models import CardDefinition


def manifest(name: str, dependencies=(), card_id: str | None = None, revision: int = 1):
    cards = () if card_id is None else (CardDefinition(card_id, card_id, CardKind.CREATURE, 0, base_strength=1, set_id=name),)
    return CollectionManifest(name, name, revision, "0.1.0", cards, dependencies=tuple(dependencies))


class Policy:
    def __init__(self, accept=True): self.accept = accept; self.calls = []
    def validate(self, item, canonical, digest, envelope):
        self.calls.append((item, canonical, digest))
        if not self.accept: raise ValueError("confianza rechazada")


class CollectionRegistryTests(unittest.TestCase):
    @staticmethod
    def signed(item, key_id="release", key=b"trusted", algorithm="hmac-sha256"):
        canonical = dump_manifest(item, indent=None)
        signature = hmac.new(key, canonical.encode(), hashlib.sha256).hexdigest()
        return CollectionSignatureEnvelope(canonical, key_id, algorithm, signature)

    @staticmethod
    def strict(keys=None):
        class Resolver:
            def resolve(self, key_id):
                return (keys or {}).get(key_id)
        return CollectionTrustPolicy(Resolver())

    def test_valid_signature_and_envelope_does_not_change_manifest_digest(self):
        item = manifest("signed", card_id="signed-card")
        envelope = self.signed(item)
        registry = CollectionRegistry(trust_policy=self.strict({
            "release": TrustedKey("release", b"trusted")
        }))
        provenance = registry.register(envelope)
        expected = hashlib.sha256(dump_manifest(item, indent=None).encode()).hexdigest()
        self.assertEqual(provenance.manifest_sha256, expected)

    def test_tampered_content_signature_and_unknown_or_revoked_key_are_rejected(self):
        trusted = {"release": TrustedKey("release", b"trusted")}
        original = self.signed(manifest("changed"))
        changed_content = replace(
            original, manifest=dump_manifest(manifest("changed", revision=2), indent=None)
        )
        cases = [
            (changed_content, "inválida", trusted),
            (CollectionSignatureEnvelope(dump_manifest(manifest("signature"), indent=None),
                                         "release", "hmac-sha256", "0" * 64), "inválida", trusted),
            (self.signed(manifest("unknown"), key_id="missing"), "desconocida", trusted),
            (self.signed(manifest("revoked")), "revocada",
             {"release": TrustedKey("release", b"trusted", revoked=True)}),
            (self.signed(manifest("algorithm"), algorithm="future-signature"),
             "no permitido", trusted),
        ]
        for envelope, message, keys in cases:
            registry = CollectionRegistry(trust_policy=self.strict(keys))
            with self.assertRaisesRegex(ValueError, message):
                registry.register(envelope)
            self.assertEqual(dict(registry.collections), {})

    def test_mixed_signed_batch_is_rejected_before_any_mutation(self):
        registry = CollectionRegistry(trust_policy=self.strict({
            "release": TrustedKey("release", b"trusted")
        }))
        valid = self.signed(manifest("a", card_id="a-card"))
        invalid = self.signed(manifest("b", ("a",), "b-card"), key=b"wrong")
        with self.assertRaisesRegex(ValueError, "inválida"):
            registry.register_batch([valid, invalid])
        self.assertEqual(len(registry.catalog), 0)
        self.assertEqual(dict(registry.collections), {})

    def test_explicit_permissive_policy_accepts_unsigned_collection(self):
        registry = CollectionRegistry(trust_policy=PermissiveCollectionTrustPolicy())
        registry.register(manifest("unsigned", card_id="unsigned-card"))
        self.assertIn("unsigned-card", registry.catalog)

    def test_strict_policy_rejects_unsigned_collection(self):
        registry = CollectionRegistry(trust_policy=self.strict({}))
        with self.assertRaisesRegex(ValueError, "exige"):
            registry.register(manifest("unsigned"))

    def test_signature_envelope_rejects_unknown_missing_and_wrong_typed_fields(self):
        envelope = self.signed(manifest("strict-envelope"))
        raw = {
            "schema_version": envelope.schema_version,
            "manifest": envelope.manifest,
            "key_id": envelope.key_id,
            "algorithm": envelope.algorithm,
            "signature": envelope.signature,
        }
        for changed in (
            {**raw, "extra": "no"},
            {key: value for key, value in raw.items() if key != "signature"},
            {**raw, "key_id": 7},
        ):
            with self.assertRaisesRegex(ValueError, "estructura|texto"):
                load_signature_envelope(changed)

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

    def test_manifest_document_rejects_wrong_json_types_atomically(self):
        item = manifest("valid", card_id="valid-card")
        valid = __import__("json").loads(dump_manifest(item))
        invalid_values = (
            ("schema_version", 2),
            ("collection_id", None),
            ("name", {"text": "name"}),
            ("engine_min_version", 1),
            ("revision", True),
            ("revision", "1"),
            ("cards", "cards"),
            ("cards", {}),
            ("cards", None),
            ("cards", 7),
            ("dependencies", "base"),
            ("dependencies", {"base": True}),
            ("dependencies", None),
            ("dependencies", 7),
            ("dependencies", ["base", 7]),
            ("metadata", []),
            ("metadata", None),
            ("metadata", "author"),
            ("metadata", {"author": 7}),
            ("metadata", {7: "author"}),
        )
        registry = CollectionRegistry()
        registry.register(item)
        original_collections = dict(registry.collections)
        original_cards = registry.catalog.definitions()
        for field, value in invalid_values:
            with self.subTest(field=field, value=value):
                malformed = {**valid, field: value}
                with self.assertRaises(ValueError):
                    registry.register(load_manifest(malformed))
                self.assertEqual(dict(registry.collections), original_collections)
                self.assertEqual(registry.catalog.definitions(), original_cards)

    def test_manifest_v2_round_trip_remains_valid(self):
        item = CollectionManifest(
            "round-trip",
            "Formato v2",
            2,
            "0.1.0",
            (),
            metadata={"author": "tests"},
            dependencies=("base",),
        )
        serialized = dump_manifest(item, indent=None)
        self.assertEqual(load_manifest(serialized), item)

    def test_engine_accepts_registry_and_enforces_exact_definition(self):
        registry = CollectionRegistry(); item = manifest("set", card_id="card"); registry.register(item)
        engine = GameEngine(catalog=registry); self.assertIs(engine.catalog, registry.catalog)
        altered = CardDefinition("card", "altered", CardKind.CREATURE, 0, base_strength=1, set_id="set")
        with self.assertRaisesRegex(ValueError, "no coincide"):
            engine.new_match({"a": [item.cards[0]] * 6, "b": [altered] * 6})

        unknown = CardDefinition("unknown", "Unknown", CardKind.CREATURE, 0, base_strength=1)
        with self.assertRaisesRegex(ValueError, "no está registrada"):
            engine.new_match({"a": [item.cards[0]] * 6, "b": [unknown] * 6})
        self.assertNotIn("unknown", registry.catalog)

    def test_failed_match_preflight_does_not_partially_mutate_catalog_or_state(self):
        first = CardDefinition("first", "First", CardKind.CREATURE, 0, base_strength=1)
        conflicting = CardDefinition("same", "One", CardKind.CREATURE, 0, base_strength=1)
        altered = CardDefinition("same", "Two", CardKind.CREATURE, 0, base_strength=2)
        engine = GameEngine()
        with self.assertRaisesRegex(ValueError, "incompatibles"):
            engine.new_match({"a": [first, conflicting], "b": [altered]})
        self.assertEqual(engine.catalog.definitions(), ())
        self.assertIsNone(engine.state)

    def test_seeded_small_dags(self):
        for seed in range(12):
            rng = random.Random(seed); nodes = [f"n{i}" for i in range(6)]
            batch = [manifest(node, tuple(prior for prior in nodes[:i] if rng.choice((True, False)))) for i, node in enumerate(nodes)]
            rng.shuffle(batch); result = CollectionRegistry().register_batch(batch)
            positions = {name: i for i, name in enumerate(result)}
            self.assertTrue(all(positions[dep] < positions[item.collection_id] for item in batch for dep in item.dependencies))


if __name__ == "__main__": unittest.main()
