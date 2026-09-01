"""Pruebas de aceptación del corpus base a través de sus APIs públicas."""

from __future__ import annotations

import ast
from collections import Counter
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path

import pytest

from card_duel_engine import (
    CardCatalog,
    CardPresentation,
    CardPresentationCatalog,
    CollectionManifest,
    CollectionRegistry,
    GameEngine,
    PublicCard,
    PublicCardCatalog,
    classic_deck_policy,
    validate_card_presentations,
)
from card_duel_engine.content import (
    BASE_CARD_DEFINITIONS,
    BASE_CARD_PRESENTATIONS,
    BASE_SET_ID,
    BASE_SET_MANIFEST,
    BASE_SET_REVISION,
    build_base_card_catalog,
    build_base_card_presentation_catalog,
    dump_manifest,
    load_manifest,
)


EXPECTED_CARD_IDS = frozenset(f"base-c{number:03d}" for number in range(1, 9))
EXPECTED_TOKENS = frozenset(f"BASE-{number:03d}" for number in range(1, 9))
MECHANICAL_FIELDS = (
    "card_id",
    "mechanical_name",
    "kind",
    "cost",
    "rank",
    "base_strength",
    "set_id",
    "revision",
    "keywords",
    "subtypes",
)


def test_real_corpus_has_exactly_eight_definitions_and_presentations() -> None:
    definition_ids = [card.card_id for card in BASE_CARD_DEFINITIONS]
    presentation_ids = [card.card_id for card in BASE_CARD_PRESENTATIONS]
    tokens = [card.token for card in BASE_CARD_PRESENTATIONS]

    assert len(BASE_CARD_DEFINITIONS) == len(BASE_CARD_PRESENTATIONS) == 8
    assert set(definition_ids) == set(presentation_ids) == EXPECTED_CARD_IDS
    assert set(tokens) == EXPECTED_TOKENS
    assert len(definition_ids) == len(set(definition_ids))
    assert len(presentation_ids) == len(set(presentation_ids))
    assert len(tokens) == len(set(tokens))


def test_real_catalogs_also_reject_duplicate_ids_and_tokens() -> None:
    mechanics = build_base_card_catalog()
    presentations = build_base_card_presentation_catalog()

    with pytest.raises(ValueError, match="Definición duplicada"):
        mechanics.register(BASE_CARD_DEFINITIONS[0])
    with pytest.raises(ValueError, match="card_id duplicado"):
        presentations.register(BASE_CARD_PRESENTATIONS[0])
    with pytest.raises(ValueError, match="token duplicado"):
        presentations.register(
            replace(BASE_CARD_PRESENTATIONS[1], card_id="base-editorial-extra")
        )


def test_real_catalogs_are_paired_and_both_mismatch_directions_are_rejected() -> None:
    mechanics = build_base_card_catalog()
    presentations = build_base_card_presentation_catalog()
    assert validate_card_presentations(mechanics, presentations) is None

    orphan_catalog = CardPresentationCatalog()
    for presentation in BASE_CARD_PRESENTATIONS:
        orphan_catalog.register(presentation)
    orphan_catalog.register(
        CardPresentation("orphan-card", "ORPHAN-001", "Orphan", "", "")
    )
    with pytest.raises(ValueError, match="Presentaciones huérfanas: orphan-card"):
        validate_card_presentations(mechanics, orphan_catalog)

    missing_catalog = CardPresentationCatalog()
    for presentation in BASE_CARD_PRESENTATIONS[:-1]:
        missing_catalog.register(presentation)
    with pytest.raises(
        ValueError, match="Definiciones mecánicas sin presentación: base-c008"
    ):
        validate_card_presentations(mechanics, missing_catalog)


def test_manifest_identity_contents_and_lossless_round_trip() -> None:
    assert BASE_SET_ID == "base"
    assert BASE_SET_REVISION == 1
    assert BASE_SET_MANIFEST.collection_id == BASE_SET_ID
    assert BASE_SET_MANIFEST.revision == BASE_SET_REVISION
    assert {card.card_id for card in BASE_SET_MANIFEST.cards} == EXPECTED_CARD_IDS
    assert len(BASE_SET_MANIFEST.cards) == 8

    serialized = dump_manifest(BASE_SET_MANIFEST)
    assert load_manifest(serialized) == BASE_SET_MANIFEST
    assert dump_manifest(load_manifest(serialized)) == serialized


