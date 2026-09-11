from dataclasses import FrozenInstanceError, fields

import pytest

from card_duel_engine import GameEngine, InMemoryMatchStore, MatchService
from card_duel_engine.controllers import PendingDecisionView
from card_duel_engine.domain import DecisionAudience, PendingDecisionStatus

from fixtures import test_deck


def engine_with_decision(
    *, audience: DecisionAudience = DecisionAudience.ELECTOR
) -> GameEngine:
    engine = GameEngine()
    engine.new_match(
        {"A": test_deck("view-A"), "B": test_deck("view-B")}, seed=12
    )
    engine._open_pending_decision(
        decision_id="decision:view:1",
        semantic_family="test-choice/v1",
        authorized_elector="A",
        audience=audience,
        authorized_opaque_options=("opaque-a", "opaque-b"),
        state_version=7,
        origin=("private-origin",),
    )
    return engine


def test_pending_decision_view_is_a_minimal_frozen_dto() -> None:
    view = engine_with_decision().observe("A").pending_decision

    assert view is not None
    assert tuple(field.name for field in fields(view)) == (
        "decision_id",
        "semantic_family",
        "status",
        "state_version",
        "audience",
        "authorized_opaque_options",
    )
    assert not hasattr(view, "origin")
    assert not hasattr(view, "authorized_elector")
    with pytest.raises(FrozenInstanceError):
        view.status = PendingDecisionStatus.CLOSED  # type: ignore[misc]


def test_only_pending_elector_receives_resolvable_internal_options() -> None:
    engine = engine_with_decision()

    elector_view = engine.observe("A").pending_decision
    opponent_view = engine.observe("B").pending_decision
    assert elector_view is not None
    assert elector_view.authorized_opaque_options == ("opaque-a", "opaque-b")
    assert opponent_view is not None
    assert opponent_view.authorized_opaque_options == ()

    engine._close_pending_decision("decision:view:1", "A", "opaque-a", 7)
    closed_view = engine.observe("A").pending_decision
    assert closed_view is not None
    assert closed_view.status is PendingDecisionStatus.CLOSED
    assert closed_view.authorized_opaque_options == ()


def test_internal_audience_fails_closed_even_for_elector() -> None:
    view = engine_with_decision(
        audience=DecisionAudience.INTERNAL
    ).observe("A").pending_decision

    assert view is not None
    assert view.audience is DecisionAudience.INTERNAL
    assert view.authorized_opaque_options == ()


def test_match_view_propagates_observers_projection_and_none_compatibly() -> None:
    engine = engine_with_decision()
    store = InMemoryMatchStore()
    store.create("decision-view", engine)

    view = MatchService(store).view("decision-view", "B")

    assert isinstance(view.pending_decision, PendingDecisionView)
    assert view.pending_decision is view.observation.pending_decision
    assert view.pending_decision.authorized_opaque_options == ()

    clean_engine = GameEngine()
    clean_engine.new_match(
        {"A": test_deck("clean-A"), "B": test_deck("clean-B")}, seed=13
    )
    clean_store = InMemoryMatchStore()
    clean_store.create("clean-view", clean_engine)
    clean_view = MatchService(clean_store).view("clean-view", "A")
    assert clean_view.pending_decision is None
    assert clean_view.observation.pending_decision is None
