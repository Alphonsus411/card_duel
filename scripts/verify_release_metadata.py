#!/usr/bin/env python3
"""Comprueba que todos los metadatos activos describen la misma release."""

from __future__ import annotations

import re
from pathlib import Path
import tomllib

from project_metadata import read_project_version

ROOT = Path(__file__).resolve().parents[1]


def _first_release_heading(text: str, source: str) -> str:
    match = re.search(r"^## ([0-9]+\.[0-9]+\.[0-9]+)\s*$", text, re.MULTILINE)
    if match is None:
        raise ValueError(f"{source} no contiene un encabezado de release")
    return match.group(1)


def _validation_version(text: str, source: str) -> str:
    match = re.search(r"^# .*?([0-9]+\.[0-9]+\.[0-9]+)\s*$", text, re.MULTILINE)
    if match is None:
        raise ValueError(f"{source} no identifica la versión en su título")
    return match.group(1)


def verify(root: Path = ROOT) -> dict[str, str]:
    """Devuelve los cuatro valores si coinciden; falla con diagnóstico si divergen."""
    project = read_project_version(root)
    lock = tomllib.loads((root / "uv.lock").read_text(encoding="utf-8"))
    package = next((item for item in lock["package"] if item["name"] == "card-duel-engine"), None)
    if package is None:
        raise ValueError("uv.lock no contiene el paquete card-duel-engine")
    values = {
        "pyproject": project,
        "uv_lock": str(package["version"]),
        "changelog": _first_release_heading(
            (root / "CHANGELOG.md").read_text(encoding="utf-8"), "CHANGELOG.md"
        ),
        "validation": _validation_version(
            (root / f"docs/VALIDATION_{project}.md").read_text(encoding="utf-8"),
            f"docs/VALIDATION_{project}.md",
        ),
    }
    divergent = {source: value for source, value in values.items() if value != project}
    if divergent:
        details = ", ".join(f"{source}={value}" for source, value in divergent.items())
        raise ValueError(f"Deriva de versión respecto de {project}: {details}")
    return values


def main() -> None:
    values = verify()
    print("Metadatos de release coherentes: " + ", ".join(f"{key}={value}" for key, value in values.items()))


if __name__ == "__main__":
    main()
