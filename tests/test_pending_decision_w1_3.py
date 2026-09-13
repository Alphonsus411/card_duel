"""Contrato W1.3 del lifecycle y replay de decisiones agnósticas a cartas."""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Callable

import pytest

from card_duel_engine import GameEngine
from card_duel_engine.domain import (
    DecisionAudience,
    DecisionClosed,
    DecisionConsumed,
    DecisionOpened,
    DecisionTransitionEntry,
    ExecutedCommand,
    PendingDecisionStatus,
)
from card_duel_engine.domain.errors import (
    DecisionAlreadyClosed,
    DecisionIdMismatch,
    DecisionNotClosed,
    DecisionSlotEmpty,
    DecisionSlotOccupied,
    StaleDecisionVersion,
    UnauthorizedDecisionElector,
    UnauthorizedDecisionOption,
)
from card_duel_engine.engine.commands import PassPriority
from card_duel_engine.persistence.codec import decode_value
from card_duel_engine.persistence.replay import dump_replay, replay_from_log
from card_duel_engine.persistence.snapshot import (
    dump_snapshot,
    load_snapshot,
    state_digest,
)

from test_pending_decision_w1_1 import (
    DECISION_ID,
    FAMILY,
    OPTIONS,
    ORIGIN,
    VERSION,
    make_engine,
    open_decision,
)


SECOND = {
    "decision_id": "opaque_second_D2",
    "semantic_family": "second-choice/v2",
    "authorized_elector": "B",
    "audience": DecisionAudience.OPPONENT,
    "authorized_opaque_options": ("opaque_second_a", "opaque_second_b"),
    "state_version": VERSION + 9,
    "origin": ("opaque_second_origin",),
}


def _close(engine: GameEngine) -> None:
    engine._close_pending_decision(DECISION_ID, "A", OPTIONS[1], VERSION)


def _consume(engine: GameEngine) -> None:
    engine._consume_pending_decision(DECISION_ID, VERSION)


def _observables(engine: GameEngine) -> object:
    """Copia todo lo que una transición rechazada podría alterar."""
    assert engine.state is not None
    state = engine.state
    return deepcopy(
        (
            state.pending_decision,
            state.history,
            state.command_history,
            state.event_log,
            state.turn_number,
            engine._next_instance,
            engine._next_stack_item,
            engine._replacement_replay_cursor,
            engine._replacement_replay_choices,
        )
    )


def _assert_rejected_atomically(
    engine: GameEngine,
    error: type[BaseException],
    operation: Callable[[], None],
) -> None:
    before = _observables(engine)
    state_identity = engine.state
    with pytest.raises(error):
        operation()
    assert engine.state is state_identity
    assert _observables(engine) == before


def _transitions(engine: GameEngine) -> tuple[object, ...]:
    assert engine.state is not None
    return tuple(
        entry.transition
        for entry in engine.state.history
        if isinstance(entry, DecisionTransitionEntry)
    )


def _complete_first_lifecycle(engine: GameEngine) -> None:
    open_decision(engine)
    _close(engine)
    _consume(engine)


def _assert_first_contract_in_history(engine: GameEngine) -> None:
    """Comprueba metadatos opacos incluso cuando el slot ya fue consumido."""
    transitions = _transitions(engine)
    opened = transitions[0]
    assert isinstance(opened, DecisionOpened)
    assert opened.decision_id == DECISION_ID
    assert opened.semantic_family == FAMILY
    assert opened.authorized_elector == "A"
    assert opened.audience is DecisionAudience.ELECTOR
    assert opened.authorized_opaque_options == OPTIONS
    assert opened.state_version == VERSION
    assert opened.origin == ORIGIN
    if len(transitions) > 1:
        closed = transitions[1]
        assert isinstance(closed, DecisionClosed)
        assert closed.selected_option == OPTIONS[1]


def test_complete_path_none_pending_closed_none_pending() -> None:
    engine = make_engine()
    assert engine.state is not None and engine.state.pending_decision is None

    open_decision(engine)
    assert engine.state.pending_decision is not None
    assert engine.state.pending_decision.status is PendingDecisionStatus.PENDING
    _close(engine)
    assert engine.state.pending_decision.status is PendingDecisionStatus.CLOSED
    _consume(engine)
    assert engine.state.pending_decision is None
    open_decision(engine, **SECOND)
    assert engine.state.pending_decision is not None
    assert engine.state.pending_decision.decision_id == SECOND["decision_id"]
    assert engine.state.pending_decision.status is PendingDecisionStatus.PENDING
    assert tuple(type(item) for item in _transitions(engine)) == (
        DecisionOpened,
        DecisionClosed,
        DecisionConsumed,
        DecisionOpened,
    )


def test_open_rejects_pending_slot_atomically() -> None:
    engine = make_engine()
    open_decision(engine)
    _assert_rejected_atomically(
        engine,
        DecisionSlotOccupied,
        lambda: open_decision(engine, **SECOND),
    )


def test_open_rejects_closed_slot_atomically() -> None:
    engine = make_engine()
    open_decision(engine)
    _close(engine)
    _assert_rejected_atomically(
        engine,
        DecisionSlotOccupied,
        lambda: open_decision(engine, **SECOND),
    )


def test_close_rejects_empty_slot_atomically() -> None:
    engine = make_engine()
    _assert_rejected_atomically(engine, DecisionSlotEmpty, lambda: _close(engine))


def test_close_rejects_second_close_atomically() -> None:
    engine = make_engine()
    open_decision(engine)
    _close(engine)
    _assert_rejected_atomically(engine, DecisionAlreadyClosed, lambda: _close(engine))


