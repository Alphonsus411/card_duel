from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Mapping

from ..controllers.base import DecisionRequest, PlayerController
from ..domain.enums import MatchStatus
from ..engine.game import GameEngine


class SimulationStopReason(Enum):
    """Motivo, propio del runner, por el que terminó una simulación."""

    MATCH_ENDED = auto()
    COMMAND_LIMIT_REACHED = auto()


@dataclass(frozen=True)
class SimulationReport:
    commands_executed: int
    turn_reached: int
    status: MatchStatus
    winner_ids: tuple[str, ...]
    event_count: int
    stop_reason: SimulationStopReason


def run_headless(
    engine: GameEngine,
    controllers: Mapping[str, PlayerController],
    *,
    max_commands: int = 1_000,
) -> SimulationReport:
    """Ejecuta decisiones sin interfaz y conserva el registro para depuración."""

    if isinstance(max_commands, bool) or not isinstance(max_commands, int):
        raise TypeError("max_commands debe ser un entero positivo")
    if max_commands <= 0:
        raise ValueError("max_commands debe ser un entero positivo")

    state = engine.state
    if state is None:
        raise ValueError("No se puede simular un motor sin una partida iniciada")

    executed = 0
    while state.status is MatchStatus.RUNNING and executed < max_commands:
        combat = state.combat
        if combat is not None and not combat.blockers_declared and not state.stack:
            player_id = combat.defending_player_id
        elif state.phase_priority_complete and not state.stack:
            player_id = state.active_player_id
        else:
            priority_player_id = state.priority_player_id
            if priority_player_id is None:
                raise RuntimeError("La partida en curso no tiene jugador con prioridad")
            player_id = priority_player_id
        controller = controllers[player_id]
        request = DecisionRequest(
            observation=engine.observe(player_id),
            legal_actions=engine.legal_actions(player_id),
        )
        engine.execute(controller.choose_action(request))
        executed += 1

    stop_reason = (
        SimulationStopReason.COMMAND_LIMIT_REACHED
        if state.status is MatchStatus.RUNNING
        else SimulationStopReason.MATCH_ENDED
    )

    return SimulationReport(
        commands_executed=executed,
        turn_reached=state.turn_number,
        status=state.status,
        winner_ids=state.winner_ids,
        event_count=len(state.event_log),
        stop_reason=stop_reason,
    )
