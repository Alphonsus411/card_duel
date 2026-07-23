#!/usr/bin/env python3
"""Punto de entrada multiplataforma para las verificaciones largas."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from verify_headless_simulations import verify as verify_simulations
from verify_persistence_roundtrips import verify as verify_persistence


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", metavar="PATH", help="Escribe un resumen JSON ('-' para stdout)")
    args = parser.parse_args()
    summary = {"simulations": verify_simulations(), "persistence": verify_persistence()}
    rendered = json.dumps(summary, sort_keys=True)
    if args.json == "-":
        print(rendered)
    elif args.json:
        Path(args.json).write_text(rendered + "\n", encoding="utf-8")
    else:
        print("OK: validación larga de la entrega completada")


if __name__ == "__main__":
    main()
