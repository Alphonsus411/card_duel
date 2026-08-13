from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from ..domain.enums import MatchStatus, Phase, Zone
from ..domain.errors import IllegalAction
from ..domain.models import GameState


class PhaseContext(Protocol):
    """Operaciones mínimas que la coordinación de fases delega al motor."""

    def _require_running_state(self) -> GameState: ...
    @property
    def _phase_sequence(self) -> Sequence[Phase]: ...
    @property
    def _phase_hand_limit(self) -> int: ...
    def _cleanup_end_of_turn(self) -> None: ...
    def _phase_is_suppressed(self, player_id: str, phase: Phase) -> bool: ...
    def _enter_phase(self, phase: Phase) -> None: ...
    def _emit(
        self,
        event_type: str,
        player_id: str | None = None,
        card_id: str | None = None,
        payload: dict[str, object] | None = None,
    ) -> None: ...


class PhaseManager:
    """Coordina transiciones sin poseer reglas ni estado de dominio."""

    def __init__(self, context: PhaseContext) -> None:
        self._context = context

    def advance_phase(self, player_id: str) -> None:
        context = self._context
        state = context._require_running_state()
        if player_id != state.active_player_id:
            raise IllegalAction("Solo el jugador activo puede avanzar la fase")
        if state.stack or not state.phase_priority_complete:
            raise IllegalAction("La ventana de prioridad debe estar cerrada")
        if state.phase is Phase.COMBAT and state.combat and not state.combat.resolved:
            raise IllegalAction("El combate declarado debe resolverse")
        if state.phase is Phase.DISCARD:
            if len(state.players[player_id].zones[Zone.HAND]) > context._phase_hand_limit:
                raise IllegalAction("Debe descartarse hasta el límite de mano")
            self.finish_turn()
            self.enter_phase_or_skip(Phase.DRAW)
            return
        index = context._phase_sequence.index(state.phase)
        self.enter_phase_or_skip(context._phase_sequence[index + 1])

    def finish_turn(self) -> None:
        context = self._context
        state = context._require_running_state()
        context._cleanup_end_of_turn()
        state.turn_serial += 1
        state.active_player_index = (state.active_player_index + 1) % len(
            state.turn_order
        )
        if state.active_player_index == 0:
            state.turn_number += 1

    def enter_phase_or_skip(self, phase: Phase) -> None:
        context = self._context
        state = context._require_running_state()
        skipped = 0
        while context._phase_is_suppressed(state.active_player_id, phase):
            context._emit(
                "PHASE_SKIPPED",
                state.active_player_id,
                payload={"phase": phase.name},
            )
            skipped += 1
            if skipped > len(context._phase_sequence) * len(state.turn_order):
                state.status = MatchStatus.BLOCKED
                context._emit("ALL_PHASES_SUPPRESSED")
                return
            if phase is Phase.DISCARD:
                self.finish_turn()
                phase = Phase.DRAW
            else:
                index = context._phase_sequence.index(phase)
                phase = context._phase_sequence[index + 1]
        context._enter_phase(phase)
