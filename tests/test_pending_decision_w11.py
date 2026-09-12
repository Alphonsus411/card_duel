from __future__ import annotations

from copy import deepcopy

import pytest

from card_duel_engine import GameEngine
from card_duel_engine.domain import (
    DecisionAudience,
    DecisionClosed,
    DecisionConsumed,
    DecisionHistoryStatus,
    DecisionOpened,
    DecisionTransitionEntry,
    PendingDecisionStatus,
)
from card_duel_engine.domain.errors import (
    DecisionAlreadyClosed,
    DecisionIdMismatch,
    DecisionNotClosed,
    DecisionSlotEmpty,
    DecisionSlotOccupied,
    IllegalAction,
    InvariantViolation,
    StaleDecisionVersion,
    UnauthorizedDecisionElector,
    UnauthorizedDecisionOption,
)

from fixtures import test_deck


def make_engine() -> GameEngine:
    engine = GameEngine()
    engine.new_match({"A": test_deck("W11-A"), "B": test_deck("W11-B")}, seed=11)
    return engine


def open_decision(engine: GameEngine, **changes: object) -> None:
    values = {
        "decision_id": "decision:test:1",
        "semantic_family": "test-choice/v1",
        "authorized_elector": "A",
        "audience": DecisionAudience.ELECTOR,
        "authorized_opaque_options": ("opaque-a", "opaque-b"),
        "state_version": 0,
        "origin": ("test", "1"),
    }
    values.update(changes)
    engine._open_pending_decision(**values)  # type: ignore[arg-type]


def test_open_and_close_replace_the_frozen_authoritative_value() -> None:
    engine = make_engine()
    open_decision(engine)
    assert engine.state is not None
    opened = engine.state.pending_decision
    assert opened is not None
    assert opened.status is PendingDecisionStatus.PENDING
    assert opened.selected_option is None
    events_before_close = tuple(engine.state.event_log)

    engine._close_pending_decision("decision:test:1", "A", "opaque-b", 0)

    closed = engine.state.pending_decision
    assert closed is not None and closed is not opened
    for field in (
        "decision_id", "semantic_family", "authorized_elector", "audience",
        "authorized_opaque_options", "state_version", "origin",
    ):
        assert getattr(closed, field) == getattr(opened, field)
    assert closed.status is PendingDecisionStatus.CLOSED
    assert closed.selected_option == "opaque-b"
    assert tuple(engine.state.event_log) == events_before_close


def test_open_and_close_append_typed_history_from_the_candidate_slot() -> None:
    engine = make_engine()
    assert engine.state is not None
    history_before = tuple(engine.state.history)

    open_decision(engine)

    pending = engine.state.pending_decision
    opened_entry = engine.state.history[-1]
    assert pending is not None
    assert isinstance(opened_entry, DecisionTransitionEntry)
    assert isinstance(opened_entry.transition, DecisionOpened)
    opened = opened_entry.transition
    assert opened.status is DecisionHistoryStatus.OPENED
    for field in (
        "decision_id",
        "semantic_family",
        "authorized_elector",
        "audience",
        "authorized_opaque_options",
        "state_version",
        "origin",
    ):
        assert getattr(opened, field) == getattr(pending, field)
    assert tuple(engine.state.history[:-1]) == history_before

    engine._close_pending_decision("decision:test:1", "A", "opaque-b", 0)

    closed = engine.state.pending_decision
    closed_entry = engine.state.history[-1]
    assert closed is not None
    assert isinstance(closed_entry, DecisionTransitionEntry)
    assert isinstance(closed_entry.transition, DecisionClosed)
    transition = closed_entry.transition
    assert transition.status is DecisionHistoryStatus.CLOSED
    assert transition.decision_id == closed.decision_id
    assert transition.actor == closed.authorized_elector
    assert transition.selected_option == closed.selected_option == "opaque-b"
    assert transition.known_state_version == closed.state_version
    assert engine.state.history[-2] == opened_entry


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"decision_id": " "}, "identificador"),
        ({"semantic_family": "unversioned"}, "versionada"),
        ({"authorized_elector": "missing"}, "elector"),
        ({"audience": "elector"}, "audiencia"),
        ({"authorized_opaque_options": ()}, "opciones"),
        ({"authorized_opaque_options": ("same", "same")}, "opciones"),
        ({"state_version": True}, "versión"),
        ({"state_version": -1}, "versión"),
        ({"origin": ()}, "origen"),
    ],
)
def test_open_rejects_invalid_contract_without_mutation(
    changes: dict[str, object], message: str
) -> None:
    engine = make_engine()
    before = deepcopy(engine.state)
    with pytest.raises(IllegalAction, match=message):
        open_decision(engine, **changes)
    assert engine.state == before


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        (("other", "A", "opaque-a", 0), "identidad"),
        (("decision:test:1", "B", "opaque-a", 0), "actor"),
        (("decision:test:1", "A", "other", 0), "opción"),
        (("decision:test:1", "A", "opaque-a", 1), "versión"),
    ],
)
def test_close_rejects_invalid_contract_without_mutation(
    arguments: tuple[object, ...], message: str
) -> None:
    engine = make_engine()
    open_decision(engine)
    state_before = engine.state
    before = deepcopy(engine.state)
    with pytest.raises(IllegalAction, match=message):
        engine._close_pending_decision(*arguments)  # type: ignore[arg-type]
    assert engine.state is state_before
    assert engine.state == before


