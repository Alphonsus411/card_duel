"""Pruebas dirigidas del límite transaccional de ``GameEngine.new_match``."""

from __future__ import annotations

import unittest
from dataclasses import replace
from unittest.mock import patch

from card_duel_engine import CardCatalog, CollectionManifest, CollectionRegistry, GameEngine
from card_duel_engine.domain.enums import CardKind
from card_duel_engine.domain.errors import InvalidDeckDefinition, InvariantViolation
from card_duel_engine.domain.models import CardDefinition
from card_duel_engine.persistence.snapshot import dump_snapshot, state_digest

from fixtures import test_deck


class CandidateFailure(RuntimeError):
    """Fallo accidental distinguible de un error de definición de mazo."""


def engine_values(engine: GameEngine) -> tuple[object, ...]:
    """Valores publicados por ``new_match`` que deben cambiar como una unidad."""
    return (
        engine.catalog,
        engine.state,
        engine._next_instance,
        engine._next_stack_item,
        engine._replacement_replay_choices,
        engine._replacement_replay_cursor,
    )


def registry_with_decks(prefix: str) -> tuple[CollectionRegistry, dict[str, list[CardDefinition]]]:
    collection_id = f"{prefix}-collection"
    decks = {
        "A": [replace(card, set_id=collection_id) for card in test_deck(f"{prefix}-A")],
        "B": [replace(card, set_id=collection_id) for card in test_deck(f"{prefix}-B")],
    }
    definitions = tuple(card for deck in decks.values() for card in deck)
    registry = CollectionRegistry()
    registry.register(
        CollectionManifest(
            collection_id,
            f"Colección {prefix}",
            1,
            "0.1.0",
            definitions,
        )
    )
    return registry, decks


class NewMatchTransactionTests(unittest.TestCase):
    def engines_and_decks(self):
        normal_decks = {"A": test_deck("normal-A"), "B": test_deck("normal-B")}
        registry, registry_decks = registry_with_decks("registry")
        return (
            ("catalog", GameEngine(catalog=CardCatalog()), normal_decks, None),
            ("registry", GameEngine(catalog=registry), registry_decks, registry),
        )

    def test_failure_after_candidate_catalog_keeps_every_published_value(self):
        for kind, engine, decks, registry in self.engines_and_decks():
            with self.subTest(catalog=kind):
                before = engine_values(engine)
                registry_before = registry.snapshot() if registry is not None else None
                prepare = engine._prepare_catalog

                def fail_after_preparation(prepared_decks):
                    prepare(prepared_decks)
                    raise CandidateFailure("después del catálogo candidato")

                with patch.object(engine, "_prepare_catalog", side_effect=fail_after_preparation):
                    with self.assertRaisesRegex(CandidateFailure, "catálogo candidato"):
                        engine.new_match(decks)

                self.assertEqual(engine_values(engine), before)
                self.assertIs(engine.catalog, before[0])
                self.assertIs(engine.state, before[1])
                if registry is not None:
                    self.assertEqual(registry.snapshot(), registry_before)

    def test_failure_after_partial_candidate_deck_publishes_no_instances_or_ids(self):
        for kind, engine, decks, registry in self.engines_and_decks():
            with self.subTest(catalog=kind):
                before = engine_values(engine)
                registry_before = registry.snapshot() if registry is not None else None
                original = engine._create_candidate_instance
                calls = 0

                def fail_during_instances(definition, player_id, next_instance):
                    nonlocal calls
                    calls += 1
                    if calls == 4:
                        raise CandidateFailure("mazo candidato parcial")
                    return original(definition, player_id, next_instance)

                with patch.object(
                    engine, "_create_candidate_instance", side_effect=fail_during_instances
                ):
                    with self.assertRaisesRegex(CandidateFailure, "parcial"):
                        engine.new_match(decks)

                self.assertEqual(calls, 4)
                self.assertEqual(engine_values(engine), before)
                self.assertIsNone(engine.state)
                if kind == "catalog":
                    self.assertEqual(engine.catalog.definitions(), ())
                else:
                    self.assertEqual(registry.snapshot(), registry_before)

    def test_invariant_failure_rolls_back_for_catalog_and_registry(self):
        for kind, engine, decks, registry in self.engines_and_decks():
            with self.subTest(catalog=kind):
                before = engine_values(engine)
                registry_before = registry.snapshot() if registry is not None else None
                with patch.object(
                    engine,
                    "_validate_candidate_invariants",
                    side_effect=InvariantViolation("candidato inválido"),
                ):
                    with self.assertRaisesRegex(InvariantViolation, "candidato inválido"):
                        engine.new_match(decks, seed=17)

                self.assertEqual(engine_values(engine), before)
                if registry is not None:
                    self.assertEqual(registry.snapshot(), registry_before)

    def test_late_second_match_failure_preserves_exact_previous_match(self):
        scenarios = []
        normal = GameEngine()
        scenarios.append(("catalog", normal, {"A": test_deck("next-A"), "B": test_deck("next-B")}, None))
        registry, registered_decks = registry_with_decks("previous")
        scenarios.append(("registry", GameEngine(catalog=registry), registered_decks, registry))

        for kind, engine, second_decks, registry in scenarios:
            with self.subTest(catalog=kind):
                first_decks = second_decks if registry is not None else {
                    "A": test_deck("first-A"), "B": test_deck("first-B")
                }
                engine.new_match(first_decks, seed=23)
                before_values = engine_values(engine)
                before_snapshot = dump_snapshot(engine, indent=None)
                before_digest = state_digest(engine)
                before_definitions = engine.catalog.definitions()
                registry_before = registry.snapshot() if registry is not None else None

                with patch.object(
                    engine,
                    "_validate_candidate_invariants",
                    side_effect=CandidateFailure("fallo tardío"),
                ):
                    with self.assertRaisesRegex(CandidateFailure, "tardío"):
                        engine.new_match(second_decks, seed=99)

                self.assertEqual(engine_values(engine), before_values)
                self.assertIs(engine.state, before_values[1])
                self.assertEqual(dump_snapshot(engine, indent=None), before_snapshot)
                self.assertEqual(state_digest(engine), before_digest)
                self.assertEqual(engine.catalog.definitions(), before_definitions)
                if registry is not None:
                    self.assertEqual(registry.snapshot(), registry_before)

    def test_registry_rejects_foreign_definitions_without_changing_provenance(self):
        registry, decks = registry_with_decks("closed")
        engine = GameEngine(catalog=registry)
        before_engine = engine_values(engine)
        before_registry = registry.snapshot()
        foreign = CardDefinition(
            "foreign", "Ajena", CardKind.CREATURE, 0, base_strength=1
        )
        decks["B"] = [foreign, *decks["B"][1:]]

        with self.assertRaisesRegex(InvalidDeckDefinition, "no está registrada"):
            engine.new_match(decks)

        self.assertEqual(engine_values(engine), before_engine)
        self.assertEqual(registry.snapshot(), before_registry)
        self.assertNotIn("foreign", registry.catalog)

    def test_each_input_generator_is_materialized_exactly_once(self):
        for kind, engine, decks, _registry in self.engines_and_decks():
            with self.subTest(catalog=kind):
                iterations = {"A": 0, "B": 0}

                def one_shot(player_id):
                    iterations[player_id] += 1
                    if iterations[player_id] != 1:
                        raise AssertionError("el generador se materializó más de una vez")
                    yield from decks[player_id]

                engine.new_match({"A": one_shot("A"), "B": one_shot("B")}, seed=3)
                self.assertEqual(iterations, {"A": 1, "B": 1})


if __name__ == "__main__":
    unittest.main()
