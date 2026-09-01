"""Definiciones mecánicas canónicas de la colección base."""

from __future__ import annotations

from ..catalog import CardCatalog
from ..domain.enums import CardKind, CardRank, Keyword
from ..domain.models import CardDefinition
from ..presentation import (
    CardPresentation,
    CardPresentationCatalog,
    validate_card_presentations,
)
from .manifest import CollectionManifest

BASE_SET_ID = "base"
BASE_SET_REVISION = 1


# Criaturas simples cubren el flujo existente sin introducir efectos nuevos.
BASE_CARD_DEFINITIONS: tuple[CardDefinition, ...] = (
    CardDefinition(
        card_id="base-c001",
        name="Ember Initiate",
        kind=CardKind.CREATURE,
        cost=1,
        base_strength=1,
        set_id=BASE_SET_ID,
        revision=BASE_SET_REVISION,
        subtypes=frozenset({"warrior"}),
    ),
    CardDefinition(
        card_id="base-c002",
        name="Grove Sentinel",
        kind=CardKind.CREATURE,
        cost=2,
        base_strength=3,
        set_id=BASE_SET_ID,
        revision=BASE_SET_REVISION,
        subtypes=frozenset({"guardian"}),
    ),
    CardDefinition(
        card_id="base-c003",
        name="Skyline Duelist",
        kind=CardKind.CREATURE,
        cost=3,
        base_strength=2,
        set_id=BASE_SET_ID,
        revision=BASE_SET_REVISION,
        keywords=frozenset({Keyword.CAN_CHALLENGE}),
        subtypes=frozenset({"warrior"}),
    ),
    CardDefinition(
        card_id="base-c004",
        name="Stoneback Warden",
        kind=CardKind.CREATURE,
        cost=4,
        base_strength=5,
        set_id=BASE_SET_ID,
        revision=BASE_SET_REVISION,
        subtypes=frozenset({"guardian"}),
    ),
    CardDefinition(
        card_id="base-c005",
        name="Ashen Vanguard",
        kind=CardKind.CREATURE,
        cost=5,
        base_strength=4,
        set_id=BASE_SET_ID,
        revision=BASE_SET_REVISION,
        subtypes=frozenset({"warrior"}),
    ),
    CardDefinition(
        card_id="base-c006",
        name="Verdant Colossus",
        kind=CardKind.CREATURE,
        cost=6,
        base_strength=7,
        set_id=BASE_SET_ID,
        revision=BASE_SET_REVISION,
        subtypes=frozenset({"beast"}),
    ),
    CardDefinition(
        card_id="base-c007",
        name="First Arena Champion",
        kind=CardKind.CREATURE,
        cost=7,
        rank=CardRank.LEGENDARY,
        base_strength=6,
        set_id=BASE_SET_ID,
        revision=BASE_SET_REVISION,
        keywords=frozenset({Keyword.CAN_CHALLENGE}),
        subtypes=frozenset({"warrior"}),
    ),
    CardDefinition(
        card_id="base-c008",
        name="Ancient Grove Keeper",
        kind=CardKind.CREATURE,
        cost=8,
        rank=CardRank.LEGENDARY,
        base_strength=9,
        set_id=BASE_SET_ID,
        revision=BASE_SET_REVISION,
        subtypes=frozenset({"guardian"}),
    ),
)


# Los tokens son identificadores editoriales publicados: deben permanecer
# explícitos para que reordenar este corpus no cambie su identidad externa.
BASE_CARD_PRESENTATIONS: tuple[CardPresentation, ...] = (
    CardPresentation(
        card_id="base-c001",
        token="BASE-001",
        name="Ember Initiate",
        rules_text="",
        art="",
    ),
    CardPresentation(
        card_id="base-c002",
        token="BASE-002",
        name="Grove Sentinel",
        rules_text="",
        art="",
    ),
    CardPresentation(
        card_id="base-c003",
        token="BASE-003",
        name="Skyline Duelist",
        rules_text="Puede desafiar a otras criaturas.",
        art="",
    ),
    CardPresentation(
        card_id="base-c004",
        token="BASE-004",
        name="Stoneback Warden",
        rules_text="",
        art="",
    ),
    CardPresentation(
        card_id="base-c005",
        token="BASE-005",
        name="Ashen Vanguard",
        rules_text="",
        art="",
    ),
    CardPresentation(
        card_id="base-c006",
        token="BASE-006",
        name="Verdant Colossus",
        rules_text="",
        art="",
    ),
    CardPresentation(
        card_id="base-c007",
        token="BASE-007",
        name="First Arena Champion",
        rules_text="Puede desafiar a otras criaturas.",
        art="",
    ),
    CardPresentation(
        card_id="base-c008",
        token="BASE-008",
        name="Ancient Grove Keeper",
        rules_text="",
        art="",
    ),
)


BASE_SET_MANIFEST = CollectionManifest(
    collection_id=BASE_SET_ID,
    name="Base Set",
    revision=BASE_SET_REVISION,
    engine_min_version="0.20.1",
    cards=BASE_CARD_DEFINITIONS,
)


def build_base_card_catalog() -> CardCatalog:
    """Construye un catálogo mecánico independiente de la colección base."""

    catalog = CardCatalog()
    for definition in BASE_CARD_DEFINITIONS:
        catalog.register(definition)
    return catalog


def build_base_card_presentation_catalog() -> CardPresentationCatalog:
    """Construye y coteja el catálogo editorial completo de la colección base."""

    catalog = CardPresentationCatalog()
    for presentation in BASE_CARD_PRESENTATIONS:
        catalog.register(presentation)
    validate_card_presentations(build_base_card_catalog(), catalog)
    return catalog


def build_base_catalogs() -> tuple[CardCatalog, CardPresentationCatalog]:
    """Construye ambos catálogos y valida que describan el mismo corpus."""

    mechanical = build_base_card_catalog()
    editorial = build_base_card_presentation_catalog()
    validate_card_presentations(mechanical, editorial)
    return mechanical, editorial


__all__ = [
    "BASE_CARD_DEFINITIONS",
    "BASE_CARD_PRESENTATIONS",
    "BASE_SET_ID",
    "BASE_SET_MANIFEST",
    "BASE_SET_REVISION",
    "build_base_card_catalog",
    "build_base_card_presentation_catalog",
    "build_base_catalogs",
]
