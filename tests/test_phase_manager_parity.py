"""Paridad diferencial de la coordinación extraída a ``PhaseManager``.

Esta suite es la evidencia ejecutable citada por el diagnóstico, el documento
de refactor y el informe de cierre 0.20.1. Sus comparaciones cubren el estado
persistible completo, el orden de eventos y las acciones legales sin modificar
la implementación situada bajo ``src/card_duel_engine``.
"""

from copy import deepcopy

import pytest

from card_duel_engine import GameEngine, RuleSet
from card_duel_engine.domain import (
    CardDefinition,
    CardKind,
    ContinuousEffectDefinition,
)
from card_duel_engine.domain.enums import MatchStatus, Phase, Zone
from card_duel_engine.domain.errors import IllegalAction
from card_duel_engine.domain.models import (
    CombatState,
    PhaseSuppression,
    StackItem,
    TimedModifier,
)
from card_duel_engine.engine.game import EngineSemantics
from card_duel_engine.persistence.codec import encode_value

from fixtures import test_deck


def _engine(*, hand_limit: int = 7) -> GameEngine:
    engine = GameEngine(RuleSet(hand_limit=hand_limit))
    engine.new_match({"A": test_deck("A"), "B": test_deck("B")}, seed=19)
    return engine


def _previous_finish_turn(engine: GameEngine) -> None:
    state = engine._require_running_state()
    engine._cleanup_end_of_turn()
    state.turn_serial += 1
    state.active_player_index = (state.active_player_index + 1) % len(state.turn_order)
    if state.active_player_index == 0:
        state.turn_number += 1


def _previous_enter_phase_or_skip(engine: GameEngine, phase: Phase) -> None:
    state = engine._require_running_state()
    skipped = 0
    while engine._phase_is_suppressed(state.active_player_id, phase):
        engine._emit("PHASE_SKIPPED", state.active_player_id, payload={"phase": phase.name})
        skipped += 1
        if skipped > len(engine.rules.phase_sequence) * len(state.turn_order):
            state.status = MatchStatus.BLOCKED
            engine._emit("ALL_PHASES_SUPPRESSED")
            return
        if phase is Phase.DISCARD:
            _previous_finish_turn(engine)
            phase = Phase.DRAW
        else:
            index = engine.rules.phase_sequence.index(phase)
            phase = engine.rules.phase_sequence[index + 1]
    engine._enter_phase(phase)


def _previous_advance_phase(engine: GameEngine, player_id: str) -> None:
    state = engine._require_running_state()
    if player_id != state.active_player_id:
        raise IllegalAction("Solo el jugador activo puede avanzar la fase")
    if state.stack or not state.phase_priority_complete:
        raise IllegalAction("La ventana de prioridad debe estar cerrada")
    if state.phase is Phase.COMBAT and state.combat and not state.combat.resolved:
        raise IllegalAction("El combate declarado debe resolverse")
    if state.phase is Phase.DISCARD:
        if len(state.players[player_id].zones[Zone.HAND]) > engine.rules.hand_limit:
            raise IllegalAction("Debe descartarse hasta el límite de mano")
        _previous_finish_turn(engine)
        _previous_enter_phase_or_skip(engine, Phase.DRAW)
        return
    index = engine.rules.phase_sequence.index(state.phase)
    _previous_enter_phase_or_skip(engine, engine.rules.phase_sequence[index + 1])


def _observable(engine: GameEngine) -> object:
    return encode_value(engine._require_state())


def _assert_transition_parity(extracted: GameEngine, previous: GameEngine) -> None:
    """Compara todo el estado persistible y las vistas legales ordenadas."""
    assert _observable(extracted) == _observable(previous)
    for player_id in extracted.state.turn_order:
        assert extracted.legal_actions(player_id) == previous.legal_actions(player_id)


def _advance_both(extracted: GameEngine, previous: GameEngine) -> None:
    before_extracted = {
        player_id: extracted.legal_actions(player_id)
        for player_id in extracted.state.turn_order
    }
    before_previous = {
        player_id: previous.legal_actions(player_id)
        for player_id in previous.state.turn_order
    }
    assert before_extracted == before_previous
    extracted._advance_phase(extracted.state.active_player_id)
    _previous_advance_phase(previous, previous.state.active_player_id)
    _assert_transition_parity(extracted, previous)


