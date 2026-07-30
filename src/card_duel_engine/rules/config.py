from __future__ import annotations

from dataclasses import dataclass

from ..domain.enums import Phase


@dataclass(frozen=True)
class RuleSet:
    ruleset_id: str = "universal"
    version: str = "0.19.0"
    initial_hand_size: int = 6
    hand_limit: int = 6
    wound_limit: int = 50
    steps_per_maintenance: int = 5
    recycle_discard: bool = True
    minimum_players: int = 2
    legal_action_enumeration_limit: int = 1_000
    phase_sequence: tuple[Phase, ...] = (
        Phase.DRAW,
        Phase.MAINTENANCE,
        Phase.EFFECTS,
        Phase.COMBAT,
        Phase.LEGENDARY,
        Phase.DISCARD,
    )

    def __post_init__(self) -> None:
        if self.initial_hand_size < 1:
            raise ValueError("La mano inicial debe contener al menos una carta")
        if self.hand_limit < 1 or self.wound_limit < 1:
            raise ValueError("Los límites deben ser positivos")
        if self.steps_per_maintenance < 0:
            raise ValueError("Los Pasos de mantenimiento no pueden ser negativos")
        if self.minimum_players < 2:
            raise ValueError("Una partida requiere al menos dos jugadores")
        if self.legal_action_enumeration_limit < 1:
            raise ValueError("El límite de acciones generadas debe ser positivo")
        expected_phases = (
            Phase.DRAW,
            Phase.MAINTENANCE,
            Phase.EFFECTS,
            Phase.COMBAT,
            Phase.LEGENDARY,
            Phase.DISCARD,
        )
        if self.phase_sequence != expected_phases:
            raise ValueError("La secuencia de fases no coincide con el reglamento")
