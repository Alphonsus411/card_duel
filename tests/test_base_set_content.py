from dataclasses import FrozenInstanceError
from hashlib import sha256
import json

import pytest

from card_duel_engine import (
    DeckConstructionPolicy,
    InMemoryMatchStore,
    MatchService,
    classic_deck_policy,
    deck_points,
    validate_deck_group,
)
from card_duel_engine.content import (
    BASE_CARD_DEFINITIONS,
    BASE_CARD_PRESENTATIONS,
    BASE_SET_ID,
    BASE_SET_MANIFEST,
    BASE_SET_REVISION,
    build_base_catalogs,
    build_base_card_presentation_catalog,
    build_base_collection_registry,
    build_base_public_card_catalog,
)
from card_duel_engine.content import CollectionManifest, dump_manifest
from card_duel_engine.domain.enums import CardKind, CardRank, Keyword
from card_duel_engine.domain.models import CardDefinition
from card_duel_engine.service import DeckValidationFailure
from card_duel_engine.storage import MatchNotFound


EXPECTED_PUBLIC_NAMES = {
    "base-c001": "Iniciado de la Brasa",
    "base-c002": "Centinela de la Arboleda",
    "base-c003": "Duelista del Horizonte",
    "base-c004": "Guardián de Espalda Pétrea",
    "base-c005": "Vanguardia de Ceniza",
    "base-c006": "Coloso Frondoso",
    "base-c007": "Primer Campeón de la Arena",
    "base-c008": "Guardián de la Arboleda Ancestral",
}

# Línea base mecánica y editorial estable anterior al cambio de nombres públicos.
EXPECTED_STABLE_CARD_DATA = (
    ("base-c001", "BASE-001", "Ember Initiate", 1, 1, frozenset(), frozenset({"warrior"})),
    ("base-c002", "BASE-002", "Grove Sentinel", 2, 3, frozenset(), frozenset({"guardian"})),
    ("base-c003", "BASE-003", "Skyline Duelist", 3, 2, frozenset({Keyword.CAN_CHALLENGE}), frozenset({"warrior"})),
    ("base-c004", "BASE-004", "Stoneback Warden", 4, 5, frozenset(), frozenset({"guardian"})),
    ("base-c005", "BASE-005", "Ashen Vanguard", 5, 4, frozenset(), frozenset({"warrior"})),
    ("base-c006", "BASE-006", "Verdant Colossus", 6, 7, frozenset(), frozenset({"beast"})),
    ("base-c007", "BASE-007", "First Arena Champion", 7, 6, frozenset({Keyword.CAN_CHALLENGE}), frozenset({"warrior"})),
    ("base-c008", "BASE-008", "Ancient Grove Keeper", 8, 9, frozenset(), frozenset({"guardian"})),
)


@pytest.fixture
def base_deck() -> tuple[CardDefinition, ...]:
    """Construye la microcolección como un mazo mediante datos publicados."""

    return tuple(card for card in BASE_SET_MANIFEST.cards for _ in range(5))


@pytest.fixture
def base_deck_policy() -> DeckConstructionPolicy:
    """Permite recombinar el corpus sin imponer una novena definición."""

    return classic_deck_policy(
        allowed_set_ids={BASE_SET_ID},
        max_standard_copies=None,
        point_budget=180,
    )


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
    assert {card.rank for card in BASE_CARD_DEFINITIONS} == {CardRank.STANDARD}
    assert len({card.cost for card in BASE_CARD_DEFINITIONS}) > 1
    assert len({card.base_strength for card in BASE_CARD_DEFINITIONS}) > 1
    assert len({subtype for card in BASE_CARD_DEFINITIONS for subtype in card.subtypes}) >= 2
    assert any(not card.keywords for card in BASE_CARD_DEFINITIONS)
    assert any(
        Keyword.CAN_CHALLENGE in card.keywords and card.subtypes
        for card in BASE_CARD_DEFINITIONS
    )


def test_base_deck_uses_five_copies_and_authoritative_costs(
    base_deck: tuple[CardDefinition, ...],
) -> None:
    assert tuple(card.cost for card in BASE_SET_MANIFEST.cards) == tuple(range(1, 9))
    assert len(base_deck) == 40
    assert all(base_deck.count(card) == 5 for card in BASE_SET_MANIFEST.cards)
    assert deck_points(base_deck) == 180


def test_equal_base_decks_pass_group_validation_and_create_a_match(
    base_deck: tuple[CardDefinition, ...], base_deck_policy
) -> None:
    decks = {"A": base_deck, "B": tuple(base_deck)}
    group_result = validate_deck_group(decks, require_equal_points=True)
    assert group_result.is_valid
    assert tuple(deck_points(deck) for deck in group_result.decks.values()) == (180, 180)

    store = InMemoryMatchStore()
    service = MatchService(
        store,
        catalog=build_base_collection_registry(),
        deck_policy=base_deck_policy,
        require_equal_points=True,
    )
    assert service.create_match("base-equal", decks, seed=17) == 1
    assert store.load("base-equal").engine.state is not None


def test_unequal_recombination_is_rejected_without_persisting_match(
    base_deck: tuple[CardDefinition, ...], base_deck_policy
) -> None:
    # Se sustituye una copia por otra definición ya publicada: conserva las 40
    # cartas y no modifica el corpus, pero reduce el total de 180 a 179.
    unequal_deck = base_deck[:-1] + (BASE_SET_MANIFEST.cards[-2],)
    assert deck_points(base_deck) == 180
    assert deck_points(unequal_deck) == 179
    assert base_deck_policy.validate(unequal_deck).is_valid

    store = InMemoryMatchStore()
    service = MatchService(
        store,
        catalog=build_base_collection_registry(),
        deck_policy=base_deck_policy,
        require_equal_points=True,
    )
    with pytest.raises(DeckValidationFailure):
        service.create_match(
            "base-unequal", {"A": base_deck, "B": unequal_deck}, seed=17
        )
    with pytest.raises(MatchNotFound):
        store.load("base-unequal")


