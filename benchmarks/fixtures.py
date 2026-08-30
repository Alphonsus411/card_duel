"""Fixtures deterministas para benchmarks combinatorios del motor.

Este módulo contiene únicamente contenido sintético de benchmark. No añade cartas
al catálogo productivo ni cambia las reglas del motor. Todas las fábricas crean
un :class:`GameEngine` y un :class:`GameState` nuevos.

``SCENARIO_SEED`` es la única semilla usada al barajar: mantenerla fija hace que
la distribución inicial sea reproducible en cualquier ejecución.
"""

from __future__ import annotations

from enum import StrEnum
from itertools import combinations
from typing import Iterable

from card_duel_engine import EngineSemantics, GameEngine, RuleSet
from card_duel_engine.domain import (
    AbilityDefinition,
    CardDefinition,
    CardKind,
    CompositeCost,
    CostComponent,
    CostMetric,
    CostTerm,
    DynamicCostDefinition,
    EffectDefinition,
    EffectKind,
    Phase,
    TargetAllocation,
    TargetMode,
    XCostDefinition,
    Zone,
    ZoneTarget,
)
from card_duel_engine.domain.models import StackItem
from card_duel_engine.persistence.codec import canonical_json, encode_value

SCENARIO_SEED = 20_260_814
ENUMERATION_LIMITS = (8, 32, 128, 512)
TARGET_SIZES = (4, 8, 16, 32)
ALLOCATION_AMOUNTS = (3, 5, 10, 20)
SEMANTICS = (EngineSemantics.CURRENT, EngineSemantics.LEGACY_019)


class ScenarioSize(StrEnum):
    """Perfiles crecientes, acotados por el límite configurado del motor."""

    SMALL = "SMALL"
    MEDIUM = "MEDIUM"
    STRESS_CONTROLLED = "STRESS_CONTROLLED"


SMALL = ScenarioSize.SMALL
MEDIUM = ScenarioSize.MEDIUM
STRESS_CONTROLLED = ScenarioSize.STRESS_CONTROLLED

# target_count, allocation_amount y número de triggers ordenables.
_SCENARIO_SHAPES = {
    SMALL: (4, 3, 3),
    MEDIUM: (16, 10, 5),
    STRESS_CONTROLLED: (32, 20, 7),
}


def ruleset(limit: int) -> RuleSet:
    """Crea un RuleSet nuevo para uno de los límites validados del benchmark.

    Los cuatro valores son positivos y por tanto cumplen la validación vigente
    de ``RuleSet.legal_action_enumeration_limit``.
    """

    if limit not in ENUMERATION_LIMITS:
        raise ValueError(f"Límite de benchmark no admitido: {limit}")
    return RuleSet(legal_action_enumeration_limit=limit)


def ruleset_variants() -> tuple[RuleSet, ...]:
    """Devuelve instancias independientes para 8, 32, 128 y 512."""

    return tuple(ruleset(limit) for limit in ENUMERATION_LIMITS)


def target_candidates(size: int) -> tuple[str, ...]:
    """Candidatos estables para productos de objetivos de tamaño solicitado."""

    if size not in TARGET_SIZES:
        raise ValueError(f"Tamaño de objetivos no admitido: {size}")
    return tuple(f"benchmark-target-{index:02d}" for index in range(size))


def player_zone_candidates(engine: GameEngine) -> tuple[ZoneTarget, ...]:
    """Enumera en el orden público exigido: jugadores y después sus zonas."""

    state = engine.state
    if state is None:
        raise RuntimeError("El motor de benchmark no tiene partida")
    return tuple(
        ZoneTarget(player_id, zone)
        for player_id, player in state.players.items()
        for zone in player.zones
    )


def allocation_candidates(amount: int, target_ids: Iterable[str]) -> tuple[tuple[TargetAllocation, ...], ...]:
    """Genera repartos positivos admitidos por ``TargetAllocation``.

    Se usan uno o dos objetivos: nunca se fabrica una asignación cero y sólo se
    admiten las cantidades declaradas por este módulo.
    """

    if amount not in ALLOCATION_AMOUNTS:
        raise ValueError(f"Cantidad de allocation no admitida: {amount}")
    targets = tuple(target_ids)
    results = [
        (TargetAllocation(target_id, amount),)
        for target_id in targets
    ]
    if amount >= 2:
        results.extend(
            (TargetAllocation(left, first), TargetAllocation(right, amount - first))
            for left, right in combinations(targets, 2)
            for first in range(1, amount)
        )
    return tuple(results)


