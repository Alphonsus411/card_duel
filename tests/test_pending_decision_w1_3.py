"""Carreras CAS del cierre remoto de decisiones pendientes.

La apertura de la decisión es preparación interna del escenario. El cierre, en
cambio, recorre la frontera pública completa: aplicación autenticada, servicio,
motor y ``MatchStore.save`` con versión esperada.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from threading import Barrier, Lock
from typing import Any

import pytest

from card_duel_engine import (
    AuthenticatedMatchApplication,
    Capability,
    ExternalIdentity,
    InMemoryIdentityAuthorization,
    InMemoryMatchStore,
    MatchService,
    SQLiteMatchStore,
    WriteConflict,
)
from card_duel_engine.domain import (
    DecisionClosed,
    DecisionTransitionEntry,
    PendingDecisionStatus,
)
from card_duel_engine.storage import VersionConflict

from test_pending_decision_w1_1 import OPTIONS, make_engine, open_decision


Store = InMemoryMatchStore | SQLiteMatchStore


@pytest.fixture(
    params=(
        pytest.param(lambda _path: InMemoryMatchStore(), id="memory"),
        pytest.param(lambda path: SQLiteMatchStore(path), id="sqlite"),
    )
)
def store(request: pytest.FixtureRequest, tmp_path: Path) -> Store:
    backend = request.param(tmp_path / "pending-decision-w1-3.sqlite")
    yield backend
    if isinstance(backend, SQLiteMatchStore):
        backend.close()


def _application(
    store: Store,
) -> tuple[AuthenticatedMatchApplication, ExternalIdentity]:
    authorization = InMemoryIdentityAuthorization()
    identity = ExternalIdentity("w1.3-race", "alice")
    authorization.bind_player(
        identity,
        "match",
        "A",
        capabilities=(Capability.OBSERVE, Capability.RESOLVE_PENDING_DECISION),
    )
    return (
        AuthenticatedMatchApplication(MatchService(store), authorization),
        identity,
    )


@dataclass(frozen=True)
class SaveAttempt:
    option: str
    expected_version: int
    published_version: int | None
    error: VersionConflict | None
    history: tuple[object, ...]


def test_concurrent_close_persists_only_the_cas_winner(store: Store) -> None:
    engine = make_engine()
    open_decision(engine)
    assert store.create("match", engine) == 1
    application, identity = _application(store)

    # Ambos contendientes reciben referencias HMAC distintas de la misma vista.
    baseline = application.view(identity, "match")
    assert baseline.pending_decision is not None
    option_ids = tuple(
        option.decision_option_id for option in baseline.pending_decision.options
    )
    assert len(set(option_ids)) == len(OPTIONS)
    assert not set(option_ids) & set(OPTIONS)

    original_save = store.save
    ready_to_save = Barrier(2)
    attempts: list[SaveAttempt] = []
    attempts_lock = Lock()

    def synchronized_save(
        match_id: str, candidate: Any, *, expected_version: int
    ) -> int:
        state = candidate.state
        assert state is not None and state.pending_decision is not None
        selected_option = state.pending_decision.selected_option
        assert selected_option is not None
        candidate_history = tuple(state.history)

        # Al llegar aquí, cada servicio cargó su propia copia en la misma versión
        # y cada motor ya produjo su transición CLOSED de manera aislada.
        ready_to_save.wait(timeout=10)
        try:
            published_version = original_save(
                match_id, candidate, expected_version=expected_version
            )
        except VersionConflict as error:
            with attempts_lock:
                attempts.append(
                    SaveAttempt(
                        selected_option,
                        expected_version,
                        None,
                        error,
                        candidate_history,
                    )
                )
            raise
        with attempts_lock:
            attempts.append(
                SaveAttempt(
                    selected_option,
                    expected_version,
                    published_version,
                    None,
                    candidate_history,
                )
            )
        return published_version

    store.save = synchronized_save  # type: ignore[method-assign]

    def contend(option_index: int) -> tuple[int, object]:
        try:
            published = application.resolve_pending_decision(
                identity,
                "match",
                option_ids[option_index],
                expected_version=baseline.version,
            )
            return option_index, published
        except WriteConflict as error:
            return option_index, error

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(contend, range(len(OPTIONS))))

    successful_saves = [attempt for attempt in attempts if attempt.error is None]
    rejected_saves = [attempt for attempt in attempts if attempt.error is not None]
    assert len(successful_saves) == 1
    assert len(rejected_saves) == 1
    assert isinstance(rejected_saves[0].error, VersionConflict)
    assert {attempt.expected_version for attempt in attempts} == {baseline.version}

    winner = successful_saves[0]
    loser = rejected_saves[0]
    published_views = [
        value for _, value in outcomes if not isinstance(value, WriteConflict)
    ]
    public_conflicts = [
        value for _, value in outcomes if isinstance(value, WriteConflict)
    ]
    assert len(published_views) == 1
    assert len(public_conflicts) == 1
    assert published_views[0].version == winner.published_version

    persisted = store.load("match")
    state = persisted.engine.state
    assert state is not None and state.pending_decision is not None
    closed = [
        entry
        for entry in state.history
        if isinstance(entry, DecisionTransitionEntry)
        and isinstance(entry.transition, DecisionClosed)
    ]
    assert len(closed) == 1
    assert state.pending_decision.status is PendingDecisionStatus.CLOSED
    assert state.pending_decision.selected_option == winner.option
    assert state.history == list(winner.history)
    assert state.history != list(loser.history)
    assert closed[0].transition.selected_option == winner.option
    assert closed[0].transition.selected_option != loser.option
    assert persisted.version == winner.published_version == baseline.version + 1
