"""Contrato normativo del corpus Mítico seleccionado en la fase 2-C.

Las expectativas de este módulo son una transcripción explícita de la revisión
del PDF.  Deliberadamente no se construyen a partir del manifiesto probado.
"""

from __future__ import annotations

import ast
from copy import deepcopy
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from card_duel_engine import GameEngine, RuleSet
from card_duel_engine.content import (
    MYTHIC_CARD_DEFINITIONS,
    MYTHIC_CARD_PRESENTATIONS,
    MYTHIC_SET_ID,
    MYTHIC_SET_MANIFEST,
    MYTHIC_SET_REVISION,
    build_mythic_public_card_catalog,
)
from card_duel_engine.domain import (
    CardDefinition,
    CardFilter,
    CardKind,
    CardRank,
    EffectDefinition,
    EffectKind,
    Phase,
    TargetMode,
    TriggerKind,
    Zone,
    ZoneTarget,
)
from card_duel_engine.engine import (
    ChooseTriggeredTargets,
    OrderTriggeredAbilities,
    PassPriority,
    PlayCard,
    ResolveSearchChoice,
)
from card_duel_engine.presentation import CardPresentation
from card_duel_engine.rules import deck_points, mythic_deck_policy
from card_duel_engine.rules.deck import validate_deck_group

from fixtures import test_deck


ROOT = Path(__file__).resolve().parents[1]
CORPUS_DOCUMENT = ROOT / "docs" / "PHASE_2C_MYTHIC_CORPUS.md"

# Inventario normativo de las DOS razas escogidas. No derivar del manifiesto.
REVIEWED_RACES = {
    "Elfo": {
        "023": ("Elfo de los Bosques.", "SUPPORTED"),
        "024": ("Elfo Explorador.", "PARTIAL"),
        "025": ("Elfo Montaraz.", "SUPPORTED"),
        "026": ("Elfo Adivinador.", "GAP"),
        "027": ("Elfo Duelista.", "GAP"),
        "028": ("Elfo Cabalista.", "PARTIAL"),
        "029": ("Alberich, el Rey de los Elfos.", "PARTIAL"),
    },
    "Ángel": {
        "140": ("Ángel de la Guarda.", "PARTIAL"),
        "141": ("Ángel de Piedad.", "PARTIAL"),
        "142": ("Ángel de la Justicia.", "PARTIAL"),
        "143": ("Ángel de la Verdad.", "PARTIAL"),
        "144": ("Ángel de la Muerte.", "PARTIAL"),
        "145": ("Arcángel.", "PARTIAL"),
    },
}

# Tabla mecánico-editorial transcrita del PDF para las cartas ejecutables. Cada
# campo se escribe aquí de forma independiente de MYTHIC_CARD_DEFINITIONS.
SUPPORTED_PDF_TABLE = {
    "023": {
        "card_id": "mythic-elf-023",
        "token": "nº023",
        "name": "Elfo de los Bosques.",
        "rules_text": "Cuando el Elfo de los Bosques entre en juego, busca una carta de Recurso Rápido de tu mazo de Recursos y ponla en tu mano, baraja tu mazo.",
        "cost": 10,
        "base_strength": 10,
        "kind": CardKind.CREATURE,
        "rank": CardRank.STANDARD,
        "subtypes": frozenset(),
        "keywords": frozenset(),
        "ability_id": "mythic-023-entry-search",
        "trigger": TriggerKind.ON_ENTER_BATTLEFIELD,
        "search_kind": CardKind.QUICK_RESOURCE,
    },
    "025": {
        "card_id": "mythic-elf-025",
        "token": "nº025",
        "name": "Elfo Montaraz.",
        "rules_text": "Cuando este naipe entre en juego, busca una carta de Evento y ponla en tu mano. Baraja tu mazo de Recursos.",
        "cost": 10,
        "base_strength": 10,
        "kind": CardKind.CREATURE,
        "rank": CardRank.STANDARD,
        "subtypes": frozenset(),
        "keywords": frozenset(),
        "ability_id": "mythic-025-entry-search",
        "trigger": TriggerKind.ON_ENTER_BATTLEFIELD,
        "search_kind": CardKind.EVENT,
    },
}


def _expected_supported_ids() -> set[str]:
    return {row["card_id"] for row in SUPPORTED_PDF_TABLE.values()}


def _force_zone(engine: GameEngine, definition_id: str, zone: Zone) -> str:
    instance_id = next(
        instance_id
        for instance_id, instance in engine.state.cards.items()
        if instance.definition_id == definition_id and instance.owner_id == "A"
    )
    for player in engine.state.players.values():
        for cards in player.zones.values():
            if instance_id in cards:
                cards.remove(instance_id)
    engine.state.players["A"].zones[zone].append(instance_id)
    instance = engine.state.cards[instance_id]
    instance.zone = zone
    instance.controller_id = "A"
    return instance_id


