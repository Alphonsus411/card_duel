"""Utilidades compartidas para leer metadatos autoritativos del proyecto."""

from __future__ import annotations

from pathlib import Path
import tomllib


def read_project_version(root: Path) -> str:
    """Lee ``project.version`` del ``pyproject.toml`` situado bajo ``root``."""
    with (root / "pyproject.toml").open("rb") as stream:
        project = tomllib.load(stream)
    return str(project["project"]["version"])
