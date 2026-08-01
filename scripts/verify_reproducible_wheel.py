#!/usr/bin/env python3
"""Construye y audita dos wheels aislados, seguros y binariamente idénticos."""

from __future__ import annotations

import base64
import csv
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tempfile
from zipfile import ZipFile, ZipInfo

VERSION = "0.19.0"
WHEEL_NAME = f"card_duel_engine-{VERSION}-py3-none-any.whl"
DIST_INFO = f"card_duel_engine-{VERSION}.dist-info"
FORBIDDEN_SUFFIXES = {".db", ".sqlite", ".sqlite3", ".pyc", ".pyo", ".pem", ".key"}
FORBIDDEN_PARTS = {"tests", "test", "__pycache__", ".git", ".github", ".idea"}
SECRET_PATTERN = re.compile(rb"(BEGIN (RSA |OPENSSH )?PRIVATE KEY|AKIA[0-9A-Z]{16})")

PACKAGE_FILES = frozenset({
    "card_duel_engine/__init__.py",
    "card_duel_engine/application.py",
    "card_duel_engine/catalog.py",
    "card_duel_engine/content/__init__.py",
    "card_duel_engine/content/manifest.py",
    "card_duel_engine/content/registry.py",
    "card_duel_engine/content/signature.py",
    "card_duel_engine/controllers/__init__.py",
    "card_duel_engine/controllers/base.py",
    "card_duel_engine/domain/__init__.py",
    "card_duel_engine/domain/enums.py",
    "card_duel_engine/domain/errors.py",
    "card_duel_engine/domain/models.py",
    "card_duel_engine/engine/__init__.py",
    "card_duel_engine/engine/combat.py",
    "card_duel_engine/engine/commands.py",
    "card_duel_engine/engine/effects.py",
    "card_duel_engine/engine/game.py",
    "card_duel_engine/engine/stack.py",
    "card_duel_engine/engine/zones.py",
    "card_duel_engine/persistence/__init__.py",
    "card_duel_engine/persistence/codec.py",
    "card_duel_engine/persistence/migrations.py",
    "card_duel_engine/persistence/replay.py",
    "card_duel_engine/persistence/snapshot.py",
    "card_duel_engine/rules/__init__.py",
    "card_duel_engine/rules/config.py",
    "card_duel_engine/rules/resolvers.py",
    "card_duel_engine/service.py",
    "card_duel_engine/simulation/__init__.py",
    "card_duel_engine/simulation/agents.py",
    "card_duel_engine/simulation/runner.py",
    "card_duel_engine/storage/__init__.py",
    "card_duel_engine/storage/base.py",
    "card_duel_engine/storage/sqlite.py",
})
ALLOWED_CONTENT = frozenset({
    *PACKAGE_FILES,
    f"{DIST_INFO}/METADATA",
    f"{DIST_INFO}/WHEEL",
    f"{DIST_INFO}/top_level.txt",
    f"{DIST_INFO}/RECORD",
})
CANONICAL_ORDER = (
    tuple(sorted(
        (name for name in ALLOWED_CONTENT if name.startswith("card_duel_engine/")),
        key=lambda name: (name.count("/"), name),
    ))
    + tuple(sorted(name for name in ALLOWED_CONTENT if name.startswith(f"{DIST_INFO}/") and not name.endswith("/RECORD")))
    + (f"{DIST_INFO}/RECORD",)
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(root: Path, output: Path, epoch: str) -> Path:
    env = {**os.environ, "SOURCE_DATE_EPOCH": epoch}
    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(output), str(root)],
        check=True, env=env,
    )
    wheel = output / WHEEL_NAME
    if not wheel.is_file():
        raise SystemExit(f"No se generó {WHEEL_NAME}")
    return wheel


def metadata_signature(info: ZipInfo) -> tuple[object, ...]:
    return (info.filename, info.date_time, info.compress_type, info.external_attr, info.flag_bits)


