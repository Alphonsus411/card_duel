from __future__ import annotations

import random
import hashlib
import hmac
import threading
from dataclasses import replace
import tempfile
from pathlib import Path
import unittest

from card_duel_engine import CardCatalog, CollectionRegistry, GameEngine
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


class CoordinatedTrustPolicy:
    """Detiene la validación en un punto anterior al commit del registro."""

    def __init__(self, *, accept=True):
        self.accept = accept
        self.preparing = threading.Event()
        self.release = threading.Event()

    def validate(self, item, canonical, digest, envelope):
        del item, canonical, digest, envelope
        self.preparing.set()
        if not self.release.wait(timeout=5):
            raise AssertionError("la prueba no liberó la política de confianza")
        if not self.accept:
            raise ValueError("confianza rechazada")


class ThreadCall:
    """Thread pequeño que conserva resultado o excepción para el thread principal."""

    def __init__(self, target, *args):
        self.result = None
        self.error: BaseException | None = None

        def run():
            try:
                self.result = target(*args)
            except BaseException as error:
                self.error = error

        self.thread = threading.Thread(target=run)

    def start(self):
        self.thread.start()
        return self

    def join(self):
        self.thread.join(timeout=5)
        if self.thread.is_alive():
            raise AssertionError("el thread concurrente no terminó")
        return self

    def unwrap(self):
        self.join()
        if self.error is not None:
            raise self.error
        return self.result


