#!/usr/bin/env python3
"""Verificación por etapas con perfiles reproducibles y diagnóstico completo."""

from __future__ import annotations

import argparse
from collections.abc import Callable
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from verify_headless_simulations import verify as verify_simulations
from verify_persistence_roundtrips import verify as verify_persistence
from project_metadata import read_project_version
from verify_release_metadata import verify as verify_metadata
from verify_repository_security import verify as verify_security

ROOT = Path(__file__).resolve().parents[1]
VERSION = read_project_version(ROOT)
RELEASE_RESULTS = ROOT / "docs" / "release-results" / VERSION
TRANSIENT_RELEASE_RESULT = ROOT / "dist" / "release-verification.json"
WHEEL_NAME = f"card_duel_engine-{VERSION}-py3-none-any.whl"
PYTHONS = ("3.11", "3.12", "3.13")
CommandRunner = Callable[..., subprocess.CompletedProcess[str]]


class VerificationStageError(RuntimeError):
    """Fallo diagnosticable de un comando perteneciente a una etapa."""

    def __init__(self, stage: str, command: list[str], returncode: int, stdout: str, stderr: str) -> None:
        self.stage, self.command, self.returncode = stage, tuple(command), returncode
        self.stdout, self.stderr = stdout.strip(), stderr.strip()
        super().__init__(self.diagnostic())

    def diagnostic(self) -> str:
        command = " ".join(self.command)
        return (f"Etapa: {self.stage}\nComando: {command}\nCódigo de salida: {self.returncode}"
                f"\nstdout:\n{self.stdout or '(vacío)'}\nstderr:\n{self.stderr or '(vacío)'}")


def _run(command: list[str], *, stage: str = "command", runner: CommandRunner = subprocess.run) -> str:
    try:
        result = runner(command, cwd=ROOT, check=False, text=True, capture_output=True)
    except subprocess.CalledProcessError as error:
        raise VerificationStageError(stage, command, error.returncode, error.stdout or "", error.stderr or "") from error
    if result.returncode:
        raise VerificationStageError(stage, command, result.returncode, result.stdout, result.stderr)
    return result.stdout.strip()


def _lockfile(runner: CommandRunner) -> dict[str, object]:
    lock = ROOT / "uv.lock"; before = hashlib.sha256(lock.read_bytes()).hexdigest()
    _run(["uv", "lock", "--check"], stage="lockfile", runner=runner)
    _run(["git", "diff", "--exit-code", "--", "uv.lock"], stage="lockfile", runner=runner)
    after = hashlib.sha256(lock.read_bytes()).hexdigest()
    if before != after:
        raise VerificationStageError("lockfile", ["uv", "lock", "--check"], 1, "", "uv.lock cambió durante la verificación")
    return {"status": "ok", "sha256": after, "unchanged": True}


def _quality(runner: CommandRunner) -> dict[str, object]:
    _run([sys.executable, "-m", "mypy", "src/card_duel_engine"], stage="quality:mypy", runner=runner)
    _run([sys.executable, "-m", "compileall", "-q", "src", "tests", "scripts"], stage="quality:compileall", runner=runner)
    _run([sys.executable, "-m", "coverage", "erase"], stage="quality:coverage", runner=runner)
    _run([sys.executable, "-m", "coverage", "run", "--branch", "-m", "unittest", "discover", "-s", "tests", "-v"], stage="quality:tests", runner=runner)
    coverage = float(_run([sys.executable, "-m", "coverage", "report", "--format=total"], stage="quality:coverage", runner=runner))
    if coverage < 86:
        raise VerificationStageError("quality:coverage", ["coverage", "report"], 1, str(coverage), "Cobertura inferior al 86%")
    return {"status": "ok", "mypy": True, "compileall": True, "coverage_percent": coverage}


def _metadata() -> dict[str, object]:
    try:
        values = verify_metadata(ROOT)
    except (OSError, KeyError, StopIteration, ValueError) as error:
        raise VerificationStageError("metadata", ["verify_release_metadata.py"], 1, "", str(error)) from error
    return {"status": "ok", "values": values}


def _security() -> dict[str, object]:
    try:
        result = verify_security(ROOT)
    except (OSError, subprocess.SubprocessError, SyntaxError, ValueError) as error:
        raise VerificationStageError("security", ["verify_repository_security.py"], 1, "", str(error)) from error
    return {"status": "ok", **result}


