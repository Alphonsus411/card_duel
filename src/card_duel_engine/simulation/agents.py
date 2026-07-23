from __future__ import annotations

import random

from ..controllers.base import DecisionRequest
from ..engine.commands import GameCommand
from ..engine.commands import (
    AdvancePhase,
    ChooseTriggeredTargets,
    DeclareBlockers,
    DiscardCards,
    OrderTriggeredAbilities,
    PassPriority,
    ResolveCombat,
    ResolveSearchChoice,
    ResolveMoveReplacement,
)


class FirstLegalAgent:
    def choose_action(self, request: DecisionRequest) -> GameCommand:
        if not request.legal_actions:
            raise RuntimeError("El agente no recibió acciones legales")
        return request.legal_actions[0]


class RandomLegalAgent:
    def __init__(self, seed: int = 0):
        self._random = random.Random(seed)

    def choose_action(self, request: DecisionRequest) -> GameCommand:
        if not request.legal_actions:
            raise RuntimeError("El agente no recibió acciones legales")
        return self._random.choice(tuple(request.legal_actions))


class PhaseProgressAgent:
    """Agente de diagnóstico que prioriza completar turnos sin conceder."""

    _preferred = (
        ChooseTriggeredTargets,
        ResolveSearchChoice,
        ResolveMoveReplacement,
        OrderTriggeredAbilities,
        DiscardCards,
        DeclareBlockers,
        ResolveCombat,
        AdvancePhase,
        PassPriority,
    )

    def choose_action(self, request: DecisionRequest) -> GameCommand:
        for command_type in self._preferred:
            for action in request.legal_actions:
                if isinstance(action, command_type):
                    return action
        raise RuntimeError("No existe una acción estructural para continuar la simulación")
