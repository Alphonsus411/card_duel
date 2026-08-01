"""Resolución de la versión pública desde los metadatos del proyecto."""

from __future__ import annotations

from importlib import metadata
from pathlib import Path
import tomllib


def resolve_version() -> str:
    """Devuelve la versión instalada o, en un checkout, la de ``pyproject.toml``."""
    root = Path(__file__).resolve().parents[2]
    project_file = root / "pyproject.toml"
    source_file = root / "src" / "card_duel_engine" / "_version.py"

    if project_file.is_file() and source_file.is_file():
        with project_file.open("rb") as stream:
            metadata_document = tomllib.load(stream)

        project = metadata_document.get("project")
        if not isinstance(project, dict):
            raise RuntimeError("El metadato 'project' debe ser una tabla TOML")
        if "version" not in project:
            raise RuntimeError("Falta el metadato obligatorio 'project.version'")

        version = project["version"]
        if not isinstance(version, str):
            raise ValueError("El metadato 'project.version' debe ser texto")
        if not version.strip():
            raise ValueError("El metadato 'project.version' no puede estar vacío")
        return version

    return metadata.version("card-duel-engine")
