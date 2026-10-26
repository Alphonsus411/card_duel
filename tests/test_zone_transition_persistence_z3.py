from __future__ import annotations

import hashlib
import json
from dataclasses import replace

import pytest

from card_duel_engine import GameEngine
from card_duel_engine.domain import (
    DecisionAudience,
    MoveReason,
    TransitionPriorState,
    Zone,
    ZoneTransition,
)
from card_duel_engine.persistence import dump_snapshot, load_snapshot, state_digest
from card_duel_engine.persistence.codec import canonical_json

from fixtures import test_deck


def _engine() -> GameEngine:
    engine = GameEngine()
    engine.new_match({"A": test_deck("Z3-A"), "B": test_deck("Z3-B")}, seed=326)
    return engine


def _rechecksum(envelope: dict) -> None:
    body = envelope["body"]
    body["state_digest"] = hashlib.sha256(
        canonical_json(body["state"]).encode("utf-8")
    ).hexdigest()
    envelope["sha256"] = hashlib.sha256(
        canonical_json(body).encode("utf-8")
    ).hexdigest()


def _transition(engine: GameEngine) -> ZoneTransition:
    card_id = engine.state.players["A"].zones[Zone.HAND][0]
    return ZoneTransition(
        sequence=1,
        card_id=card_id,
        origin_zone=Zone.HAND,
        origin_player_id="A",
        requested_destination=Zone.DISCARD,
        requested_player_id="A",
        effective_destination=Zone.DISCARD,
        effective_player_id="A",
        reason=MoveReason.DISCARD,
        batch_id="zone-batch-000001",
        audience=DecisionAudience.INTERNAL,
        prior_state=TransitionPriorState(Zone.HAND, "A", "A", None),
    )


def test_schema_six_round_trips_internal_causal_record_without_public_event() -> None:
    engine = _engine()
    transition = replace(
        _transition(engine), sequence=len(engine.state.zone_transition_history) + 1
    )
    events_before = tuple(engine.state.event_log)
    engine.state.zone_transition_history.append(transition)
    engine.state.zone_transition_prefix_complete = True

    snapshot = dump_snapshot(engine, indent=None)
    restored = load_snapshot(snapshot)

    assert json.loads(snapshot)["body"]["schema_version"] == "6"
    assert restored.state.zone_transition_history[-1] == transition
    assert len(restored.state.zone_transition_history) == transition.sequence
    assert restored.state.zone_transition_prefix_complete is True
    assert state_digest(restored) == state_digest(engine)
    assert tuple(restored.state.event_log) == events_before


def test_schema_five_migration_marks_causal_prefix_unknown_without_inference() -> None:
    engine = _engine()
    envelope = json.loads(dump_snapshot(engine))
    fields = envelope["body"]["state"]["fields"]
    fields.pop("zone_transition_history")
    fields.pop("zone_transition_prefix_complete")
    envelope["body"]["schema_version"] = "5"
    _rechecksum(envelope)

    restored = load_snapshot(envelope)

    assert restored.state.zone_transition_history == []
    assert restored.state.zone_transition_prefix_complete is False
    upgraded = json.loads(dump_snapshot(restored))
    assert upgraded["body"]["schema_version"] == "6"
    assert upgraded["body"]["state"]["fields"]["zone_transition_history"] == []
    assert upgraded["body"]["state"]["fields"]["zone_transition_prefix_complete"] is False


def test_schema_five_rejects_ambiguous_preexisting_causal_fields() -> None:
    envelope = json.loads(dump_snapshot(_engine()))
    envelope["body"]["schema_version"] = "5"
    _rechecksum(envelope)

    with pytest.raises(ValueError, match="mezcla historia causal incompatible"):
        load_snapshot(envelope)


def test_transition_contract_rejects_non_internal_audience_and_mismatched_origin() -> None:
    engine = _engine()
    transition = _transition(engine)

    with pytest.raises(ValueError, match="audiencia interna"):
        ZoneTransition(**{**transition.__dict__, "audience": DecisionAudience.ELECTOR})
    with pytest.raises(ValueError, match="zona previa no coincide"):
        ZoneTransition(
            **{
                **transition.__dict__,
                "prior_state": TransitionPriorState(Zone.DECK, "A", "A", None),
            }
        )
