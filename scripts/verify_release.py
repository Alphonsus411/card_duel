#!/usr/bin/env python3
"""Verificador único, reproducible y fail-fast de una entrega."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Callable

from verify_headless_simulations import verify as verify_simulations
from verify_persistence_roundtrips import verify as verify_persistence
from verify_reproducible_wheel import VERSION, WHEEL_NAME

ROOT = Path(__file__).resolve().parents[1]
PYTHONS = ("3.11", "3.12", "3.13")
CommandRunner = Callable[..., subprocess.CompletedProcess[str]]


def _run(command: list[str], *, runner: CommandRunner = subprocess.run) -> str:
    result = runner(command, cwd=ROOT, check=True, text=True, capture_output=True)
    return result.stdout.strip()


def _lockfile(runner: CommandRunner) -> dict[str, object]:
    lock = ROOT / "uv.lock"
    before = hashlib.sha256(lock.read_bytes()).hexdigest()
    _run(["uv", "lock", "--check"], runner=runner)
    _run(["git", "diff", "--exit-code", "--", "uv.lock"], runner=runner)
    after = hashlib.sha256(lock.read_bytes()).hexdigest()
    if before != after:
        raise SystemExit("uv.lock cambió durante la verificación")
    return {"status": "ok", "sha256": after, "unchanged": True}


def _quality(runner: CommandRunner) -> dict[str, object]:
    _run([sys.executable, "-m", "mypy", "src/card_duel_engine"], runner=runner)
    _run([sys.executable, "-m", "compileall", "-q", "src", "tests", "scripts"], runner=runner)
    _run([sys.executable, "-m", "coverage", "erase"], runner=runner)
    _run([sys.executable, "-m", "coverage", "run", "--branch", "-m", "unittest", "discover", "-s", "tests", "-v"], runner=runner)
    coverage = float(_run([sys.executable, "-m", "coverage", "report", "--format=total"], runner=runner))
    if coverage < 81:
        raise SystemExit(f"Cobertura insuficiente: {coverage}%")
    return {"status": "ok", "mypy": True, "compileall": True, "coverage_percent": coverage}


def _package(runner: CommandRunner) -> dict[str, object]:
    _run([sys.executable, "scripts/verify_reproducible_wheel.py"], runner=runner)
    report = json.loads((ROOT / "dist" / "wheel-audit.json").read_text(encoding="utf-8"))
    wheel = ROOT / "dist" / WHEEL_NAME
    with tempfile.TemporaryDirectory(prefix="card-duel-install-") as temporary:
        base = Path(temporary)
        for version in PYTHONS:
            _run(["uv", "python", "install", version], runner=runner)
            environment = base / version
            _run(["uv", "venv", "--python", version, str(environment)], runner=runner)
            python = environment / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
            _run(["uv", "pip", "install", "--python", str(python), "--no-deps", str(wheel)], runner=runner)
            _run([str(python), "-c", f"import card_duel_engine; assert card_duel_engine.__version__ == '{VERSION}'"], runner=runner)
    return {"status": "ok", "audit": report, "installed_python_versions": list(PYTHONS)}


def verify(*, runner: CommandRunner = subprocess.run) -> dict[str, object]:
    """Ejecuta cada control en orden; cualquier excepción detiene la entrega."""
    return {
        "schema_version": 1,
        "version": VERSION,
        "lockfile": _lockfile(runner),
        "quality": _quality(runner),
        "simulations": verify_simulations(),
        "persistence": verify_persistence(),
        "package": _package(runner),
        "status": "ok",
    }


def render(summary: dict[str, object]) -> str:
    return json.dumps(summary, indent=2, sort_keys=True, separators=(",", ": ")) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", metavar="PATH", help="Escribe el resumen JSON ('-' para stdout)")
    args = parser.parse_args()
    output = render(verify())
    if args.json == "-":
        print(output, end="")
    elif args.json:
        Path(args.json).write_text(output, encoding="utf-8")
    else:
        print("OK: validación integral de la entrega completada")


if __name__ == "__main__":
    main()
