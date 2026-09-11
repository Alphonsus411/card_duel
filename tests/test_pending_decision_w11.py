from __future__ import annotations

from copy import deepcopy

import pytest

from card_duel_engine import GameEngine
from card_duel_engine.domain import DecisionAudience, PendingDecisionStatus
from card_duel_engine.domain.errors import (
    DecisionAlreadyClosed,
    DecisionIdMismatch,
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
    before = engine.state.pending_decision  # type: ignore[union-attr]
    with pytest.raises(IllegalAction, match=message):
        engine._close_pending_decision(*arguments)  # type: ignore[arg-type]
    assert engine.state is not None and engine.state.pending_decision is before


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
