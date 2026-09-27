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


def _snapshot_3_to_4(body: dict[str, Any]) -> dict[str, Any]:
    """Make the unknowable legacy-history boundary explicit.

    Schema 3 persisted commands and a pending decision, but not the decision
    lifecycle.  Commands are retained as a compatibility projection, followed
    by a boundary saying that their interleaving with lifecycle transitions is
    unavailable.  New schema-4 entries appended after the boundary are total.
    """
    state = body.get("state")
    if not isinstance(state, dict) or state.get("$type") != "GameState":
        raise ValueError("El snapshot schema 3 no contiene un GameState válido")
    fields = state.get("fields")
    if not isinstance(fields, dict):
        raise ValueError("El GameState de schema 3 no tiene la forma esperada")
    commands_are_complete = body.pop("_legacy_history_commands_are_complete", False)
    existing_history = fields.get("history")
    if existing_history is not None:
        if not isinstance(existing_history, list):
            raise ValueError("El historial de schema 3 no es válido")
        body["state_digest"] = hashlib.sha256(
            canonical_json(state).encode("utf-8")
        ).hexdigest()
        body["schema_version"] = "4"
        return body
    commands = fields.get("command_history")
    if not isinstance(commands, list):
        raise ValueError("El snapshot schema 3 no contiene command_history válido")
    fields["history"] = [
        {"$type": "ExecutedCommand", "fields": {"command": command}}
        for command in commands
    ]
    if not commands_are_complete:
        fields["history"].append(
            {
                "$type": "HistoryBoundary",
                "fields": {
                    "source_schema_version": "3",
                    "pending_decision_was_present": (
                        fields.get("pending_decision") is not None
                    ),
                },
            }
        )
    body["state_digest"] = hashlib.sha256(
        canonical_json(state).encode("utf-8")
    ).hexdigest()
    body["schema_version"] = "4"
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
    ("snapshot", "2"): _snapshot_2_to_3,
    ("snapshot", "3"): _snapshot_3_to_4,
    ("replay", "1"): _replay_1_to_2,
    ("manifest", "1"): _manifest_1_to_2,
}


def migrate_document(
    kind: str, body: Mapping[str, Any], target_version: str
) -> dict[str, Any]:
    """Aplica una cadena explícita; nunca adivina cómo migrar una versión."""

    migrated = deepcopy(dict(body))
    original_version = migrated.get("schema_version")
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
        if kind == "snapshot" and version == "3" and original_version in {"1", "2"}:
            # Those schemas predate pending decisions, so their command-only
            # history is complete rather than an ambiguous lifecycle projection.
            migrated["_legacy_history_commands_are_complete"] = True
        migrated = migration(migrated)
    return migrated
