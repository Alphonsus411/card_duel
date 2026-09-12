from __future__ import annotations

from copy import deepcopy
from dataclasses import fields, replace
import inspect
import json
import re
from typing import Any

import pytest

from card_duel_engine import GameEngine
from card_duel_engine.domain import (
    DecisionAudience,
    DecisionClosed,
    DecisionOpened,
    DecisionTransitionEntry,
    PendingDecision,
    PendingDecisionStatus,
)
from card_duel_engine.domain.errors import (
    DecisionAlreadyClosed,
    DecisionIdMismatch,
    DecisionSlotEmpty,
    DecisionSlotOccupied,
    IllegalAction,
    StaleDecisionVersion,
    UnauthorizedDecisionElector,
    UnauthorizedDecisionOption,
)
from card_duel_engine.persistence.snapshot import (
    dump_snapshot,
    load_snapshot,
    state_digest,
)
from card_duel_engine.persistence.replay import dump_replay, replay_from_log

from fixtures import test_deck


DECISION_ID = "opaque_D7q9"
FAMILY = "test-choice/v1"
OPTIONS = ("opaque_N4x2", "opaque_K8p6")
ORIGIN = ("opaque_R3m5", "opaque_T9v1")
VERSION = 17
EXPECTED_FIELDS = {
    "decision_id",
    "semantic_family",
    "authorized_elector",
    "audience",
    "authorized_opaque_options",
    "state_version",
    "origin",
    "status",
    "selected_option",
}


def make_engine() -> GameEngine:
    engine = GameEngine()
    engine.new_match(
        {"A": test_deck("W1-1-A"), "B": test_deck("W1-1-B")}, seed=111
    )
    return engine


def opening_arguments(**changes: Any) -> dict[str, Any]:
    arguments: dict[str, Any] = {
        "decision_id": DECISION_ID,
        "semantic_family": FAMILY,
        "authorized_elector": "A",
        "audience": DecisionAudience.ELECTOR,
        "authorized_opaque_options": OPTIONS,
        "state_version": VERSION,
        "origin": ORIGIN,
    }
    arguments.update(changes)
    return arguments


def open_decision(engine: GameEngine, **changes: Any) -> None:
    engine._open_pending_decision(**opening_arguments(**changes))


def canonical_snapshot(engine: GameEngine) -> str:
    return dump_snapshot(engine, indent=None)


def test_valid_open_is_none_to_pending_with_nine_fields_and_one_authority() -> None:
    engine = make_engine()
    assert engine.state is not None
    assert engine.state.pending_decision is None
    state_before = deepcopy(engine.state)

    open_decision(engine)

    assert engine.state is not state_before
    decision = engine.state.pending_decision
    assert decision is not None
    assert {field.name for field in fields(decision)} == EXPECTED_FIELDS
    assert decision == PendingDecision(
        decision_id=DECISION_ID,
        semantic_family=FAMILY,
        authorized_elector="A",
        audience=DecisionAudience.ELECTOR,
        authorized_opaque_options=OPTIONS,
        state_version=VERSION,
        origin=ORIGIN,
        status=PendingDecisionStatus.PENDING,
        selected_option=None,
    )
    # La decisión vive en el slot, mientras su transición tipada se incorpora
    # a la historia total sin crear una autoridad paralela en el motor.
    assert not hasattr(engine, "pending_decision")
    assert len(engine.state.history) == len(state_before.history) + 1
    opened_entry = engine.state.history[-1]
    assert isinstance(opened_entry, DecisionTransitionEntry)
    assert isinstance(opened_entry.transition, DecisionOpened)
    state_after_without_slot = replace(
        engine.state,
        pending_decision=None,
        history=list(state_before.history),
    )
    assert state_after_without_slot == state_before


