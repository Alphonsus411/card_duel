from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from ..catalog import CardCatalog
from ..domain.models import CardDefinition, GameState
from ..engine.game import GameEngine
from ..rules.config import RuleSet
from .codec import canonical_json, decode_value, encode_value
from .migrations import migrate_document

SNAPSHOT_SCHEMA_VERSION = "2"


def _body(engine: GameEngine) -> dict[str, Any]:
    if engine.state is None:
        raise RuntimeError("No hay una partida que guardar")
    body = {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "engine_version": engine.rules.version,
        "rules": encode_value(engine.rules),
        "catalog": encode_value(engine.catalog.definitions()),
        "state": encode_value(engine.state),
        "next_instance": engine._next_instance,
        "next_stack_item": engine._next_stack_item,
    }
    body["state_digest"] = hashlib.sha256(
        canonical_json(body["state"]).encode("utf-8")
    ).hexdigest()
    return body


def _checksum(body: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json(body).encode("utf-8")).hexdigest()


def state_digest(engine: GameEngine) -> str:
    if engine.state is None:
        raise RuntimeError("No hay una partida que resumir")
    return hashlib.sha256(
        canonical_json(encode_value(engine.state)).encode("utf-8")
    ).hexdigest()


def dump_snapshot(engine: GameEngine, *, indent: int | None = 2) -> str:
    body = _body(engine)
    envelope = {"body": body, "sha256": _checksum(body)}
    return json.dumps(
        envelope,
        ensure_ascii=False,
        sort_keys=True,
        indent=indent,
        separators=None if indent is not None else (",", ":"),
    )


def _parse(payload: str | bytes | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8")
    parsed = json.loads(payload) if isinstance(payload, str) else dict(payload)
    if set(parsed) != {"body", "sha256"} or not isinstance(parsed["body"], dict):
        raise ValueError("La instantánea no tiene un sobre válido")
    if parsed["sha256"] != _checksum(parsed["body"]):
        raise ValueError("La huella de la instantánea no coincide")
    return migrate_document("snapshot", parsed["body"], SNAPSHOT_SCHEMA_VERSION)


def load_snapshot(payload: str | bytes | Mapping[str, Any]) -> GameEngine:
    body = _parse(payload)
    rules = decode_value(body["rules"])
    definitions = decode_value(body["catalog"])
    state = decode_value(body["state"])
    if not isinstance(rules, RuleSet) or not isinstance(state, GameState):
        raise ValueError("La instantánea no contiene reglas y estado válidos")
    if body.get("engine_version") != rules.version:
        raise ValueError("La versión declarada no coincide con las reglas persistidas")
    encoded_state_digest = hashlib.sha256(
        canonical_json(body["state"]).encode("utf-8")
    ).hexdigest()
    if body.get("state_digest") != encoded_state_digest:
        raise ValueError("La huella interna del estado no coincide")
    if not isinstance(definitions, tuple) or not all(
        isinstance(item, CardDefinition) for item in definitions
    ):
        raise ValueError("El catálogo persistido no es válido")
    catalog = CardCatalog()
    for definition in definitions:
        catalog.register(definition)
    engine = GameEngine(rules, catalog)
    engine.state = state
    engine._next_instance = int(body["next_instance"])
    engine._next_stack_item = int(body["next_stack_item"])
    if engine._next_instance < 1 or engine._next_stack_item < 1:
        raise ValueError("Los contadores persistidos no son válidos")
    engine.validate_invariants()
    return engine


def save_snapshot_file(engine: GameEngine, path: str | Path) -> Path:
    destination = Path(path)
    destination.write_text(dump_snapshot(engine), encoding="utf-8")
    return destination


def load_snapshot_file(path: str | Path) -> GameEngine:
    return load_snapshot(Path(path).read_text(encoding="utf-8"))
