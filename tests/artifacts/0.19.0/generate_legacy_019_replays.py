"""Generate the 0.19.0 replay-v2 corpus with only the historical engine."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys


GENERATOR_COMMIT = "3f21a1e2e9ba3c05b7bede3c5a7dc375d71ae39d"
WORKTREE = Path("/tmp/card-duel-019")


def run_historical_worker(output: Path) -> None:
    """Run this file again with imports resolved only from the detached tree."""
    repository = Path(__file__).resolve().parents[3]
    if WORKTREE.exists():
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(WORKTREE)],
            cwd=repository,
            check=True,
        )
    try:
        subprocess.run(
            ["git", "worktree", "add", "--detach", str(WORKTREE), GENERATOR_COMMIT],
            cwd=repository,
            check=True,
        )
        worker = WORKTREE / "generate_legacy_019_replays.py"
        shutil.copy2(__file__, worker)
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(WORKTREE / "src")
        subprocess.run(
            [sys.executable, "-I", str(worker), "--historical-worker", "--output", str(output)],
            cwd=WORKTREE,
            env=environment,
            check=True,
        )
    finally:
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(WORKTREE)],
            cwd=repository,
            check=False,
        )
        subprocess.run(["git", "worktree", "prune"], cwd=repository, check=True)


if "--historical-worker" not in sys.argv:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent,
    )
    arguments = parser.parse_args()
    run_historical_worker(arguments.output.resolve())
    raise SystemExit

# In worker mode this file lives at the root of the detached worktree.  Isolated
# mode plus this explicit path prevents the checkout containing this script from
# contributing an installed/current engine to the import resolution.
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from card_duel_engine import GameEngine, RuleSet
from card_duel_engine.domain import (
    AbilityDefinition,
    CardDefinition,
    CardKind,
    EffectDefinition,
    EffectKind,
    LordDomain,
    Phase,
    TargetMode,
)
from card_duel_engine.engine import (
    ActivateAbility,
    AdvancePhase,
    DeclareAttackers,
    DeclareChallenge,
    DrainSteps,
    PassPriority,
    PlayCard,
)
from card_duel_engine.persistence import dump_replay


def close_priority(engine: GameEngine) -> None:
    for _ in engine.state.turn_order:
        engine.execute(PassPriority(engine.state.priority_player_id))


def advance_to(engine: GameEngine, phase: Phase) -> None:
    while engine.state.phase is not phase:
        close_priority(engine)
        engine.execute(AdvancePhase(engine.state.active_player_id))


def card_in_hand(engine: GameEngine, player: str, definition_id: str) -> str:
    return next(
        card_id
        for card_id in engine.state.players[player].zones[next(z for z in engine.state.players[player].zones if z.name == "HAND")]
        if engine.state.cards[card_id].definition_id == definition_id
    )


def creature(card_id: str) -> CardDefinition:
    return CardDefinition(card_id, card_id, CardKind.CREATURE, 0, base_strength=3)


def filler(card_id: str) -> CardDefinition:
    return CardDefinition(card_id, card_id, CardKind.CREATURE, 0, base_strength=1)


def engine_for(a_cards, b_cards, seed: int) -> GameEngine:
    engine = GameEngine(RuleSet(initial_hand_size=2, hand_limit=8))
    engine.new_match({"A": a_cards, "B": b_cards}, seed=seed)
    return engine


def play_own_permanent(engine: GameEngine, player: str, definition_id: str) -> str:
    card_id = card_in_hand(engine, player, definition_id)
    engine.execute(PlayCard(player, card_id))
    close_priority(engine)
    return card_id


def finish_turn(engine: GameEngine) -> None:
    while engine.state.phase is not Phase.DISCARD:
        close_priority(engine)
        engine.execute(AdvancePhase(engine.state.active_player_id))
    close_priority(engine)
    engine.execute(AdvancePhase(engine.state.active_player_id))


def drainage() -> GameEngine:
    engine = engine_for([filler("A-F1"), filler("A-F2")], [filler("B-F1"), filler("B-F2")], 1901)
    advance_to(engine, Phase.COMBAT)
    engine.execute(DrainSteps("A", 3))
    return engine


def setup_battlefield(a_card: CardDefinition, b_card: CardDefinition, seed: int):
    engine = engine_for([a_card, filler("A-F")], [b_card, filler("B-F")], seed)
    advance_to(engine, Phase.EFFECTS)
    a_id = play_own_permanent(engine, "A", a_card.card_id)
    finish_turn(engine)
    advance_to(engine, Phase.EFFECTS)
    b_id = play_own_permanent(engine, "B", b_card.card_id)
    finish_turn(engine)
    return engine, a_id, b_id


def ordinary_combat() -> GameEngine:
    engine, attacker, _ = setup_battlefield(creature("ATTACKER"), creature("DEFENDER"), 1902)
    advance_to(engine, Phase.COMBAT)
    close_priority(engine)
    engine.execute(DeclareAttackers("A", (attacker,), "B"))
    return engine


def challenge(domain: LordDomain, seed: int) -> GameEngine:
    lord = CardDefinition(
        "CHALLENGER", "Challenger", CardKind.LORD, 0, base_strength=4,
        lord_domain=domain,
        abilities=(AbilityDefinition("awaken", (EffectDefinition(EffectKind.BECOME_CREATURE, 0, TargetMode.SOURCE),)),),
    )
    engine, challenger, challenged = setup_battlefield(lord, creature("CHALLENGED"), seed)
    # The first turn ended before the opponent established its creature. Awaken
    # through the recorded public command now that A is active again.
    advance_to(engine, Phase.EFFECTS)
    engine.execute(ActivateAbility("A", challenger, "awaken"))
    close_priority(engine)
    advance_to(engine, Phase.COMBAT)
    close_priority(engine)
    engine.execute(DeclareChallenge("A", challenger, challenged, "B"))
    return engine


def lord_ability_during_combat() -> GameEngine:
    lord = CardDefinition(
        "COMBAT-LORD",
        "Señor del combate",
        CardKind.LORD,
        0,
        base_strength=4,
        lord_domain=LordDomain.REALMS,
        abilities=(
            AbilityDefinition(
                "combat-march",
                (EffectDefinition(EffectKind.GAIN_STEPS, 2, TargetMode.SELF),),
                allowed_phases=frozenset({Phase.COMBAT}),
            ),
        ),
    )
    engine, lord_id, _ = setup_battlefield(lord, filler("B-PERMANENT"), 1905)
    advance_to(engine, Phase.COMBAT)
    engine.execute(ActivateAbility("A", lord_id, "combat-march"))
    close_priority(engine)
    return engine


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--historical-worker", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    output = arguments.output
    output.mkdir(parents=True, exist_ok=True)
    fixtures = {
        "drainage-outside-effects.replay-v2.json": drainage(),
        "challenge-combat.replay-v2.json": challenge(LordDomain.REALMS, 1903),
        "attackers-declared.replay-v2.json": ordinary_combat(),
        "challenge-non-realms.replay-v2.json": challenge(LordDomain.ABYSS, 1904),
        "lord-ability-outside-effects.replay-v2.json": lord_ability_during_combat(),
    }
    for name, engine in fixtures.items():
        (output / name).write_text(dump_replay(engine) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