@pytest.mark.parametrize(
    ("changes", "error_type"),
    [
        pytest.param(
            {"authorized_elector": "opaque_missing"},
            IllegalAction,
            id="unknown-elector",
        ),
        pytest.param({"decision_id": ""}, IllegalAction, id="empty-id"),
        pytest.param({"decision_id": "   "}, IllegalAction, id="blank-id"),
        pytest.param({"decision_id": 23}, IllegalAction, id="malformed-id"),
        pytest.param({"semantic_family": ""}, IllegalAction, id="empty-family"),
        pytest.param(
            {"semantic_family": "test-choice"},
            IllegalAction,
            id="unversioned-family",
        ),
        pytest.param(
            {"semantic_family": "test-choice/version-one"},
            IllegalAction,
            id="malformed-family",
        ),
        pytest.param(
            {"audience": "opaque_N4x2"}, IllegalAction, id="invalid-audience"
        ),
        pytest.param(
            {"authorized_opaque_options": ()}, IllegalAction, id="empty-options"
        ),
        pytest.param(
            {"authorized_opaque_options": ("opaque_N4x2",) * 2},
            IllegalAction,
            id="duplicate-options",
        ),
        pytest.param(
            {"authorized_opaque_options": ("opaque_N4x2", "")},
            IllegalAction,
            id="empty-option",
        ),
        pytest.param(
            {"authorized_opaque_options": ("opaque_N4x2", 23)},
            IllegalAction,
            id="malformed-option",
        ),
        pytest.param(
            {"authorized_opaque_options": ["opaque_N4x2"]},
            IllegalAction,
            id="mutable-options",
        ),
        pytest.param({"state_version": -1}, IllegalAction, id="negative-version"),
        pytest.param({"state_version": True}, IllegalAction, id="boolean-version"),
        pytest.param({"state_version": "17"}, IllegalAction, id="malformed-version"),
        pytest.param({"origin": ()}, IllegalAction, id="empty-origin"),
        pytest.param(
            {"origin": ("opaque_R3m5", "")}, IllegalAction, id="empty-origin-part"
        ),
        pytest.param(
            {"origin": ["opaque_R3m5"]}, IllegalAction, id="mutable-origin"
        ),
        pytest.param(
            {"status": PendingDecisionStatus.CLOSED},
            TypeError,
            id="closed-initial-state-not-in-api",
        ),
    ],
)
def test_rejected_open_is_fully_atomic(
    changes: dict[str, Any], error_type: type[BaseException]
) -> None:
    engine = make_engine()
    before_copy = deepcopy(engine.state)
    before_snapshot = canonical_snapshot(engine)

    with pytest.raises(error_type):
        open_decision(engine, **changes)

    assert engine.state == before_copy
    assert canonical_snapshot(engine) == before_snapshot


@pytest.mark.parametrize("occupied_status", list(PendingDecisionStatus))
def test_open_rejects_pending_and_closed_occupied_slots_atomically(
    occupied_status: PendingDecisionStatus,
) -> None:
    engine = make_engine()
    open_decision(engine)
    if occupied_status is PendingDecisionStatus.CLOSED:
        engine._close_pending_decision(DECISION_ID, "A", OPTIONS[0], VERSION)
    before_copy = deepcopy(engine.state)
    before_snapshot = canonical_snapshot(engine)

    with pytest.raises(DecisionSlotOccupied):
        open_decision(engine, decision_id="opaque_J2c7")

    assert engine.state == before_copy
    assert canonical_snapshot(engine) == before_snapshot


def test_valid_close_is_pending_to_closed_and_only_changes_terminal_fields() -> None:
    engine = make_engine()
    open_decision(engine)
    assert engine.state is not None and engine.state.pending_decision is not None
    pending = engine.state.pending_decision

    engine._close_pending_decision(DECISION_ID, "A", OPTIONS[1], VERSION)

    assert engine.state.pending_decision is not None
    closed = engine.state.pending_decision
    assert closed.status is PendingDecisionStatus.CLOSED
    assert closed.selected_option == OPTIONS[1]
    # De los nueve campos, status y selected_option expresan la transición;
    # los siete campos de identidad/contrato permanecen exactamente iguales.
    for field in EXPECTED_FIELDS - {"status", "selected_option"}:
        assert getattr(closed, field) == getattr(pending, field)


@pytest.mark.parametrize(
    ("setup", "arguments", "error_type"),
    [
        pytest.param(
            False,
            (DECISION_ID, "A", OPTIONS[0], VERSION),
            DecisionSlotEmpty,
            id="empty-slot",
        ),
        pytest.param(
            True,
            ("opaque_wrong", "A", OPTIONS[0], VERSION),
            DecisionIdMismatch,
            id="wrong-id",
        ),
        pytest.param(
            True,
            (DECISION_ID, "B", OPTIONS[0], VERSION),
            UnauthorizedDecisionElector,
            id="wrong-actor",
        ),
        pytest.param(
            True,
            (DECISION_ID, "A", "opaque_denied", VERSION),
            UnauthorizedDecisionOption,
            id="unauthorized-option",
        ),
        pytest.param(
            True,
            (DECISION_ID, "A", OPTIONS[0], VERSION + 1),
            StaleDecisionVersion,
            id="stale-version",
        ),
    ],
)
def test_rejected_close_is_fully_atomic(
    setup: bool,
    arguments: tuple[str, str, str, int],
    error_type: type[IllegalAction],
) -> None:
    engine = make_engine()
    if setup:
        open_decision(engine)
    before_copy = deepcopy(engine.state)
    before_snapshot = canonical_snapshot(engine)

    with pytest.raises(error_type):
        engine._close_pending_decision(*arguments)

    assert engine.state == before_copy
    assert canonical_snapshot(engine) == before_snapshot


