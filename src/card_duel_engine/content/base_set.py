"""Definiciones mecánicas canónicas de la colección base."""

from __future__ import annotations

from ..domain.enums import CardKind, CardRank, Keyword
from ..domain.models import CardDefinition

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


__all__ = ["BASE_CARD_DEFINITIONS", "BASE_SET_ID", "BASE_SET_REVISION"]