def test_slot_cannot_be_reopened_while_pending_or_after_close() -> None:
    engine = make_engine()
    with pytest.raises(IllegalAction, match="No existe"):
        engine._close_pending_decision("decision:test:1", "A", "opaque-a", 0)
    open_decision(engine)
    with pytest.raises(IllegalAction, match="Ya existe"):
        open_decision(engine, decision_id="decision:test:2")
    engine._close_pending_decision("decision:test:1", "A", "opaque-a", 0)
    closed = engine.state.pending_decision  # type: ignore[union-attr]
    with pytest.raises(DecisionSlotOccupied):
        open_decision(engine, decision_id="decision:test:2")
    assert engine.state is not None and engine.state.pending_decision is closed


def test_closed_decision_cannot_be_closed_twice() -> None:
    engine = make_engine()
    open_decision(engine)
    engine._close_pending_decision("decision:test:1", "A", "opaque-a", 0)
    with pytest.raises(IllegalAction, match="ya no está pendiente"):
        engine._close_pending_decision("decision:test:1", "A", "opaque-a", 0)


def test_state_version_is_the_callers_declared_link_not_an_engine_counter() -> None:
    engine = make_engine()
    open_decision(engine, state_version=41)

    engine._close_pending_decision("decision:test:1", "A", "opaque-b", 41)

    assert engine.state is not None
    assert engine.state.pending_decision is not None
    assert engine.state.pending_decision.state_version == 41


@pytest.mark.parametrize(
    ("arguments", "error_type", "code"),
    [
        (("decision:test:1", "A", "opaque-a", 0), DecisionSlotEmpty,
         "decision_slot_empty"),
        (("other", "A", "opaque-a", 0), DecisionIdMismatch,
         "decision_id_mismatch"),
        (("decision:test:1", "B", "opaque-a", 0), UnauthorizedDecisionElector,
         "unauthorized_decision_elector"),
        (("decision:test:1", "A", "other", 0), UnauthorizedDecisionOption,
         "unauthorized_decision_option"),
        (("decision:test:1", "A", "opaque-a", 1), StaleDecisionVersion,
         "stale_decision_version"),
    ],
)
def test_close_errors_have_stable_domain_codes(
    arguments: tuple[object, ...],
    error_type: type[IllegalAction],
    code: str,
) -> None:
    engine = make_engine()
    if error_type is not DecisionSlotEmpty:
        open_decision(engine)

    with pytest.raises(error_type) as caught:
        engine._close_pending_decision(*arguments)  # type: ignore[arg-type]

    assert caught.value.code == code  # type: ignore[attr-defined]
    assert "opaque-a" not in str(caught.value)
    assert "opaque-b" not in str(caught.value)


def test_slot_conflicts_and_terminal_state_have_specific_errors() -> None:
    engine = make_engine()
    open_decision(engine)
    with pytest.raises(DecisionSlotOccupied) as occupied:
        open_decision(engine)
    assert occupied.value.code == "decision_slot_occupied"

    engine._close_pending_decision("decision:test:1", "A", "opaque-a", 0)
    with pytest.raises(DecisionAlreadyClosed) as closed:
        engine._close_pending_decision("decision:test:1", "A", "opaque-a", 0)
    assert closed.value.code == "decision_already_closed"


