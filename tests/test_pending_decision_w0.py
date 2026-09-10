from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
import hashlib
import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from threading import Barrier
from typing import Callable

import pytest

from card_duel_engine import GameEngine, RuleSet
from card_duel_engine.domain import (
    DecisionAudience,
    MoveReason,
    PendingDecision,
    PendingDecisionStatus,
    Zone,
    ZoneTarget,
)
from card_duel_engine.domain.errors import InvariantViolation
from card_duel_engine.domain.models import (
    PendingMoveReplacement,
    PendingSearch,
    StackItem,
)
from card_duel_engine.engine import Concede
from card_duel_engine.persistence import dump_snapshot, load_snapshot, state_digest
from card_duel_engine.persistence.codec import canonical_json, decode_value, encode_value
from card_duel_engine.persistence.migrations import migrate_document
from card_duel_engine.persistence.replay import REPLAY_SCHEMA_VERSION
from card_duel_engine.storage import InMemoryMatchStore, SQLiteMatchStore, VersionConflict

from fixtures import test_deck


ARTIFACTS = Path(__file__).parent / "artifacts" / "pending-decision-w0"


def make_engine(seed: int = 901) -> GameEngine:
    engine = GameEngine()
    engine.new_match({"A": test_deck("W0-A"), "B": test_deck("W0-B")}, seed=seed)
    return engine


def decision(*, closed: bool = False) -> PendingDecision:
    return PendingDecision(
        decision_id="decision:test-choice:0001",
        semantic_family="test-choice/v1",
        authorized_elector="A",
        audience=DecisionAudience.ELECTOR,
        authorized_opaque_options=("opt_7xQm2", "opt_B9kL4"),
        state_version=1,
        origin=("test-choice", "fixture", "0001"),
        status=(PendingDecisionStatus.CLOSED if closed else PendingDecisionStatus.PENDING),
        selected_option="opt_B9kL4" if closed else None,
    )


def checksum(body: dict[str, object]) -> str:
    return hashlib.sha256(canonical_json(body).encode()).hexdigest()


def as_v2(engine: GameEngine) -> dict[str, object]:
    document = json.loads(dump_snapshot(engine))
    fields = document["body"]["state"]["fields"]
    fields.pop("pending_decision")
    document["body"]["schema_version"] = "2"
    document["body"]["state_digest"] = hashlib.sha256(
        canonical_json(document["body"]["state"]).encode()
    ).hexdigest()
    document["sha256"] = checksum(document["body"])
    return document


def test_model_has_exactly_nine_fields_and_value_equality() -> None:
    expected = {
        "decision_id", "semantic_family", "authorized_elector", "audience",
        "authorized_opaque_options", "state_version", "origin", "status",
        "selected_option",
    }
    assert set(decision().__dataclass_fields__) == expected
    assert tuple(PendingDecisionStatus) == (
        PendingDecisionStatus.PENDING,
        PendingDecisionStatus.CLOSED,
    )
    assert decision() == decision()
    assert decision() != replace(decision(), state_version=2)


