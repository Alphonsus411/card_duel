from __future__ import annotations

import json

import pytest

from card_duel_engine import GameEngine
from card_duel_engine.domain.enums import (
    EffectKind,
    Phase,
    RevealExhaustionPolicy,
    TargetMode,
    Zone,
)
from card_duel_engine.domain.models import (
    CardFilter,
    EffectDefinition,
    StackItem,
    TextPatchDefinition,
)
from card_duel_engine.engine.commands import AdvancePhase, PassPriority, PlayCard
from card_duel_engine.persistence import (
    decode_value,
    dump_replay,
    dump_snapshot,
    encode_value,
    load_snapshot,
    replay_from_log,
    state_digest,
)

from fixtures import quick_damage_fixture, test_deck


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
_PERMANENT_KINDS = frozenset(
    {
        EffectKind.DEAL_DAMAGE,
        EffectKind.MODIFY_STRENGTH,
        EffectKind.TAP,
        EffectKind.UNTAP,
        EffectKind.DESTROY,
        EffectKind.PREVENT_DAMAGE,
        EffectKind.BECOME_CREATURE,
        EffectKind.ADD_REGENERATION,
        EffectKind.CHANGE_CONTROL,
        EffectKind.COPY_DEFINITION,
        EffectKind.TRANSFORM_DEFINITION,
        EffectKind.MODIFY_TEXT,
    }
)

def _definition_for(kind: EffectKind) -> EffectDefinition:
    if kind in _PLAYER_KINDS:
        return EffectDefinition(
            kind, 1, phase=Phase.DRAW if kind is EffectKind.SKIP_PHASE else None
        )
    if kind in _PERMANENT_KINDS:
        kwargs: dict[str, object] = {"target": TargetMode.CHOSEN_PERMANENT}
        if kind is EffectKind.MODIFY_STRENGTH:
            return EffectDefinition(kind, -1, **kwargs)
        if kind is EffectKind.TRANSFORM_DEFINITION:
            kwargs["transform_definition_id"] = "target-definition"
        if kind is EffectKind.MODIFY_TEXT:
            kwargs["text_patch"] = TextPatchDefinition(
                grant_keywords=frozenset({"FLYING"})
            )
        return EffectDefinition(kind, 1, **kwargs)
    if kind is EffectKind.DEAL_HARM:
        return EffectDefinition(kind, 1, TargetMode.CHOSEN_ENTITY, distributed=True)
    if kind is EffectKind.MOVE_CARDS:
        return EffectDefinition(kind, 1, TargetMode.CHOSEN_ZONE, destination_zone=Zone.HAND)
    if kind is EffectKind.SEARCH_ZONE:
        return EffectDefinition(
            kind, 0, TargetMode.CHOSEN_ZONE, destination_zone=Zone.HAND,
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


def _close_priority(engine: GameEngine) -> None:
    for _ in engine.state.turn_order:
        engine.execute(PassPriority(engine.state.priority_player_id))


def _advance_to_effects(engine: GameEngine) -> None:
    while engine.state.phase is not Phase.EFFECTS:
        _close_priority(engine)
        engine.execute(AdvancePhase(engine.state.active_player_id))


def test_effect_definitions_round_trip_for_the_closed_vocabulary() -> None:
    definitions = tuple(_definition_for(kind) for kind in EffectKind)

    assert decode_value(encode_value(definitions)) == definitions


def test_snapshot_round_trip_preserves_effects_nested_in_catalog_and_stack() -> None:
    definitions = tuple(_definition_for(kind) for kind in EffectKind)
    source = quick_damage_fixture("E4-SOURCE")
    target = quick_damage_fixture("E4-TARGET")
    engine = GameEngine()
    engine.new_match({"A": [source, *test_deck("E4-A")], "B": [target, *test_deck("E4-B")]}, seed=403)

    # El catálogo cubre todas las primitivas y la pila conserva el mismo lote
    # sin resolverlo: ambos son portadores persistidos de EffectDefinition.
    engine.catalog.register(
        type(source)(
            card_id="E4-ALL-EFFECTS",
            name="Cobertura E4",
            kind=source.kind,
            cost=0,
            permanent=False,
            transmutable=False,
            effects=definitions,
            set_id="test-e4",
        )
    )
    engine.state.stack.append(
        StackItem("e4-stack", "A", next(iter(engine.state.cards)), definitions)
    )

    restored = load_snapshot(dump_snapshot(engine, indent=None))

    assert restored.catalog.get("E4-ALL-EFFECTS").effects == definitions
    assert restored.state.stack[-1].effects == definitions
    assert state_digest(restored) == state_digest(engine)


def test_replay_round_trip_replays_an_effectful_card_without_schema_change() -> None:
    # Las nueve cartas distintas evitan depender de mutaciones fuera del historial.
    a_deck = [quick_damage_fixture(f"E4-A-{index}") for index in range(9)]
    b_deck = test_deck("E4-B", 9)
    engine = GameEngine()
    engine.new_match({"A": a_deck, "B": b_deck}, seed=404)
    _advance_to_effects(engine)
    engine.state.players["A"].steps = 5
    card_id = engine.state.players["A"].zones[Zone.HAND][0]
    engine.execute(PlayCard("A", card_id, chosen_player_ids=("B",)))
    _close_priority(engine)

    restored = replay_from_log(dump_replay(engine, indent=None))

    assert restored.state.players["B"].wounds == 5
    assert state_digest(restored) == state_digest(engine)


def test_legacy_reveal_fields_are_not_invented_by_compatibility_defaults() -> None:
    legacy = json.loads(json.dumps(encode_value(_definition_for(EffectKind.REVEAL_UNTIL))))
    del legacy["fields"]["failure_destination_zone"]
    del legacy["fields"]["exhaustion_policy"]

    with pytest.raises(ValueError, match="Revelar hasta necesita"):
        decode_value(legacy)
