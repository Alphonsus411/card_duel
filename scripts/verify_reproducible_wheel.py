#!/usr/bin/env python3
"""Construye y audita dos wheels desde un worktree inmutable de ``HEAD``."""

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
from typing import NamedTuple
from zipfile import ZipFile, ZipInfo

from project_metadata import read_project_version

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_SUFFIXES = {
    ".db", ".sqlite", ".sqlite3", ".pyc", ".pyo", ".pem", ".key", ".pdf"
}
FORBIDDEN_PARTS = {"tests", "test", "__pycache__", ".git", ".github", ".idea"}
SECRET_PATTERN = re.compile(rb"(BEGIN (RSA |OPENSSH )?PRIVATE KEY|AKIA[0-9A-Z]{16})")


class WheelPolicy(NamedTuple):
    version: str
    wheel_name: str
    dist_info: str
    package_files: frozenset[str]
    allowed_content: frozenset[str]
    canonical_order: tuple[str, ...]


def policy_for(source: Path) -> WheelPolicy:
    """Deriva toda la política del contenido del checkout que se va a construir."""
    version = read_project_version(source)
    dist_info = f"card_duel_engine-{version}.dist-info"
    package_root = source / "src" / "card_duel_engine"
    package_files = frozenset(
        path.relative_to(source / "src").as_posix()
        for path in package_root.rglob("*.py")
        if path.is_file()
    )
    allowed = frozenset({
        *package_files,
        f"{dist_info}/METADATA",
        f"{dist_info}/WHEEL",
        f"{dist_info}/top_level.txt",
        f"{dist_info}/RECORD",
    })
    order = (
        tuple(sorted(package_files, key=lambda name: (name.count("/"), name)))
        + tuple(sorted(name for name in allowed if name.startswith(f"{dist_info}/") and not name.endswith("/RECORD")))
        + (f"{dist_info}/RECORD",)
    )
    return WheelPolicy(
        version=version,
        wheel_name=f"card_duel_engine-{version}-py3-none-any.whl",
        dist_info=dist_info,
        package_files=package_files,
        allowed_content=allowed,
        canonical_order=order,
    )


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(source: Path, output: Path, source_date_epoch: str, policy: WheelPolicy) -> Path:
    """Construye un wheel desde el checkout y con el timestamp indicado."""
    env = {**os.environ, "SOURCE_DATE_EPOCH": source_date_epoch}
    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(output), str(source)],
        check=True, env=env, cwd=source,
    )
    wheel = output / policy.wheel_name
    if not wheel.is_file():
        raise SystemExit(f"No se generó {policy.wheel_name}")
    return wheel


def metadata_signature(info: ZipInfo) -> tuple[object, ...]:
    return (info.filename, info.date_time, info.compress_type, info.external_attr, info.flag_bits)


def audit(wheel: Path, policy: WheelPolicy) -> dict[str, object]:
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
            if not (info.filename.startswith("card_duel_engine/") or info.filename.startswith(f"{policy.dist_info}/")):
                raise SystemExit(f"Archivo ajeno al paquete: {info.filename}")
            mode = (info.external_attr >> 16) & 0o777
            if mode not in {0, 0o644, 0o664}:
                raise SystemExit(f"Permisos no deterministas: {info.filename} ({mode:o})")
            if SECRET_PATTERN.search(archive.read(info)):
                raise SystemExit(f"Posible secreto en {info.filename}")

        if set(names) != policy.allowed_content:
            missing = sorted(policy.allowed_content - set(names))
            unexpected = sorted(set(names) - policy.allowed_content)
            raise SystemExit(f"Contenido divergente; faltan={missing}, sobran={unexpected}")
        if tuple(names) != policy.canonical_order:
            raise SystemExit("Orden ZIP divergente del orden canónico")

        metadata = archive.read(f"{policy.dist_info}/METADATA").decode("utf-8")
        wheel_metadata = archive.read(f"{policy.dist_info}/WHEEL").decode("utf-8")
        if f"Version: {policy.version}" not in metadata or "License-Expression: Apache-2.0" not in metadata:
            raise SystemExit("Versión o licencia incorrectas")
        runtime_dependencies = [
            line.removeprefix("Requires-Dist:").strip()
            for line in metadata.splitlines()
            if line.startswith("Requires-Dist:") and "extra ==" not in line
        ]
        if runtime_dependencies:
            raise SystemExit("El wheel declara dependencias de ejecución")
        if "Tag: py3-none-any" not in wheel_metadata or "Root-Is-Purelib: true" not in wheel_metadata:
            raise SystemExit("El wheel no es universal purelib")

        record_name = f"{policy.dist_info}/RECORD"
        rows = list(csv.reader(io.StringIO(archive.read(record_name).decode("utf-8"))))
        if len(rows) != len(names) or any(len(row) != 3 for row in rows) or {row[0] for row in rows} != set(names):
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
            "version": policy.version, "license": "Apache-2.0", "tag": "py3-none-any",
            "root_is_purelib": True, "runtime_dependencies": runtime_dependencies,
            "record_integrity": True,
            "pdfs_absent": ["Fantasy Tokens.pdf", "Fantasy Tokens Edicion Mitica.pdf"],
            "fixtures_absent": True, "production_cards_absent": True,
            "zip_order": names,
            "zip_entries": [metadata_signature(info) for info in infos],
        }


def main() -> None:
    root = ROOT
    # Capturamos identidad y tiempo antes de crear el directorio de build.
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    epoch = subprocess.check_output(
        ["git", "show", "-s", "--format=%ct", commit], cwd=root, text=True
    ).strip()
    destination = root / "dist"
    worktree: Path | None = None
    try:
        with tempfile.TemporaryDirectory(prefix="card-duel-wheel-") as temporary:
            base = Path(temporary)
            worktree = base / "source"
            subprocess.run(
                ["git", "worktree", "add", "--detach", str(worktree), commit],
                cwd=root, check=True,
            )
            policy = policy_for(worktree)
            first = build(worktree, base / "first", epoch, policy)
            second = build(worktree, base / "second", epoch, policy)
            first_report, second_report = audit(first, policy), audit(second, policy)
            if first.read_bytes() != second.read_bytes():
                raise SystemExit("Los wheels no son reproducibles byte a byte")
            if first_report["zip_entries"] != second_report["zip_entries"]:
                raise SystemExit("Timestamps, permisos, contenido u orden ZIP divergentes")

            destination.mkdir(exist_ok=True)
            final_wheel = destination / policy.wheel_name
            shutil.copyfile(first, final_wheel)
            if final_wheel.read_bytes() != first.read_bytes():
                raise SystemExit("El wheel copiado no coincide con el wheel auditado")
            digest = sha256(final_wheel)
            (destination / "SHA256SUMS").write_text(f"{digest}  {policy.wheel_name}\n", encoding="utf-8")
            public_report = {key: value for key, value in first_report.items() if key != "zip_entries"}
            public_report.update({
                "binary_identical_builds": True,
                "builds_compared": 2,
                "build_source": "detached-worktree",
                "source_tree_clean": True,
                "source_commit": commit,
                "source_date_epoch": int(epoch),
            })
            (destination / "wheel-audit.json").write_text(
                json.dumps(public_report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            print(json.dumps(public_report, sort_keys=True))
    finally:
        if worktree is not None:
            subprocess.run(["git", "worktree", "remove", "--force", str(worktree)], cwd=root, check=False)
        subprocess.run(["git", "worktree", "prune"], cwd=root, check=False)


if __name__ == "__main__":
    main()