def _resolve_one(engine: GameEngine) -> None:
    engine.execute(PassPriority(engine.state.priority_player_id))
    engine.execute(PassPriority(engine.state.priority_player_id))


def _engine_for(definition: CardDefinition, searchable: CardDefinition) -> GameEngine:
    engine = GameEngine(RuleSet())
    engine.new_match(
        {
            "A": [definition, searchable, *test_deck("MIT-A", 14)],
            "B": test_deck("MIT-B", 14),
        },
        seed=203,
    )
    engine.state.phase = Phase.EFFECTS
    engine.state.priority_player_id = "A"
    return engine


def test_selected_race_inventory_is_explicit_complete_and_has_no_third_race() -> None:
    assert set(REVIEWED_RACES) == {"Elfo", "Ángel"}
    assert tuple(REVIEWED_RACES["Elfo"]) == (
        "023", "024", "025", "026", "027", "028", "029"
    )
    assert tuple(REVIEWED_RACES["Ángel"]) == (
        "140", "141", "142", "143", "144", "145"
    )
    assert sum(map(len, REVIEWED_RACES.values())) == 13


def test_manifest_contains_every_and_only_fully_supported_reviewed_card() -> None:
    reviewed = {
        number: classification
        for cards in REVIEWED_RACES.values()
        for number, (_, classification) in cards.items()
    }
    expected_numbers = {
        number for number, classification in reviewed.items() if classification == "SUPPORTED"
    }
    actual_numbers = {card.card_id.rsplit("-", 1)[-1] for card in MYTHIC_SET_MANIFEST.cards}
    assert actual_numbers == expected_numbers == set(SUPPORTED_PDF_TABLE)
    assert all(number in reviewed for number in actual_numbers)


def test_ids_tokens_revision_and_definition_presentation_join_are_bijective() -> None:
    definitions = {card.card_id: card for card in MYTHIC_CARD_DEFINITIONS}
    presentations = {card.card_id: card for card in MYTHIC_CARD_PRESENTATIONS}
    assert len(definitions) == len(MYTHIC_CARD_DEFINITIONS)
    assert len(presentations) == len(MYTHIC_CARD_PRESENTATIONS)
    assert len({card.token for card in MYTHIC_CARD_PRESENTATIONS}) == len(presentations)
    assert definitions.keys() == presentations.keys() == _expected_supported_ids()
    assert MYTHIC_SET_ID == "mythic"
    assert MYTHIC_SET_REVISION == 1
    assert MYTHIC_SET_MANIFEST.collection_id == "mythic"
    assert MYTHIC_SET_MANIFEST.revision == 1
    assert all((card.set_id, card.revision) == ("mythic", 1) for card in definitions.values())


@pytest.mark.parametrize("number", tuple(SUPPORTED_PDF_TABLE))
def test_supported_card_matches_explicit_pdf_table(number: str) -> None:
    expected = SUPPORTED_PDF_TABLE[number]
    definition = next(card for card in MYTHIC_CARD_DEFINITIONS if card.card_id == expected["card_id"])
    presentation = next(card for card in MYTHIC_CARD_PRESENTATIONS if card.card_id == expected["card_id"])
    assert {
        "card_id": definition.card_id,
        "name": definition.name,
        "cost": definition.cost,
        "base_strength": definition.base_strength,
        "kind": definition.kind,
        "rank": definition.rank,
        "subtypes": definition.subtypes,
        "keywords": definition.keywords,
    } == {key: expected[key] for key in (
        "card_id", "name", "cost", "base_strength", "kind", "rank", "subtypes", "keywords"
    )}
    assert (presentation.token, presentation.name, presentation.rules_text) == (
        expected["token"], expected["name"], expected["rules_text"]
    )
    assert len(definition.effects) == 0
    assert len(definition.abilities) == 1
    ability = definition.abilities[0]
    assert (ability.ability_id, ability.trigger, ability.cost, len(ability.effects)) == (
        expected["ability_id"], expected["trigger"], ability.cost.__class__(), 1
    )
    assert ability.effects[0] == EffectDefinition(
        kind=EffectKind.SEARCH_ZONE,
        amount=0,
        target=TargetMode.CHOSEN_ZONE,
        destination_zone=Zone.HAND,
        selection_minimum=0,
        selection_maximum=1,
        search_filter=CardFilter(kinds=frozenset({expected["search_kind"]})),
        shuffle_after_search=True,
    )


