#!/usr/bin/env python3
"""Benchmark reproducible de enumeración de opciones y acciones legales.

El percentil p95 usa *nearest rank*: para ``n`` observaciones ordenadas se toma
la observación en la posición ``ceil(0.95 * n)`` (posiciones numeradas desde
uno). Esta convención no interpola y, por tanto, es determinista.

El script vive deliberadamente fuera de ``src/`` y no forma parte del paquete
distribuido. Puede ejecutarse directamente desde cualquier directorio.
"""

from __future__ import annotations

import argparse
import copy
import gc
import hashlib
import json
import math
import os
import platform
import statistics
import subprocess
import sys
import time
import tracemalloc
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
for import_root in (SOURCE_ROOT, REPOSITORY_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from benchmarks.fixtures import (  # noqa: E402
    ENUMERATION_LIMITS,
    MEDIUM,
    SMALL,
    STRESS_CONTROLLED,
    build_scenario,
    build_trigger_scenario,
    canonical_state,
    cost_definitions,
    ruleset,
    target_candidates,
)
from card_duel_engine import EngineSemantics, GameEngine  # noqa: E402
from card_duel_engine.domain import (  # noqa: E402
    CardDefinition,
    CardKind,
    EffectDefinition,
    EffectKind,
    TargetMode,
    Zone,
)
from card_duel_engine.persistence.codec import canonical_json, encode_value  # noqa: E402

DEFAULT_OUTPUT = Path("benchmarks/results/action_options_benchmark.json")


class NoGo(RuntimeError):
    """Fallo de corrección que invalida por completo la medición."""


@dataclass(frozen=True)
class Case:
    name: str
    fixture: Any
    query: Callable[[], Any]
    result_kind: str = "options"
    copied_state: bool = False
    parameters: dict[str, Any] | None = None


def _canonical_result(result: Any) -> str:
    """Serializa conservando el orden de secuencias y ordenando claves JSON."""

    return canonical_json(encode_value(result))


def _fingerprint(canonical: str) -> str:
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _result_count(result: Any) -> int:
    try:
        return len(result)
    except TypeError:
        return 1


def _observe(case: Case) -> tuple[Any, str]:
    before = canonical_state(case.fixture)
    result = case.query()
    after = canonical_state(case.fixture)
    if before != after:
        raise NoGo(f"{case.name}: GameState mutó durante la consulta")
    canonical = _canonical_result(result)
    if case.copied_state and canonical != before:
        raise NoGo(f"{case.name}: deepcopy no conservó el contenido del GameState")
    return result, canonical


def _validate(case: Case, result: Any, canonical: str, baseline: tuple[int, str, str]) -> None:
    count = _result_count(result)
    digest = _fingerprint(canonical)
    expected_count, expected_digest, expected_canonical = baseline
    if count != expected_count:
        raise NoGo(f"{case.name}: conteo cambiante ({count} != {expected_count})")
    if digest != expected_digest:
        raise NoGo(f"{case.name}: fingerprint SHA-256 inestable ({digest} != {expected_digest})")
    if canonical != expected_canonical:
        raise NoGo(f"{case.name}: cambió el orden o contenido del resultado")


def _percentile_95(samples: list[int]) -> int:
    ordered = sorted(samples)
    return ordered[math.ceil(0.95 * len(ordered)) - 1]


def _measure_case(case: Case, warmups: int, repetitions: int) -> dict[str, Any]:
    initial, initial_canonical = _observe(case)
    baseline = (_result_count(initial), _fingerprint(initial_canonical), initial_canonical)

    for _ in range(warmups):
        result, canonical = _observe(case)
        _validate(case, result, canonical, baseline)

    durations: list[int] = []
    for _ in range(repetitions):
        state_before = canonical_state(case.fixture)
        start = time.perf_counter_ns()
        result = case.query()
        elapsed = time.perf_counter_ns() - start
        state_after = canonical_state(case.fixture)
        if state_before != state_after:
            raise NoGo(f"{case.name}: GameState mutó durante una repetición medida")
        canonical = _canonical_result(result)
        _validate(case, result, canonical, baseline)
        durations.append(elapsed)

    # Cada caso obtiene un trazado nuevo; ni allocations ni picos pasan al siguiente.
    gc.collect()
    tracemalloc.start()
    tracemalloc.reset_peak()
    try:
        memory_result = case.query()
        current_bytes, peak_bytes = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    if canonical_state(case.fixture) != state_before:
        raise NoGo(f"{case.name}: GameState mutó durante la medición de memoria")
    memory_canonical = _canonical_result(memory_result)
    _validate(case, memory_result, memory_canonical, baseline)

    measured = {
        "repetitions": repetitions,
        "warmup_repetitions": warmups,
        "duration_ns": {
            "mean": statistics.fmean(durations),
            "median": statistics.median(durations),
            "minimum": min(durations),
            "p95": _percentile_95(durations),
            "standard_deviation": statistics.stdev(durations),
        },
        "memory_bytes": {"current": current_bytes, "peak": peak_bytes},
        "result": {"count": baseline[0], "sha256": baseline[1]},
    }
    derived: dict[str, float] = {}
    if baseline[0] > 0:
        derived["nanoseconds_per_option"] = measured["duration_ns"]["mean"] / baseline[0]
        derived["peak_bytes_per_option"] = peak_bytes / baseline[0]
        if case.result_kind == "legal_commands":
            derived["microseconds_per_legal_command"] = (
                measured["duration_ns"]["mean"] / 1_000 / baseline[0]
            )
    return {
        "name": case.name,
        "parameters": case.parameters or {},
        "measured": measured,
        "derived": derived,
    }


def _effect(
    mode: TargetMode, minimum: int, maximum: int, *, amount: int = 1,
    distributed: bool = False, x_multiplier: int = 0,
) -> tuple[EffectDefinition, ...]:
    kind = EffectKind.DEAL_HARM if distributed else (
        EffectKind.SHUFFLE_ZONE if mode is TargetMode.CHOSEN_ZONE
        else EffectKind.DEAL_WOUNDS
    )
    return (EffectDefinition(
        kind, amount, mode, minimum_targets=minimum, maximum_targets=maximum,
        distributed=distributed, x_multiplier=x_multiplier,
    ),)


def _zone_engine(players: int, zones: int, limit: int) -> GameEngine:
    """Crea sólo el estado mínimo; recortar zonas es seguro para esta consulta pura."""

    engine = GameEngine(ruleset(limit))
    decks = {
        f"P{player}": (
            CardDefinition(f"ZONE-{player}", f"Zona {player}", CardKind.ARTIFACT, 0),
        )
        for player in range(players)
    }
    engine.new_match(decks, auto_start=False)
    for player in engine.state.players.values():
        player.zones = dict(tuple(player.zones.items())[:zones])
    return engine


def _allocation_engine(candidates: int, limit: int) -> GameEngine:
    engine = build_scenario(STRESS_CONTROLLED, limit=limit)
    # Los jugadores siempre son candidatos; dejamos exactamente n - 2 permanentes.
    battlefield_ids = [
        card_id
        for player in engine.state.players.values()
        for card_id in player.zones[Zone.BATTLEFIELD]
    ]
    for card_id in battlefield_ids[candidates - len(engine.state.turn_order):]:
        owner = engine.state.cards[card_id].controller_id
        engine.state.players[owner].zones[Zone.BATTLEFIELD].remove(card_id)
        engine.state.players[owner].zones[Zone.DECK].append(card_id)
        engine.state.cards[card_id].zone = Zone.DECK
    return engine


def _microbenchmark_cases(profile: str) -> list[Case]:
    """Matriz explícita y semánticamente neutra de los helpers del resolver."""

    cases: list[Case] = []
    limits = (32,) if profile == "quick" else ENUMERATION_LIMITS

    # Cada n tiene una selección exacta y un rango; full repite ambos con 4 límites.
    for size in (4, 8, 16, 32):
        for minimum, maximum, cardinality in ((1, 1, "exact-1"), (1, min(4, size), "range-1-4")):
            for limit in limits:
                engine = build_scenario(SMALL, limit=limit)
                target_pool = target_candidates(size)
                effects = _effect(TargetMode.CHOSEN_PLAYER, minimum, maximum)
                params: dict[str, Any] = {
                    "candidates": size, "minimum_targets": minimum,
                    "maximum_targets": maximum, "enumeration_limit": limit,
                }
                cases.append(Case(
                    f"target_selections/n-{size}/{cardinality}/limit-{limit}", engine,
                    lambda engine=engine, effects=effects, target_pool=target_pool:
                        engine._options.target_selections(
                            effects, TargetMode.CHOSEN_PLAYER, target_pool
                        ),
                    parameters=params,
                ))

    zone_shapes = ((2, 2, 1, 1), (2, 8, 1, 3), (3, 4, 2, 2), (4, 8, 0, 3))
    for players, zones, minimum, maximum in zone_shapes:
        for limit in limits:
            engine = _zone_engine(players, zones, limit)
            effects = _effect(TargetMode.CHOSEN_ZONE, minimum, maximum)
            params = {
                "players": players, "zones_per_player": zones,
                "minimum_targets": minimum, "maximum_targets": maximum,
                "enumeration_limit": limit,
                "observable_order": "players_then_zones",
            }
            cases.append(Case(
                f"zone_target_selections/players-{players}/zones-{zones}/targets-{minimum}-{maximum}/limit-{limit}",
                engine, lambda engine=engine, effects=effects:
                    engine._options.zone_target_selections(effects), parameters=params,
            ))

    # Curated rows cover every requested axis without an unhelpful Cartesian explosion.
    allocation_rows = (
        (4, 3, 1, 1, 0), (8, 5, 1, 2, 0),
        (16, 10, 2, 3, 0), (32, 20, 1, 4, 0),
        (8, 3, 1, 2, 2), (16, 5, 2, 4, 3),
        (32, 10, 3, 5, 5), (32, 20, 2, 6, 10),
    )
    for candidate_count, amount, minimum, maximum, x_value in allocation_rows:
        for limit in limits:
            engine = _allocation_engine(candidate_count, limit)
            x_multiplier = int(x_value > 0)
            base_amount = amount - x_multiplier * x_value
            effects = _effect(TargetMode.CHOSEN_ENTITY, minimum, maximum,
                              amount=base_amount, distributed=True,
                              x_multiplier=x_multiplier)
            source = engine.catalog.get("BENCH_PLAY")
            params = {
                "candidates": candidate_count, "amount": amount,
                "minimum_targets": minimum, "maximum_targets": maximum,
                "x_value": x_value, "x_multiplier": x_multiplier,
                "enumeration_limit": limit, "memory_profiler": "tracemalloc",
            }
            cases.append(Case(
                f"allocation_selections/n-{candidate_count}/amount-{amount}"
                f"/targets-{minimum}-{maximum}/x-{x_value}/limit-{limit}",
                engine, lambda engine=engine, effects=effects, source=source, x_value=x_value:
                    engine._options.allocation_selections(
                        effects, source, x_value=x_value
                    ), parameters=params,
            ))

    for definition in cost_definitions():
        for limit in limits:
            engine = build_scenario(SMALL, limit=limit)
            family = definition.card_id.removeprefix("BENCH_").lower().replace("_", "-")
            params = {"cost_family": family, "definition_id": definition.card_id,
                      "enumeration_limit": limit}
            cases.append(Case(
                f"card_cost_options/{family}/limit-{limit}", engine,
                lambda engine=engine, definition=definition:
                    engine._options.card_cost_options(definition, "A"), parameters=params,
            ))
    return cases


def _cases(profile: str) -> list[Case]:
    shapes = [SMALL] if profile == "quick" else [SMALL, MEDIUM, STRESS_CONTROLLED]
    limits = [32] if profile == "quick" else [32, 128, 512]
    cases = _microbenchmark_cases(profile)
    for shape in shapes:
        for limit in limits:
            engine = build_scenario(shape, semantics=EngineSemantics.CURRENT, limit=limit)
            cases.append(Case(
                f"legal_actions/{shape.value.lower()}/limit-{limit}", engine,
                lambda engine=engine: engine.legal_actions("A"), "legal_commands",
                parameters={"scenario_size": shape.value, "player_id": "A",
                            "enumeration_limit": limit},
            ))
    if profile == "full":
        for shape in shapes:
            engine = build_trigger_scenario(shape, limit=512)
            cases.append(Case(
                f"trigger_order_options/{shape.value.lower()}/limit-512", engine,
                lambda engine=engine: engine.legal_actions("A"), "legal_commands",
                parameters={"scenario_size": shape.value, "player_id": "A",
                            "enumeration_limit": 512},
            ))
        clone_engine = build_scenario(MEDIUM, limit=128)
        state = clone_engine.state
        cases.append(Case(
            "deepcopy/game_state/medium", state, lambda state=state: copy.deepcopy(state),
            copied_state=True, parameters={"scenario_size": MEDIUM.value,
                                           "enumeration_limit": 128},
        ))
    return cases


def _git_sha() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPOSITORY_ROOT, check=True,
        text=True, capture_output=True,
    ).stdout.strip()


