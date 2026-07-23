#!/usr/bin/env python3
"""Construye dos wheels aislados y exige identidad binaria y metadatos válidos."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from zipfile import ZipFile

WHEEL_NAME = "card_duel_engine-0.14.0-py3-none-any.whl"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(root: Path, output: Path, epoch: str) -> Path:
    env = {**os.environ, "SOURCE_DATE_EPOCH": epoch}
    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(output), str(root)],
        check=True,
        env=env,
    )
    wheel = output / WHEEL_NAME
    if not wheel.is_file():
        raise SystemExit(f"No se generó {WHEEL_NAME}")
    return wheel


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    epoch = subprocess.check_output(
        ["git", "show", "-s", "--format=%ct", "HEAD"], cwd=root, text=True
    ).strip()
    with tempfile.TemporaryDirectory(prefix="card-duel-wheel-") as temporary:
        base = Path(temporary)
        first = build(root, base / "first", epoch)
        second = build(root, base / "second", epoch)
        hashes = (sha256(first), sha256(second))
        print(f"SOURCE_DATE_EPOCH={epoch}")
        print(f"first  {hashes[0]}  {WHEEL_NAME}")
        print(f"second {hashes[1]}  {WHEEL_NAME}")
        if hashes[0] != hashes[1] or first.read_bytes() != second.read_bytes():
            raise SystemExit("Los wheels no son reproducibles")
        with ZipFile(first) as archive:
            metadata = archive.read(
                "card_duel_engine-0.14.0.dist-info/METADATA"
            ).decode("utf-8")
        required = ("Version: 0.14.0", "License-Expression: Apache-2.0")
        if not all(item in metadata for item in required):
            raise SystemExit("Los metadatos de versión o licencia son incorrectos")
        runtime_requirements = [
            line for line in metadata.splitlines()
            if line.startswith("Requires-Dist:") and 'extra == "dev"' not in line
        ]
        if runtime_requirements:
            raise SystemExit("El wheel declara dependencias de ejecución")


if __name__ == "__main__":
    main()
