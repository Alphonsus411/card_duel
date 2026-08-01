"""Resolución de la versión pública desde los metadatos del proyecto."""

from __future__ import annotations

from importlib import metadata
from pathlib import Path
import tomllib


def resolve_version() -> str:
    """Devuelve la versión instalada o, en un checkout, la de ``pyproject.toml``."""
    try:
        return metadata.version("card-duel-engine")
    except metadata.PackageNotFoundError:
        project_file = Path(__file__).resolve().parents[2] / "pyproject.toml"
        with project_file.open("rb") as stream:
            project = tomllib.load(stream)
        return str(project["project"]["version"])
