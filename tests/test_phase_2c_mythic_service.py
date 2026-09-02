"""Integración extremo a extremo del contenido Mítico SUPPORTED por la API pública."""

from __future__ import annotations

from dataclasses import replace

import pytest

from card_duel_engine import (
    AccessDenied,
    AuthenticatedMatchApplication,
    CommandRejected,
    ExternalIdentity,
    InMemoryIdentityAuthorization,
    InMemoryMatchStore,
    MatchService,
    OptionRejected,
    PublicLegalAction,
    PublicMatchView,
    WriteConflict,
    dump_replay,
    dump_snapshot,
    load_snapshot,
    replay_from_log,
)
from card_duel_engine.content import (
    CollectionManifest,
    CollectionRegistry,
    MYTHIC_CARD_DEFINITIONS,
    MYTHIC_CARD_PRESENTATIONS,
    MYTHIC_SET_MANIFEST,
)
from card_duel_engine.domain import Phase, Zone, ZoneTarget
from card_duel_engine.engine import (
    AdvancePhase,
    ChooseTriggeredTargets,
    OrderTriggeredAbilities,
    PassPriority,
    PlayCard,
    ResolveSearchChoice,
)
from card_duel_engine.engine.game import GameEngine
from card_duel_engine.persistence.snapshot import state_digest
from card_duel_engine.presentation import CardPresentation, CardPresentationCatalog
from card_duel_engine.public_catalog import PublicCardCatalog
from card_duel_engine.rules import deck_points, mythic_deck_policy, validate_deck_group
from card_duel_engine.rules.config import RuleSet

from fixtures import quick_damage_fixture, test_deck


MATCH_ID = "phase-2c-mythic-service"


def _decks_and_support_cards():
    """Usa las fábricas públicas y deja una sola Mítica jugable al llegar a Efectos."""
    mythic_023, mythic_025 = MYTHIC_CARD_DEFINITIONS
    searchable = replace(quick_damage_fixture("mythic-searchable"), cost=50)
    support_a = tuple(replace(card, cost=50) for card in test_deck("SERVICE-A", 37))
    support_b = tuple(replace(card, cost=50) for card in test_deck("SERVICE-B", 37))
    return (
        {
            "A": (mythic_023, mythic_025, searchable, *support_a),
            "B": (mythic_023, mythic_025, searchable, *support_b),
        },
        (searchable, *support_a, *support_b),
    )


def _public_catalog(registry: CollectionRegistry) -> PublicCardCatalog:
    editorial = CardPresentationCatalog()
    mythic_presentations = {card.card_id: card for card in MYTHIC_CARD_PRESENTATIONS}
    for definition in registry.catalog.definitions():
        presentation = mythic_presentations.get(definition.card_id)
        editorial.register(
            presentation
            or CardPresentation(
                definition.card_id,
                f"fixture-{definition.card_id}",
                definition.name,
                "Carta auxiliar de integración.",
                "",
            )
        )
    return PublicCardCatalog(registry.catalog, editorial)


def _assert_public_boundary(view: PublicMatchView) -> None:
    payload = view.to_dict()
    assert isinstance(view, PublicMatchView)
    assert all(isinstance(option, PublicLegalAction) for option in view.legal_actions)
    assert all(
        set(option.to_dict()) == {"option_id", "action"}
        for option in view.legal_actions
    )
    assert set(payload["observation"]) == {
        "player_id", "active_player_id", "phase", "own_hand", "own_steps",
        "own_wounds", "opponent_hand_sizes", "public_event_count",
        "own_battlefield", "opponent_battlefields", "stack_size",
    }
    serialized = repr(payload).lower()
    for private_name in (
        "command", "card_id", "chosen_card_ids", "chosen_zone_targets",
        "searchable_card_ids", "pending_triggers", "state", "snapshot",
    ):
        assert private_name not in serialized


def _submit_option(
    app, service, identity, command_type, predicate=lambda command: True
):
    """Localiza la alternativa autoritativa, pero cruza la frontera sólo con su token."""
    public = app.view(identity, MATCH_ID)
    internal = service.view(MATCH_ID, public.observation.player_id)
    index = next(
        index
        for index, command in enumerate(internal.legal_actions)
        if isinstance(command, command_type) and predicate(command)
    )
    option = public.legal_actions[index]
    assert option.action == command_type.__name__
    return app.submit_option(
        identity, MATCH_ID, option.option_id, expected_version=public.version
    )