def test_model_is_deeply_immutable_at_its_option_and_reference_boundaries() -> None:
    value = decision()
    with pytest.raises(FrozenInstanceError):
        value.status = PendingDecisionStatus.CLOSED  # type: ignore[misc]
    with pytest.raises(TypeError):
        value.authorized_opaque_options[0] = "changed"  # type: ignore[index]
    with pytest.raises(ValueError, match="inmutables"):
        replace(value, origin=["mutable"])  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        pytest.param({"audience": "elector"}, "audiencia", id="audience-not-enum"),
        pytest.param({"status": "pending"}, "estado", id="status-not-enum"),
        pytest.param(
            {"authorized_opaque_options": ["opt_7xQm2"]},
            "inmutables",
            id="options-list",
        ),
        pytest.param({"origin": ["setup"]}, "inmutables", id="origin-list"),
    ],
)
def test_enum_and_immutable_boundary_types_are_rejected(
    changes: dict[str, object], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        replace(decision(), **changes)


@pytest.mark.parametrize(
    "field", ["decision_id", "semantic_family", "authorized_elector"]
)
@pytest.mark.parametrize(
    "invalid_value",
    [
        pytest.param(None, id="none"),
        pytest.param(7, id="integer"),
        pytest.param(" \t\n", id="blank-string"),
    ],
)
def test_required_identifiers_are_rejected(
    field: str, invalid_value: object
) -> None:
    with pytest.raises(ValueError, match="identificadores"):
        replace(decision(), **{field: invalid_value})


@pytest.mark.parametrize(
    "invalid_version",
    [
        pytest.param(True, id="boolean"),
        pytest.param(1.5, id="non-integer"),
        pytest.param(0, id="zero"),
        pytest.param(-1, id="negative"),
    ],
)
def test_state_version_must_be_a_positive_non_boolean_integer(
    invalid_version: object,
) -> None:
    with pytest.raises(ValueError, match="positiva"):
        replace(decision(), state_version=invalid_version)


@pytest.mark.parametrize(
    "invalid_origin",
    [
        pytest.param((), id="empty"),
        pytest.param(("setup", ""), id="empty-reference"),
        pytest.param(("setup", 1), id="non-text-reference"),
    ],
)
def test_origin_references_must_be_non_empty_text(
    invalid_origin: tuple[object, ...],
) -> None:
    with pytest.raises(ValueError, match="origen"):
        replace(decision(), origin=invalid_origin)


@pytest.mark.parametrize(
    ("invalid_options", "message"),
    [
        pytest.param((), "vacías", id="empty-options"),
        pytest.param(("same", "same"), "únicos", id="duplicate-options"),
        pytest.param(("opt_7xQm2", ""), "vacías", id="empty-token"),
        pytest.param(("opt_7xQm2", 1), "vacías", id="non-text-token"),
    ],
)
def test_authorized_options_must_be_non_empty_unique_text_tokens(
    invalid_options: tuple[object, ...], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        replace(decision(), authorized_opaque_options=invalid_options)


@pytest.mark.parametrize(
    "selected_option",
    [
        pytest.param("opt_7xQm2", id="authorized-token"),
        pytest.param("unknown", id="unauthorized-token"),
        pytest.param("", id="empty-token"),
        pytest.param(1, id="non-text-token"),
    ],
)
def test_pending_status_rejects_any_selected_option(
    selected_option: object,
) -> None:
    with pytest.raises(ValueError, match="pendiente"):
        replace(decision(), selected_option=selected_option)


@pytest.mark.parametrize(
    "selected_option",
    [
        pytest.param(None, id="none"),
        pytest.param("unknown", id="unauthorized-token"),
    ],
)
def test_closed_status_requires_an_authorized_selected_option(
    selected_option: str | None,
) -> None:
    with pytest.raises(ValueError, match="autorizada"):
        replace(
            decision(),
            status=PendingDecisionStatus.CLOSED,
            selected_option=selected_option,
        )


def test_tokens_remain_opaque_through_codec_round_trip() -> None:
    encoded = encode_value(decision())
    serialized = canonical_json(encoded)
    assert "W0-A" not in serialized
    assert "card-" not in serialized
    assert decode_value(json.loads(serialized)) == decision()


def test_game_state_rejects_an_unknown_elector() -> None:
    engine = make_engine()
    engine.state.pending_decision = replace(decision(), authorized_elector="unknown")
    with pytest.raises(InvariantViolation, match="elector inexistente"):
        engine.validate_invariants()


@pytest.mark.parametrize("closed", [False, True])
def test_snapshot_v3_round_trip_with_decision_and_digest(closed: bool) -> None:
    engine = make_engine()
    engine.state.pending_decision = decision(closed=closed)
    payload = dump_snapshot(engine, indent=None)
    document = json.loads(payload)
    assert document["body"]["schema_version"] == "3"
    restored = load_snapshot(payload)
    assert restored.state.pending_decision == engine.state.pending_decision
    assert state_digest(restored) == state_digest(engine)
    assert dump_snapshot(restored, indent=None) == payload


def test_snapshot_v2_migrates_to_v3_without_inventing_a_decision() -> None:
    legacy = as_v2(make_engine())
    restored = load_snapshot(legacy)
    assert restored.state.pending_decision is None
    assert json.loads(dump_snapshot(restored))["body"]["schema_version"] == "3"


def test_snapshot_v2_migration_adds_only_pending_decision_and_recalculates_digest(
) -> None:
    legacy_body = as_v2(make_engine())["body"]
    legacy_state = deepcopy(legacy_body["state"])

    migrated = migrate_document("snapshot", legacy_body, "3")

    expected_state = deepcopy(legacy_state)
    expected_state["fields"]["pending_decision"] = None
    assert migrated["state"] == expected_state
    assert migrated["state_digest"] == hashlib.sha256(
        canonical_json(expected_state).encode("utf-8")
    ).hexdigest()


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        pytest.param(
            lambda body: body.pop("state"),
            "GameState válido",
            id="missing-state",
        ),
        pytest.param(
            lambda body: body.__setitem__("state", []),
            "GameState válido",
            id="state-not-dict",
        ),
        pytest.param(
            lambda body: body["state"].__setitem__("$type", "PlayerState"),
            "GameState válido",
            id="wrong-state-discriminator",
        ),
        pytest.param(
            lambda body: body["state"].pop("fields"),
            "forma esperada",
            id="missing-fields",
        ),
        pytest.param(
            lambda body: body["state"].__setitem__("fields", []),
            "forma esperada",
            id="fields-not-dict",
        ),
        pytest.param(
            lambda body: body["state"]["fields"].__setitem__(
                "pending_decision", None
            ),
            "forma esperada",
            id="pending-decision-already-present",
        ),
    ],
)
def test_snapshot_v2_migration_rejects_invalid_shapes_without_mutating_input(
    mutate: Callable[[dict[str, object]], object], message: str
) -> None:
    legacy_body = as_v2(make_engine())["body"]
    mutate(legacy_body)
    before = deepcopy(legacy_body)

    with pytest.raises(ValueError, match=message):
        migrate_document("snapshot", legacy_body, "3")

    assert legacy_body == before


