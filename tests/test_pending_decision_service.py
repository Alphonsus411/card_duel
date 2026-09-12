from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock

import pytest

from card_duel_engine import (
    AccessDenied,
    AuthenticatedMatchApplication,
    Capability,
    ExternalIdentity,
    GameEngine,
    InMemoryIdentityAuthorization,
    InMemoryMatchStore,
    MatchService,
    OptionRejected,
    WriteConflict,
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
        "internal-b",
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
    with pytest.raises(ValueError):
        service.resolve_pending_decision(
            "match", "A", "internal-a", expected_version=True
        )
    store.load.assert_not_called()

    store.load.return_value.version = 2
    with pytest.raises(VersionConflict):
        service.resolve_pending_decision(
            "match", "A", "internal-a", expected_version=1
        )
    store.save.assert_not_called()


def test_application_resolves_only_the_current_public_reference() -> None:
    service, store = prepared_service()
    authorization = InMemoryIdentityAuthorization()
    identity = ExternalIdentity("tests", "A")
    authorization.bind_player(
        identity,
        "match",
        "A",
        capabilities=(
            Capability.OBSERVE,
            Capability.RESOLVE_PENDING_DECISION,
        ),
    )
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


def test_resolution_capability_is_independent_from_command_submission() -> None:
    service, store = prepared_service()
    authorization = InMemoryIdentityAuthorization()
    identity = ExternalIdentity("tests", "A")
    authorization.bind_player(
        identity,
        "match",
        "A",
        capabilities=(Capability.OBSERVE, Capability.SUBMIT_COMMAND),
    )
    application = AuthenticatedMatchApplication(service, authorization)
    public = application.view(identity, "match")
    assert public.pending_decision is not None

    with pytest.raises(AccessDenied) as captured:
        application.resolve_pending_decision(
            identity,
            "match",
            public.pending_decision.options[0].decision_option_id,
            expected_version=public.version,
        )

    assert captured.value.args == (AccessDenied.public_message,)
    assert store.load("match").version == 1


def test_application_uses_authorized_view_and_rejects_tampered_reference() -> None:
    service, store = prepared_service()
    service.view = Mock(wraps=service.view)  # type: ignore[method-assign]
    authorization = InMemoryIdentityAuthorization()
    identity = ExternalIdentity("tests", "A")
    authorization.bind_player(
        identity,
        "match",
        "A",
        capabilities=(Capability.OBSERVE, Capability.RESOLVE_PENDING_DECISION),
    )
    application = AuthenticatedMatchApplication(service, authorization)
    public = application.view(identity, "match")
    assert public.pending_decision is not None
    service.view.reset_mock()

    with pytest.raises(OptionRejected) as captured:
        application.resolve_pending_decision(
            identity,
            "match",
            "manipulated-token",
            expected_version=public.version,
        )

    service.view.assert_called_once_with("match", "A")
    assert captured.value.args == (OptionRejected.public_message,)
    assert captured.value.__context__ is None
    assert store.load("match").version == 1


def test_losing_cas_does_not_publish_a_success_view() -> None:
    service, store = prepared_service()
    authorization = InMemoryIdentityAuthorization()
    identity = ExternalIdentity("tests", "A")
    authorization.bind_player(
        identity,
        "match",
        "A",
        capabilities=(Capability.OBSERVE, Capability.RESOLVE_PENDING_DECISION),
    )
    application = AuthenticatedMatchApplication(service, authorization)
    public = application.view(identity, "match")
    assert public.pending_decision is not None
    option_id = public.pending_decision.options[0].decision_option_id
    application._public_view = Mock(  # type: ignore[method-assign]
        wraps=application._public_view
    )

    def resolve() -> str:
        try:
            application.resolve_pending_decision(
                identity, "match", option_id, expected_version=public.version
            )
            return "winner"
        except WriteConflict:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: resolve(), range(2)))

    assert sorted(outcomes) == ["conflict", "winner"]
    assert application._public_view.call_count == 1
    assert store.load("match").version == 2
