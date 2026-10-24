"""Regresiones conservadoras para vocabulario y procedencia taxonómicos.

Estas pruebas fijan el comportamiento disponible mientras CAP-TAXONOMY-001
sigue parcial: los subtipos son literales, no hay normalización heurística de
aliases y la procedencia publicada permanece ligada al manifiesto que los
contiene. No introducen un registro canónico ni semántica de selección nueva.
"""

from __future__ import annotations

import hashlib

from card_duel_engine.content import CollectionManifest, CollectionRegistry, dump_manifest
from card_duel_engine.domain.enums import CardKind
from card_duel_engine.domain.models import CardDefinition, CardFilter
from card_duel_engine.presentation import CardPresentation
from card_duel_engine.public_catalog import PublicCard


def _definition(card_id: str, subtype: str) -> CardDefinition:
    return CardDefinition(
        card_id=card_id,
        name=card_id,
        kind=CardKind.CREATURE,
        cost=1,
        base_strength=1,
        set_id="taxonomy-regression-fixture",
        subtypes=frozenset({subtype}),
    )


def _presentation(card_id: str) -> CardPresentation:
    return CardPresentation(card_id, card_id, card_id, "", f"art/{card_id}.webp")


def test_unapproved_aliases_remain_distinct_literal_subtypes() -> None:
    """Pixy/Pixie no se fusionan sin autoridad normativa explícita."""
    pixy = _definition("fixture-pixy", "Pixy")
    pixie = _definition("fixture-pixie", "Pixie")

    assert CardFilter(subtypes=frozenset({"Pixy"})).matches(pixy)
    assert not CardFilter(subtypes=frozenset({"Pixy"})).matches(pixie)
    assert CardFilter(subtypes=frozenset({"Pixie"})).matches(pixie)
    assert not CardFilter(subtypes=frozenset({"Pixie"})).matches(pixy)


def test_public_projection_preserves_literal_vocabulary_without_rewriting() -> None:
    """La proyección pública conserva ambas grafías y las ordena establemente."""
    definition = CardDefinition(
        card_id="fixture-vocabulary",
        name="fixture-vocabulary",
        kind=CardKind.CREATURE,
        cost=1,
        base_strength=1,
        set_id="taxonomy-regression-fixture",
        subtypes=frozenset({"Pixie", "Pixy"}),
    )

    public = PublicCard.from_sources(definition, _presentation(definition.card_id))

    assert public.subtypes == ("Pixie", "Pixy")
    assert public.to_dict()["subtypes"] == ["Pixie", "Pixy"]
    assert definition.subtypes == frozenset({"Pixie", "Pixy"})


def test_fixture_provenance_is_bound_to_the_exact_published_vocabulary() -> None:
    """El digest de procedencia identifica el manifiesto y sus grafías literales."""
    manifest = CollectionManifest(
        collection_id="taxonomy-regression-fixture",
        name="Taxonomy regression fixture",
        revision=1,
        engine_min_version="0.20.1",
        cards=(
            _definition("fixture-pixy", "Pixy"),
            _definition("fixture-pixie", "Pixie"),
        ),
        metadata={"source": "CANONICAL_TAXONOMY.md §3"},
    )
    registry = CollectionRegistry()

    provenance = registry.register(manifest)

    expected_digest = hashlib.sha256(
        dump_manifest(manifest, indent=None).encode("utf-8")
    ).hexdigest()
    assert provenance.collection_id == manifest.collection_id
    assert provenance.manifest_sha256 == expected_digest
    assert {
        definition.card_id: definition.subtypes
        for definition in registry.snapshot().catalog.definitions()
    } == {
        "fixture-pixy": frozenset({"Pixy"}),
        "fixture-pixie": frozenset({"Pixie"}),
    }
