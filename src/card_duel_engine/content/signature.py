"""Sobres de firma de colecciones tratados exclusivamente como datos."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping

from .manifest import CollectionManifest, dump_manifest, load_manifest

SIGNATURE_ENVELOPE_SCHEMA_VERSION = "1"


@dataclass(frozen=True)
class CollectionSignatureEnvelope:
    """Firma separada cuyo contenido firmado es el manifiesto canónico."""

    manifest: str
    key_id: str
    algorithm: str
    signature: str
    schema_version: str = SIGNATURE_ENVELOPE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        values = (self.manifest, self.key_id, self.algorithm, self.signature)
        if any(type(value) is not str for value in values):
            raise ValueError("Los campos del sobre de firma deben ser texto")
        if self.schema_version != SIGNATURE_ENVELOPE_SCHEMA_VERSION:
            raise ValueError("Versión de sobre de firma no compatible")
        if not self.key_id or not self.algorithm or not self.signature:
            raise ValueError("El sobre de firma contiene campos vacíos")
        parsed = load_manifest(self.manifest)
        if self.manifest != dump_manifest(parsed, indent=None):
            raise ValueError("El manifiesto del sobre no es canónico")

    def collection_manifest(self) -> CollectionManifest:
        return load_manifest(self.manifest)


def dump_signature_envelope(
    envelope: CollectionSignatureEnvelope, *, indent: int | None = 2
) -> str:
    payload = {
        "schema_version": envelope.schema_version,
        "manifest": envelope.manifest,
        "key_id": envelope.key_id,
        "algorithm": envelope.algorithm,
        "signature": envelope.signature,
    }
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        indent=indent,
        separators=None if indent is not None else (",", ":"),
    )


def load_signature_envelope(
    payload: str | bytes | Mapping[str, Any],
) -> CollectionSignatureEnvelope:
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8")
    raw = json.loads(payload) if isinstance(payload, str) else dict(payload)
    expected = {"schema_version", "manifest", "key_id", "algorithm", "signature"}
    if type(raw) is not dict or set(raw) != expected:
        raise ValueError("La estructura del sobre de firma no es válida")
    if any(type(raw[field]) is not str for field in expected):
        raise ValueError("Los campos del sobre de firma deben ser texto")
    return CollectionSignatureEnvelope(
        schema_version=raw["schema_version"],
        manifest=raw["manifest"],
        key_id=raw["key_id"],
        algorithm=raw["algorithm"],
        signature=raw["signature"],
    )
