from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from ..catalog import CardCatalog
from ..domain.enums import MatchStatus
from ..domain.models import CardDefinition
from ..engine.commands import GameCommand
from ..engine.game import GameEngine
from ..rules.config import RuleSet
from .codec import canonical_json, decode_value, encode_value
from .migrations import migrate_document
from .snapshot import state_digest

REPLAY_SCHEMA_VERSION = "2"


def _checksum(body: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json(body).encode("utf-8")).hexdigest()


def dump_replay(engine: GameEngine, *, indent: int | None = 2) -> str:
    state = engine.state
    if state is None:
        raise RuntimeError("No hay una partida que reproducir")
    body = {
        "schema_version": REPLAY_SCHEMA_VERSION,
        "engine_version": engine.rules.version,
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
    if body.get("engine_version") != rules.version:
        raise ValueError("La versión declarada no coincide con las reglas de reproducción")
    if not isinstance(definitions, tuple) or not all(
        isinstance(item, CardDefinition) for item in definitions
    ):
        raise ValueError("Catálogo de reproducción no válido")
    if not isinstance(commands, tuple) or not all(
        isinstance(item, GameCommand) for item in commands
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
    engine = GameEngine(rules, catalog)
    engine.new_match(decks, seed=int(body["seed"]), auto_start=False)
    for player_id in mulligans:
        engine.mulligan(player_id)
    if body["started"]:
        engine.start_match()
    for command in commands:
        engine.execute(command)
    if verify_digest and state_digest(engine) != body["final_digest"]:
        raise ValueError("La reproducción diverge de la huella final registrada")
    return engine