def cost_definitions() -> tuple[CardDefinition, ...]:
    """Cartas sintéticas con las seis familias de coste soportadas."""

    dynamic = DynamicCostDefinition(
        CostComponent.STEPS,
        (CostTerm(CostMetric.OWN_WOUNDS, 1),),
        offset=1,
        minimum=0,
        maximum=20,
    )
    return (
        CardDefinition("BENCH_FIXED", "Coste fijo", CardKind.ARTIFACT, 3),
        CardDefinition("BENCH_DYNAMIC", "Coste dinámico", CardKind.ARTIFACT, 0, dynamic_cost=dynamic),
        CardDefinition("BENCH_X", "Coste X", CardKind.ARTIFACT, 0,
                       x_cost=XCostDefinition(CostComponent.STEPS, minimum=0, maximum=20)),
        CardDefinition("BENCH_ALT_FIXED", "Alternativa fija", CardKind.ARTIFACT, 30,
                       alternative_costs=(CompositeCost(wounds=1), CompositeCost(discard_count=1))),
        CardDefinition("BENCH_ALT_DYNAMIC", "Alternativa dinámica", CardKind.ARTIFACT, 30,
                       dynamic_alternative_costs=(dynamic,)),
        CardDefinition("BENCH_ALT_X", "Alternativa X", CardKind.ARTIFACT, 30,
                       x_alternative_costs=(XCostDefinition(CostComponent.DISCARD_COUNT, minimum=0, maximum=20),)),
    )


def _scenario_definitions(allocation_amount: int) -> tuple[CardDefinition, ...]:
    chosen_players = EffectDefinition(
        EffectKind.DEAL_WOUNDS, 1, TargetMode.CHOSEN_PLAYER,
        minimum_targets=1, maximum_targets=2,
    )
    distributed = EffectDefinition(
        EffectKind.DEAL_HARM, allocation_amount, TargetMode.CHOSEN_ENTITY,
        minimum_targets=1, maximum_targets=3, distributed=True,
    )
    chosen_permanents = EffectDefinition(
        EffectKind.DEAL_DAMAGE, 1, TargetMode.CHOSEN_PERMANENT,
        minimum_targets=1, maximum_targets=2,
    )
    chosen_zones = EffectDefinition(
        EffectKind.SHUFFLE_ZONE, 0, TargetMode.CHOSEN_ZONE,
        minimum_targets=1, maximum_targets=1,
    )
    combined_effects = (chosen_players, chosen_permanents, chosen_zones, distributed)
    return (
        *cost_definitions(),
        CardDefinition("BENCH_PLAY", "Jugada combinatoria", CardKind.QUICK_RESOURCE, 0,
                       permanent=False, effects=combined_effects,
                       alternative_costs=(CompositeCost(
                           discard_count=1, sacrifice_count=1,
                       ),)),
        CardDefinition("BENCH_ABILITY", "Activación combinatoria", CardKind.CREATURE, 1,
                       base_strength=2, abilities=(AbilityDefinition(
                           "benchmark-pulse", combined_effects,
                           cost=CompositeCost(discard_count=1, sacrifice_count=1),
                       ),)),
        CardDefinition("BENCH_TRIGGER", "Trigger combinatorio", CardKind.CREATURE, 1,
                       base_strength=2, abilities=(AbilityDefinition(
                           "benchmark-hit", combined_effects,
                       ),)),
    )


def _filler(prefix: str, size: int) -> list[CardDefinition]:
    return [
        CardDefinition(f"{prefix}-{index:03d}", f"Objetivo {prefix} {index}",
                       CardKind.CREATURE, 1, base_strength=2, set_id="benchmarks")
        for index in range(size)
    ]


def _force_zone(engine: GameEngine, definition_id: str, player_id: str, zone: Zone) -> str:
    state = engine.state
    if state is None:
        raise RuntimeError("El motor de benchmark no tiene partida")
    card_id = next(
        instance_id for instance_id, card in state.cards.items()
        if card.definition_id == definition_id
    )
    for player in state.players.values():
        for cards in player.zones.values():
            if card_id in cards:
                cards.remove(card_id)
    state.players[player_id].zones[zone].append(card_id)
    state.cards[card_id].zone = zone
    state.cards[card_id].controller_id = player_id
    return card_id