def test_close_is_exactly_once_and_second_attempt_is_atomic() -> None:
    engine = make_engine()
    open_decision(engine)
    engine._close_pending_decision(DECISION_ID, "A", OPTIONS[0], VERSION)
    before_copy = deepcopy(engine.state)
    before_snapshot = canonical_snapshot(engine)

    with pytest.raises(DecisionAlreadyClosed):
        engine._close_pending_decision(DECISION_ID, "A", OPTIONS[0], VERSION)

    assert engine.state == before_copy
    assert canonical_snapshot(engine) == before_snapshot


@pytest.mark.parametrize("closed", [False, True], ids=["pending", "closed"])
def test_real_snapshot_v4_round_trip_preserves_lifecycle_state(closed: bool) -> None:
    engine = make_engine()
    open_decision(engine)
    if closed:
        engine._close_pending_decision(DECISION_ID, "A", OPTIONS[1], VERSION)

    payload = dump_snapshot(engine, indent=None)
    restored = load_snapshot(payload)

    assert json.loads(payload)["body"]["schema_version"] == "4"
    assert restored.state == engine.state
    assert state_digest(restored) == state_digest(engine)
    assert dump_snapshot(restored, indent=None) == payload


def test_digest_distinguishes_absence_options_status_and_selected_option() -> None:
    empty = make_engine()
    pending_a = make_engine()
    pending_b = make_engine()
    closed_a = make_engine()
    closed_b = make_engine()
    open_decision(pending_a)
    open_decision(pending_b, authorized_opaque_options=("opaque_Q1w4", "opaque_Z6h8"))
    open_decision(closed_a)
    open_decision(closed_b)
    closed_a._close_pending_decision(DECISION_ID, "A", OPTIONS[0], VERSION)
    closed_b._close_pending_decision(DECISION_ID, "A", OPTIONS[1], VERSION)

    assert state_digest(empty) != state_digest(pending_a)
    assert state_digest(pending_a) != state_digest(pending_b)
    assert state_digest(pending_a) != state_digest(closed_a)
    assert state_digest(closed_a) != state_digest(closed_b)


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        pytest.param("decision_id", "opaque_other", id="decision-id"),
        pytest.param("semantic_family", "other-choice/v2", id="semantic-family"),
        pytest.param("authorized_elector", "B", id="authorized-elector"),
        pytest.param("audience", DecisionAudience.OPPONENT, id="audience"),
        pytest.param(
            "authorized_opaque_options",
            ("opaque_other_a", "opaque_other_b"),
            id="authorized-options",
        ),
        pytest.param("state_version", VERSION + 1, id="state-version"),
        pytest.param("origin", ("opaque_other_origin",), id="origin"),
    ],
)
def test_digest_includes_each_pending_decision_contract_field(
    field: str, replacement: object
) -> None:
    baseline = make_engine()
    changed = make_engine()
    open_decision(baseline)
    open_decision(changed, **{field: replacement})

    assert state_digest(changed) != state_digest(baseline)


def test_replay_v3_reconstructs_internal_lifecycle_mutation() -> None:
    engine = make_engine()
    open_decision(engine)

    payload = dump_replay(engine, indent=None)

    assert json.loads(payload)["body"]["schema_version"] == "3"
    restored = replay_from_log(payload)
    assert restored.state is not None
    assert restored.state.pending_decision == engine.state.pending_decision


def test_inv_14_close_only_changes_decision_slot_and_appends_typed_history() -> None:
    engine = make_engine()
    open_decision(engine)
    assert engine.state is not None
    before = deepcopy(engine.state)

    engine._close_pending_decision(DECISION_ID, "A", OPTIONS[0], VERSION)

    assert engine.state is not None
    compared = {field.name for field in fields(engine.state)} - {
        "pending_decision",
        "history",
    }
    # Esta lista hace explícita la cobertura de jugadores/vida-heridas, pasos,
    # todas las zonas y cartas, stack, combate, prioridad, fase, turno y logs.
    assert {
        "players",
        "cards",
        "resolution",
        "void",
        "stack",
        "combat",
        "priority_player_id",
        "phase",
        "turn_number",
        "event_log",
        "command_history",
    } <= compared
    for field in compared:
        assert getattr(engine.state, field) == getattr(before, field), field
    assert engine.state.history[:-1] == before.history
    closed_entry = engine.state.history[-1]
    assert isinstance(closed_entry, DecisionTransitionEntry)
    assert isinstance(closed_entry.transition, DecisionClosed)
    assert closed_entry.transition.selected_option == OPTIONS[0]


def test_lifecycle_operations_are_structurally_card_agnostic() -> None:
    forbidden = {"card_id", "definition_id", "card_name", "set_id", "expansion"}
    for method in (
        GameEngine._open_pending_decision,
        GameEngine._close_pending_decision,
    ):
        source = inspect.getsource(method)
        identifiers = set(re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", source))
        assert forbidden.isdisjoint(identifiers)
        parameters = inspect.signature(method).parameters
        assert all(token not in parameters for token in forbidden)