def audit(wheel: Path) -> dict[str, object]:
    with ZipFile(wheel) as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        if len(names) != len(set(names)):
            raise SystemExit("El ZIP contiene rutas duplicadas")
        for info in infos:
            path = PurePosixPath(info.filename)
            if (path.is_absolute() or ".." in path.parts or "\\" in info.filename
                    or any(part.lower() in FORBIDDEN_PARTS for part in path.parts)
                    or path.suffix.lower() in FORBIDDEN_SUFFIXES):
                raise SystemExit(f"Ruta peligrosa o ajena: {info.filename}")
            if not (info.filename.startswith("card_duel_engine/") or info.filename.startswith(f"{DIST_INFO}/")):
                raise SystemExit(f"Archivo ajeno al paquete: {info.filename}")
            mode = (info.external_attr >> 16) & 0o777
            if mode not in {0, 0o644, 0o664}:
                raise SystemExit(f"Permisos no deterministas: {info.filename} ({mode:o})")
            if SECRET_PATTERN.search(archive.read(info)):
                raise SystemExit(f"Posible secreto en {info.filename}")

        if set(names) != ALLOWED_CONTENT:
            missing = sorted(ALLOWED_CONTENT - set(names))
            unexpected = sorted(set(names) - ALLOWED_CONTENT)
            raise SystemExit(f"Contenido divergente; faltan={missing}, sobran={unexpected}")
        if tuple(names) != CANONICAL_ORDER:
            raise SystemExit("Orden ZIP divergente del orden canónico")

        metadata = archive.read(f"{DIST_INFO}/METADATA").decode("utf-8")
        wheel_metadata = archive.read(f"{DIST_INFO}/WHEEL").decode("utf-8")
        if f"Version: {VERSION}" not in metadata or "License-Expression: Apache-2.0" not in metadata:
            raise SystemExit("Versión o licencia incorrectas")
        if any(line.startswith("Requires-Dist:") and 'extra == "dev"' not in line for line in metadata.splitlines()):
            raise SystemExit("El wheel declara dependencias de ejecución")
        if "Tag: py3-none-any" not in wheel_metadata or "Root-Is-Purelib: true" not in wheel_metadata:
            raise SystemExit("El wheel no es universal purelib")

        record_name = f"{DIST_INFO}/RECORD"
        rows = list(csv.reader(io.StringIO(archive.read(record_name).decode("utf-8"))))
        if len(rows) != len(names) or {row[0] for row in rows} != set(names):
            raise SystemExit("RECORD no enumera exactamente todo el wheel")
        for name, digest, size in rows:
            data = archive.read(name)
            if name == record_name:
                if digest or size:
                    raise SystemExit("La entrada RECORD debe carecer de hash y tamaño")
                continue
            expected = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
            if digest != f"sha256={expected}" or size != str(len(data)):
                raise SystemExit(f"RECORD corrupto para {name}")

        return {
            "filename": wheel.name, "sha256": sha256(wheel), "files": len(infos),
            "version": VERSION, "license": "Apache-2.0", "tag": "py3-none-any",
            "root_is_purelib": True, "runtime_dependencies": 0,
            "record_integrity": True,
            "zip_order": names,
            "zip_entries": [metadata_signature(info) for info in infos],
        }


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    epoch = subprocess.check_output(["git", "show", "-s", "--format=%ct", "HEAD"], cwd=root, text=True).strip()
    destination = root / "dist"
    destination.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="card-duel-wheel-") as temporary:
        base = Path(temporary)
        first = build(root, base / "first", epoch)
        second = build(root, base / "second", epoch)
        first_report, second_report = audit(first), audit(second)
        if first.read_bytes() != second.read_bytes():
            raise SystemExit("Los wheels o sus SHA-256 no son reproducibles")
        if first_report["zip_entries"] != second_report["zip_entries"]:
            raise SystemExit("Timestamps, permisos, contenido u orden ZIP divergentes")
        final_wheel = destination / WHEEL_NAME
        shutil.copyfile(first, final_wheel)
        digest = sha256(final_wheel)
        (destination / "SHA256SUMS").write_text(f"{digest}  {WHEEL_NAME}\n", encoding="utf-8")
        public_report = {key: value for key, value in first_report.items() if key != "zip_entries"}
        public_report.update({"binary_identical_builds": 2, "source_date_epoch": int(epoch)})
        (destination / "wheel-audit.json").write_text(json.dumps(public_report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(public_report, sort_keys=True))


if __name__ == "__main__":
    main()