class CollectionRegistryTests(unittest.TestCase):
    CONCURRENT_ITERATIONS = 6

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

    def assert_catalog_matches_provenance(self, registry):
        """Cada carta de estas carreras pertenece a una colección publicada."""
        provenance_ids = set(registry.collections)
        catalog_collection_ids = {
            card.set_id for card in registry.catalog.definitions()
        }
        self.assertEqual(catalog_collection_ids, provenance_ids)

    def assert_registry_snapshot_consistent(
        self, snapshot, known_manifests, allowed_collection_sets
    ):
        """Comprueba conjuntamente catálogo, procedencia y lotes indivisibles."""
        manifests = {item.collection_id: item for item in known_manifests}
        published = frozenset(snapshot.collections)
        allowed = {frozenset(collections) for collections in allowed_collection_sets}
        self.assertIn(published, allowed, "apareció una colección o lote parcial")

        cards_by_id = {
            card.card_id: card for card in snapshot.catalog.definitions()
        }
        expected_cards = {
            card.card_id: (collection_id, card)
            for collection_id in published
            for card in manifests[collection_id].cards
        }
        self.assertEqual(set(cards_by_id), set(expected_cards))
        for collection_id in published:
            provenance = snapshot.collections.get(collection_id)
            self.assertIsNotNone(provenance, "colección publicada sin procedencia")
            self.assertEqual(provenance.collection_id, collection_id)
            for card in manifests[collection_id].cards:
                self.assertIn(card.card_id, cards_by_id)
        for card_id, card in cards_by_id.items():
            expected_collection, expected_card = expected_cards[card_id]
            self.assertEqual(card, expected_card)
            self.assertEqual(card.set_id, expected_collection)

    def assert_event(self, event, description):
        self.assertTrue(event.wait(timeout=5), description)

    def test_reader_sees_old_snapshot_until_valid_batch_is_published(self):
        old = manifest("old", card_id="old-card")
        new = manifest("new", card_id="new-card")
        for iteration in range(self.CONCURRENT_ITERATIONS):
            with self.subTest(iteration=iteration):
                policy = CoordinatedTrustPolicy()
                registry = CollectionRegistry(trust_policy=policy)
                policy.release.set()
                registry.register(old)
                policy.release.clear()
                policy.preparing.clear()
                old_snapshot = registry.snapshot()

                writer = ThreadCall(registry.register, new).start()
                self.assert_event(policy.preparing, "el escritor no alcanzó la preparación")
                readers = [
                    ThreadCall(
                        self.assert_registry_snapshot_consistent,
                        old_snapshot,
                        (old, new),
                        ({"old"}, {"old", "new"}),
                    ).start()
                    for _ in range(2)
                ]
                for reader in readers:
                    reader.unwrap()
                self.assert_registry_snapshot_consistent(
                    old_snapshot, (old, new), ({"old"},)
                )

                policy.release.set()
                writer.unwrap()
                self.assert_registry_snapshot_consistent(
                    registry.snapshot(), (old, new), ({"old", "new"},)
                )

    def test_rejected_batch_preserves_exact_catalog_and_provenance(self):
        base = manifest("base", card_id="base-card")
        rejected = manifest("rejected", card_id="rejected-card")
        for iteration in range(self.CONCURRENT_ITERATIONS):
            with self.subTest(iteration=iteration):
                policy = CoordinatedTrustPolicy()
                policy.release.set()
                registry = CollectionRegistry(trust_policy=policy)
                registry.register(base)
                before = registry.snapshot()
                policy.accept = False
                policy.release.clear()
                policy.preparing.clear()
                reader_done = threading.Event()

                writer = ThreadCall(registry.register, rejected).start()
                self.assert_event(policy.preparing, "el escritor no alcanzó la preparación")
                reader = ThreadCall(
                    lambda: (
                        self.assert_registry_snapshot_consistent(
                            before, (base, rejected), ({"base"},)
                        ),
                        reader_done.set(),
                    )
                ).start()
                self.assert_event(reader_done, "el lector no comprobó el estado anterior")
                reader.unwrap()
                policy.release.set()
                writer.join()
                self.assertIsInstance(writer.error, ValueError)
                self.assertEqual(str(writer.error), "confianza rechazada")
                after = registry.snapshot()
                self.assertEqual(after.catalog.definitions(), before.catalog.definitions())
                self.assertEqual(dict(after.collections), dict(before.collections))

    def test_two_compatible_writers_only_expose_complete_snapshots(self):
        first = (manifest("a", card_id="a-card"), manifest("b", ("a",), "b-card"))
        second = (manifest("c", card_id="c-card"), manifest("d", ("c",), "d-card"))
        all_manifests = first + second
        allowed = (set(), {"a", "b"}, {"c", "d"}, {"a", "b", "c", "d"})
        for iteration in range(self.CONCURRENT_ITERATIONS):
            with self.subTest(iteration=iteration):
                registry = CollectionRegistry()
                writer_gates = [threading.Event(), threading.Event()]
                read_gates = [threading.Event() for _ in range(3)]
                read_done = [threading.Event() for _ in range(3)]
                observed = []

                def write(gate, batch):
                    if not gate.wait(timeout=5):
                        raise AssertionError("no se liberó el escritor")
                    return dict(registry.register_batch(batch))

                def read():
                    for gate, done in zip(read_gates, read_done):
                        if not gate.wait(timeout=5):
                            raise AssertionError("no se coordinó el lector")
                        observed.append(registry.snapshot())
                        done.set()

                writers = [
                    ThreadCall(write, gate, batch).start()
                    for gate, batch in zip(writer_gates, (first, second))
                ]
                reader = ThreadCall(read).start()

                read_gates[0].set()
                self.assert_event(read_done[0], "no se observó el estado inicial")
                order = (iteration % 2, 1 - (iteration % 2))
                writer_gates[order[0]].set()
                writers[order[0]].unwrap()
                read_gates[1].set()
                self.assert_event(read_done[1], "no se observó el primer commit")
                writer_gates[order[1]].set()
                writers[order[1]].unwrap()
                read_gates[2].set()
                self.assert_event(read_done[2], "no se observó el segundo commit")
                reader.unwrap()
                for snapshot in observed:
                    self.assert_registry_snapshot_consistent(
                        snapshot, all_manifests, allowed
                    )
                self.assertEqual(
                    set(observed[-1].collections), {"a", "b", "c", "d"}
                )

    def test_colliding_writers_publish_exactly_one_batch_without_residue(self):
        first = (manifest("first", card_id="shared"), manifest("first-child", ("first",), "first-only"))
        second = (manifest("second", card_id="shared"), manifest("second-child", ("second",), "second-only"))
        all_manifests = first + second
        for iteration in range(self.CONCURRENT_ITERATIONS):
            with self.subTest(iteration=iteration):
                registry = CollectionRegistry()
                start = threading.Barrier(3)

                def write(batch):
                    start.wait()
                    return dict(registry.register_batch(batch))

                calls = [ThreadCall(write, batch).start() for batch in (first, second)]
                start.wait()
                for call in calls:
                    call.join()
                successes = [call for call in calls if call.error is None]
                failures = [call for call in calls if call.error is not None]
                self.assertEqual(len(successes), 1)
                self.assertEqual(len(failures), 1)
                self.assertIsInstance(failures[0].error, ValueError)
                self.assertIn("colisiona", str(failures[0].error))
                winner = frozenset(successes[0].result)
                self.assertIn(winner, ({"first", "first-child"}, {"second", "second-child"}))
                self.assert_registry_snapshot_consistent(
                    registry.snapshot(), all_manifests, (winner,)
                )

    def test_catalog_snapshot_rejects_mutation_and_registry_stays_authoritative(self):
        item = manifest("immutable", card_id="immutable-card")
        registry = CollectionRegistry()
        registry.register(item)
        before = registry.snapshot()
        exposed = registry.catalog

        self.assertFalse(hasattr(exposed, "register"))
        self.assertFalse(hasattr(exposed, "remove"))
        with self.assertRaises(TypeError):
            exposed._cards["injected"] = item.cards[0]  # type: ignore[index]
        self.assertEqual(registry.snapshot(), before)

    def run_concurrent_batches(self, first, second):
        """Libera dos registros a la vez y devuelve sus resultados y errores."""
        registry = CollectionRegistry()
        barrier = threading.Barrier(3)
        results = []
        errors = []

        def register_batch(batch):
            barrier.wait()
            try:
                results.append(dict(registry.register_batch(batch)))
            except ValueError as error:
                errors.append(error)

        threads = [
            threading.Thread(target=register_batch, args=(batch,))
            for batch in (first, second)
        ]
        for thread in threads:
            thread.start()
        barrier.wait()
        for thread in threads:
            thread.join()
        return registry, results, errors

    def test_concurrent_compatible_batches_are_both_published_without_loss(self):
        first = [manifest("a", card_id="a-card"), manifest("b", ("a",), "b-card")]
        second = [manifest("c", card_id="c-card"), manifest("d", ("c",), "d-card")]

        for iteration in range(12):
            with self.subTest(iteration=iteration):
                registry, results, errors = self.run_concurrent_batches(first, second)
                self.assertEqual(errors, [])
                self.assertEqual(len(results), 2)
                self.assertEqual(set(registry.collections), {"a", "b", "c", "d"})
                self.assertEqual(
                    {card.card_id for card in registry.catalog.definitions()},
                    {"a-card", "b-card", "c-card", "d-card"},
                )
                self.assert_catalog_matches_provenance(registry)

    def test_initial_catalog_and_returned_snapshots_cannot_mutate_published_state(self):
        initial_card = manifest("initial", card_id="initial-card").cards[0]
        external = CardCatalog({initial_card.card_id: initial_card})
        registry = CollectionRegistry(external)
        before = registry.snapshot()

        external.register(manifest("external", card_id="external-card").cards[0])
        registry.register(manifest("published", card_id="published-card"))

        self.assertNotIn("external-card", registry.catalog)
        self.assertNotIn("published-card", before.catalog)
        self.assertEqual(dict(before.collections), {})
        self.assertFalse(hasattr(registry.catalog, "register"))
        with self.assertRaises(TypeError):
            before.collections["x"] = registry.provenance("published")  # type: ignore[index]

    def test_old_collections_snapshot_is_independent_of_later_commits(self):
        registry = CollectionRegistry()
        registry.register(manifest("first", card_id="first-card"))
        old_collections = registry.collections

        registry.register(manifest("second", card_id="second-card"))

        self.assertEqual(tuple(old_collections), ("first",))
        self.assertEqual(tuple(registry.collections), ("first", "second"))

    def test_concurrent_colliding_batches_publish_exactly_one_whole_batch(self):
        first = [
            manifest("first-base", card_id="shared-card"),
            manifest("first-child", ("first-base",), "first-only"),
        ]
        second = [
            manifest("second-base", card_id="shared-card"),
            manifest("second-child", ("second-base",), "second-only"),
        ]

        for iteration in range(12):
            with self.subTest(iteration=iteration):
                registry, results, errors = self.run_concurrent_batches(first, second)
                self.assertEqual(len(results), 1)
                self.assertEqual(len(errors), 1)
                self.assertIn("colisiona", str(errors[0]))
                winner = set(results[0])
                alternatives = (
                    ({"first-base", "first-child"}, "first-only", "second-only"),
                    ({"second-base", "second-child"}, "second-only", "first-only"),
                )
                winner_ids, winner_card, rejected_card = next(
                    option for option in alternatives if option[0] == winner
                )
                self.assertEqual(set(registry.collections), winner_ids)
                self.assertIn(winner_card, registry.catalog)
                self.assertNotIn(rejected_card, registry.catalog)
                self.assert_catalog_matches_provenance(registry)

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

    def test_manifest_engine_versions_compare_three_non_negative_components(self):
        item = replace(manifest("versions"), engine_min_version="1.2.3")

        self.assertEqual(load_manifest(dump_manifest(item), engine_version="1.2.3"), item)
        self.assertEqual(load_manifest(dump_manifest(item), engine_version="1.2.4"), item)
        self.assertEqual(
            load_manifest(
                dump_manifest(replace(item, engine_min_version="0.0.0")),
                engine_version="999.999.999",
            ).engine_min_version,
            "0.0.0",
        )
        with self.assertRaisesRegex(ValueError, "requiere motor 1.2.3"):
            load_manifest(dump_manifest(item), engine_version="1.2.2")

    def test_manifest_rejects_unsupported_minimum_and_application_versions(self):
        invalid_versions = (
            "",
            " ",
            "1.2",
            "1..2",
            "-1.2.3",
            "1.-2.3",
            "1.2.-3",
            "1.2.3.4",
            "1.2.3-alpha",
            "1.2.3+build",
            " 1.2.3",
            "1.2.3 ",
        )
        message = (
            "Versión semántica no válida: se requiere exactamente "
            "MAJOR.MINOR.PATCH con enteros no negativos"
        )
        valid = manifest("version-format")
        for invalid in invalid_versions:
            with self.subTest(field="engine_min_version", version=invalid):
                with self.assertRaisesRegex(ValueError, f"^{message}$"):
                    replace(valid, engine_min_version=invalid)
            with self.subTest(field="engine_version", version=invalid):
                with self.assertRaisesRegex(ValueError, f"^{message}$"):
                    load_manifest(dump_manifest(valid), engine_version=invalid)

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