def test_mythic_collection_catalog_service_public_options_snapshot_and_replay():
    decks, support_cards = _decks_and_support_cards()

    # Colección -> catálogo mecánico/editorial/público.
    registry = CollectionRegistry()
    registry.register(MYTHIC_SET_MANIFEST)
    registry.register(
        CollectionManifest(
            "test-fixtures", "Fixtures de integración", 1, "0.20.1", support_cards
        )
    )
    public_catalog = _public_catalog(registry)
    assert {card.card_id for card in public_catalog.cards} == {
        card.card_id for card in registry.catalog.definitions()
    }

    # Catálogo -> política individual y equivalencia relacional -> servicio.
    policy = mythic_deck_policy(
        allowed_set_ids={"mythic", "test-fixtures"},
        mythic_set_ids={"mythic"},
        point_budget=None,
    )
    assert policy.point_budget is None
    assert {card.card_id for card in MYTHIC_SET_MANIFEST.cards} == {
        "mythic-elf-023",
        "mythic-elf-025",
    }
    assert all(policy.validate(deck).is_valid for deck in decks.values())
    assert all(len(deck) == 40 and deck_points(deck) >= 50 for deck in decks.values())
    group = validate_deck_group(decks, require_equal_points=True)
    assert group.is_valid
    assert deck_points(group.decks["A"]) == deck_points(group.decks["B"])

    store = InMemoryMatchStore()
    service = MatchService(
        store,
        engine_factory=lambda: GameEngine(
            RuleSet(steps_per_maintenance=10), catalog=registry
        ),
        deck_policy=policy,
        require_equal_points=True,
    )
    authorization = InMemoryIdentityAuthorization()
    app = AuthenticatedMatchApplication(service, authorization)
    alice = ExternalIdentity("integration", "alice")
    bob = ExternalIdentity("integration", "bob")
    authorization.bind_player(alice, MATCH_ID, "A")
    authorization.bind_player(bob, MATCH_ID, "B")
    assert service.create_match(MATCH_ID, decks, seed=9) == 1

    # Avanza exclusivamente mediante option_id hasta Efectos.
    for _ in range(2):
        _submit_option(app, service, alice, PassPriority)
        _submit_option(app, service, bob, PassPriority)
        _submit_option(app, service, alice, AdvancePhase)
    authoritative = service.get_match(MATCH_ID).engine
    assert authoritative.state.phase is Phase.EFFECTS
    assert authoritative.state.players["A"].steps == 10

    # La semilla elegida deja 023 en mano; la alternativa exacta se envía opacamente.
    source_id = next(
        card_id
        for card_id in authoritative.state.players["A"].zones[Zone.HAND]
        if authoritative.state.cards[card_id].definition_id == "mythic-elf-023"
    )
    before_steps = authoritative.state.players["A"].steps
    played = _submit_option(
        app, service, alice, PlayCard, lambda command: command.card_id == source_id
    )
    _assert_public_boundary(played)
    authoritative = service.get_match(MATCH_ID).engine
    assert authoritative.state.players["A"].steps == before_steps - 10
    assert authoritative.state.cards[source_id].zone is Zone.RESOLUTION

    # Fallos públicos: CAS obsoleto, token inexistente y actor incorrecto.
    fingerprint = (played.version, state_digest(authoritative))
    with pytest.raises(WriteConflict):
        app.submit_option(
            alice,
            MATCH_ID,
            played.legal_actions[0].option_id,
            expected_version=played.version - 1,
        )
    with pytest.raises(OptionRejected):
        app.submit_option(alice, MATCH_ID, "0" * 64, expected_version=played.version)
    with pytest.raises(OptionRejected):
        app.submit_option(
            bob,
            MATCH_ID,
            played.legal_actions[0].option_id,
            expected_version=played.version,
        )
    assert (
        service.get_match(MATCH_ID).version,
        state_digest(service.get_match(MATCH_ID).engine),
    ) == fingerprint

    # Resuelve la carta, apunta al mazo y apila el disparo, siempre por opciones.
    for _ in range(2):
        current = service.get_match(MATCH_ID).engine.state.priority_player_id
        _submit_option(app, service, alice if current == "A" else bob, PassPriority)
    pending_id = service.get_match(MATCH_ID).engine.state.pending_triggers[0].item_id

    # Un objetivo forjado se rechaza atómicamente; no se ofrece como opción pública.
    invalid_target = ChooseTriggeredTargets(
        "A",
        pending_id,
        chosen_zone_targets=(ZoneTarget("jugador-inexistente", Zone.DECK),),
    )
    before_invalid = (
        service.get_match(MATCH_ID).version,
        state_digest(service.get_match(MATCH_ID).engine),
    )
    with pytest.raises(CommandRejected):
        app.submit(alice, MATCH_ID, invalid_target, expected_version=before_invalid[0])
    with pytest.raises(AccessDenied):
        app.submit(
            bob,
            MATCH_ID,
            replace(invalid_target, player_id="A"),
            expected_version=before_invalid[0],
        )
    assert (
        service.get_match(MATCH_ID).version,
        state_digest(service.get_match(MATCH_ID).engine),
    ) == before_invalid

    _submit_option(
        app,
        service,
        alice,
        ChooseTriggeredTargets,
        lambda command: command.chosen_zone_targets == (ZoneTarget("A", Zone.DECK),),
    )
    _submit_option(app, service, alice, OrderTriggeredAbilities)
    for _ in range(2):
        current = service.get_match(MATCH_ID).engine.state.priority_player_id
        _submit_option(app, service, alice if current == "A" else bob, PassPriority)

    search_view = app.view(alice, MATCH_ID)
    _assert_public_boundary(search_view)
    search_command = next(
        command
        for command in service.view(MATCH_ID, "A").legal_actions
        if isinstance(command, ResolveSearchChoice) and command.selected_card_ids
    )
    searched_id = search_command.selected_card_ids[0]
    assert searched_id not in repr(search_view.to_dict())
    opponent_hand = service.get_match(MATCH_ID).engine.state.players["B"].zones[Zone.HAND]
    assert all(card_id not in repr(search_view.to_dict()) for card_id in opponent_hand)

    # Snapshot tras la secuencia Mítica; original y restaurado continúan igual.
    snapshot_source = service.get_match(MATCH_ID).engine
    restored = load_snapshot(dump_snapshot(snapshot_source))
    snapshot_source.execute(search_command)
    restored.execute(search_command)
    assert restored.state.cards[searched_id].zone is Zone.HAND
    assert state_digest(restored) == state_digest(snapshot_source)

    # El replay vuelve a ejecutar toda la historia y acredita determinismo final.
    replayed = replay_from_log(dump_replay(snapshot_source))
    assert state_digest(replayed) == state_digest(snapshot_source)