def build_scenario(
    size: ScenarioSize | str,
    *,
    semantics: EngineSemantics = EngineSemantics.CURRENT,
    limit: int = 128,
) -> GameEngine:
    """Construye una partida de jugadas/activaciones de complejidad controlada."""

    scenario = ScenarioSize(size)
    if not isinstance(semantics, EngineSemantics):
        raise TypeError("La semántica debe ser EngineSemantics")
    target_count, allocation_amount, _trigger_count = _SCENARIO_SHAPES[scenario]
    engine = GameEngine(ruleset(limit))
    engine.new_match(
        {
            "A": [*_scenario_definitions(allocation_amount), *_filler("A-BENCH", max(14, target_count))],
            "B": _filler("B-BENCH", max(14, target_count)),
        },
        seed=SCENARIO_SEED,
    )
    # Es la misma vía de compatibilidad caracterizada por los tests de paridad.
    engine._semantics = semantics
    state = engine.state
    assert state is not None
    state.phase = Phase.EFFECTS
    state.priority_player_id = "A"
    state.players["A"].steps = 40
    state.players["A"].wounds = 5
    for definition in _scenario_definitions(allocation_amount):
        _force_zone(engine, definition.card_id, "A", Zone.DECK)
    for definition_id in (*[item.card_id for item in cost_definitions()], "BENCH_PLAY"):
        _force_zone(engine, definition_id, "A", Zone.HAND)
    _force_zone(engine, "BENCH_ABILITY", "A", Zone.BATTLEFIELD)
    _force_zone(engine, "BENCH_TRIGGER", "A", Zone.BATTLEFIELD)
    for index in range(target_count):
        owner = "A" if index % 2 == 0 else "B"
        _force_zone(engine, f"{owner}-BENCH-{index:03d}", owner, Zone.BATTLEFIELD)
    return engine


def build_trigger_scenario(
    size: ScenarioSize | str,
    *,
    semantics: EngineSemantics = EngineSemantics.CURRENT,
    limit: int = 128,
    targets_locked: bool = True,
) -> GameEngine:
    """Construye triggers ordenables (n!) o, opcionalmente, con objetivos."""

    scenario = ScenarioSize(size)
    engine = build_scenario(scenario, semantics=semantics, limit=limit)
    _target_count, _amount, trigger_count = _SCENARIO_SHAPES[scenario]
    source = next(
        card_id for card_id, card in engine.state.cards.items()
        if card.definition_id == "BENCH_TRIGGER"
    )
    effects = engine.catalog.get("BENCH_TRIGGER").abilities[0].effects
    engine.state.pending_triggers = [
        StackItem(f"benchmark-trigger-{index:02d}", "A", source, effects,
                  ability_id="benchmark-hit", targets_locked=targets_locked)
        for index in range(trigger_count)
    ]
    return engine


def scenario_variants(size: ScenarioSize | str) -> tuple[GameEngine, ...]:
    """Producto completo semánticas × límites, siempre con estados nuevos."""

    return tuple(
        build_scenario(size, semantics=semantics, limit=limit)
        for semantics in SEMANTICS
        for limit in ENUMERATION_LIMITS
    )


def canonical_state(engine_or_state: GameEngine | object) -> str:
    """Representación JSON persistible, canónica y estable para consultas puras."""

    state = engine_or_state.state if isinstance(engine_or_state, GameEngine) else engine_or_state
    return canonical_json(encode_value(state))


def small(
    *, semantics: EngineSemantics = EngineSemantics.CURRENT, limit: int = 128
) -> GameEngine:
    return build_scenario(SMALL, semantics=semantics, limit=limit)


def medium(
    *, semantics: EngineSemantics = EngineSemantics.CURRENT, limit: int = 128
) -> GameEngine:
    return build_scenario(MEDIUM, semantics=semantics, limit=limit)


def stress_controlled(
    *, semantics: EngineSemantics = EngineSemantics.CURRENT, limit: int = 128
) -> GameEngine:
    return build_scenario(STRESS_CONTROLLED, semantics=semantics, limit=limit)


__all__ = [
    "ALLOCATION_AMOUNTS", "ENUMERATION_LIMITS", "MEDIUM", "SCENARIO_SEED",
    "SEMANTICS", "SMALL", "STRESS_CONTROLLED", "ScenarioSize", "TARGET_SIZES",
    "allocation_candidates", "build_scenario", "build_trigger_scenario",
    "canonical_state", "cost_definitions", "medium", "player_zone_candidates",
    "ruleset", "ruleset_variants", "scenario_variants", "small",
    "stress_controlled", "target_candidates",
]