def test_snapshot_migration_rejects_unknown_schema_without_mutating_input() -> None:
    body = {"schema_version": "99", "nested": {"items": [1, 2]}}
    before = deepcopy(body)

    with pytest.raises(ValueError, match="No existe migración"):
        migrate_document("snapshot", body, "3")

    assert body == before


def test_repeated_migration_of_v3_result_is_equal_and_does_not_mutate_inputs() -> None:
    legacy_body = as_v2(make_engine())["body"]
    legacy_before = deepcopy(legacy_body)
    migrated = migrate_document("snapshot", legacy_body, "3")
    migrated_before = deepcopy(migrated)

    repeated = migrate_document("snapshot", migrated, "3")

    assert legacy_body == legacy_before
    assert migrated == migrated_before
    assert repeated == migrated
    assert repeated is not migrated


@pytest.mark.parametrize("specialized", ["search", "move-replacement"])
def test_snapshot_v2_migration_does_not_infer_from_specialized_pending_models(
    specialized: str,
) -> None:
    engine = make_engine()
    if specialized == "search":
        card_id = engine.state.players["A"].zones[Zone.DECK][0]
        engine.state.pending_search = PendingSearch(
            StackItem("migration-search", "A", card_id, ()),
            0,
            "A",
            ZoneTarget("A", Zone.DECK),
            (card_id,),
            1,
            1,
            Zone.HAND,
            True,
            False,
        )
    else:
        card_id = engine.state.players["A"].zones[Zone.DECK][0]
        engine.state.pending_move_replacement = PendingMoveReplacement(
            Concede("A"),
            "A",
            card_id,
            MoveReason.DESTROY,
            (0,),
            (Zone.EXILE,),
            "A",
        )
    legacy_body = as_v2(engine)["body"]
    legacy_fields = deepcopy(legacy_body["state"]["fields"])

    migrated = migrate_document("snapshot", legacy_body, "3")
    migrated_fields = migrated["state"]["fields"]

    assert migrated_fields["pending_decision"] is None
    assert {
        key: value
        for key, value in migrated_fields.items()
        if key != "pending_decision"
    } == legacy_fields


