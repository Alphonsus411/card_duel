from __future__ import annotations

import json

from card_duel_engine import GameEngine, RuleSet
from card_duel_engine.domain.enums import CardKind, LordDomain
from card_duel_engine.domain.models import CardDefinition
from card_duel_engine.persistence import dump_replay, dump_snapshot, load_snapshot, replay_from_log

from fixtures import test_deck


def _accredited_lords() -> tuple[CardDefinition, CardDefinition]:
    return (
        CardDefinition(
            "taxonomy-t3-explicit-lord",
            "Señor explícito",
            CardKind.LORD,
            4,
            lord_domain=LordDomain.REALMS,
        ),
        CardDefinition(
            "taxonomy-t3-creature-lord",
            "Criatura Señor",
            CardKind.CREATURE,
            4,
            lord_domain=LordDomain.ABYSS,
        ),
    )


def _engine_with_accredited_lords() -> GameEngine:
    explicit_lord, creature_lord = _accredited_lords()
    engine = GameEngine(RuleSet())
    engine.new_match(
        {
            "A": [explicit_lord, creature_lord, *test_deck("taxonomy-t3-a", 12)],
            "B": test_deck("taxonomy-t3-b", 12),
        },
        seed=103,
    )
    return engine


def _assert_accredited_lord_dimensions(engine: GameEngine) -> None:
    explicit_lord = engine.catalog.get("taxonomy-t3-explicit-lord")
    creature_lord = engine.catalog.get("taxonomy-t3-creature-lord")

    assert explicit_lord.kind is CardKind.LORD
    assert explicit_lord.lord_domain is LordDomain.REALMS
    assert creature_lord.kind is CardKind.CREATURE
    assert creature_lord.lord_domain is LordDomain.ABYSS


def test_snapshot_and_replay_preserve_accredited_lord_forms_without_schema_change() -> None:
    engine = _engine_with_accredited_lords()

    snapshot = dump_snapshot(engine, indent=None)
    replay = dump_replay(engine, indent=None)

    assert json.loads(snapshot)["body"]["schema_version"] == "6"
    assert json.loads(replay)["body"]["schema_version"] == "4"

    _assert_accredited_lord_dimensions(load_snapshot(snapshot))
    _assert_accredited_lord_dimensions(replay_from_log(replay))
