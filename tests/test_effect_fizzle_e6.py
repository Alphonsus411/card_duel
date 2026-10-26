from __future__ import annotations

from copy import deepcopy

import pytest

from card_duel_engine import GameEngine
from card_duel_engine.catalog import CardCatalog
from card_duel_engine.domain.enums import (
    CardKind,
    EffectKind,
    MatchStatus,
    Phase,
    RevealExhaustionPolicy,
    TargetMode,
    Zone,
)
from card_duel_engine.domain.models import (
    CardDefinition,
    CardFilter,
    CardInstance,
    EffectDefinition,
    GameState,
    PlayerState,
    StackItem,
    TextPatchDefinition,
)


_PLAYER_KINDS = frozenset(
    {
        EffectKind.DEAL_WOUNDS,
        EffectKind.HEAL_WOUNDS,
        EffectKind.GAIN_STEPS,
        EffectKind.DRAW_CARDS,
        EffectKind.PREVENT_WOUNDS,
        EffectKind.SKIP_PHASE,
    }
)
_PERMANENT_KINDS = frozenset(EffectKind) - _PLAYER_KINDS - {
    EffectKind.DEAL_HARM,
    EffectKind.MOVE_CARDS,
    EffectKind.SEARCH_ZONE,
    EffectKind.SHUFFLE_ZONE,
    EffectKind.REVEAL_UNTIL,
}


def _invalid_target_probe(kind: EffectKind) -> EffectDefinition:
    if kind in _PLAYER_KINDS:
        return EffectDefinition(
            kind,
            1,
            TargetMode.CHOSEN_PLAYER,
            phase=Phase.DRAW if kind is EffectKind.SKIP_PHASE else None,
        )
    if kind in _PERMANENT_KINDS:
        kwargs: dict[str, object] = {"target": TargetMode.CHOSEN_PERMANENT}
        if kind is EffectKind.TRANSFORM_DEFINITION:
            kwargs["transform_definition_id"] = "target"
        if kind is EffectKind.MODIFY_TEXT:
            kwargs["text_patch"] = TextPatchDefinition()
        return EffectDefinition(kind, 1, **kwargs)
    if kind is EffectKind.DEAL_HARM:
        return EffectDefinition(kind, 1, TargetMode.CHOSEN_ENTITY, distributed=True)
    if kind is EffectKind.MOVE_CARDS:
        return EffectDefinition(kind, 1, TargetMode.CHOSEN_ZONE, destination_zone=Zone.HAND)
    if kind is EffectKind.SEARCH_ZONE:
        return EffectDefinition(
            kind,
            0,
            TargetMode.CHOSEN_ZONE,
            destination_zone=Zone.HAND,
            selection_minimum=0,
        )
    if kind is EffectKind.SHUFFLE_ZONE:
        return EffectDefinition(kind, 0, TargetMode.CHOSEN_ZONE)
    if kind is EffectKind.REVEAL_UNTIL:
        return EffectDefinition(
            kind,
            0,
            TargetMode.CHOSEN_ZONE,
            destination_zone=Zone.HAND,
            failure_destination_zone=Zone.DISCARD,
            search_filter=CardFilter(),
            exhaustion_policy=RevealExhaustionPolicy.COMPLETE,
        )
    raise AssertionError(f"EffectKind no clasificado: {kind}")


def _engine() -> tuple[GameEngine, StackItem]:
    source = CardDefinition("source", "Fuente", CardKind.ARTIFACT, 0)
    target = CardDefinition("target", "Objetivo", CardKind.CREATURE, 1, base_strength=1)
    engine = GameEngine(catalog=CardCatalog({"source": source, "target": target}))
    state = GameState(
        ruleset_id=engine.rules.ruleset_id,
        ruleset_version=engine.rules.version,
        players={"A": PlayerState("A"), "B": PlayerState("B")},
        turn_order=("A", "B"),
        cards={
            "source-i": CardInstance("source-i", "source", "A", "A", Zone.BATTLEFIELD),
            "target-i": CardInstance("target-i", "target", "B", "B", Zone.BATTLEFIELD),
        },
        priority_player_id="A",
        phase=Phase.EFFECTS,
        status=MatchStatus.RUNNING,
    )
    state.players["A"].zones[Zone.BATTLEFIELD].append("source-i")
    state.players["B"].zones[Zone.BATTLEFIELD].append("target-i")
    engine.state = state
    return engine, StackItem("e6-stack", "A", "source-i", ())


@pytest.mark.parametrize("effect", tuple(_invalid_target_probe(kind) for kind in EffectKind))
def test_invalid_runtime_target_fizzles_without_state_mutation(
    effect: EffectDefinition,
) -> None:
    engine, item = _engine()
    before = deepcopy(engine.state)

    engine._effects.apply(effect, item, None)

    assert engine.state is not None
    event = engine.state.event_log.pop()
    assert event.event_type == "EFFECT_FIZZLED"
    assert event.payload == {"reason": "invalid_target"}
    assert engine.state == before
