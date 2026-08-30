#!/usr/bin/env python3
"""Verifica de forma reproducible las fuentes PDF del reglamento."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePath
import sys
from typing import cast, TypedDict

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs" / "RULES_SOURCES.json"
REQUIRED_FIELDS = {
    "id": str,
    "path": str,
    "name": str,
    "sha256": str,
    "size": int,
    "pages": int,
    "title": str,
    "declared_date": str,
    "normative_role": str,
    "repository_required": bool,
}
ROLES = {"base", "later-update"}


class Source(TypedDict):
    id: str
    path: str
    name: str
    sha256: str
    size: int
    pages: int
    title: str
    declared_date: str
    normative_role: str
    repository_required: bool


class Manifest(TypedDict):
    schema_version: int
    sources: list[object]


class RulesSourceError(ValueError):
    """Error determinista en el manifiesto o en una fuente declarada."""


def _fail(message: str) -> None:
    raise RulesSourceError(message)


def _load_manifest(path: Path) -> Manifest:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        _fail(f"manifiesto ilegible: {path}: {error}")
    if not isinstance(value, dict):
        _fail("manifiesto inválido: la raíz debe ser un objeto")
    if value.get("schema_version") != 1:
        _fail("manifiesto inválido: schema_version debe ser 1")
    if set(value) != {"schema_version", "sources"}:
        _fail("manifiesto inválido: campos raíz inesperados")
    if not isinstance(value["sources"], list) or not value["sources"]:
        _fail("manifiesto inválido: sources debe ser una lista no vacía")
    return cast(Manifest, value)


def _validate_source(value: object, index: int) -> Source:
    label = f"sources[{index}]"
    if not isinstance(value, dict):
        _fail(f"manifiesto inválido: {label} debe ser un objeto")
    source = cast(dict[str, object], value)
    if set(source) != set(REQUIRED_FIELDS):
        _fail(f"manifiesto inválido: campos incorrectos en {label}")
    for field, expected_type in REQUIRED_FIELDS.items():
        field_value = source[field]
        if type(field_value) is not expected_type or (expected_type is str and not field_value):
            _fail(f"manifiesto inválido: {label}.{field} tiene tipo o valor incorrecto")
    sha256 = cast(str, source["sha256"])
    if len(sha256) != 64 or any(character not in "0123456789abcdef" for character in sha256):
        _fail(f"manifiesto inválido: {label}.sha256 no es SHA-256 hexadecimal minúsculo")
    if cast(int, source["size"]) < 1 or cast(int, source["pages"]) < 1:
        _fail(f"manifiesto inválido: {label}.size y pages deben ser positivos")
    if source["normative_role"] not in ROLES:
        _fail(f"manifiesto inválido: {label}.normative_role desconocido")
    path = cast(str, source["path"])
    relative = PurePath(path)
    if relative.is_absolute():
        _fail(f"ruta absoluta rechazada: {path}")
    if ".." in relative.parts:
        _fail(f"traversal rechazado: {path}")
    return cast(Source, source)


def verify(manifest_path: Path = MANIFEST, root: Path = ROOT) -> list[str]:
    """Valida el manifiesto y sus archivos; devuelve diagnósticos ordenados."""
    manifest = _load_manifest(manifest_path)
    validated = [_validate_source(source, index) for index, source in enumerate(manifest["sources"])]
    ids = [source["id"] for source in validated]
    if len(ids) != len(set(ids)):
        _fail("manifiesto inválido: los id deben ser únicos")

    results: list[str] = []
    for source in sorted(validated, key=lambda item: item["id"]):
        identifier, relative = source["id"], source["path"]
        pdf = root / relative
        if not pdf.is_file():
            if not source["repository_required"]:
                results.append(f"SKIP [{identifier}] fuente no versionada ausente: {relative}")
                continue
            _fail(f"[{identifier}] archivo ausente: {relative}")
        size = pdf.stat().st_size
        if size != source["size"]:
            _fail(f"[{identifier}] tamaño divergente: esperado {source['size']}, obtenido {size}")
        with pdf.open("rb") as stream:
            header = stream.read(5)
            digest = hashlib.sha256(header)
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        if header != b"%PDF-":
            _fail(f"[{identifier}] cabecera PDF incorrecta: {relative}")
        actual_hash = digest.hexdigest()
        if actual_hash != source["sha256"]:
            _fail(f"[{identifier}] SHA-256 divergente: esperado {source['sha256']}, obtenido {actual_hash}")
        results.append(f"OK [{identifier}] {relative}")
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        results = verify(args.manifest, args.root)
    except RulesSourceError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1) from error
    for result in results:
        print(result)


if __name__ == "__main__":
    main()