def _metadata(profile: str) -> dict[str, str]:
    return {
        "git_sha": _git_sha(),
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "processor": platform.processor() or os.environ.get("PROCESSOR_IDENTIFIER", "unavailable"),
        "profile": profile,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("quick", "full"), default="quick")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--warmup", type=int, help="Repeticiones de calentamiento (>= 0)")
    parser.add_argument("--repetitions", type=int, help="Muestras medidas (>= 2)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    warmups = args.warmup if args.warmup is not None else (2 if args.profile == "quick" else 5)
    repetitions = args.repetitions if args.repetitions is not None else (5 if args.profile == "quick" else 15)
    if warmups < 0:
        _parser().error("--warmup no puede ser negativo")
    if repetitions < 2:
        _parser().error("--repetitions debe ser al menos 2; no se acepta una sola muestra")
    try:
        cases = [_measure_case(case, warmups, repetitions) for case in _cases(args.profile)]
        document = {
            "schema_version": 1,
            "metadata": _metadata(args.profile),
            "statistical_conventions": {
                "p95": "nearest-rank: sorted_samples[ceil(0.95 * n) - 1], without interpolation",
                "standard_deviation": "sample standard deviation (n - 1 denominator)",
            },
            "cases": cases,
        }
        output = args.output if args.output.is_absolute() else REPOSITORY_ROOT / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"GO: benchmark válido escrito en {output}")
        return 0
    except (NoGo, Exception) as error:
        print(f"NO-GO: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
