from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path
from typing import Any, Mapping

from ..catalog import CardCatalog
from ..domain.enums import CardKind, Zone
from ..domain.models import AbilitySourceProfile, CardDefinition, GameState, StackItem
from ..engine.game import EngineSemantics, GameEngine
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
        "engine_semantics": engine.semantics.name,
        "rules": encode_value(engine.rules),
        "catalog": encode_value(engine.catalog.definitions()),
        "state": _canonical_encoded_state(engine),
        "next_instance": engine._next_instance,
        "next_stack_item": engine._next_stack_item,
    }
    body["state_digest"] = hashlib.sha256(
        canonical_json(body["state"]).encode("utf-8")
    ).hexdigest()
    return body


def _checksum(body: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json(body).encode("utf-8")).hexdigest()


def _canonical_encoded_state(engine: GameEngine) -> Any:
    if engine.state is None:
        raise RuntimeError("No hay una partida que resumir")
    return encode_value(engine.state)


def _digest_encoded_state(encoded_state: Any) -> str:
    return hashlib.sha256(canonical_json(encoded_state).encode("utf-8")).hexdigest()


def state_digest(engine: GameEngine) -> str:
    return _digest_encoded_state(_canonical_encoded_state(engine))


def legacy_state_digest_without_ability_source_profile(engine: GameEngine) -> str:
    """Calcula la huella emitida por 0.20.x antes de AbilitySourceProfile.

    La poda se hace sobre la representación persistente, no sobre el estado vivo,
    para alcanzar cualquier ``StackItem`` contenido en el grafo codificado sin
    modificar el motor que se devuelve al llamador.
    """

    def omit_profile(value: Any) -> Any:
        if isinstance(value, list):
            return [omit_profile(item) for item in value]
        if not isinstance(value, dict):
            return value
        transformed = {key: omit_profile(item) for key, item in value.items()}
        if transformed.get("$type") == "StackItem":
            fields = transformed.get("fields")
            if isinstance(fields, dict):
                fields.pop("ability_source_profile", None)
        if transformed.get("$type") == "EffectDefinition":
            fields = transformed.get("fields")
            if isinstance(fields, dict):
                fields.pop("failure_destination_zone", None)
                fields.pop("exhaustion_policy", None)
        return transformed

    return _digest_encoded_state(omit_profile(_canonical_encoded_state(engine)))


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
    semantics_name = body.get("engine_semantics", EngineSemantics.CURRENT.name)
    if not isinstance(semantics_name, str):
        raise ValueError("La semántica declarada debe ser una cadena")
    try:
        semantics = EngineSemantics[semantics_name]
    except KeyError as exc:
        raise ValueError(
            f"Semántica de motor desconocida: {semantics_name!r}"
        ) from exc
    rules = decode_value(body["rules"])
    definitions = decode_value(body["catalog"])
    state = decode_value(body["state"])
    if not isinstance(rules, RuleSet) or not isinstance(state, GameState):
        raise ValueError("La instantánea no contiene reglas y estado válidos")
    if body.get("engine_version") != rules.version:
        raise ValueError("La versión declarada no coincide con las reglas persistidas")
    if (
        semantics is EngineSemantics.LEGACY_019
        and body["engine_version"] != "0.19.0"
    ):
        raise ValueError("LEGACY_019 solo es compatible con engine_version 0.19.0")
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
    engine = GameEngine._for_restoration(rules, catalog, semantics)
    engine.state = state
    engine._next_instance = int(body["next_instance"])
    engine._next_stack_item = int(body["next_stack_item"])
    if engine._next_instance < 1 or engine._next_stack_item < 1:
        raise ValueError("Los contadores persistidos no son válidos")
    _restore_safe_ability_source_profiles(engine)
    engine.validate_invariants()
    return engine


def _restore_safe_ability_source_profiles(engine: GameEngine) -> None:
    """Reconstruye perfiles históricos sin revalidar una activación ya apilada.

    Los snapshots anteriores al perfil conservan el id de instancia y el catálogo.
    Esos datos permiten recuperar la naturaleza impresa y, cuando sigue registrada,
    la definición sustituida. Si falta alguna pieza se materializa un perfil marcado
    como incierto; resolución lo tratará de forma conservadora ante inmunidades.
    """

    assert engine.state is not None
    state = engine.state

    def restore(item: StackItem) -> StackItem:
        if item.ability_id is None or item.ability_source_profile is not None:
            return item
        source = state.cards.get(item.source_card_id)
        printed = (
            engine.catalog.get(source.definition_id)
            if source is not None and source.definition_id in engine.catalog
            else None
        )
        effective_id = (
            source.overridden_definition_id or source.definition_id
            if source is not None
            else None
        )
        effective = (
            engine.catalog.get(effective_id)
            if effective_id is not None and effective_id in engine.catalog
            else None
        )
        ability_definition = next(
            (
                definition
                for definition in (effective, printed)
                if definition is not None
                and any(
                    ability.ability_id == item.ability_id
                    for ability in definition.abilities
                )
            ),
            None,
        )
        nature_is_certain = (
            source is not None
            and printed is not None
            and effective is not None
            and ability_definition is not None
            and (
                effective.kind is CardKind.CREATURE
                or source.transformed_as_creature
                or source.zone is Zone.BATTLEFIELD
            )
        )
        return replace(
            item,
            ability_source_profile=AbilitySourceProfile(
                source_card_id=item.source_card_id,
                printed_kind=(printed.kind if printed is not None else CardKind.EVENT),
                was_effective_creature=(
                    effective.kind is CardKind.CREATURE
                    if effective is not None
                    else True
                ) or bool(source and source.transformed_as_creature),
                was_permanent=(printed.permanent if printed is not None else True),
                was_on_battlefield=bool(source and source.zone is Zone.BATTLEFIELD),
                nature_is_certain=nature_is_certain,
            ),
        )

    state.stack[:] = [restore(item) for item in state.stack]
    state.pending_triggers[:] = [
        restore(item) for item in state.pending_triggers
    ]
    if state.pending_search is not None:
        state.pending_search.stack_item = restore(
            state.pending_search.stack_item
        )


def save_snapshot_file(engine: GameEngine, path: str | Path) -> Path:
    destination = Path(path)
    destination.write_text(dump_snapshot(engine), encoding="utf-8")
    return destination


def load_snapshot_file(path: str | Path) -> GameEngine:
    return load_snapshot(Path(path).read_text(encoding="utf-8"))
