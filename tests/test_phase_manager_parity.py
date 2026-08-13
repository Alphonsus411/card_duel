"""Paridad diferencial de la coordinación extraída a ``PhaseManager``."""

from copy import deepcopy

import pytest

from card_duel_engine import GameEngine, RuleSet
from card_duel_engine.domain.enums import MatchStatus, Phase, Zone
from card_duel_engine.domain.errors import IllegalAction
from card_duel_engine.domain.models import PhaseSuppression
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