def _package(runner: CommandRunner) -> dict[str, object]:
    _run([sys.executable, "scripts/verify_reproducible_wheel.py"], stage="package:build-audit", runner=runner)
    report = json.loads((ROOT / "dist" / "wheel-audit.json").read_text(encoding="utf-8")); wheel = ROOT / "dist" / WHEEL_NAME
    digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
    checksum = (ROOT / "dist" / "SHA256SUMS").read_text(encoding="utf-8")
    if report.get("filename") != wheel.name or report.get("sha256") != digest:
        raise VerificationStageError("package:artifact-coherence", ["wheel-audit.json"], 1, "", "La auditoría no identifica el wheel seleccionado")
    if checksum != f"{digest}  {wheel.name}\n":
        raise VerificationStageError("package:artifact-coherence", ["SHA256SUMS"], 1, "", "SHA256SUMS no identifica el wheel seleccionado")
    with tempfile.TemporaryDirectory(prefix="card-duel-install-") as temporary:
        for version in PYTHONS:
            _run(["uv", "python", "install", version], stage=f"package:python-{version}", runner=runner)
            environment = Path(temporary) / version
            _run(["uv", "venv", "--python", version, str(environment)], stage=f"package:install-{version}", runner=runner)
            python = environment / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
            _run(["uv", "pip", "install", "--python", str(python), "--no-deps", str(wheel)], stage=f"package:install-{version}", runner=runner)
            _run([str(python), "-c", f"import card_duel_engine; assert card_duel_engine.__version__ == '{VERSION}'"], stage=f"package:import-{version}", runner=runner)
    return {"status": "ok", "wheel": wheel.name, "sha256": digest,
            "audit": report, "installed_python_versions": list(PYTHONS)}


def _rules_sources(runner: CommandRunner) -> dict[str, object]:
    output = _run([sys.executable, "scripts/verify_rules_sources.py"], stage="rules-sources", runner=runner)
    return {"status": "ok", "verified_sources": len(output.splitlines())}


def _simulations() -> dict[str, object]:
    return dict(verify_simulations())


def _persistence() -> dict[str, object]:
    return dict(verify_persistence())


def verify(profile: str = "full", *, runner: CommandRunner = subprocess.run) -> dict[str, object]:
    """Ejecuta el perfil solicitado; ``full`` conserva el comportamiento histórico."""
    stages: list[tuple[str, Callable[[], dict[str, object]]]] = [
        ("metadata", _metadata), ("lockfile", lambda: _lockfile(runner)),
        ("security", _security), ("quality", lambda: _quality(runner))
    ]
    if profile == "full":
        full_stages: list[tuple[str, Callable[[], dict[str, object]]]] = [
            ("rules-sources", lambda: _rules_sources(runner)),
            ("simulations", _simulations),
            ("persistence", _persistence),
            ("package", lambda: _package(runner)),
        ]
        stages.extend(full_stages)
    elif profile != "runtime":
        raise ValueError(f"Perfil desconocido: {profile}")
    summary: dict[str, object] = {"schema_version": 2, "version": VERSION, "profile": profile, "executed_stages": []}
    executed: list[str] = []
    for name, operation in stages:
        summary[name] = operation(); executed.append(name)
    summary["executed_stages"] = executed; summary["status"] = "ok"
    return summary


def render(summary: dict[str, object]) -> str:
    return json.dumps(summary, indent=2, sort_keys=True, separators=(",", ": ")) + "\n"


def release_result_path(value: str) -> Path:
    """Resolve a JSON destination without allowing cross-release evidence writes."""
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    path = path.resolve()
    expected = RELEASE_RESULTS.resolve()
    if path != TRANSIENT_RELEASE_RESULT.resolve() and (
        path.parent != expected or path.suffix != ".json"
    ):
        raise ValueError(
            f"La evidencia de {VERSION} debe escribirse como JSON dentro de "
            f"{RELEASE_RESULTS.relative_to(ROOT)} o como "
            f"{TRANSIENT_RELEASE_RESULT.relative_to(ROOT)}"
        )
    return path


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--profile", choices=("runtime", "full"), default="full")
    parser.add_argument("--json", metavar="PATH", help="Escribe el resumen JSON ('-' para stdout)"); args = parser.parse_args()
    try:
        output = render(verify(args.profile))
    except VerificationStageError as error:
        print(error.diagnostic(), file=sys.stderr); raise SystemExit(1) from error
    if args.json == "-": print(output, end="")
    elif args.json:
        try:
            destination = release_result_path(args.json)
        except ValueError as error:
            parser.error(str(error))
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(output, encoding="utf-8")
    else: print(f"OK: perfil {args.profile} completado")


if __name__ == "__main__": main()
