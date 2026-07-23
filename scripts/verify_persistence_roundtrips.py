#!/usr/bin/env python3
"""Comprueba instantáneas y replays contra la misma huella de estado."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from card_duel_engine import GameEngine
from card_duel_engine.persistence import (
    dump_replay, dump_snapshot, load_snapshot, replay_from_log, state_digest,
)
from card_duel_engine.controllers.base import DecisionRequest
from card_duel_engine.simulation import PhaseProgressAgent

from verify_headless_simulations import COMMANDS_PER_SIMULATION, deck

ROUNDTRIPS = 30


def verify() -> dict[str, int | str]:
    for seed in range(ROUNDTRIPS):
        engine = GameEngine()
        engine.new_match({"A": deck("A"), "B": deck("B")}, seed=seed)
        agents = {"A": PhaseProgressAgent(), "B": PhaseProgressAgent()}
        # Se ejecuta la misma carga de comandos sin usar el límite del runner:
        # BLOCKED es una señal operacional y no forma parte del replay.
        for _ in range(COMMANDS_PER_SIMULATION):
            state = engine.state
            assert state is not None
            if state.combat is not None and not state.combat.blockers_declared and not state.stack:
                player_id = state.combat.defending_player_id
            elif state.phase_priority_complete and not state.stack:
                player_id = state.active_player_id
            else:
                assert state.priority_player_id is not None
                player_id = state.priority_player_id
            actions = engine.legal_actions(player_id)
            engine.execute(agents[player_id].choose_action(DecisionRequest(engine.observe(player_id), actions)))
        expected = state_digest(engine)
        snapshot_digest = state_digest(load_snapshot(dump_snapshot(engine)))
        replay_digest = state_digest(replay_from_log(dump_replay(engine)))
        if len({expected, snapshot_digest, replay_digest}) != 1:
            raise SystemExit(f"Persistencia divergente para seed={seed}")
    return {"status": "ok", "roundtrips": ROUNDTRIPS}


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
        print(f"OK: {ROUNDTRIPS} pares snapshot/replay")


if __name__ == "__main__":
    main()
