from unittest.mock import Mock

import pytest

from card_duel_engine import (
    AuthenticatedMatchApplication,
    ExternalIdentity,
    GameEngine,
    InMemoryIdentityAuthorization,
    InMemoryMatchStore,
    MatchService,
    VersionConflict,
)
from card_duel_engine.domain import DecisionAudience, PendingDecisionStatus

from fixtures import test_deck


def prepared_service() -> tuple[MatchService, InMemoryMatchStore]:
    engine = GameEngine()
    engine.new_match({"A": test_deck("A"), "B": test_deck("B")}, seed=4)
    engine._open_pending_decision(
        "decision:service:1",
        "test-choice/v1",
        "A",
        DecisionAudience.ELECTOR,
        ("internal-a", "internal-b"),
        19,
        ("test",),
    )
    store = InMemoryMatchStore()
    store.create("match", engine)
    return MatchService(store), store


def test_service_closes_and_saves_once_without_lifecycle_history() -> None:
    service, store = prepared_service()
    before = store.load("match").engine.state
    assert before is not None
    events = tuple(before.event_log)
    commands = tuple(before.command_history)

    view = service.resolve_pending_decision(
        "match",
        "A",
        lambda *context: context[-1][1],
        expected_version=1,
    )

    assert view.version == 2
    saved = store.load("match").engine.state
    assert saved is not None and saved.pending_decision is not None
    assert saved.pending_decision.status is PendingDecisionStatus.CLOSED
    assert saved.pending_decision.selected_option == "internal-b"
    assert tuple(saved.event_log) == events
    assert tuple(saved.command_history) == commands


def test_service_validates_and_compares_cas_before_resolving() -> None:
    store = Mock()
    service = MatchService(store)
    resolver = Mock()
    with pytest.raises(ValueError):
        service.resolve_pending_decision(
            "match", "A", resolver, expected_version=True
        )
    store.load.assert_not_called()

    store.load.return_value.version = 2
    with pytest.raises(VersionConflict):
        service.resolve_pending_decision(
            "match", "A", resolver, expected_version=1
        )
    resolver.assert_not_called()
    store.save.assert_not_called()


def test_application_resolves_only_the_current_public_reference() -> None:
    service, store = prepared_service()
    authorization = InMemoryIdentityAuthorization()
    identity = ExternalIdentity("tests", "A")
    authorization.bind_player(identity, "match", "A")
    application = AuthenticatedMatchApplication(service, authorization)
    public = application.view(identity, "match")
    assert public.pending_decision is not None

    closed = application.resolve_pending_decision(
        identity,
        "match",
        public.pending_decision.options[0].decision_option_id,
        expected_version=public.version,
    )

    assert closed.version == 2
    decision = store.load("match").engine.state.pending_decision  # type: ignore[union-attr]
    assert decision is not None
    assert decision.selected_option == "internal-a"
