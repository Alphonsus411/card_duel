from __future__ import annotations

import hashlib
from copy import deepcopy
from dataclasses import replace
from typing import Any, Callable, Mapping

from ..domain.enums import PendingDecisionStatus
from ..domain.models import (
    DecisionClosed,
    DecisionConsumed,
    DecisionOpened,
    DecisionTransitionEntry,
    ExecutedCommand,
    PendingDecision,
)
from ..engine.commands import EXECUTABLE_COMMAND_TYPE_SET
from .codec import canonical_json, decode_value, encode_value

Migration = Callable[[dict[str, Any]], dict[str, Any]]


def _history_reconstructs_pending_decision(
    history: list[ExecutedCommand | DecisionTransitionEntry],
    pending_decision: PendingDecision | None,
) -> bool:
    """Comprueba que el lifecycle preservado demuestra el slot final."""
    reconstructed: PendingDecision | None = None
    for entry in history:
        if isinstance(entry, ExecutedCommand):
            continue
        transition = entry.transition
        if isinstance(transition, DecisionOpened):
            if reconstructed is not None:
                return False
            reconstructed = PendingDecision(
                decision_id=transition.decision_id,
                semantic_family=transition.semantic_family,
                authorized_elector=transition.authorized_elector,
                audience=transition.audience,
                authorized_opaque_options=transition.authorized_opaque_options,
                state_version=transition.state_version,
                origin=transition.origin,
                status=PendingDecisionStatus.PENDING,
            )
        elif isinstance(transition, DecisionClosed):
            if (
                reconstructed is None
                or reconstructed.status is not PendingDecisionStatus.PENDING
                or transition.decision_id != reconstructed.decision_id
                or transition.actor != reconstructed.authorized_elector
                or transition.selected_option
                not in reconstructed.authorized_opaque_options
                or transition.known_state_version != reconstructed.state_version
            ):
                return False
            reconstructed = replace(
                reconstructed,
                status=PendingDecisionStatus.CLOSED,
                selected_option=transition.selected_option,
            )
        elif isinstance(transition, DecisionConsumed):
            if (
                reconstructed is None
                or reconstructed.status is not PendingDecisionStatus.CLOSED
                or transition.decision_id != reconstructed.decision_id
                or transition.state_version != reconstructed.state_version
            ):
                return False
            reconstructed = None
        else:
            return False
    return reconstructed == pending_decision


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

    Los primeros snapshots v3 no persistían el lifecycle de decisiones. Durante
    W1.3 hubo además escritores v3 que ya incluían ``history``; esa historia es
    autoritativa y debe conservarse. Para la forma antigua sólo materializamos
    lo demostrable a partir de ``command_history``.
    """
    state = body.get("state")
    if not isinstance(state, dict) or state.get("$type") != "GameState":
        raise ValueError("El snapshot v3 no contiene el GameState esperado")
    fields = state.get("fields")
    if not isinstance(fields, dict):
        raise ValueError("El GameState de schema 3 no tiene la forma esperada")
    if "history_prefix_complete" in fields:
        raise ValueError("El GameState v3 contiene historia nueva de forma ambigua")
    if "command_history" not in fields or "pending_decision" not in fields:
        raise ValueError("El GameState de schema 3 no tiene la forma esperada")

    commands = decode_value(fields["command_history"])
    if not isinstance(commands, list) or not all(
        type(command) in EXECUTABLE_COMMAND_TYPE_SET for command in commands
    ):
        raise ValueError("El historial de comandos v3 no es válido")
    if "history" in fields:
        history = decode_value(fields["history"])
        if not isinstance(history, list) or any(
            not isinstance(entry, (ExecutedCommand, DecisionTransitionEntry))
            for entry in history
        ):
            raise ValueError("El historial total v3 no es válido")
        projected_commands = [
            entry.command for entry in history if isinstance(entry, ExecutedCommand)
        ]
        if projected_commands != commands:
            raise ValueError("La proyección de comandos del historial v3 no coincide")
        pending_decision = decode_value(fields["pending_decision"])
        if pending_decision is not None and not isinstance(
            pending_decision, PendingDecision
        ):
            raise ValueError("La decisión pendiente v3 no es válida")
        # Algunos escritores interinos volvieron a serializar una historia
        # sintetizada (sólo comandos). La presencia del campo no demuestra que
        # incluya el lifecycle necesario para reconstruir el slot pendiente.
        fields["history_prefix_complete"] = _history_reconstructs_pending_decision(
            history, pending_decision
        )
    else:
        # No se sintetizan DecisionOpened/Closed/Consumed: no están en esta forma.
        fields["history"] = encode_value(
            [ExecutedCommand(command) for command in commands]
        )
        fields["history_prefix_complete"] = fields["pending_decision"] is None
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
    ("snapshot", "3"): _snapshot_3_to_4,
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
