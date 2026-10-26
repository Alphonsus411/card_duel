"""W1.4B/C: bloqueo selectivo y su revalidación autoritativa."""

import pytest

from card_duel_engine import (
    AuthenticatedMatchApplication,
    Capability,
    ExternalIdentity,
    InMemoryIdentityAuthorization,
    InMemoryMatchStore,
    MatchService,
)
from card_duel_engine.domain import PendingDecisionStatus
from card_duel_engine.domain.errors import IllegalAction
from card_duel_engine.engine.commands import Concede, PassPriority
from card_duel_engine.persistence import (
    dump_replay,
    dump_snapshot,
    load_snapshot,
    replay_from_log,
    state_digest,
)

from test_pending_decision_w1_1 import OPTIONS, make_engine, open_decision


def _actions(engine):
    return {player_id: engine.legal_actions(player_id) for player_id in ("A", "B")}


def test_test_choice_pending_blocks_every_command_except_concede_for_all_players():
    engine = make_engine()
    open_decision(engine)

    assert _actions(engine) == {
        "A": (Concede("A"),),
        "B": (Concede("B"),),
    }


def test_closed_and_unregistered_families_preserve_the_existing_action_lists():
    baseline = _actions(make_engine())

    closed = make_engine()
    open_decision(closed)
    closed._close_pending_decision("opaque_D7q9", "A", OPTIONS[0], 17)
    assert closed.state is not None
    assert closed.state.pending_decision is not None
    assert closed.state.pending_decision.status is PendingDecisionStatus.CLOSED
    assert _actions(closed) == baseline

    unregistered = make_engine()
    open_decision(unregistered, semantic_family="second-choice/v2")
    assert _actions(unregistered) == baseline


def test_blocking_policy_survives_snapshot_and_replay_without_new_state():
    engine = make_engine()
    open_decision(engine)
    expected = _actions(engine)

    restored_snapshot = load_snapshot(dump_snapshot(engine, indent=None))
    restored_replay = replay_from_log(dump_replay(engine, indent=None))

    assert _actions(restored_snapshot) == expected
    assert _actions(restored_replay) == expected


def test_blocking_does_not_prevent_the_elector_from_resolving_through_application():
    engine = make_engine()
    open_decision(engine)
    store = InMemoryMatchStore()
    assert store.create("w14b", engine) == 1
    authorization = InMemoryIdentityAuthorization()
    identities = {
        player_id: ExternalIdentity("w1.4b-tests", player_id)
        for player_id in ("A", "B")
    }
    for player_id, identity in identities.items():
        authorization.bind_player(
            identity,
            "w14b",
            player_id,
            capabilities=(Capability.OBSERVE, Capability.RESOLVE_PENDING_DECISION),
        )
    application = AuthenticatedMatchApplication(MatchService(store), authorization)

    before = application.view(identities["A"], "w14b")
    assert before.pending_decision is not None
    token = before.pending_decision.options[0].decision_option_id
    after = application.resolve_pending_decision(
        identities["A"], "w14b", token, expected_version=before.version
    )

    assert after.pending_decision is not None
    assert after.pending_decision.status == PendingDecisionStatus.CLOSED.value


def test_direct_command_cannot_bypass_the_selective_pending_decision_block():
    engine = make_engine()
    open_decision(engine)
    assert engine.state is not None
    actor = engine.state.priority_player_id
    assert actor is not None
    before = state_digest(engine)

    with pytest.raises(IllegalAction, match="bloquea comandos"):
        engine.execute(PassPriority(actor))

    assert state_digest(engine) == before


def test_service_submission_cannot_bypass_the_selective_pending_decision_block():
    engine = make_engine()
    open_decision(engine)
    assert engine.state is not None
    actor = engine.state.priority_player_id
    assert actor is not None
    store = InMemoryMatchStore()
    assert store.create("w14c", engine) == 1
    service = MatchService(store)
    before = state_digest(store.load("w14c").engine)

    with pytest.raises(IllegalAction, match="bloquea comandos"):
        service.submit("w14c", PassPriority(actor), expected_version=1)

    stored = store.load("w14c")
    assert stored.version == 1
    assert state_digest(stored.engine) == before
