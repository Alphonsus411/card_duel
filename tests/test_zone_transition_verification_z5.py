from __future__ import annotations

import json
from copy import deepcopy
from unittest.mock import patch

import pytest

from card_duel_engine import GameEngine
from card_duel_engine.application import PublicPlayerObservation
from card_duel_engine.domain.enums import Phase, Zone
from card_duel_engine.domain.errors import InvariantViolation
from card_duel_engine.engine.commands import AdvancePhase, DiscardCards, PassPriority
from card_duel_engine.persistence import dump_replay, dump_snapshot, load_snapshot, replay_from_log

from fixtures import test_deck


def _engine() -> GameEngine:
    engine = GameEngine()
    engine.new_match({"A": test_deck("Z5-A"), "B": test_deck("Z5-B")}, seed=526)
    return engine


def _close_priority(engine: GameEngine) -> None:
    for _ in engine.state.turn_order:
        engine.execute(PassPriority(engine.state.priority_player_id))


def _advance_to_discard(engine: GameEngine) -> None:
    while engine.state.phase is not Phase.DISCARD:
        _close_priority(engine)
        engine.execute(AdvancePhase("A"))


def test_public_command_rollback_restores_causal_history_atomically() -> None:
    engine = _engine()
    _advance_to_discard(engine)
    command = DiscardCards("A", (engine.state.players["A"].zones[Zone.HAND][0],))
    state_before = deepcopy(engine.state)

    with patch.object(
        engine,
        "_validate_invariants",
        side_effect=InvariantViolation("fallo de verificación inyectado"),
    ):
        with pytest.raises(InvariantViolation, match="inyectado"):
            engine.execute(command)

    assert engine.state == state_before


def test_snapshot_and_replay_preserve_causal_order_and_identity() -> None:
    engine = _engine()
    snapshot_restored = load_snapshot(dump_snapshot(engine, indent=None))
    replay_restored = replay_from_log(dump_replay(engine, indent=None))

    assert snapshot_restored.state.zone_transition_history == engine.state.zone_transition_history
    assert replay_restored.state.zone_transition_history == engine.state.zone_transition_history
    assert replay_restored.state.zone_transition_prefix_complete is True
    assert [item.sequence for item in replay_restored.state.zone_transition_history] == list(
        range(1, len(replay_restored.state.zone_transition_history) + 1)
    )


def test_internal_transition_history_is_absent_from_player_projection() -> None:
    engine = _engine()
    public = PublicPlayerObservation.from_observation(engine.observe("B")).to_dict()
    serialized = json.dumps(public, sort_keys=True)

    assert "zone_transition" not in serialized
    assert "zone-batch-" not in serialized
    assert "prior_state" not in serialized
