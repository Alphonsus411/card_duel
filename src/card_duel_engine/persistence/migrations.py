from __future__ import annotations

import hashlib
from copy import deepcopy
from typing import Any, Callable, Mapping

from ..domain.models import ExecutedCommand
from ..engine.commands import EXECUTABLE_COMMAND_TYPE_SET
from .codec import canonical_json, decode_value, encode_value

Migration = Callable[[dict[str, Any]], dict[str, Any]]


def _snapshot_1_to_2(body: dict[str, Any]) -> dict[str, Any]:
    body["state_digest"] = hashlib.sha256(
        canonical_json(body["state"]).encode("utf-8")
    ).hexdigest()
    body["schema_version"] = "2"
    return body


def _snapshot_2_to_3(body: dict[str, Any]) -> dict[str, Any]:
    state = body.get("state")
    if not isinstance(state, dict) or state.get("$type") != "GameState":
        raise ValueError("El snapshot antiguo no contiene un GameState válido")
    fields = state.get("fields")
    if not isinstance(fields, dict) or "pending_decision" in fields:
        raise ValueError("El GameState de schema 2 no tiene la forma esperada")
    fields["pending_decision"] = None
    body["state_digest"] = hashlib.sha256(
        canonical_json(state).encode("utf-8")
    ).hexdigest()
    body["schema_version"] = "3"
    return body


def _replay_1_to_2(body: dict[str, Any]) -> dict[str, Any]:
    commands = decode_value(body["commands"])
    if not isinstance(commands, tuple):
        raise ValueError("El historial antiguo no contiene una tupla de comandos")
    body["command_count"] = len(commands)
    body["schema_version"] = "2"
    return body


def _replay_2_to_3(body: dict[str, Any]) -> dict[str, Any]:
    """Proyecta el historial v2 (sólo comandos) al historial total tipado."""
    commands = decode_value(body.get("commands"))
    if not isinstance(commands, tuple) or not all(
        type(command) in EXECUTABLE_COMMAND_TYPE_SET for command in commands
    ):
        raise ValueError("El historial v2 no contiene comandos válidos")
    command_count = body.get("command_count")
    if type(command_count) is not int or command_count != len(commands):
        raise ValueError("El número declarado de comandos v2 no coincide")
    history = tuple(ExecutedCommand(command) for command in commands)
    body["history"] = encode_value(history)
    body["history_count"] = len(history)
    body["schema_version"] = "3"
    return body


def _manifest_1_to_2(body: dict[str, Any]) -> dict[str, Any]:
    body["metadata"] = {}
    body["dependencies"] = []
    body["schema_version"] = "2"
    return body


_MIGRATIONS: dict[tuple[str, str], Migration] = {
    ("snapshot", "1"): _snapshot_1_to_2,
    ("snapshot", "2"): _snapshot_2_to_3,
    ("replay", "1"): _replay_1_to_2,
    ("replay", "2"): _replay_2_to_3,
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