def test_public_names_and_texts_are_spanish_json_safe_and_do_not_leak_sources() -> None:
    public = build_mythic_public_card_catalog()
    expected_text = {row["rules_text"] for row in SUPPORTED_PDF_TABLE.values()}
    expected_names = {row["name"] for row in SUPPORTED_PDF_TABLE.values()}
    assert {card.name for card in public.cards} == expected_names
    assert {card.rules_text for card in public.cards} == expected_text
    payload = public.to_dict()
    json.dumps(payload, ensure_ascii=False)

    def assert_no_source_objects(value: object) -> None:
        assert not isinstance(value, (CardDefinition, CardPresentation))
        if isinstance(value, dict):
            for child in value.values():
                assert_no_source_objects(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                assert_no_source_objects(child)

    assert_no_source_objects(payload)


@pytest.mark.parametrize("number", tuple(SUPPORTED_PDF_TABLE))
def test_executable_search_legal_action_cost_target_resolution_and_atomic_rollback(number: str) -> None:
    expected = SUPPORTED_PDF_TABLE[number]
    definition = next(card for card in MYTHIC_CARD_DEFINITIONS if card.card_id == expected["card_id"])
    searchable = CardDefinition(
        f"objetivo-{number}", "Objetivo de búsqueda", expected["search_kind"], 5,
        permanent=False, transmutable=False,
    )
    engine = _engine_for(definition, searchable)
    source_id = _force_zone(engine, definition.card_id, Zone.HAND)
    target_id = _force_zone(engine, searchable.card_id, Zone.DECK)
    engine.state.players["A"].steps = 10
    command = PlayCard("A", source_id)
    assert command in engine.legal_actions("A")
    engine.execute(command)
    assert engine.state.players["A"].steps == 0
    _resolve_one(engine)  # carta: entra y crea el disparo
    pending = engine.state.pending_triggers
    assert len(pending) == 1
    pending_id = pending[0].item_id
    engine.execute(
        ChooseTriggeredTargets(
            "A", pending_id, chosen_zone_targets=(ZoneTarget("A", Zone.DECK),)
        )
    )
    engine.execute(OrderTriggeredAbilities("A", (pending_id,)))
    _resolve_one(engine)  # disparo: solicita la elección del objetivo oculto
    assert engine.observe("A").searchable_card_ids == (target_id,)
    assert ResolveSearchChoice("A", (target_id,)) in engine.legal_actions("A")

    before = deepcopy(engine.state)
    with patch.object(engine._stack, "_shuffle_zone", side_effect=RuntimeError("fallo inducido")):
        with pytest.raises(RuntimeError, match="fallo inducido"):
            engine.execute(ResolveSearchChoice("A", (target_id,)))
    assert engine.state == before

    engine.execute(ResolveSearchChoice("A", (target_id,)))
    assert target_id in engine.state.players["A"].zones[Zone.HAND]
    assert engine.state.pending_search is None


def test_blocked_cards_are_absent_and_documented_with_review_classification() -> None:
    executable_numbers = {card.card_id.rsplit("-", 1)[-1] for card in MYTHIC_CARD_DEFINITIONS}
    document = CORPUS_DOCUMENT.read_text(encoding="utf-8")
    for race_cards in REVIEWED_RACES.values():
        for number, (name, classification) in race_cards.items():
            if classification == "SUPPORTED":
                continue
            assert number not in executable_numbers
            section = document.split(f"**CARD:** nº{number}", 1)[1].split("\n### ", 1)[0]
            assert name in section
            assert f"**CLASSIFICATION:** `{classification}`" in section


def test_resolution_sources_have_no_editorial_or_identity_branches() -> None:
    forbidden_literals = {
        value
        for race, cards in REVIEWED_RACES.items()
        for number, (name, _) in cards.items()
        for value in (race, number, f"nº{number}", name)
    } | _expected_supported_ids()
    resolution_files = (
        ROOT / "src/card_duel_engine/engine/effects.py",
        ROOT / "src/card_duel_engine/engine/stack.py",
        ROOT / "src/card_duel_engine/engine/actions.py",
        ROOT / "src/card_duel_engine/rules/resolvers.py",
    )
    for path in resolution_files:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        branch_literals = {
            node.value
            for branch in ast.walk(tree)
            if isinstance(branch, (ast.If, ast.IfExp, ast.Match, ast.While))
            for node in ast.walk(branch.test if hasattr(branch, "test") else branch.subject)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        }
        assert branch_literals.isdisjoint(forbidden_literals), path


def test_mythic_points_keep_cost_sum_open_budget_and_existing_multideck_equality() -> None:
    assert deck_points(MYTHIC_CARD_DEFINITIONS) == sum(
        row["cost"] for row in SUPPORTED_PDF_TABLE.values()
    )
    policy = mythic_deck_policy()
    assert policy.min_points == 50
    assert policy.point_budget is None
    first = tuple(test_deck("igual-a", 12))
    second = tuple(test_deck("igual-b", 12))
    result = validate_deck_group({"A": first, "B": second}, require_equal_points=True)
    assert result.is_valid
    assert tuple(map(deck_points, result.decks.values())) == (60, 60)