def test_migrated_digest_and_envelope_checksum_are_validated_by_load_snapshot() -> None:
    legacy = as_v2(make_engine())
    migrated_body = migrate_document("snapshot", legacy["body"], "3")
    migrated_envelope = {"body": migrated_body, "sha256": checksum(migrated_body)}

    restored = load_snapshot(migrated_envelope)

    assert migrated_body["state_digest"] == state_digest(restored)
    corrupted = deepcopy(migrated_envelope)
    corrupted["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="huella de la instantánea"):
        load_snapshot(corrupted)


def test_019_runtime_digest_includes_pending_decision() -> None:
    first = GameEngine(RuleSet(version="0.19.0"))
    second = GameEngine(RuleSet(version="0.19.0"))
    decks = {"A": test_deck("W0-A"), "B": test_deck("W0-B")}
    first.new_match(decks, seed=902)
    second.new_match(decks, seed=902)

    second.state.pending_decision = decision()

    assert state_digest(first) != state_digest(second)


def test_migration_is_pure_repeatable_and_rejects_unknown_versions() -> None:
    legacy_body = as_v2(make_engine())["body"]
    before = json.loads(json.dumps(legacy_body))
    first = migrate_document("snapshot", legacy_body, "3")
    second = migrate_document("snapshot", first, "3")
    assert legacy_body == before
    assert canonical_json(first) == canonical_json(second)
    with pytest.raises(ValueError, match="No existe migración"):
        migrate_document("snapshot", {"schema_version": "99"}, "3")


def test_golden_snapshots_cover_v2_and_v3_absent_pending_and_closed() -> None:
    for name in ("snapshot-v2-none.json", "snapshot-v3-none.json", "snapshot-v3-pending.json", "snapshot-v3-closed.json"):
        payload = (ARTIFACTS / name).read_text()
        restored = load_snapshot(payload)
        expected = None if "none" in name else decision(closed="closed" in name)
        assert restored.state.pending_decision == expected
        if expected is not None:
            assert "mulligan/v1" not in payload
            assert "setup/mulligan" not in payload


@pytest.mark.parametrize("store_kind", ["memory", "sqlite"])
def test_stores_load_old_db_and_update_to_v3_with_parity(store_kind: str) -> None:
    engine = make_engine()
    legacy = json.dumps(as_v2(engine), sort_keys=True)
    if store_kind == "memory":
        store = InMemoryMatchStore()
        store._records["match"] = (1, legacy)
    else:
        store = SQLiteMatchStore(":memory:")
        with store._connect() as connection:
            connection.execute("INSERT INTO matches(match_id, version, snapshot) VALUES ('match', 1, ?)", (legacy,))
    loaded = store.load("match")
    assert loaded.engine.state.pending_decision is None
    loaded.engine.state.pending_decision = decision()
    assert store.save("match", loaded.engine, expected_version=1) == 2
    assert store.load("match").engine.state.pending_decision == decision()


def test_sqlite_invalid_snapshot_rolls_back_and_repeated_startup_keeps_one_table() -> None:
    with TemporaryDirectory() as directory:
        path = Path(directory) / "matches.db"
        store = SQLiteMatchStore(path)
        store.create("winner", make_engine())
        with sqlite3.connect(path) as connection:
            original = connection.execute("SELECT snapshot FROM matches WHERE match_id='winner'").fetchone()[0]
            with pytest.raises(sqlite3.IntegrityError):
                with connection:
                    connection.execute("UPDATE matches SET snapshot = NULL WHERE match_id='winner'")
            assert connection.execute("SELECT snapshot FROM matches WHERE match_id='winner'").fetchone()[0] == original
        store.close()
        SQLiteMatchStore(path).close()
        with sqlite3.connect(path) as connection:
            assert [row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")] == ["matches"]


def assert_snapshot_cas_race(
    store: InMemoryMatchStore | SQLiteMatchStore,
) -> None:
    store.create("race", make_engine())
    candidates = [store.load("race").engine for _ in range(2)]
    candidates[0].state.pending_decision = decision()
    candidates[0].state.players["A"].wounds = 1
    candidates[1].state.pending_decision = decision(closed=True)
    candidates[1].state.players["A"].wounds = 2
    candidate_snapshots = {
        dump_snapshot(candidate, indent=None) for candidate in candidates
    }
    barrier = Barrier(2)

    def save(candidate: GameEngine) -> int | VersionConflict:
        barrier.wait()
        try:
            return store.save("race", candidate, expected_version=1)
        except VersionConflict as exc:
            return exc

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(save, candidates))

    assert sum(outcome == 2 for outcome in outcomes) == 1
    assert sum(isinstance(outcome, VersionConflict) for outcome in outcomes) == 1
    winning = store.load("race")
    assert winning.version == 2
    assert dump_snapshot(winning.engine, indent=None) in candidate_snapshots


def test_two_in_memory_writers_with_same_expected_version_have_one_winner(
) -> None:
    assert_snapshot_cas_race(InMemoryMatchStore())


def test_two_sqlite_writers_with_same_expected_version_have_one_winner() -> None:
    with TemporaryDirectory() as directory:
        path = Path(directory) / "race.db"
        with SQLiteMatchStore(path) as store:
            assert_snapshot_cas_race(store)


def test_replay_remains_v2_until_w1_lifecycle_exists() -> None:
    assert REPLAY_SCHEMA_VERSION == "2"
