from __future__ import annotations

from copy import deepcopy

import pytest

from card_duel_engine import GameEngine
from card_duel_engine.domain import DecisionAudience, PendingDecisionStatus
from card_duel_engine.domain.errors import IllegalAction

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


def test_slot_cannot_be_reopened_or_closed_twice() -> None:
    engine = make_engine()
    with pytest.raises(IllegalAction, match="No existe"):
        engine._close_pending_decision("decision:test:1", "A", "opaque-a", 0)
    open_decision(engine)
    with pytest.raises(IllegalAction, match="Ya existe"):
        open_decision(engine)
    engine._close_pending_decision("decision:test:1", "A", "opaque-a", 0)
    with pytest.raises(IllegalAction, match="ya no está pendiente"):
        engine._close_pending_decision("decision:test:1", "A", "opaque-a", 0)
