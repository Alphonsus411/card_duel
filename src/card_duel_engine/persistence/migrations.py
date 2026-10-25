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


def _snapshot_3_to_4(body: dict[str, Any]) -> dict[str, Any]:
    """Materializa sólo la historia que un snapshot v3 puede demostrar.

    V3 persistía ``command_history``, pero no el lifecycle de decisiones. Si hay
    una decisión en el slot, su apertura (y quizá su cierre) no puede inferirse
    honestamente del estado final: conservamos el estado, marcamos el prefijo
    incompleto y dejamos que ``dump_replay`` falle de forma cerrada.
    """
    state = body.get("state")
    if not isinstance(state, dict) or state.get("$type") != "GameState":
        raise ValueError("El snapshot v3 no contiene el GameState esperado")
    fields = state.get("fields")
    if not isinstance(fields, dict):
        raise ValueError("El GameState de schema 3 no tiene la forma esperada")
    if "history" in fields or "history_prefix_complete" in fields:
        raise ValueError("El GameState v3 contiene historia nueva de forma ambigua")
    if "command_history" not in fields or "pending_decision" not in fields:
        raise ValueError("El GameState de schema 3 no tiene la forma esperada")

    commands = decode_value(fields["command_history"])
    if not isinstance(commands, list) or not all(
        type(command) in EXECUTABLE_COMMAND_TYPE_SET for command in commands
    ):
        raise ValueError("El historial de comandos v3 no es válido")
    # No se sintetizan DecisionOpened/Closed/Consumed: no están en v3.
    fields["history"] = encode_value(
        [ExecutedCommand(command) for command in commands]
    )
    fields["history_prefix_complete"] = fields["pending_decision"] is None
    body["state_digest"] = hashlib.sha256(
        canonical_json(state).encode("utf-8")
    ).hexdigest()
    body["schema_version"] = "4"
    return body


def _add_legacy_prevention_profile(
    encoded_mapping: Any,
    *,
    type_name: str,
    legacy_amount_field: str,
    profile_field: str,
    reservations_field: str,
) -> None:
    if not isinstance(encoded_mapping, dict) or set(encoded_mapping) != {"$mapping"}:
        raise ValueError("El snapshot v4 no contiene un mapeo de prevención válido")
    entries = encoded_mapping["$mapping"]
    if not isinstance(entries, list):
        raise ValueError("El snapshot v4 contiene entradas de prevención inválidas")
    for entry in entries:
        if not isinstance(entry, list) or len(entry) != 2:
            raise ValueError("El snapshot v4 contiene una entrada de prevención inválida")
        value = entry[1]
        if not isinstance(value, dict) or value.get("$type") != type_name:
            raise ValueError("El snapshot v4 contiene un estado de prevención inválido")
        fields = value.get("fields")
        if not isinstance(fields, dict):
            raise ValueError("El snapshot v4 contiene campos de prevención inválidos")
        if profile_field in fields or reservations_field in fields:
            raise ValueError("El snapshot v4 mezcla perfiles de prevención incompatibles")
        if type(fields.get(legacy_amount_field)) is not int:
            raise ValueError("El snapshot v4 no contiene una reserva escalar válida")
        fields[profile_field] = {
            "$enum": "DamagePreventionProfile",
            "name": "LEGACY_UNTYPED",
        }
        fields[reservations_field] = {"$tuple": []}


def _snapshot_4_to_5(body: dict[str, Any]) -> dict[str, Any]:
    """Hace explícito el perfil de reservas escalares sin reclasificarlas."""

    state = body.get("state")
    if not isinstance(state, dict) or state.get("$type") != "GameState":
        raise ValueError("El snapshot v4 no contiene el GameState esperado")
    fields = state.get("fields")
    if not isinstance(fields, dict):
        raise ValueError("El GameState de schema 4 no tiene la forma esperada")
    _add_legacy_prevention_profile(
        fields.get("cards"),
        type_name="CardInstance",
        legacy_amount_field="damage_prevention",
        profile_field="damage_prevention_profile",
        reservations_field="damage_prevention_reservations",
    )
    _add_legacy_prevention_profile(
        fields.get("players"),
        type_name="PlayerState",
        legacy_amount_field="wound_prevention",
        profile_field="wound_prevention_profile",
        reservations_field="wound_prevention_reservations",
    )
    body["state_digest"] = hashlib.sha256(
        canonical_json(state).encode("utf-8")
    ).hexdigest()
    body["schema_version"] = "5"
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


def _replay_3_to_4(body: dict[str, Any]) -> dict[str, Any]:
    """Versiona el digest que incorpora perfiles de prevención persistibles."""

    body["schema_version"] = "4"
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
    ("snapshot", "4"): _snapshot_4_to_5,
    ("replay", "1"): _replay_1_to_2,
    ("replay", "2"): _replay_2_to_3,
    ("replay", "3"): _replay_3_to_4,
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
