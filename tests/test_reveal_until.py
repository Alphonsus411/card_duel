from __future__ import annotations

import pytest

from card_duel_engine import GameEngine, dump_snapshot, load_snapshot
from card_duel_engine.catalog import CardCatalog
from card_duel_engine.domain.enums import (
    CardKind, EffectKind, MatchStatus, Phase, RevealExhaustionPolicy,
    TargetMode, Zone,
)
from card_duel_engine.domain.models import (
    CardDefinition, CardFilter, CardInstance, EffectDefinition, GameState,
    PlayerState, StackItem, ZoneTarget,
)
from card_duel_engine.engine.effects import EffectManager
from card_duel_engine.engine.commands import PassPriority


def _fixture() -> tuple[GameEngine, StackItem, EffectDefinition]:
    definitions = {
        "source": CardDefinition("source", "Fuente", CardKind.ARTIFACT, 0),
        "miss-a": CardDefinition("miss-a", "Fallo A", CardKind.EVENT, 0),
        "miss-b": CardDefinition("miss-b", "Fallo B", CardKind.EVENT, 0),
        "match": CardDefinition(
            "match", "Acierto", CardKind.CREATURE, 0,
            subtypes=frozenset({"scout"}), base_strength=1,
        ),
    }
    engine = GameEngine(catalog=CardCatalog(definitions))
    player = PlayerState("A")
    # La cima es el último elemento: fallo A, fallo B y después acierto.
    player.zones[Zone.DECK] = ["match-i", "miss-b-i", "miss-a-i"]
    state = GameState(
        engine.rules.ruleset_id, engine.rules.version, {"A": player}, ("A",),
        {
            name + "-i": CardInstance(name + "-i", name, "A", "A", Zone.DECK)
            for name in ("match", "miss-a", "miss-b")
        } | {"source-i": CardInstance("source-i", "source", "A", "A", Zone.BATTLEFIELD)},
        priority_player_id="A", phase=Phase.EFFECTS, status=MatchStatus.RUNNING,
    )
    player.zones[Zone.BATTLEFIELD].append("source-i")
    engine.state = state
    effect = EffectDefinition(
        EffectKind.REVEAL_UNTIL, 0, TargetMode.CHOSEN_ZONE,
        destination_zone=Zone.HAND,
        failure_destination_zone=Zone.DISCARD,
        search_filter=CardFilter(subtypes=frozenset({"scout"})),
        exhaustion_policy=RevealExhaustionPolicy.COMPLETE,
    )
    return engine, StackItem("stack-1", "A", "source-i", (effect,)), effect


def test_reveal_until_moves_failures_in_top_order_and_match() -> None:
    engine, item, effect = _fixture()
    EffectManager(engine).apply(effect, item, ZoneTarget("A", Zone.DECK))
    assert engine.state.players["A"].zones[Zone.DISCARD] == ["miss-a-i", "miss-b-i"]
    assert engine.state.players["A"].zones[Zone.HAND] == ["match-i"]
    assert [event.card_id for event in engine.state.event_log if event.event_type == "CARD_REVEALED"] == ["miss-a-i", "miss-b-i", "match-i"]


def test_reveal_until_exhaustion_is_explicit_and_deterministic() -> None:
    left, item, effect = _fixture()
    left.catalog._cards["match"] = CardDefinition("match", "No coincide", CardKind.CREATURE, 0, base_strength=1)
    right = load_snapshot(dump_snapshot(left, indent=None))
    EffectManager(left).apply(effect, item, ZoneTarget("A", Zone.DECK))
    restored_item = right.state.stack[-1] if right.state.stack else item
    EffectManager(right).apply(effect, restored_item, ZoneTarget("A", Zone.DECK))
    assert left.state.players["A"].zones[Zone.DECK] == []
    assert left.state.players["A"].zones[Zone.DISCARD] == ["miss-a-i", "miss-b-i", "match-i"]
    assert dump_snapshot(left, indent=None) == dump_snapshot(right, indent=None)


def test_reveal_until_rejects_incomplete_declarations() -> None:
    with pytest.raises(ValueError, match="filtro mecánico"):
        EffectDefinition(
            EffectKind.REVEAL_UNTIL, 0, TargetMode.CHOSEN_ZONE,
            destination_zone=Zone.HAND, failure_destination_zone=Zone.DISCARD,
            exhaustion_policy=RevealExhaustionPolicy.COMPLETE,
        )
    with pytest.raises(ValueError, match="sólo pertenecen"):
        EffectDefinition(EffectKind.DRAW_CARDS, 1, failure_destination_zone=Zone.DISCARD)


def test_reveal_until_snapshot_roundtrip_preserves_contract() -> None:
    engine, item, _ = _fixture()
    item = StackItem(**{**item.__dict__, "chosen_zone_targets": (ZoneTarget("A", Zone.DECK),)})
    engine.state.stack.append(item)
    payload = dump_snapshot(engine, indent=None)
    restored = load_snapshot(payload)
    assert dump_snapshot(restored, indent=None) == payload
    assert "REVEAL_UNTIL" in payload


def test_reveal_until_failure_does_not_leave_partial_state(monkeypatch: pytest.MonkeyPatch) -> None:
    engine, item, effect = _fixture()
    before = dump_snapshot(engine, indent=None)
    original = engine._move_card
    calls = 0

    def fail_second(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("fallo inyectado")
        return original(*args, **kwargs)

    monkeypatch.setattr(engine, "_move_card", fail_second)
    # La atomicidad pertenece a execute; el gestor no es una frontera transaccional.
    engine.state.stack.append(StackItem(**{**item.__dict__, "chosen_zone_targets": (ZoneTarget("A", Zone.DECK),)}))
    before_resolution = dump_snapshot(engine, indent=None)
    with pytest.raises(RuntimeError, match="fallo inyectado"):
        engine._execute_transaction(PassPriority("A"), ())
    assert dump_snapshot(engine, indent=None) == before_resolution
    assert before != before_resolution