@pytest.mark.parametrize(
    ("actor", "option", "error"),
    [
        pytest.param(
            "A",
            "opaque_not_authorized",
            UnauthorizedDecisionOption,
            id="option",
        ),
        pytest.param("B", OPTIONS[0], UnauthorizedDecisionElector, id="elector"),
    ],
)
def test_close_rejects_unauthorized_input_atomically(
    actor: str, option: str, error: type[BaseException]
) -> None:
    engine = make_engine()
    open_decision(engine)
    _assert_rejected_atomically(
        engine,
        error,
        lambda: engine._close_pending_decision(DECISION_ID, actor, option, VERSION),
    )


def test_consume_rejects_pending_slot_atomically() -> None:
    engine = make_engine()
    open_decision(engine)
    _assert_rejected_atomically(engine, DecisionNotClosed, lambda: _consume(engine))


def test_consume_rejects_empty_slot_atomically() -> None:
    engine = make_engine()
    _assert_rejected_atomically(engine, DecisionSlotEmpty, lambda: _consume(engine))


@pytest.mark.parametrize(
    ("decision_id", "version", "error"),
    [
        pytest.param("opaque_wrong", VERSION, DecisionIdMismatch, id="decision-id"),
        pytest.param(
            DECISION_ID,
            VERSION + 1,
            StaleDecisionVersion,
            id="stale-version",
        ),
    ],
)
def test_consume_rejects_wrong_contract_atomically(
    decision_id: str, version: int, error: type[BaseException]
) -> None:
    engine = make_engine()
    open_decision(engine)
    _close(engine)
    _assert_rejected_atomically(
        engine,
        error,
        lambda: engine._consume_pending_decision(decision_id, version),
    )


@pytest.mark.parametrize(
    "final_stage",
    ["pending", "closed", "consumed", "second-pending"],
)
def test_replay_v3_preserves_every_lifecycle_final_state(final_stage: str) -> None:
    engine = make_engine()
    open_decision(engine)
    if final_stage != "pending":
        _close(engine)
    if final_stage in {"consumed", "second-pending"}:
        _consume(engine)
    if final_stage == "second-pending":
        open_decision(engine, **SECOND)

    dumped = dump_replay(engine, indent=None)
    document = json.loads(dumped)
    assert document["body"]["schema_version"] == "3"
    assert engine.state is not None
    assert document["body"]["history_count"] == len(engine.state.history)
    replayed = replay_from_log(dumped)

    assert replayed.state == engine.state
    assert state_digest(replayed) == state_digest(engine)
    assert dump_replay(replayed, indent=None) == dumped
    assert replayed.state is not None
    assert replayed.state.history == engine.state.history
    assert _transitions(replayed) == _transitions(engine)
    _assert_first_contract_in_history(replayed)

    decision = replayed.state.pending_decision
    if final_stage == "consumed":
        assert decision is None
    else:
        assert decision is not None
        expected = SECOND if final_stage == "second-pending" else {
            "decision_id": DECISION_ID,
            "semantic_family": FAMILY,
            "authorized_elector": "A",
            "audience": DecisionAudience.ELECTOR,
            "authorized_opaque_options": OPTIONS,
            "state_version": VERSION,
            "origin": ORIGIN,
        }
        for field, value in expected.items():
            assert getattr(decision, field) == value
        expected_status = (
            PendingDecisionStatus.CLOSED
            if final_stage == "closed"
            else PendingDecisionStatus.PENDING
        )
        assert decision.status is expected_status
        expected_option = OPTIONS[1] if final_stage == "closed" else None
        assert decision.selected_option == expected_option


def test_replay_document_and_engine_preserve_command_transition_interleaving() -> None:
    engine = make_engine()
    assert engine.state is not None
    command_a = PassPriority(engine.state.priority_player_id)
    engine.execute(command_a)
    _complete_first_lifecycle(engine)
    command_b = PassPriority(engine.state.priority_player_id)
    engine.execute(command_b)
    expected_types = (
        ExecutedCommand,
        DecisionTransitionEntry,
        DecisionTransitionEntry,
        DecisionTransitionEntry,
        ExecutedCommand,
    )
    assert tuple(type(entry) for entry in engine.state.history) == expected_types

    dumped = dump_replay(engine, indent=None)
    persisted_history = decode_value(json.loads(dumped)["body"]["history"])
    assert persisted_history == tuple(engine.state.history)
    assert tuple(type(entry) for entry in persisted_history) == expected_types
    rebuilt = replay_from_log(dumped)
    assert rebuilt.state is not None
    assert rebuilt.state.history == engine.state.history
    assert rebuilt.state.command_history == [command_a, command_b]


def test_snapshot_v4_restore_dump_replay_v3_keeps_pre_snapshot_transitions() -> None:
    engine = make_engine()
    _complete_first_lifecycle(engine)
    open_decision(engine, **SECOND)
    transitions_before = _transitions(engine)

    snapshot = dump_snapshot(engine, indent=None)
    assert json.loads(snapshot)["body"]["schema_version"] == "4"
    restored = load_snapshot(snapshot)
    assert _transitions(restored) == transitions_before

    replay_dump = dump_replay(restored, indent=None)
    assert json.loads(replay_dump)["body"]["schema_version"] == "3"
    replayed = replay_from_log(replay_dump)
    assert replayed.state == restored.state == engine.state
    assert state_digest(replayed) == state_digest(restored) == state_digest(engine)
    assert _transitions(replayed) == transitions_before