def test_registry_publishes_catalog_and_provenance_atomically_on_collision() -> None:
    registry = CollectionRegistry()
    provenance = registry.register(BASE_SET_MANIFEST)
    expected_digest = sha256(
        dump_manifest(BASE_SET_MANIFEST, indent=None).encode("utf-8")
    ).hexdigest()

    assert {card.card_id for card in registry.catalog.definitions()} == EXPECTED_CARD_IDS
    assert registry.provenance(BASE_SET_ID) == provenance
    assert provenance.collection_id == BASE_SET_ID
    assert provenance.revision == BASE_SET_REVISION
    assert provenance.manifest_sha256 == expected_digest

    collision = replace(
        BASE_CARD_DEFINITIONS[0], name="Collision", set_id="collision-set"
    )
    colliding_manifest = CollectionManifest(
        "collision-set", "Collision", 1, "0.20.1", (collision,)
    )
    before = registry.snapshot()
    with pytest.raises(ValueError, match="colisiona con el catálogo"):
        registry.register(colliding_manifest)
    assert registry.snapshot() == before
    assert "collision-set" not in registry.collections


def test_public_catalog_is_complete_sorted_and_deeply_json_safe() -> None:
    public = PublicCardCatalog(
        build_base_card_catalog(), build_base_card_presentation_catalog()
    )
    payload = public.to_dict()
    ids = [card.card_id for card in public.cards]

    assert set(ids) == EXPECTED_CARD_IDS
    assert ids == sorted(EXPECTED_CARD_IDS)
    assert isinstance(json.dumps(payload), str)
    assert all(isinstance(card["keywords"], list) for card in payload["cards"])
    assert all(isinstance(card["subtypes"], list) for card in payload["cards"])

    forbidden_types = (type(BASE_CARD_DEFINITIONS[0]), type(BASE_CARD_PRESENTATIONS[0]))

    def assert_no_domain_objects(value: object) -> None:
        assert not isinstance(value, forbidden_types)
        if isinstance(value, dict):
            for child in value.values():
                assert_no_domain_objects(child)
        elif isinstance(value, list):
            for child in value:
                assert_no_domain_objects(child)

    assert_no_domain_objects(payload)


def test_editorial_variants_do_not_change_mechanics_or_deck_behavior() -> None:
    definition = BASE_CARD_DEFINITIONS[0]
    presentation = BASE_CARD_PRESENTATIONS[0]
    baseline = PublicCard.from_sources(definition, presentation)
    variants = (
        replace(presentation, token="ALT-001"),
        replace(presentation, name="Alternative title"),
        replace(presentation, rules_text="Alternative editorial text."),
        replace(presentation, art="art/alternative.webp"),
    )
    policy = classic_deck_policy(allowed_set_ids={BASE_SET_ID})

    for variant in variants:
        projected = PublicCard.from_sources(definition, variant)
        assert tuple(getattr(projected, field) for field in MECHANICAL_FIELDS) == tuple(
            getattr(baseline, field) for field in MECHANICAL_FIELDS
        )

    deck = tuple(card for card in BASE_CARD_DEFINITIONS for _ in range(5))
    assert policy.require_valid(deck) == deck


def test_base_module_has_no_card_id_specific_behavior_tables_or_branches() -> None:
    module_path = (
        Path(__file__).parents[1]
        / "src/card_duel_engine/content/base_set.py"
    )
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    card_ids = EXPECTED_CARD_IDS

    assert not any(isinstance(node, (ast.If, ast.IfExp, ast.Match)) for node in ast.walk(tree))
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            keys = {
                key.value for key in node.keys if isinstance(key, ast.Constant)
            }
            assert not keys.intersection(card_ids)


def test_cards_only_use_declared_enum_members() -> None:
    for card in BASE_CARD_DEFINITIONS:
        assert card.kind.name in type(card.kind).__members__
        assert card.rank.name in type(card.rank).__members__
        assert all(keyword.name in type(keyword).__members__ for keyword in card.keywords)


def test_real_forty_card_deck_is_validated_before_engine_smoke_test() -> None:
    deck = tuple(card for card in BASE_CARD_DEFINITIONS for _ in range(5))
    counts = Counter(card.card_id for card in deck)
    policy = classic_deck_policy(allowed_set_ids={BASE_SET_ID})

    assert len(deck) == 40
    assert set(counts) == EXPECTED_CARD_IDS
    for card in BASE_CARD_DEFINITIONS:
        limit = 4 if card.rank.name == "LEGENDARY" else 5
        assert counts[card.card_id] <= limit

    validation = policy.validate(deck)
    assert validation.is_valid
    validated_deck = policy.require_valid(deck)

    engine = GameEngine(catalog=build_base_card_catalog())
    engine.new_match({"A": validated_deck, "B": validated_deck}, seed=1)
    assert engine.state is not None
