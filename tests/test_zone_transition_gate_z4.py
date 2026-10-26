from __future__ import annotations

import pytest

from card_duel_engine import GameEngine
from card_duel_engine.domain import CardDefinition, CardKind, MoveReason, MoveReplacementDefinition, Zone

from fixtures import test_deck


def _engine(*, special: CardDefinition | None = None) -> GameEngine:
    engine = GameEngine()
    engine.new_match(
        {
            "A": ([special] if special is not None else []) + test_deck("Z4-A"),
            "B": test_deck("Z4-B"),
        },
        seed=426,
    )
    return engine


def test_match_initialization_crosses_the_gate_with_contiguous_internal_records() -> None:
    engine = _engine()
    transitions = engine.state.zone_transition_history

    assert engine.state.zone_transition_prefix_complete is True
    assert [item.sequence for item in transitions] == list(range(1, len(transitions) + 1))
    assert all(item.audience.value == "internal" for item in transitions)
    assert all(item.batch_id == f"zone-batch-{item.sequence:06d}" for item in transitions)
    assert all(item.origin_zone is Zone.DECK for item in transitions)
    assert all(item.effective_destination is Zone.HAND for item in transitions)


def test_gate_captures_requested_and_effective_placement_without_emitting_event() -> None:
    engine = _engine()
    card_id = engine.state.players["A"].zones[Zone.HAND][0]
    events_before = tuple(engine.state.event_log)
    transition_count = len(engine.state.zone_transition_history)

    engine._move_card(card_id, Zone.DISCARD, "A", reason=MoveReason.DISCARD)

    transition = engine.state.zone_transition_history[-1]
    assert transition.sequence == transition_count + 1
    assert transition.card_id == card_id
    assert transition.origin_zone is Zone.HAND
    assert transition.origin_player_id == "A"
    assert transition.requested_destination is Zone.DISCARD
    assert transition.requested_player_id == "A"
    assert transition.effective_destination is Zone.DISCARD
    assert transition.effective_player_id == "A"
    assert transition.reason is MoveReason.DISCARD
    assert transition.prior_state.zone is Zone.HAND
    assert transition.prior_state.container_player_id == "A"
    assert tuple(engine.state.event_log) == events_before


def test_replacement_that_keeps_battlefield_still_leaves_causal_evidence() -> None:
    replacement = MoveReplacementDefinition(
        Zone.BATTLEFIELD, applies_to=frozenset({MoveReason.DESTROY})
    )
    special = CardDefinition(
        "z4-replacement", "Sustitución", CardKind.CREATURE, 0,
        base_strength=2, move_replacement=replacement,
    )
    engine = _engine(special=special)
    card_id = next(
        card_id
        for card_id, instance in engine.state.cards.items()
        if instance.definition_id == special.card_id
    )
    engine._move_card(card_id, Zone.BATTLEFIELD, "A")
    transition_count = len(engine.state.zone_transition_history)

    assert engine._move_card(
        card_id, Zone.DISCARD, "A", reason=MoveReason.DESTROY
    ) is Zone.BATTLEFIELD

    transition = engine.state.zone_transition_history[-1]
    assert transition.sequence == transition_count + 1
    assert transition.origin_zone is Zone.BATTLEFIELD
    assert transition.requested_destination is Zone.DISCARD
    assert transition.effective_destination is Zone.BATTLEFIELD
    assert engine.state.cards[card_id].zone is Zone.BATTLEFIELD


def test_failed_move_does_not_leave_a_causal_entry() -> None:
    engine = _engine()
    card_id = engine.state.players["A"].zones[Zone.HAND][0]
    transitions_before = tuple(engine.state.zone_transition_history)

    with pytest.raises(ValueError, match="no almacenable"):
        engine._move_card(card_id, Zone.REVEAL, "missing")

    assert tuple(engine.state.zone_transition_history) == transitions_before
