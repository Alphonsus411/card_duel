from __future__ import annotations

import copy
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from benchmarks.benchmark_action_options import (
    ENGINE_VERSION,
    _cases,
    _metadata,
    _profile_legal_actions,
)
from benchmarks.fixtures import SMALL, build_scenario, build_trigger_scenario, canonical_state
from card_duel_engine import EngineSemantics


def test_controlled_fixture_exercises_all_direct_enumeration_dimensions() -> None:
    engine = build_scenario(SMALL, limit=128)
    plays = engine._legal_plays("A")
    source = next(
        card_id for card_id, card in engine.state.cards.items()
        if card.definition_id == "BENCH_ABILITY"
    )
    activations = engine._legal_ability_activations("A", source)
    trigger_engine = build_trigger_scenario(SMALL, limit=128, targets_locked=False)
    triggers = trigger_engine._trigger_target_commands(
        "A", trigger_engine.state.pending_triggers[0]
    )

    play_source = next(
        card_id for card_id, card in engine.state.cards.items()
        if card.definition_id == "BENCH_PLAY"
    )
    combined_play = next(
        command for command in plays
        if command.card_id == play_source and command.discard_card_ids
    )
    assert combined_play.sacrifice_card_ids
    assert combined_play.chosen_player_ids
    assert combined_play.chosen_card_ids
    assert combined_play.chosen_zone_targets
    assert combined_play.allocations

    combined_activation = activations[0]
    assert combined_activation.discard_card_ids
    assert combined_activation.sacrifice_card_ids
    assert combined_activation.chosen_player_ids
    assert combined_activation.chosen_card_ids
    assert combined_activation.chosen_zone_targets
    assert combined_activation.allocations

    combined_trigger = triggers[0]
    assert combined_trigger.chosen_player_ids
    assert combined_trigger.chosen_card_ids
    assert combined_trigger.chosen_zone_targets
    assert combined_trigger.allocations


def test_quick_matrix_keeps_semantics_and_limits_separate() -> None:
    cases = _cases("quick")
    names = {case.name for case in cases}
    for semantics in EngineSemantics:
        assert f"legal_plays/{semantics.name.lower()}/small" in names
        assert f"legal_ability_activations/{semantics.name.lower()}/small" in names
        assert f"trigger_target_commands/{semantics.name.lower()}/small" in names
        for limit in (8, 32, 128, 512):
            assert f"legal_actions/{semantics.name.lower()}/small/limit-{limit}" in names


def test_deepcopy_fixture_is_equivalent_distinct_and_non_mutating() -> None:
    engine = build_scenario(SMALL)
    original = engine.state
    stable = canonical_state(original)
    cloned = copy.deepcopy(original)

    assert canonical_state(original) == stable
    assert canonical_state(cloned) == stable
    assert cloned is not original


def test_benchmark_metadata_and_cprofile_are_comparable() -> None:
    metadata = _metadata("quick")
    assert metadata["engine_version"] == ENGINE_VERSION == "0.20.1"
    assert metadata["profile"] == "quick"
    assert "timestamp" not in metadata
    assert metadata["hardware"]["machine"]

    profile = _profile_legal_actions(SMALL)
    assert profile["sort"] == "cumulative"
    assert profile["function_limit"] == 20
    assert profile["result"]["count"] > 0
    assert len(profile["result"]["sha256"]) == 64
    assert "function calls" in profile["text"]
