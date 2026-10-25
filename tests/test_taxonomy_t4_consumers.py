from __future__ import annotations

from dataclasses import fields

from card_duel_engine.domain.enums import CardKind, LordDomain
from card_duel_engine.domain.models import CardDefinition, CardFilter
from card_duel_engine.presentation import CardPresentation
from card_duel_engine.public_catalog import PublicCard


def _accredited_lords() -> tuple[CardDefinition, CardDefinition]:
    return (
        CardDefinition(
            "taxonomy-t4-explicit-lord",
            "Señor explícito",
            CardKind.LORD,
            4,
            lord_domain=LordDomain.REALMS,
        ),
        CardDefinition(
            "taxonomy-t4-creature-lord",
            "Criatura Señor",
            CardKind.CREATURE,
            4,
            lord_domain=LordDomain.ABYSS,
        ),
    )


def _public(definition: CardDefinition) -> PublicCard:
    return PublicCard.from_sources(
        definition,
        CardPresentation(definition.card_id, definition.card_id, definition.name, "", ""),
    )


def test_filters_keep_accredited_kinds_distinct_without_a_domain_selector() -> None:
    explicit_lord, creature_lord = _accredited_lords()

    assert CardFilter(kinds=frozenset({CardKind.LORD})).matches(explicit_lord)
    assert not CardFilter(kinds=frozenset({CardKind.LORD})).matches(creature_lord)
    assert CardFilter(kinds=frozenset({CardKind.CREATURE})).matches(creature_lord)
    assert not CardFilter(kinds=frozenset({CardKind.CREATURE})).matches(explicit_lord)
    assert "lord_domain" not in {field.name for field in fields(CardFilter)}


def test_public_catalog_preserves_kind_without_projecting_or_inferring_domain() -> None:
    explicit_lord, creature_lord = _accredited_lords()

    explicit_payload = _public(explicit_lord).to_dict()
    creature_payload = _public(creature_lord).to_dict()

    assert explicit_payload["kind"] == "lord"
    assert creature_payload["kind"] == "creature"
    assert "lord_domain" not in explicit_payload
    assert "lord_domain" not in creature_payload