@pytest.mark.parametrize("semantics", [EngineSemantics.CURRENT, EngineSemantics.LEGACY_019])
@pytest.mark.parametrize("phase", [Phase.DRAW, Phase.EFFECTS, Phase.DISCARD])
def test_advance_matches_previous_body(semantics: EngineSemantics, phase: Phase) -> None:
    extracted = _engine(hand_limit=20)
    extracted._semantics = semantics
    extracted.state.phase = phase
    extracted.state.phase_priority_complete = True
    previous = deepcopy(extracted)

    extracted._advance_phase("A")
    _previous_advance_phase(previous, "A")

    assert _observable(extracted) == _observable(previous)


def test_next_occurrence_skip_matches_previous_body() -> None:
    extracted = _engine()
    extracted.state.phase_suppressions.append(PhaseSuppression("A", Phase.MAINTENANCE))
    extracted.state.phase_priority_complete = True
    previous = deepcopy(extracted)

    extracted._advance_phase("A")
    _previous_advance_phase(previous, "A")

    assert _observable(extracted) == _observable(previous)
    assert extracted.state.phase is Phase.EFFECTS
    assert [event.event_type for event in extracted.state.event_log[-2:]] == [
        "PHASE_SKIPPED",
        "PHASE_STARTED",
    ]


@pytest.mark.parametrize(
    ("player_id", "priority_complete", "message"),
    [("B", True, "jugador activo"), ("A", False, "prioridad")],
)
def test_rejections_match_previous_body(
    player_id: str, priority_complete: bool, message: str
) -> None:
    extracted = _engine()
    extracted.state.phase_priority_complete = priority_complete
    previous = deepcopy(extracted)

    with pytest.raises(IllegalAction, match=message):
        extracted._advance_phase(player_id)
    with pytest.raises(IllegalAction, match=message):
        _previous_advance_phase(previous, player_id)

    assert _observable(extracted) == _observable(previous)


def test_manager_has_no_independent_state() -> None:
    engine = _engine()
    assert vars(engine._phases) == {"_context": engine}


def test_two_compatible_next_occurrence_suppressions_are_both_consumed() -> None:
    extracted = _engine()
    extracted.state.phase = Phase.DRAW
    extracted.state.phase_priority_complete = True
    extracted.state.phase_suppressions.extend(
        [
            PhaseSuppression("A", Phase.MAINTENANCE),
            PhaseSuppression("A", Phase.MAINTENANCE),
        ]
    )
    previous = deepcopy(extracted)

    _advance_both(extracted, previous)

    assert extracted.state.phase is Phase.EFFECTS
    assert extracted.state.phase_suppressions == []
    assert [event.event_type for event in extracted.state.event_log[-2:]] == [
        "PHASE_SKIPPED",
        "PHASE_STARTED",
    ]


def test_continuous_suppression_coexists_with_stored_suppression() -> None:
    extracted = _engine()
    source_id = extracted.state.players["A"].zones[Zone.HAND][0]
    source = extracted.state.cards[source_id]
    extracted.catalog._cards[source.definition_id] = CardDefinition(
        source.definition_id,
        "Fuente continua",
        CardKind.ARTIFACT,
        0,
        continuous_effects=(
            ContinuousEffectDefinition(
                suppressed_phases=frozenset({Phase.MAINTENANCE})
            ),
        ),
    )
    extracted._move_card(source_id, Zone.BATTLEFIELD, "A")
    extracted.state.phase = Phase.DRAW
    extracted.state.phase_priority_complete = True
    extracted.state.phase_suppressions.append(
        PhaseSuppression("A", Phase.MAINTENANCE)
    )
    previous = deepcopy(extracted)

    _advance_both(extracted, previous)

    assert extracted.state.phase is Phase.EFFECTS
    assert extracted.state.phase_suppressions == []


