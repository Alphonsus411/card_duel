from __future__ import annotations

import hashlib
from copy import deepcopy
from typing import Any, Callable, Mapping

from .codec import canonical_json, decode_value

Migration = Callable[[dict[str, Any]], dict[str, Any]]


def _snapshot_1_to_2(body: dict[str, Any]) -> dict[str, Any]:
    body["state_digest"] = hashlib.sha256(
        canonical_json(body["state"]).encode("utf-8")
    ).hexdigest()
    body["schema_version"] = "2"
    return body


def _replay_1_to_2(body: dict[str, Any]) -> dict[str, Any]:
    commands = decode_value(body["commands"])
    if not isinstance(commands, tuple):
        raise ValueError("El historial antiguo no contiene una tupla de comandos")
    body["command_count"] = len(commands)
    body["schema_version"] = "2"
    return body


def _manifest_1_to_2(body: dict[str, Any]) -> dict[str, Any]:
    body["metadata"] = {}
    body["dependencies"] = []
    body["schema_version"] = "2"
    return body


_MIGRATIONS: dict[tuple[str, str], Migration] = {
    ("snapshot", "1"): _snapshot_1_to_2,
    ("replay", "1"): _replay_1_to_2,
    ("manifest", "1"): _manifest_1_to_2,
}


def migrate_document(
    kind: str, body: Mapping[str, Any], target_version: str
) -> dict[str, Any]:
    """Aplica una cadena explícita; nunca adivina cómo migrar una versión."""

    migrated = deepcopy(dict(body))
    seen: set[str] = set()
    while migrated.get("schema_version") != target_version:
        version = migrated.get("schema_version")
        if not isinstance(version, str) or version in seen:
            raise ValueError(f"Versión de {kind} no válida o ciclo de migración")
        seen.add(version)
        migration = _MIGRATIONS.get((kind, version))
        if migration is None:
            raise ValueError(
                f"No existe migración de {kind} desde esquema {version}"
            )
        migrated = migration(migrated)
    return migrated
