from dataclasses import FrozenInstanceError

import pytest

from card_duel_engine.content import (
    BASE_CARD_DEFINITIONS,
    BASE_CARD_PRESENTATIONS,
    BASE_SET_ID,
    BASE_SET_MANIFEST,
    BASE_SET_REVISION,
    build_base_catalogs,
    build_base_card_presentation_catalog,
)
from card_duel_engine.domain.enums import CardKind, CardRank, Keyword


def test_base_set_is_a_deterministic_tuple_of_eight_unique_definitions() -> None:
    assert isinstance(BASE_CARD_DEFINITIONS, tuple)
    assert len(BASE_CARD_DEFINITIONS) == 8
    assert tuple(card.card_id for card in BASE_CARD_DEFINITIONS) == tuple(
        f"base-c{number:03d}" for number in range(1, 9)
    )


def test_base_set_has_uniform_provenance_and_immutable_definitions() -> None:
    assert BASE_SET_ID == "base"
    assert BASE_SET_REVISION == 1
    assert {card.set_id for card in BASE_CARD_DEFINITIONS} == {BASE_SET_ID}
    assert {card.revision for card in BASE_CARD_DEFINITIONS} == {BASE_SET_REVISION}

    with pytest.raises(FrozenInstanceError):
        BASE_CARD_DEFINITIONS[0].name = "Renamed"  # type: ignore[misc]


def test_base_set_covers_supported_creature_mechanics() -> None:
    assert {card.kind for card in BASE_CARD_DEFINITIONS} == {CardKind.CREATURE}
    assert {card.rank for card in BASE_CARD_DEFINITIONS} == {
        CardRank.STANDARD,
        CardRank.LEGENDARY,
    }
    assert len({card.cost for card in BASE_CARD_DEFINITIONS}) > 1
    assert len({card.base_strength for card in BASE_CARD_DEFINITIONS}) > 1
    assert len({subtype for card in BASE_CARD_DEFINITIONS for subtype in card.subtypes}) >= 2
    assert any(not card.keywords for card in BASE_CARD_DEFINITIONS)
    assert any(
        Keyword.CAN_CHALLENGE in card.keywords and card.subtypes
        for card in BASE_CARD_DEFINITIONS
    )


def test_base_presentations_have_explicit_stable_tokens_and_matching_ids() -> None:
    assert isinstance(BASE_CARD_PRESENTATIONS, tuple)
    assert tuple(card.token for card in BASE_CARD_PRESENTATIONS) == (
        "BASE-001",
        "BASE-002",
        "BASE-003",
        "BASE-004",
        "BASE-005",
        "BASE-006",
        "BASE-007",
        "BASE-008",
    )
    assert tuple(card.card_id for card in BASE_CARD_PRESENTATIONS) == tuple(
        card.card_id for card in BASE_CARD_DEFINITIONS
    )
    assert all(card.art == "" for card in BASE_CARD_PRESENTATIONS)
    assert tuple(card.name for card in BASE_CARD_PRESENTATIONS) == tuple(
        card.name for card in BASE_CARD_DEFINITIONS
    )


def test_base_presentation_text_only_describes_declared_challenge_keyword() -> None:
    definitions = {card.card_id: card for card in BASE_CARD_DEFINITIONS}
    for presentation in BASE_CARD_PRESENTATIONS:
        has_challenge = Keyword.CAN_CHALLENGE in definitions[presentation.card_id].keywords
        assert bool(presentation.rules_text) is has_challenge


def test_base_catalog_builders_return_complete_validated_corpus() -> None:
    editorial = build_base_card_presentation_catalog()
    mechanical, paired_editorial = build_base_catalogs()

    assert editorial.presentations() == paired_editorial.presentations()
    assert mechanical.definitions() == BASE_CARD_DEFINITIONS
    assert len(editorial) == len(mechanical) == 8
    assert BASE_SET_MANIFEST.cards == BASE_CARD_DEFINITIONS
