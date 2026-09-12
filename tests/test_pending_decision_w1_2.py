"""Contrato W1.2 de resolución remota y persistencia de decisiones.

Las decisiones de estos escenarios son preparación interna de prueba: se abren
exclusivamente con ``GameEngine._open_pending_decision`` y no representan una
API remota ni incorporan una mecánica de cartas concreta.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import fields
from threading import Barrier, Lock
from typing import Any

import pytest

from card_duel_engine import (
    AuthenticatedMatchApplication,
    Capability,
    ExternalIdentity,
    InMemoryIdentityAuthorization,
    InMemoryMatchStore,
    InvalidExpectedVersion,
    MatchService,
    OptionRejected,
    SQLiteMatchStore,
    WriteConflict,
)
from card_duel_engine.application import ApplicationError
from card_duel_engine.domain import DecisionAudience, PendingDecisionStatus
from card_duel_engine.storage import VersionConflict

# Reutilizamos la preparación W1.1; no duplicamos ni inventamos una mecánica.
from test_pending_decision_w1_1 import OPTIONS, make_engine, open_decision


@pytest.fixture(params=("memory", "sqlite"))
def store(request: pytest.FixtureRequest, tmp_path: Any) -> Any:
    if request.param == "memory":
        yield InMemoryMatchStore()
    else:
        backend = SQLiteMatchStore(tmp_path / "pending-w12.sqlite")
        yield backend
        backend.close()


def _application(store: Any, match_id: str = "match") -> tuple[
    AuthenticatedMatchApplication, dict[str, ExternalIdentity]
]:
    authorization = InMemoryIdentityAuthorization()
    identities = {
        player: ExternalIdentity("w1.2-tests", player) for player in ("A", "B")
    }
    for player, identity in identities.items():
        authorization.bind_player(
            identity,
            match_id,
            player,
            capabilities=(Capability.OBSERVE, Capability.RESOLVE_PENDING_DECISION),
        )
    return AuthenticatedMatchApplication(MatchService(store), authorization), identities


def _persist_pending(store: Any, match_id: str = "match", **changes: object) -> None:
    engine = make_engine()
    # Preparación interna del test; _open_pending_decision no es una API remota.
    open_decision(engine, **changes)
    assert store.create(match_id, engine) == 1


def _snapshot(store: Any, match_id: str = "match") -> tuple[int, object]:
    loaded = store.load(match_id)
    return loaded.version, deepcopy(loaded.engine.state)


def _assert_safe_error(error: BaseException, forbidden: tuple[str, ...]) -> None:
    rendered = f"{error!r} {error} {error.args!r}"
    assert isinstance(error, ApplicationError)
    assert error.args == (error.public_message,)
    assert error.__context__ is None
    assert all(secret not in rendered for secret in forbidden)


def test_persistence_contract_exposes_pending_resolvable_ids_only_to_elector(store: Any) -> None:
    _persist_pending(store, state_version=73, origin=("private-origin-w12",))
    application, identities = _application(store)

    elector = application.view(identities["A"], "match")
    opponent = application.view(identities["B"], "match")

    assert elector.pending_decision is not None
    assert elector.pending_decision.status == PendingDecisionStatus.PENDING.value
    assert len(elector.pending_decision.options) == 2
    assert all(option.decision_option_id for option in elector.pending_decision.options)
    assert opponent.pending_decision is not None
    assert opponent.pending_decision.options == ()

    forbidden = (*OPTIONS, "private-origin-w12")
    serialized = repr(elector.to_dict())
    dto_reprs = " ".join(
        repr(value)
        for value in (elector, elector.pending_decision, *elector.pending_decision.options)
    )
    assert all(secret not in serialized and secret not in dto_reprs for secret in forbidden)
    assert all(
        private_name not in serialized and private_name not in dto_reprs
        for private_name in (
            "authorized_opaque_options", "origin", "authorized_elector", "state_version"
        )
    )
    assert tuple(field.name for field in fields(elector.pending_decision)) == (
        "decision_id", "semantic_family", "status", "options"
    )


def test_opponent_cannot_reuse_electors_identifier_and_snapshot_is_unchanged(store: Any) -> None:
    _persist_pending(store)
    application, identities = _application(store)
    elector = application.view(identities["A"], "match")
    assert elector.pending_decision is not None
    token = elector.pending_decision.options[0].decision_option_id
    before = _snapshot(store)

    with pytest.raises(OptionRejected) as caught:
        application.resolve_pending_decision(
            identities["B"], "match", token, expected_version=1
        )

    _assert_safe_error(caught.value, (token, *OPTIONS))
    assert _snapshot(store) == before


def test_internal_and_closed_decisions_have_metadata_but_no_public_options(store: Any) -> None:
    _persist_pending(store, audience=DecisionAudience.INTERNAL)
    application, identities = _application(store)
    internal = application.view(identities["A"], "match")
    assert internal.pending_decision is not None
    assert internal.pending_decision.options == ()

    closed_store = InMemoryMatchStore()
    engine = make_engine()
    open_decision(engine)
    internal_decision = engine.state.pending_decision  # type: ignore[union-attr]
    assert internal_decision is not None
    engine._close_pending_decision(
        internal_decision.decision_id,
        "A",
        OPTIONS[1],
        internal_decision.state_version,
    )
    closed_store.create("closed", engine)
    closed_app, closed_identities = _application(closed_store, "closed")
    closed = closed_app.view(closed_identities["A"], "closed")
    assert closed.pending_decision is not None
    assert closed.pending_decision.status == PendingDecisionStatus.CLOSED.value
    assert closed.pending_decision.options == ()


def test_valid_pending_to_closed_is_exactly_once_and_has_no_mechanical_history(store: Any) -> None:
    _persist_pending(store)
    application, identities = _application(store)
    public = application.view(identities["A"], "match")
    assert public.pending_decision is not None
    token = public.pending_decision.options[1].decision_option_id
    loaded = store.load("match")
    assert loaded.engine.state is not None
    events = tuple(loaded.engine.state.event_log)
    commands = tuple(loaded.engine.state.command_history)

    resolved = application.resolve_pending_decision(
        identities["A"], "match", token, expected_version=public.version
    )
    assert resolved.version == public.version + 1
    saved = store.load("match")
    decision = saved.engine.state.pending_decision  # type: ignore[union-attr]
    assert decision is not None
    assert decision.status is PendingDecisionStatus.CLOSED
    assert decision.selected_option == OPTIONS[1]
    assert tuple(saved.engine.state.event_log) == events  # type: ignore[union-attr]
    assert tuple(saved.engine.state.command_history) == commands  # type: ignore[union-attr]

    closed_snapshot = _snapshot(store)
    with pytest.raises(OptionRejected):
        application.resolve_pending_decision(
            identities["A"], "match", token, expected_version=resolved.version
        )
    assert _snapshot(store) == closed_snapshot


@pytest.mark.parametrize("bad_token", ["invalid", "{token}x", "missing-decision-token"])
def test_invalid_tampered_or_nonexistent_decision_reference_is_safe_and_atomic(
    store: Any, bad_token: str
) -> None:
    _persist_pending(store)
    application, identities = _application(store)
    view = application.view(identities["A"], "match")
    assert view.pending_decision is not None
    valid = view.pending_decision.options[0].decision_option_id
    candidate = bad_token.format(token=valid)
    before = _snapshot(store)

    with pytest.raises(OptionRejected) as caught:
        application.resolve_pending_decision(
            identities["A"], "match", candidate, expected_version=view.version
        )
    _assert_safe_error(caught.value, (candidate, *OPTIONS))
    assert _snapshot(store) == before


@pytest.mark.parametrize("malformed", [None, True, 0, -1, 1.0, "1"])
def test_malformed_expected_version_is_rejected_before_load(
    malformed: object,
) -> None:
    class NoLoadStore:
        def load(self, _match_id: str) -> object:
            raise AssertionError("load no debe ejecutarse")

    application, identities = _application(NoLoadStore())
    with pytest.raises(InvalidExpectedVersion) as caught:
        application.resolve_pending_decision(
            identities["A"], "match", "anything", expected_version=malformed  # type: ignore[arg-type]
        )
    _assert_safe_error(caught.value, ("anything",))


def test_stale_cas_is_public_write_conflict_and_does_not_mutate(store: Any) -> None:
    _persist_pending(store)
    application, identities = _application(store)
    before = _snapshot(store)
    with pytest.raises(WriteConflict) as caught:
        application.resolve_pending_decision(
            identities["A"], "match", "not-inspected", expected_version=2
        )
    _assert_safe_error(caught.value, ("not-inspected", *OPTIONS))
    assert _snapshot(store) == before


def test_token_is_bound_to_match_player_decision_and_cas_version() -> None:
    stores = {name: InMemoryMatchStore() for name in ("source", "other")}
    _persist_pending(stores["source"], "source")
    _persist_pending(stores["other"], "other", decision_id="decision:test:other")
    source_app, source_ids = _application(stores["source"], "source")
    other_app, other_ids = _application(stores["other"], "other")
    source_view = source_app.view(source_ids["A"], "source")
    token = source_view.pending_decision.options[0].decision_option_id  # type: ignore[union-attr]

    attempts = (
        (source_app, source_ids["B"], "source", 1),  # otro jugador
        (other_app, other_ids["A"], "other", 1),  # otra partida y decisión
    )
    for application, identity, match_id, version in attempts:
        before = _snapshot(application._service.store, match_id)  # type: ignore[attr-defined]
        with pytest.raises(OptionRejected):
            application.resolve_pending_decision(
                identity, match_id, token, expected_version=version
            )
        assert _snapshot(application._service.store, match_id) == before  # type: ignore[attr-defined]

    # Un incremento CAS, aun sin cambiar la decisión, invalida el identificador.
    loaded = stores["source"].load("source")
    assert stores["source"].save("source", loaded.engine, expected_version=1) == 2
    before = _snapshot(stores["source"], "source")
    with pytest.raises(OptionRejected):
        source_app.resolve_pending_decision(
            source_ids["A"], "source", token, expected_version=2
        )
    assert _snapshot(stores["source"], "source") == before


def test_token_is_bound_to_decision_even_with_same_match_player_and_version(store: Any) -> None:
    _persist_pending(store)
    application, identities = _application(store)
    old = application.view(identities["A"], "match")
    token = old.pending_decision.options[0].decision_option_id  # type: ignore[union-attr]
    # Sustitución controlada de fixture, preservando V, aísla el campo decision_id.
    replacement = make_engine()
    open_decision(replacement, decision_id="decision:test:replacement")
    if isinstance(store, InMemoryMatchStore):
        store._records["match"] = (1, store._records["match"][1])
        from card_duel_engine.persistence import dump_snapshot
        store._records["match"] = (1, dump_snapshot(replacement, indent=None))
    else:
        from card_duel_engine.persistence import dump_snapshot
        with store._connect() as connection:
            connection.execute(
                "UPDATE matches SET snapshot = ? WHERE match_id = ?",
                (dump_snapshot(replacement, indent=None), "match"),
            )
    before = _snapshot(store)
    with pytest.raises(OptionRejected):
        application.resolve_pending_decision(
            identities["A"], "match", token, expected_version=1
        )
    assert _snapshot(store) == before


def test_deterministic_cas_race_has_one_winner_without_ghost_publication(store: Any) -> None:
    _persist_pending(store)
    service = MatchService(store)
    loaded_barrier = Barrier(2)
    save_versions: list[int] = []
    guard = Lock()
    original_save = store.save

    def synchronized_save(match_id: str, engine: object, *, expected_version: int) -> int:
        with guard:
            save_versions.append(expected_version)
        # Instrumentación previa a save: ambos candidatos ya cargaron y cerraron V.
        loaded_barrier.wait(timeout=10)
        return original_save(match_id, engine, expected_version=expected_version)

    store.save = synchronized_save
    baseline = store.load("match")
    state = baseline.engine.state
    assert state is not None
    events = tuple(state.event_log)
    commands = tuple(state.command_history)

    def contend(option: str) -> tuple[str, object]:
        try:
            result = service.resolve_pending_decision(
                "match", "A", option, expected_version=baseline.version
            )
            return "success", result
        except VersionConflict as error:
            return "conflict", error

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(contend, OPTIONS))

    assert sorted(kind for kind, _ in outcomes) == ["conflict", "success"]
    assert save_versions == [baseline.version, baseline.version]
    winner_view = next(value for kind, value in outcomes if kind == "success")
    assert winner_view.version == baseline.version + 1
    final = store.load("match")
    decision = final.engine.state.pending_decision  # type: ignore[union-attr]
    assert final.version == baseline.version + 1
    assert decision is not None and decision.status is PendingDecisionStatus.CLOSED
    assert decision.selected_option in OPTIONS
    assert tuple(final.engine.state.event_log) == events  # type: ignore[union-attr]
    assert tuple(final.engine.state.command_history) == commands  # type: ignore[union-attr]
