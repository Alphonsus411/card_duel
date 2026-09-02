from dataclasses import FrozenInstanceError

import pytest

from card_duel_engine.catalog import CardCatalog
from card_duel_engine.content import (
    MYTHIC_CARD_DEFINITIONS,
    MYTHIC_CARD_PRESENTATIONS,
    MYTHIC_SET_ID,
    MYTHIC_SET_MANIFEST,
    build_mythic_catalogs,
    build_mythic_collection_registry,
    build_mythic_public_card_catalog,
)
from card_duel_engine.content.registry import CollectionRegistry
from card_duel_engine.presentation import CardPresentationCatalog


def test_mythic_revision_publishes_only_supported_cards() -> None:
    assert MYTHIC_SET_ID == "mythic"
    assert MYTHIC_SET_MANIFEST.engine_min_version == "0.20.1"
    assert tuple(card.card_id for card in MYTHIC_CARD_DEFINITIONS) == (
        "mythic-elf-023",
        "mythic-elf-025",
    )
    assert tuple(card.token for card in MYTHIC_CARD_PRESENTATIONS) == ("nº023", "nº025")
    assert all(
        card.cost == card.base_strength == 10 for card in MYTHIC_CARD_DEFINITIONS
    )
    with pytest.raises(FrozenInstanceError):
        MYTHIC_CARD_DEFINITIONS[0].cost = 1  # type: ignore[misc]


def test_mythic_builders_validate_and_join_by_card_id() -> None:
    mechanical, editorial = build_mythic_catalogs()
    assert mechanical.definitions() == MYTHIC_CARD_DEFINITIONS
    assert editorial.presentations() == MYTHIC_CARD_PRESENTATIONS
    public = build_mythic_public_card_catalog()
    assert tuple(card.card_id for card in public.cards) == tuple(
        card.card_id for card in MYTHIC_CARD_DEFINITIONS
    )
    assert (
        build_mythic_collection_registry().catalog.definitions()
        == MYTHIC_CARD_DEFINITIONS
    )


def test_importing_mythic_exports_does_not_populate_consumer_catalogs() -> None:
    assert len(CardCatalog()) == 0
    assert len(CardPresentationCatalog()) == 0
    registry = CollectionRegistry()
    assert len(registry.catalog) == 0
    assert registry.snapshot().collections == {}
