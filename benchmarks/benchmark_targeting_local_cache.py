"""Benchmark reproducible de la caché local de consultas de targeting.

El controlador ejecuta dos checkouts mediante el mismo ``sys.executable`` y
alterna su orden en cada ronda.  El modo worker existe para que cada checkout
importe su propia copia del paquete sin contaminar ``sys.modules``.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import time
import tracemalloc
from types import MethodType
from typing import Any, Callable


CASES = (
    ("medium_legal_actions", "MEDIUM", "legal_actions"),
    ("stress_legal_actions", "STRESS_CONTROLLED", "legal_actions"),
    ("stress_legal_plays", "STRESS_CONTROLLED", "_legal_plays"),
)
METHODS = (
    "_definition",
    "_effective_keywords",
    "_continuous_effects_for",
    "_card_can_be_targeted",
)


def _encode(value: object) -> str:
    from card_duel_engine.persistence.codec import canonical_json, encode_value

    return canonical_json(encode_value(value))


def _fingerprint(serialized: str) -> str:
    return hashlib.sha256(serialized.encode()).hexdigest()


def _build(size: str):
    from benchmarks.fixtures import build_scenario

    return build_scenario(size, limit=128)


def _invoke(engine: object, operation: str):
    return getattr(engine, operation)("A")


def _validate(engine: object, operation: str, *, timed: bool) -> dict[str, Any]:
    before = _encode(engine.state)
    if timed:
        started = time.perf_counter_ns()
        result = _invoke(engine, operation)
        elapsed = time.perf_counter_ns() - started
    else:
        result = _invoke(engine, operation)
        elapsed = None
    after = _encode(engine.state)
    serialized = _encode(result)
    if before != after:
        raise AssertionError("la consulta mutó GameState")
    return {
        "ns": elapsed,
        "count": len(result),
        "serialized": serialized,
        "fingerprint": _fingerprint(serialized),
        "state_fingerprint": _fingerprint(before),
    }


def _worker(args: argparse.Namespace) -> None:
    if hasattr(os, "sched_setaffinity"):
        os.sched_setaffinity(0, {args.cpu})
    engine = _build(args.size)
    if args.mode == "time":
        payload = _validate(engine, args.operation, timed=True)
    elif args.mode == "memory":
        gc.collect()
        tracemalloc.start()
        result = _invoke(engine, args.operation)
        _current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        # La serialización y la verificación quedan fuera de tracemalloc.
        before_engine = _build(args.size)
        expected_state = _encode(before_engine.state)
        actual_state = _encode(engine.state)
        serialized = _encode(result)
        if actual_state != expected_state:
            raise AssertionError("la consulta de memoria mutó GameState")
        payload = {
            "peak_bytes": peak,
            "count": len(result),
            "serialized": serialized,
            "fingerprint": _fingerprint(serialized),
            "state_fingerprint": _fingerprint(actual_state),
        }
    else:
        counts = dict.fromkeys(METHODS, 0)
        originals = {name: getattr(engine, name) for name in METHODS}

        def wrapper(name: str) -> Callable[..., Any]:
            original = originals[name]

            def counted(_self: object, *pos: object, **kw: object) -> Any:
                counts[name] += 1
                return original(*pos, **kw)

            return counted

        try:
            for name in METHODS:
                setattr(engine, name, MethodType(wrapper(name), engine))
            payload = _validate(engine, args.operation, timed=False)
            payload["counters"] = counts
        finally:
            for name, original in originals.items():
                setattr(engine, name, original)
    payload.pop("serialized", None)
    print(json.dumps(payload, sort_keys=True))


def _percentile95(values: list[int]) -> float:
    ordered = sorted(values)
    return float(ordered[max(0, int(len(ordered) * 0.95 + 0.999999) - 1)])


def _summary(values: list[int]) -> dict[str, float]:
    return {
        "median": statistics.median(values),
        "mean": statistics.mean(values),
        "p95": _percentile95(values),
        "stdev": statistics.stdev(values),
    }


def _run(root: Path, case: tuple[str, str, str], mode: str, cpu: int) -> dict[str, Any]:
    _name, size, operation = case
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = "20260814"
    env["PYTHONPATH"] = os.pathsep.join((str(root), str(root / "src")))
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--worker",
        "--size", size,
        "--operation", operation,
        "--mode", mode,
        "--cpu", str(cpu),
    ]
    completed = subprocess.run(
        command, cwd=root, env=env, check=True, text=True, capture_output=True
    )
    return json.loads(completed.stdout)


def _controller(args: argparse.Namespace) -> None:
    roots = {"baseline": args.baseline.resolve(), "optimized": args.optimized.resolve()}
    revisions = {
        name: subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip()
        for name, root in roots.items()
    }
    results: dict[str, Any] = {}
    for case in CASES:
        case_name = case[0]
        samples = {name: [] for name in roots}
        # Warmups también se contrabalancean y se descartan.
        for round_index in range(args.warmups):
            order = ("baseline", "optimized") if round_index % 2 == 0 else ("optimized", "baseline")
            for name in order:
                _run(roots[name], case, "time", args.cpu)
        validations: dict[str, list[dict[str, Any]]] = {name: [] for name in roots}
        for round_index in range(args.samples):
            order = ("optimized", "baseline") if round_index % 2 == 0 else ("baseline", "optimized")
            round_payload: dict[str, dict[str, Any]] = {}
            for name in order:
                payload = _run(roots[name], case, "time", args.cpu)
                samples[name].append(payload.pop("ns"))
                validations[name].append(payload)
                round_payload[name] = payload
            comparable = ("count", "fingerprint", "state_fingerprint")
            if any(round_payload["baseline"][key] != round_payload["optimized"][key] for key in comparable):
                raise AssertionError(f"paridad rota en {case_name}, ronda {round_index}")
        memory = {name: _run(root, case, "memory", args.cpu) for name, root in roots.items()}
        counters = {name: _run(root, case, "counters", args.cpu) for name, root in roots.items()}
        for evidence in (memory, counters):
            if evidence["baseline"]["fingerprint"] != evidence["optimized"]["fingerprint"]:
                raise AssertionError(f"paridad rota con instrumentación en {case_name}")
        results[case_name] = {
            "raw_ns": samples,
            "summary_ns": {name: _summary(values) for name, values in samples.items()},
            "memory": memory,
            "counters": counters,
            "validation": validations["optimized"][0],
        }
    output = {
        "protocol": {"warmups": args.warmups, "samples": args.samples, "cpu": args.cpu},
        "revisions": revisions,
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "executable": sys.executable,
        },
        "cases": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(args.output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--optimized", type=Path)
    parser.add_argument("--output", type=Path, default=Path("benchmarks/results/targeting_local_cache.json"))
    parser.add_argument("--warmups", type=int, default=5)
    parser.add_argument("--samples", type=int, default=30)
    parser.add_argument("--cpu", type=int, default=min(os.sched_getaffinity(0)))
    parser.add_argument("--size", choices=("MEDIUM", "STRESS_CONTROLLED"))
    parser.add_argument("--operation", choices=("legal_actions", "_legal_plays"))
    parser.add_argument("--mode", choices=("time", "memory", "counters"))
    args = parser.parse_args()
    if args.worker:
        _worker(args)
    elif args.baseline is None or args.optimized is None:
        parser.error("--baseline y --optimized son obligatorios")
    else:
        _controller(args)


if __name__ == "__main__":
    main()
