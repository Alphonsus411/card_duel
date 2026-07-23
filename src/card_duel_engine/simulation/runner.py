from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from ..controllers.base import DecisionRequest, PlayerController
from ..domain.enums import MatchStatus
from ..engine.game import GameEngine


@dataclass(frozen=True)
class SimulationReport:
    commands_executed: int
    turn_reached: int
    status: MatchStatus
    winner_ids: tuple[str, ...]
    event_count: int


def run_headless(
    engine: GameEngine,
    controllers: Mapping[str, PlayerController],
    *,
    max_commands: int = 1_000,
) -> SimulationReport:
    """Ejecuta decisiones sin interfaz y conserva el registro para depuración."""

    executed = 0
    while engine.state.status is MatchStatus.RUNNING and executed < max_commands:
        combat = engine.state.combat
        if combat is not None and not combat.blockers_declared and not engine.state.stack:
            player_id = combat.defending_player_id
        elif engine.state.phase_priority_complete and not engine.state.stack:
            player_id = engine.state.active_player_id
        else:
            player_id = engine.state.priority_player_id
        controller = controllers[player_id]
        request = DecisionRequest(
            observation=engine.observe(player_id),
            legal_actions=engine.legal_actions(player_id),
        )
        engine.execute(controller.choose_action(request))
        executed += 1

    if engine.state.status is MatchStatus.RUNNING:
        engine.state.status = MatchStatus.BLOCKED

    return SimulationReport(
        commands_executed=executed,
        turn_reached=engine.state.turn_number,
        status=engine.state.status,
        winner_ids=engine.state.winner_ids,
        event_count=len(engine.state.event_log),
    )
