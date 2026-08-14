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
    MEDIUM,
    SMALL,
    STRESS_CONTROLLED,
    build_scenario,
    build_trigger_scenario,
    canonical_state,
)
from card_duel_engine import EngineSemantics  # noqa: E402
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
    return {"name": case.name, "measured": measured, "derived": derived}


def _cases(profile: str) -> list[Case]:
    shapes = [SMALL] if profile == "quick" else [SMALL, MEDIUM, STRESS_CONTROLLED]
    limits = [32] if profile == "quick" else [32, 128, 512]
    cases: list[Case] = []
    for shape in shapes:
        for limit in limits:
            engine = build_scenario(shape, semantics=EngineSemantics.CURRENT, limit=limit)
            cases.append(Case(
                f"legal_actions/{shape.value.lower()}/limit-{limit}", engine,
                lambda engine=engine: engine.legal_actions("A"), "legal_commands",
            ))
    if profile == "full":
        for shape in shapes:
            engine = build_trigger_scenario(shape, limit=512)
            cases.append(Case(
                f"trigger_order_options/{shape.value.lower()}/limit-512", engine,
                lambda engine=engine: engine.legal_actions("A"), "legal_commands",
            ))
        clone_engine = build_scenario(MEDIUM, limit=128)
        state = clone_engine.state
        cases.append(Case(
            "deepcopy/game_state/medium", state, lambda state=state: copy.deepcopy(state),
            copied_state=True,
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