def test_three_equal_base_decks_create_a_match(
    base_deck: tuple[CardDefinition, ...], base_deck_policy
) -> None:
    decks = {player: tuple(base_deck) for player in ("A", "B", "C")}
    assert all(deck_points(deck) == 180 for deck in decks.values())

    store = InMemoryMatchStore()
    service = MatchService(
        store,
        catalog=build_base_collection_registry(),
        deck_policy=base_deck_policy,
        require_equal_points=True,
    )
    assert service.create_match("base-three-player", decks, seed=23) == 1
    state = store.load("base-three-player").engine.state
    assert state is not None
    assert state.turn_order == ("A", "B", "C")


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
    assert {card.card_id: card.name for card in BASE_CARD_PRESENTATIONS} == (
        EXPECTED_PUBLIC_NAMES
    )


def test_public_name_translation_preserves_all_stable_card_data() -> None:
    presentations = {card.card_id: card for card in BASE_CARD_PRESENTATIONS}
    actual = tuple(
        (
            definition.card_id,
            presentations[definition.card_id].token,
            definition.name,
            definition.cost,
            definition.base_strength,
            definition.keywords,
            definition.subtypes,
        )
        for definition in BASE_CARD_DEFINITIONS
    )

    assert actual == EXPECTED_STABLE_CARD_DATA


def test_base_presentation_text_only_describes_declared_challenge_keyword() -> None:
    definitions = {card.card_id: card for card in BASE_CARD_DEFINITIONS}
    for presentation in BASE_CARD_PRESENTATIONS:
        has_challenge = Keyword.CAN_CHALLENGE in definitions[presentation.card_id].keywords
        assert bool(presentation.rules_text) is has_challenge
        assert presentation.rules_text == (
            "Puede desafiar a otras criaturas." if has_challenge else ""
        )


def test_base_catalog_builders_return_complete_validated_corpus() -> None:
    editorial = build_base_card_presentation_catalog()
    mechanical, paired_editorial = build_base_catalogs()

    assert editorial.presentations() == paired_editorial.presentations()
    assert mechanical.definitions() == BASE_CARD_DEFINITIONS
    assert len(editorial) == len(mechanical) == 8
    assert BASE_SET_MANIFEST.cards == BASE_CARD_DEFINITIONS


def test_base_manifest_and_registry_publish_exact_corpus_and_provenance() -> None:
    assert BASE_SET_MANIFEST.collection_id == BASE_SET_ID
    assert BASE_SET_MANIFEST.revision == 1
    assert BASE_SET_MANIFEST.engine_min_version == "0.20.1"
    assert BASE_SET_MANIFEST.dependencies == ()
    assert BASE_SET_MANIFEST.metadata == {"corpus": "initial"}

    snapshot = build_base_collection_registry().snapshot()
    assert snapshot.catalog.definitions() == BASE_CARD_DEFINITIONS
    assert len(snapshot.catalog) == 8
    provenance = snapshot.collections[BASE_SET_ID]
    assert provenance.collection_id == BASE_SET_ID
    assert provenance.revision == BASE_SET_REVISION
    assert provenance.dependencies == ()
    expected_digest = sha256(
        dump_manifest(BASE_SET_MANIFEST, indent=None).encode("utf-8")
    ).hexdigest()
    assert provenance.manifest_sha256 == expected_digest


def test_base_public_catalog_joins_independent_sources_by_card_id() -> None:
    public = build_base_public_card_catalog()

    assert tuple(card.card_id for card in public.cards) == tuple(
        definition.card_id for definition in BASE_CARD_DEFINITIONS
    )
    assert len(public.cards) == 8
    assert {card.card_id: card.name for card in public.cards} == EXPECTED_PUBLIC_NAMES
    assert tuple(
        (
            card.card_id,
            card.token,
            card.mechanical_name,
            card.cost,
            card.base_strength,
            frozenset(
                {Keyword.CAN_CHALLENGE}
                if "can_challenge" in card.keywords
                else set()
            ),
            frozenset(card.subtypes),
        )
        for card in public.cards
    ) == EXPECTED_STABLE_CARD_DATA
    assert isinstance(json.dumps(public.to_dict(), ensure_ascii=False), str)


def test_failed_batch_keeps_complete_base_registry_snapshot_unchanged() -> None:
    registry = build_base_collection_registry()
    before = registry.snapshot()
    valid_card = CardDefinition(
        card_id="extension-c001",
        name="Extension",
        kind=CardKind.CREATURE,
        cost=1,
        base_strength=1,
        set_id="extension",
    )
    collision = CardDefinition(
        card_id=BASE_CARD_DEFINITIONS[0].card_id,
        name="Collision",
        kind=CardKind.CREATURE,
        cost=1,
        base_strength=1,
        set_id="invalid",
    )
    batch = (
        CollectionManifest("extension", "Extension", 1, "0.20.1", (valid_card,)),
        CollectionManifest("invalid", "Invalid", 1, "0.20.1", (collision,)),
    )

    with pytest.raises(ValueError, match="colisiona con el catálogo"):
        registry.register_batch(batch)

    after = registry.snapshot()
    assert after == before
    assert after.catalog.definitions() == BASE_CARD_DEFINITIONS
    assert after.collections == before.collections
