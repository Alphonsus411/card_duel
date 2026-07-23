from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from ..catalog import CardCatalog
from ..domain.models import CardDefinition
from ..persistence.codec import decode_value, encode_value
from ..persistence.migrations import migrate_document
from ..rules.config import RuleSet

MANIFEST_SCHEMA_VERSION = "2"


def _version_tuple(value: str) -> tuple[int, ...]:
    try:
        return tuple(int(part) for part in value.split("."))
    except ValueError as exc:
        raise ValueError(f"Versión semántica no válida: {value}") from exc


@dataclass(frozen=True)
class CollectionManifest:
    collection_id: str
    name: str
    revision: int
    engine_min_version: str
    cards: tuple[CardDefinition, ...]
    metadata: dict[str, str] = field(default_factory=dict)
    dependencies: tuple[str, ...] = ()
    schema_version: str = MANIFEST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != MANIFEST_SCHEMA_VERSION:
            raise ValueError("Versión de manifiesto no compatible")
        if not self.collection_id or not self.name:
            raise ValueError("La colección necesita identificador y nombre")
        if self.revision < 1:
            raise ValueError("La revisión de colección debe ser positiva")
        if type(self.revision) is not int:
            raise ValueError("La revisión de colección debe ser un entero")
        _version_tuple(self.engine_min_version)
        if any(not isinstance(key, str) or not isinstance(value, str) for key, value in self.metadata.items()):
            raise ValueError("Los metadatos de colección deben ser pares de texto")
        if len(self.dependencies) != len(set(self.dependencies)):
            raise ValueError("La colección contiene dependencias duplicadas")
        if self.collection_id in self.dependencies:
            raise ValueError("Una colección no puede depender de sí misma")
        ids = [card.card_id for card in self.cards]
        if len(ids) != len(set(ids)):
            raise ValueError("El manifiesto contiene identificadores de carta duplicados")
        if any(card.set_id != self.collection_id for card in self.cards):
            raise ValueError("Todas las cartas deben pertenecer a la colección declarada")


def dump_manifest(manifest: CollectionManifest, *, indent: int | None = 2) -> str:
    payload = {
        "schema_version": manifest.schema_version,
        "collection_id": manifest.collection_id,
        "name": manifest.name,
        "revision": manifest.revision,
        "engine_min_version": manifest.engine_min_version,
        "cards": [encode_value(card) for card in manifest.cards],
        "metadata": dict(manifest.metadata),
        "dependencies": list(manifest.dependencies),
    }
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        indent=indent,
        separators=None if indent is not None else (",", ":"),
    )


def load_manifest(
    payload: str | bytes | Mapping[str, Any],
    *,
    engine_version: str | None = None,
) -> CollectionManifest:
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8")
    raw = json.loads(payload) if isinstance(payload, str) else dict(payload)
    data = migrate_document("manifest", raw, MANIFEST_SCHEMA_VERSION)
    expected = {
        "schema_version",
        "collection_id",
        "name",
        "revision",
        "engine_min_version",
        "cards",
        "metadata",
        "dependencies",
    }
    if set(data) != expected or not isinstance(data["cards"], list):
        raise ValueError("La estructura del manifiesto no es válida")
    cards = tuple(decode_value(item) for item in data["cards"])
    if not all(isinstance(card, CardDefinition) for card in cards):
        raise ValueError("El manifiesto contiene elementos que no son cartas")
    manifest = CollectionManifest(
        schema_version=data["schema_version"],
        collection_id=data["collection_id"],
        name=data["name"],
        revision=data["revision"],
        engine_min_version=data["engine_min_version"],
        cards=cards,
        metadata=data["metadata"],
        dependencies=tuple(data["dependencies"]),
    )
    current = engine_version or RuleSet().version
    if _version_tuple(current) < _version_tuple(manifest.engine_min_version):
        raise ValueError(
            f"La colección requiere motor {manifest.engine_min_version} o posterior"
        )
    return manifest


def save_manifest_file(manifest: CollectionManifest, path: str | Path) -> Path:
    destination = Path(path)
    destination.write_text(dump_manifest(manifest), encoding="utf-8")
    return destination


def load_manifest_file(
    path: str | Path, *, engine_version: str | None = None
) -> CollectionManifest:
    return load_manifest(
        Path(path).read_text(encoding="utf-8"), engine_version=engine_version
    )


def register_manifest(catalog: CardCatalog, manifest: CollectionManifest) -> None:
    conflicts = tuple(card.card_id for card in manifest.cards if card.card_id in catalog)
    if conflicts:
        raise ValueError(f"La colección colisiona con el catálogo: {conflicts}")
    for card in manifest.cards:
        catalog.register(card)
