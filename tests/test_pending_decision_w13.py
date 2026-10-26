from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from card_duel_engine.domain import ExecutedCommand
from card_duel_engine.persistence.codec import canonical_json
from card_duel_engine.persistence.migrations import migrate_document
from card_duel_engine.persistence.replay import dump_replay
from card_duel_engine.persistence.snapshot import load_snapshot

from test_pending_decision_w11 import make_engine, open_decision


GOLDEN_V4 = Path(__file__).parent / "artifacts/pending-decision-w1.3/snapshot-v4-lifecycle.json"


def _checksum(body: dict[str, object]) -> str:
    return hashlib.sha256(canonical_json(body).encode("utf-8")).hexdigest()


def test_v4_golden_migrates_to_current_snapshot_and_preserves_lifecycle() -> None:
    engine = make_engine()
    open_decision(engine)
    engine._close_pending_decision("decision:test:1", "A", "opaque-b", 0)
    restored = load_snapshot(GOLDEN_V4.read_text(encoding="utf-8"))
    assert restored.state is not None and engine.state is not None
    assert restored.state.history == engine.state.history
    assert restored.state.zone_transition_history == []
    assert restored.state.zone_transition_prefix_complete is False
    with pytest.raises(ValueError, match="prefijo causal"):
        dump_replay(restored)


def test_v3_migration_wraps_only_commands_and_marks_pending_prefix_incomplete() -> None:
    historical = json.loads(
        (Path(__file__).parent / "artifacts/pending-decision-w0/snapshot-v3-pending.json")
        .read_text(encoding="utf-8")
    )
    restored = load_snapshot(historical)
    assert restored.state is not None
    assert all(isinstance(entry, ExecutedCommand) for entry in restored.state.history)
    assert [
        entry.command
        for entry in restored.state.history
        if isinstance(entry, ExecutedCommand)
    ] == restored.state.command_history
    assert restored.state.history_prefix_complete is False
    with pytest.raises(ValueError, match="prefijo completo"):
        dump_replay(restored)


@pytest.mark.parametrize("unexpected", ["history", "history_prefix_complete"])
def test_v3_migration_rejects_ambiguous_new_history_fields(unexpected: str) -> None:
    document = json.loads(
        (Path(__file__).parent / "artifacts/pending-decision-w0/snapshot-v3-none.json")
        .read_text(encoding="utf-8")
    )
    body = deepcopy(document["body"])
    body["state"]["fields"][unexpected] = [] if unexpected == "history" else True
    with pytest.raises(ValueError, match="ambigua"):
        migrate_document("snapshot", body, "4")


def test_v1_v2_v3_chain_remains_readable() -> None:
    for relative in (
        "artifacts/0.19.0/snapshot-v1.json",
        "artifacts/pending-decision-w0/snapshot-v2-none.json",
        "artifacts/pending-decision-w0/snapshot-v3-none.json",
    ):
        restored = load_snapshot((Path(__file__).parent / relative).read_text())
        assert restored.state is not None
        assert restored.state.history_prefix_complete is True
        assert restored.state.zone_transition_prefix_complete is False
