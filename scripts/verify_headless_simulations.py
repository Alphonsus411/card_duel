#!/usr/bin/env python3
"""Ejecuta la carga headless determinista exigida para una entrega."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from card_duel_engine import GameEngine
from card_duel_engine.domain.enums import CardKind
from card_duel_engine.domain.models import CardDefinition
from card_duel_engine.simulation import PhaseProgressAgent, run_headless

SIMULATIONS = 300
COMMANDS_PER_SIMULATION = 180
EXPECTED_COMMANDS = 54_000
EXPECTED_EVENTS = 84_000


def deck(prefix: str) -> list[CardDefinition]:
    return [
        CardDefinition(
            card_id=f"{prefix}-{index:03d}", name=f"Carta {index}",
            kind=CardKind.CREATURE, cost=5, base_strength=5, set_id="verification",
        )
        for index in range(12)
    ]


def verify() -> dict[str, int | str]:
    commands = events = 0
    for seed in range(SIMULATIONS):
        engine = GameEngine()
        engine.new_match({"A": deck("A"), "B": deck("B")}, seed=seed)
        report = run_headless(
            engine, {"A": PhaseProgressAgent(), "B": PhaseProgressAgent()},
            max_commands=COMMANDS_PER_SIMULATION,
        )
        commands += report.commands_executed
        events += report.event_count
    if (commands, events) != (EXPECTED_COMMANDS, EXPECTED_EVENTS):
        raise SystemExit(
            f"Carga divergente: comandos={commands}, eventos={events}; "
            f"esperados={EXPECTED_COMMANDS}/{EXPECTED_EVENTS}"
        )
    return {"status": "ok", "simulations": SIMULATIONS, "commands": commands, "events": events}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", metavar="PATH", help="Escribe el resumen JSON ('-' para stdout)")
    args = parser.parse_args()
    summary = verify()
    rendered = json.dumps(summary, sort_keys=True)
    if args.json == "-":
        print(rendered)
    elif args.json:
        Path(args.json).write_text(rendered + "\n", encoding="utf-8")
    else:
        print(f"OK: {SIMULATIONS} simulaciones, {EXPECTED_COMMANDS} comandos, {EXPECTED_EVENTS} eventos")


if __name__ == "__main__":
    main()