def test_consume_requires_closed_decision_before_validating_its_identity() -> None:
    engine = make_engine()
    open_decision(engine)
    state_before = engine.state

    with pytest.raises(DecisionNotClosed) as pending:
        engine._consume_pending_decision("other", 0)

    assert pending.value.code == "decision_not_closed"
    assert engine.state is state_before


@pytest.mark.parametrize(
    ("prepare", "arguments", "error_type"),
    [
        (False, ("decision:test:1", 0), DecisionSlotEmpty),
        (True, ("other", 0), DecisionIdMismatch),
        (True, ("decision:test:1", 1), StaleDecisionVersion),
    ],
)
def test_consume_validates_closed_decision_without_releasing_slot(
    prepare: bool,
    arguments: tuple[object, ...],
    error_type: type[IllegalAction],
) -> None:
    engine = make_engine()
    if prepare:
        open_decision(engine)
        engine._close_pending_decision("decision:test:1", "A", "opaque-a", 0)
    state_before = engine.state

    with pytest.raises(error_type):
        engine._consume_pending_decision(*arguments)  # type: ignore[arg-type]

    assert engine.state is state_before


def test_consume_publishes_validated_candidate_records_history_and_reopens_slot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = make_engine()
    open_decision(engine)
    engine._close_pending_decision("decision:test:1", "A", "opaque-b", 0)
    closed_state = engine.state
    assert closed_state is not None and closed_state.pending_decision is not None
    history_before = tuple(closed_state.history)
    validated_candidates = []
    validate = engine._validate_invariants

    def observe_candidate(*args: object) -> None:
        candidate = args[0]
        assert candidate is not closed_state
        assert candidate.pending_decision is None  # type: ignore[union-attr]
        validated_candidates.append(candidate)
        validate(*args)  # type: ignore[arg-type]

    monkeypatch.setattr(engine, "_validate_invariants", observe_candidate)
    engine._consume_pending_decision("decision:test:1", 0)

    assert engine.state is validated_candidates[0]
    assert engine.state.pending_decision is None
    consumed = engine.state.history[-1]
    assert isinstance(consumed, DecisionTransitionEntry)
    assert isinstance(consumed.transition, DecisionConsumed)
    assert consumed.transition.status is DecisionHistoryStatus.CONSUMED
    assert consumed.transition.decision_id == "decision:test:1"
    assert consumed.transition.state_version == 0
    assert tuple(engine.state.history[:-1]) == history_before

    monkeypatch.setattr(engine, "_validate_invariants", validate)
    open_decision(engine, decision_id="decision:test:2")
    assert engine.state.pending_decision is not None
    assert engine.state.pending_decision.decision_id == "decision:test:2"


def test_consume_does_not_publish_candidate_when_invariants_fail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = make_engine()
    open_decision(engine)
    engine._close_pending_decision("decision:test:1", "A", "opaque-a", 0)
    state_before = engine.state
    snapshot_before = deepcopy(state_before)

    def reject_candidate(*_args: object) -> None:
        raise InvariantViolation("La copia candidata no supera las invariantes")

    monkeypatch.setattr(engine, "_validate_invariants", reject_candidate)
    with pytest.raises(InvariantViolation):
        engine._consume_pending_decision("decision:test:1", 0)

    assert engine.state is state_before
    assert engine.state == snapshot_before


@pytest.mark.parametrize("operation", ["open", "close"])
def test_invariant_failure_does_not_publish_candidate_or_technical_state(
    monkeypatch: pytest.MonkeyPatch, operation: str
) -> None:
    engine = make_engine()
    if operation == "close":
        open_decision(engine)
    state_before = engine.state
    snapshot_before = deepcopy(engine.state)
    technical_before = (
        engine._next_instance,
        engine._next_stack_item,
        engine._replacement_replay_choices,
        engine._replacement_replay_cursor,
    )

    def reject_candidate(*_args: object) -> None:
        raise InvariantViolation("La copia candidata no supera las invariantes")

    monkeypatch.setattr(engine, "_validate_invariants", reject_candidate)
    with pytest.raises(InvariantViolation):
        if operation == "open":
            open_decision(engine)
        else:
            engine._close_pending_decision("decision:test:1", "A", "opaque-a", 0)

    assert engine.state is state_before
    assert engine.state == snapshot_before
    assert technical_before == (
        engine._next_instance,
        engine._next_stack_item,
        engine._replacement_replay_choices,
        engine._replacement_replay_cursor,
    )