def test_discard_cleanup_rotation_draw_expires_end_of_turn_item() -> None:
    extracted = _engine(hand_limit=20)
    extracted.state.phase = Phase.DISCARD
    extracted.state.phase_priority_complete = True
    extracted.state.phase_suppressions.append(
        PhaseSuppression(
            "A", Phase.COMBAT, extracted.state.turn_serial, remaining_occurrences=None
        )
    )
    previous = deepcopy(extracted)

    _advance_both(extracted, previous)

    assert extracted.state.active_player_id == "B"
    assert extracted.state.phase is Phase.DRAW
    assert extracted.state.turn_serial == 2
    assert extracted.state.phase_suppressions == []
    assert [event.event_type for event in extracted.state.event_log[-3:]] == [
        "END_OF_TURN_CLEANUP",
        "PHASE_STARTED",
        "CARD_DRAWN",
    ]


def test_three_player_rotation_a_b_c_a() -> None:
    extracted = GameEngine(RuleSet(hand_limit=20, minimum_players=3))
    extracted.new_match(
        {player_id: test_deck(player_id) for player_id in ("A", "B", "C")},
        seed=19,
    )

    for expected_player in ("B", "C", "A"):
        extracted.state.phase = Phase.DISCARD
        extracted.state.phase_priority_complete = True
        previous = deepcopy(extracted)
        _advance_both(extracted, previous)
        assert extracted.state.active_player_id == expected_player

    assert extracted.state.turn_serial == 4
    assert extracted.state.turn_number == 2


def test_enter_draw_without_available_card_matches_previous_body() -> None:
    extracted = _engine(hand_limit=20)
    for zone in (Zone.DECK, Zone.DISCARD):
        for card_id in tuple(extracted.state.players["B"].zones[zone]):
            extracted._move_card(card_id, Zone.HAND, "B")
    extracted.state.phase = Phase.DISCARD
    extracted.state.phase_priority_complete = True
    previous = deepcopy(extracted)

    _advance_both(extracted, previous)

    assert extracted.state.active_player_id == "B"
    assert extracted.state.phase is Phase.DRAW
    assert not any(
        event.event_type == "CARD_DRAWN"
        for event in extracted.state.event_log[-3:]
    )


def test_draw_recycles_discard_deterministically() -> None:
    extracted = _engine(hand_limit=20)
    player = extracted.state.players["B"]
    for card_id in tuple(player.zones[Zone.DECK]):
        extracted._move_card(card_id, Zone.DISCARD, "B")
    discard_before = tuple(player.zones[Zone.DISCARD])
    extracted.state.phase = Phase.DISCARD
    extracted.state.phase_priority_complete = True
    previous = deepcopy(extracted)

    _advance_both(extracted, previous)

    assert extracted.state.players["B"].zones[Zone.HAND][-1] in discard_before
    assert [event.event_type for event in extracted.state.event_log[-4:]] == [
        "END_OF_TURN_CLEANUP",
        "PHASE_STARTED",
        "DISCARD_RECYCLED",
        "CARD_DRAWN",
    ]


def test_cleanup_removes_a_really_expirable_modifier() -> None:
    extracted = _engine(hand_limit=20)
    target = extracted.state.players["A"].zones[Zone.HAND][0]
    extracted.state.timed_modifiers.append(
        TimedModifier("temporary", target, 3, extracted.state.turn_serial)
    )
    extracted.state.phase = Phase.DISCARD
    extracted.state.phase_priority_complete = True
    previous = deepcopy(extracted)

    _advance_both(extracted, previous)

    assert extracted.state.timed_modifiers == []


def test_all_phases_suppressed_uses_strict_greater_than_guard() -> None:
    extracted = _engine()
    extracted.state.phase = Phase.DRAW
    extracted.state.phase_priority_complete = True
    extracted.state.phase_suppressions.extend(
        PhaseSuppression("A", phase, remaining_occurrences=None)
        for phase in extracted.rules.phase_sequence
    )
    extracted.state.phase_suppressions.extend(
        PhaseSuppression("B", phase, remaining_occurrences=None)
        for phase in extracted.rules.phase_sequence
    )
    previous = deepcopy(extracted)

    _advance_both(extracted, previous)

    threshold = len(extracted.rules.phase_sequence) * len(extracted.state.turn_order)
    skipped = [
        event for event in extracted.state.event_log if event.event_type == "PHASE_SKIPPED"
    ]
    assert extracted.state.status is MatchStatus.BLOCKED
    assert len(skipped) == threshold + 1
    assert extracted.state.event_log[-1].event_type == "ALL_PHASES_SUPPRESSED"


