from dataclasses import FrozenInstanceError

import pytest

from card_duel_engine.content import (
    BASE_CARD_DEFINITIONS,
    BASE_SET_ID,
    BASE_SET_REVISION,
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
