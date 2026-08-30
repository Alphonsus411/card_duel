#!/usr/bin/env python3
"""Comprueba que todos los metadatos activos describen la misma release."""

from __future__ import annotations

import re
from pathlib import Path
import tomllib
import json

from project_metadata import read_project_version

ROOT = Path(__file__).resolve().parents[1]
RESULT_FILENAMES = {
    "full-python-3.13.json",
    "runtime-python-3.11.json",
    "runtime-python-3.12.json",
    "runtime-python-3.13.json",
}


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


def _readme_scope_version(text: str, source: str) -> str:
    match = re.search(
        r"^## Alcance de la versión ([0-9]+\.[0-9]+\.[0-9]+)\s*$",
        text,
        re.MULTILINE,
    )
    if match is None:
        raise ValueError(f"{source} no contiene el encabezado de alcance de la versión")
    return match.group(1)


def verify(root: Path = ROOT) -> dict[str, str]:
    """Devuelve los campos normativos si coinciden; falla si divergen."""
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
        "readme_scope": _readme_scope_version(
            (root / "README.md").read_text(encoding="utf-8"), "README.md"
        ),
    }
    divergent = {source: value for source, value in values.items() if value != project}
    if divergent:
        details = ", ".join(f"{source}={value}" for source, value in divergent.items())
        raise ValueError(f"Deriva de versión respecto de {project}: {details}")
    results_root = root / "docs" / "release-results"
    directories = (path for path in results_root.iterdir() if path.is_dir()) if results_root.is_dir() else ()
    for directory in sorted(directories):
        version = directory.name
        files = {path.name for path in directory.glob("*.json")}
        if files != RESULT_FILENAMES:
            raise ValueError(f"Conjunto de evidencia incompleto para {version}: {sorted(files)}")
        for path in sorted(directory.glob("*.json")):
            result = json.loads(path.read_text(encoding="utf-8"))
            if result.get("version") != version:
                raise ValueError(
                    f"{path.relative_to(root)} declara {result.get('version')!r}, no {version}"
                )
            package = result.get("package")
            if package is not None:
                expected_wheel = f"card_duel_engine-{version}-py3-none-any.whl"
                wheel = package.get("wheel", package.get("audit", {}).get("filename"))
                if wheel != expected_wheel:
                    raise ValueError(
                        f"{path.relative_to(root)} identifica un wheel de otra versión"
                    )
    return values


def main() -> None:
    values = verify()
    print("Metadatos de release coherentes: " + ", ".join(f"{key}={value}" for key, value in values.items()))


if __name__ == "__main__":
    main()
