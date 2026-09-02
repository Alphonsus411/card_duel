"""Contenido Mítico que superó íntegramente la auditoría mecánica."""

from __future__ import annotations

from ..catalog import CardCatalog
from ..domain.enums import CardKind, EffectKind, TargetMode, TriggerKind, Zone
from ..domain.models import (
    AbilityDefinition,
    CardDefinition,
    CardFilter,
    EffectDefinition,
)
from ..presentation import (
    CardPresentation,
    CardPresentationCatalog,
    validate_card_presentations,
)
from ..public_catalog import PublicCardCatalog
from .manifest import CollectionManifest
from .registry import CollectionRegistry

MYTHIC_SET_ID = "mythic"
MYTHIC_SET_REVISION = 1


def _entry_search_ability(ability_id: str, kind: CardKind) -> AbilityDefinition:
    return AbilityDefinition(
        ability_id=ability_id,
        trigger=TriggerKind.ON_ENTER_BATTLEFIELD,
        effects=(
            EffectDefinition(
                kind=EffectKind.SEARCH_ZONE,
                amount=0,
                target=TargetMode.CHOSEN_ZONE,
                destination_zone=Zone.HAND,
                selection_minimum=0,
                selection_maximum=1,
                search_filter=CardFilter(kinds=frozenset({kind})),
                shuffle_after_search=True,
            ),
        ),
    )


# Sólo se publican cartas clasificadas SUPPORTED en la auditoría. Los IDs son
# identidad mecánica deliberada; no se calculan desde el orden de esta tupla.
MYTHIC_CARD_DEFINITIONS: tuple[CardDefinition, ...] = (
    CardDefinition(
        card_id="mythic-elf-023",
        name="Elfo de los Bosques.",
        kind=CardKind.CREATURE,
        cost=10,
        base_strength=10,
        set_id=MYTHIC_SET_ID,
        revision=MYTHIC_SET_REVISION,
        abilities=(
            _entry_search_ability("mythic-023-entry-search", CardKind.QUICK_RESOURCE),
        ),
    ),
    CardDefinition(
        card_id="mythic-elf-025",
        name="Elfo Montaraz.",
        kind=CardKind.CREATURE,
        cost=10,
        base_strength=10,
        set_id=MYTHIC_SET_ID,
        revision=MYTHIC_SET_REVISION,
        abilities=(_entry_search_ability("mythic-025-entry-search", CardKind.EVENT),),
    ),
)

MYTHIC_CARD_PRESENTATIONS: tuple[CardPresentation, ...] = (
    CardPresentation(
        card_id="mythic-elf-023",
        token="nº023",
        name="Elfo de los Bosques.",
        rules_text="Cuando el Elfo de los Bosques entre en juego, busca una carta de Recurso Rápido de tu mazo de Recursos y ponla en tu mano, baraja tu mazo.",
        art="",
    ),
    CardPresentation(
        card_id="mythic-elf-025",
        token="nº025",
        name="Elfo Montaraz.",
        rules_text="Cuando este naipe entre en juego, busca una carta de Evento y ponla en tu mano. Baraja tu mazo de Recursos.",
        art="",
    ),
)

MYTHIC_SET_MANIFEST = CollectionManifest(
    collection_id=MYTHIC_SET_ID,
    name="Edición Mítica",
    revision=MYTHIC_SET_REVISION,
    engine_min_version="0.20.1",
    cards=MYTHIC_CARD_DEFINITIONS,
    metadata={"corpus": "audited-supported-only", "phase": "2-C-in-progress"},
    dependencies=(),
)


def build_mythic_collection_registry() -> CollectionRegistry:
    registry = CollectionRegistry()
    registry.register(MYTHIC_SET_MANIFEST)
    return registry


def build_mythic_card_catalog() -> CardCatalog:
    catalog = CardCatalog()
    for definition in MYTHIC_CARD_DEFINITIONS:
        catalog.register(definition)
    return catalog


def build_mythic_card_presentation_catalog() -> CardPresentationCatalog:
    catalog = CardPresentationCatalog()
    for presentation in MYTHIC_CARD_PRESENTATIONS:
        catalog.register(presentation)
    validate_card_presentations(build_mythic_card_catalog(), catalog)
    return catalog


def build_mythic_public_card_catalog() -> PublicCardCatalog:
    registry = build_mythic_collection_registry()
    return PublicCardCatalog(registry.catalog, build_mythic_card_presentation_catalog())


def build_mythic_catalogs() -> tuple[CardCatalog, CardPresentationCatalog]:
    mechanical = build_mythic_card_catalog()
    editorial = build_mythic_card_presentation_catalog()
    validate_card_presentations(mechanical, editorial)
    return mechanical, editorial


__all__ = [
    "MYTHIC_CARD_DEFINITIONS",
    "MYTHIC_CARD_PRESENTATIONS",
    "MYTHIC_SET_ID",
    "MYTHIC_SET_MANIFEST",
    "MYTHIC_SET_REVISION",
    "build_mythic_card_catalog",
    "build_mythic_card_presentation_catalog",
    "build_mythic_catalogs",
    "build_mythic_collection_registry",
    "build_mythic_public_card_catalog",
]