@pytest.mark.parametrize("entrypoint", ["advance", "finish", "enter"])
def test_finished_state_rejections_match_at_phase_boundaries(entrypoint: str) -> None:
    extracted = _engine()
    extracted.state.status = MatchStatus.FINISHED
    previous = deepcopy(extracted)
    before_extracted = _observable(extracted)
    before_previous = _observable(previous)

    current_call = {
        "advance": lambda: extracted._advance_phase("A"),
        "finish": extracted._finish_turn,
        "enter": lambda: extracted._enter_phase_or_skip(Phase.DRAW),
    }[entrypoint]
    historical_call = {
        "advance": lambda: _previous_advance_phase(previous, "A"),
        "finish": lambda: _previous_finish_turn(previous),
        "enter": lambda: _previous_enter_phase_or_skip(previous, Phase.DRAW),
    }[entrypoint]

    with pytest.raises(Exception) as current_error:
        current_call()
    with pytest.raises(Exception) as historical_error:
        historical_call()

    assert type(current_error.value) is type(historical_error.value)
    assert str(current_error.value) == str(historical_error.value)
    assert _observable(extracted) == before_extracted
    assert _observable(previous) == before_previous
    assert _observable(extracted) == _observable(previous)


def test_unresolved_combat_rejection_matches_without_mutation() -> None:
    extracted = _engine()
    attacker = extracted.state.players["A"].zones[Zone.HAND][0]
    extracted.state.phase = Phase.COMBAT
    extracted.state.combat = CombatState("A", "B", (attacker,))
    extracted.state.phase_priority_complete = True
    previous = deepcopy(extracted)
    before = _observable(extracted)

    with pytest.raises(IllegalAction) as current_error:
        extracted._advance_phase("A")
    with pytest.raises(IllegalAction) as historical_error:
        _previous_advance_phase(previous, "A")

    assert type(current_error.value) is type(historical_error.value)
    assert str(current_error.value) == str(historical_error.value)
    assert _observable(extracted) == before == _observable(previous)


def test_nonempty_stack_rejection_matches_without_mutation() -> None:
    extracted = _engine()
    source = extracted.state.players["A"].zones[Zone.HAND][0]
    extracted.state.stack.append(StackItem("pending", "A", source, ()))
    extracted.state.phase_priority_complete = True
    previous = deepcopy(extracted)
    before = _observable(extracted)

    with pytest.raises(IllegalAction) as current_error:
        extracted._advance_phase("A")
    with pytest.raises(IllegalAction) as historical_error:
        _previous_advance_phase(previous, "A")

    assert type(current_error.value) is type(historical_error.value)
    assert str(current_error.value) == str(historical_error.value)
    assert _observable(extracted) == before == _observable(previous)


@pytest.mark.parametrize(
    ("priority_complete", "priority_player"),
    [(False, "A"), (True, "B")],
)
def test_priority_boundaries_match_previous_body(
    priority_complete: bool, priority_player: str
) -> None:
    extracted = _engine()
    extracted.state.phase_priority_complete = priority_complete
    extracted.state.priority_player_id = priority_player
    previous = deepcopy(extracted)

    if not priority_complete:
        before = _observable(extracted)
        with pytest.raises(IllegalAction) as current_error:
            extracted._advance_phase("A")
        with pytest.raises(IllegalAction) as historical_error:
            _previous_advance_phase(previous, "A")
        assert type(current_error.value) is type(historical_error.value)
        assert str(current_error.value) == str(historical_error.value)
        assert _observable(extracted) == before == _observable(previous)
    else:
        _advance_both(extracted, previous)
        assert extracted.state.priority_player_id == "A"


def test_legacy_019_suppression_across_turn_change_matches_previous_body() -> None:
    extracted = _engine(hand_limit=20)
    extracted._semantics = EngineSemantics.LEGACY_019
    extracted.state.phase = Phase.DISCARD
    extracted.state.phase_priority_complete = True
    extracted.state.phase_suppressions.append(PhaseSuppression("B", Phase.DRAW))
    previous = deepcopy(extracted)

    _advance_both(extracted, previous)

    assert extracted.state.active_player_id == "B"
    assert extracted.state.phase is Phase.MAINTENANCE
    assert extracted.state.phase_suppressions == []
