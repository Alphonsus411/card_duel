from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from ..catalog import CardCatalog
from ..domain.enums import MatchStatus
from ..domain.models import CardDefinition
from ..engine.commands import EXECUTABLE_COMMAND_TYPE_SET
from ..engine.game import EngineSemantics, GameEngine
from ..rules.config import RuleSet
from .codec import canonical_json, decode_value, encode_value
from .migrations import migrate_document
from .snapshot import legacy_state_digest_without_ability_source_profile, state_digest

REPLAY_SCHEMA_VERSION = "2"
LEGACY_PROFILE_DIGEST_VERSIONS = frozenset(("0.20.0", "0.20.1"))


def _checksum(body: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json(body).encode("utf-8")).hexdigest()


def dump_replay(engine: GameEngine, *, indent: int | None = 2) -> str:
    state = engine.state
    if state is None:
        raise RuntimeError("No hay una partida que reproducir")
    body = {
        "schema_version": REPLAY_SCHEMA_VERSION,
        "engine_version": (
            "0.19.0"
            if engine.semantics is EngineSemantics.LEGACY_019
            else engine.rules.version
        ),
        "engine_semantics": engine.semantics.name,
        "rules": encode_value(engine.rules),
        "catalog": encode_value(engine.catalog.definitions()),
        "initial_decks": encode_value(state.initial_decks),
        "turn_order": encode_value(state.turn_order),
        "seed": state.random_seed,
        "mulligans": encode_value(tuple(state.setup_mulligans)),
        "started": state.status is not MatchStatus.SETUP,
        "commands": encode_value(tuple(state.command_history)),
        "command_count": len(state.command_history),
        "final_digest": state_digest(engine),
    }
    return json.dumps(
        {"body": body, "sha256": _checksum(body)},
        ensure_ascii=False,
        sort_keys=True,
        indent=indent,
        separators=None if indent is not None else (",", ":"),
    )


def replay_from_log(
    payload: str | bytes | Mapping[str, Any], *, verify_digest: bool = True
) -> GameEngine:
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8")
    envelope = json.loads(payload) if isinstance(payload, str) else dict(payload)
    if set(envelope) != {"body", "sha256"} or not isinstance(envelope["body"], dict):
        raise ValueError("El registro de reproducción no tiene un sobre válido")
    original_body = envelope["body"]
    if envelope["sha256"] != _checksum(original_body):
        raise ValueError("La huella del registro de reproducción no coincide")
    body = migrate_document("replay", original_body, REPLAY_SCHEMA_VERSION)
    rules = decode_value(body["rules"])
    definitions = decode_value(body["catalog"])
    initial_decks = decode_value(body["initial_decks"])
    turn_order = decode_value(body["turn_order"])
    mulligans = decode_value(body["mulligans"])
    commands = decode_value(body["commands"])
    if not isinstance(rules, RuleSet):
        raise ValueError("Reglas de reproducción no válidas")
    engine_version = body.get("engine_version")
    if engine_version != rules.version:
        raise ValueError("La versión declarada no coincide con las reglas de reproducción")
    if engine_version != "0.19.0" and not str(engine_version).startswith("0.20."):
        raise ValueError(f"Versión de reproducción no compatible: {engine_version!r}")
    if not isinstance(definitions, tuple) or not all(
        isinstance(item, CardDefinition) for item in definitions
    ):
        raise ValueError("Catálogo de reproducción no válido")
    if not isinstance(commands, tuple) or not all(
        type(item) in EXECUTABLE_COMMAND_TYPE_SET for item in commands
    ):
        raise ValueError("Secuencia de comandos no válida")
    if body.get("command_count") != len(commands):
        raise ValueError("El número declarado de comandos no coincide")
    by_id = {definition.card_id: definition for definition in definitions}
    catalog = CardCatalog()
    for definition in definitions:
        catalog.register(definition)
    try:
        if not isinstance(turn_order, tuple) or set(turn_order) != set(initial_decks):
            raise ValueError("Orden inicial de jugadores no válido")
        decks = {
            player_id: [by_id[definition_id] for definition_id in initial_decks[player_id]]
            for player_id in turn_order
        }
    except (AttributeError, KeyError, TypeError) as exc:
        raise ValueError("Mazos iniciales no válidos") from exc
    if "engine_semantics" not in body:
        semantics = (
            EngineSemantics.LEGACY_019
            if engine_version == "0.19.0"
            else EngineSemantics.CURRENT
        )
    else:
        semantics_name = body["engine_semantics"]
        if not isinstance(semantics_name, str):
            raise ValueError("Semántica de motor de reproducción no válida")
        try:
            semantics = EngineSemantics[semantics_name]
        except KeyError as exc:
            raise ValueError(
                "Semántica de motor de reproducción no válida"
            ) from exc
        if semantics not in (EngineSemantics.CURRENT, EngineSemantics.LEGACY_019):
            raise ValueError("Semántica de motor de reproducción no válida")
        if semantics is EngineSemantics.LEGACY_019 and engine_version != "0.19.0":
            raise ValueError(
                "La semántica LEGACY_019 requiere la versión 0.19.0"
            )
    engine = GameEngine._for_restoration(rules, catalog, semantics)
    engine.new_match(decks, seed=int(body["seed"]), auto_start=False)
    for player_id in mulligans:
        engine.mulligan(player_id)
    if body["started"]:
        engine.start_match()
    for command in commands:
        engine.execute(command)
    if verify_digest:
        expected_digest = body["final_digest"]
        digest_matches = state_digest(engine) == expected_digest
        if not digest_matches and _is_affected_020_version(engine_version):
            digest_matches = (
                legacy_state_digest_without_ability_source_profile(engine)
                == expected_digest
            )
        if not digest_matches:
            raise ValueError("La reproducción diverge de la huella final registrada")
    return engine


def _is_affected_020_version(version: object) -> bool:
    """Limit the compatibility escape hatch to versions that emitted the digest."""
    return version in LEGACY_PROFILE_DIGEST_VERSIONS
