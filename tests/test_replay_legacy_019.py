from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest

from card_duel_engine import GameEngine, RuleSet
from card_duel_engine.domain import Phase
from card_duel_engine.domain.errors import IllegalAction
from card_duel_engine.engine import AdvancePhase, DrainSteps, PassPriority
from card_duel_engine.engine.game import EngineSemantics
from card_duel_engine.persistence import dump_replay, replay_from_log, state_digest
from card_duel_engine.persistence.codec import canonical_json
from card_duel_engine.storage import InMemoryMatchStore, SQLiteMatchStore

from fixtures import test_deck


ARTIFACTS = Path(__file__).parent / "artifacts" / "0.19.0"
EXPECTED = {
    "drainage-outside-effects.replay-v2.json": "f216145cb50c9cd8648debce523581f6f537d801558ee6e8a05497a85fa06110",
    "challenge-combat.replay-v2.json": "044970d424cc449607164dc3df955df3f04d4e8ebdef28670f7348c09edddd31",
    "attackers-declared.replay-v2.json": "1f2f8124a44f4d599587be89b564fea84d8d53b8513dab3e01bbdcb679be117a",
    "challenge-non-realms.replay-v2.json": "ec7f638d0c8897d0549e639731bf13634513a78f3ed1345897fc8895e41f9b6e",
    "lord-ability-outside-effects.replay-v2.json": "b78a99c291fe95ecc44f5d5f16bbdda02e129088093ff65788ae19f3cc4f5490",
}
EXPECTED_OBSERVABLES = {
    "drainage-outside-effects.replay-v2.json": (1, 10, 21, "DRAINAGE_USED", 5, 1),
    "challenge-combat.replay-v2.json": (3, 57, 91, "CHALLENGE_DECLARED", 5, 4),
    "attackers-declared.replay-v2.json": (3, 54, 86, "ATTACKERS_DECLARED", 5, 3),
    "challenge-non-realms.replay-v2.json": (3, 57, 91, "CHALLENGE_DECLARED", 5, 4),
    "lord-ability-outside-effects.replay-v2.json": (3, 54, 87, "STACK_ITEM_RESOLVED", 5, 4),
}


def _observables(engine: GameEngine) -> tuple[object, ...]:
    state = engine.state
    players = tuple(
        (
            player_id,
            player.wounds,
            player.steps,
            player.drainage_used_turn_serial,
            tuple((zone.name, tuple(cards)) for zone, cards in player.zones.items()),
        )
        for player_id, player in state.players.items()
    )
    events = tuple(
        (event.sequence, event.event_type, event.player_id, event.card_id, event.payload)
        for event in state.event_log
    )
    return (
        state.phase,
        state.turn_serial,
        tuple(state.command_history),
        events,
        players,
        tuple(state.stack),
        engine._next_instance,
        engine._next_stack_item,
        engine.semantics,
    )


def _rechecksum(document: dict) -> str:
    document["sha256"] = hashlib.sha256(
        canonical_json(document["body"]).encode("utf-8")
    ).hexdigest()
    return json.dumps(document)


class Legacy019ReplayTests(unittest.TestCase):
    def test_legacy_replays_preserve_digest_and_observables(self) -> None:
        for name, digest in EXPECTED.items():
            source = (ARTIFACTS / name).read_text(encoding="utf-8")
            expected = EXPECTED_OBSERVABLES[name]
            baseline = _observables(replay_from_log(source))
            for repetition in range(10):
                with self.subTest(name=name, repetition=repetition):
                    engine = replay_from_log(source)
                    state = engine.state
                    event = state.event_log[-1]
                    self.assertEqual(state_digest(engine), digest)
                    self.assertEqual(_observables(engine), baseline)
                    self.assertEqual(
                        (
                            state.turn_serial,
                            len(state.command_history),
                            len(state.event_log),
                            event.event_type,
                            engine._next_instance,
                            engine._next_stack_item,
                        ),
                        expected,
                    )
                    self.assertIs(state.phase, Phase.COMBAT)
                    self.assertIs(engine.semantics, EngineSemantics.LEGACY_019)
                    self.assertNotIn("turn_serial", event.payload)
                    self.assertTrue(
                        all(len(player.zones) == 6 for player in state.players.values())
                    )
                    if name.startswith("drainage"):
                        self.assertEqual(
                            (state.players["A"].wounds, state.players["A"].steps),
                            (6, 8),
                        )
                        self.assertEqual(state.players["A"].drainage_used_turn_serial, 1)
                    elif name.startswith("lord-ability"):
                        self.assertEqual(
                            [(p.wounds, p.steps) for p in state.players.values()],
                            [(0, 12), (0, 5)],
                        )
                        self.assertEqual(state.event_log[-2].event_type, "STEPS_GAINED")
                        self.assertEqual(state.event_log[-2].payload, {"amount": 2})
                    else:
                        self.assertEqual(
                            [(p.wounds, p.steps) for p in state.players.values()],
                            [(0, 10), (0, 5)],
                        )

    def test_failed_load_does_not_return_a_partially_built_engine(self) -> None:
        document = json.loads(
            (ARTIFACTS / "drainage-outside-effects.replay-v2.json").read_text()
        )
        document["body"]["final_digest"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "diverge"):
            replay_from_log(_rechecksum(document))

    def test_manual_019_rules_do_not_enable_historical_semantics(self) -> None:
        engine = GameEngine(RuleSet(version="0.19.0"))
        self.assertIs(engine.semantics, EngineSemantics.CURRENT)

    def test_legacy_continuations_survive_two_roundtrips_repeatedly(self) -> None:
        # Los cinco documentos cubren ataque, Drenaje, los dos Desafíos y la
        # habilidad de Señor activada durante combate.
        for name in EXPECTED:
            source = (ARTIFACTS / name).read_text(encoding="utf-8")
            for repetition in range(5):
                with self.subTest(name=name, repetition=repetition):
                    continued = replay_from_log(source)
                    continued.execute(PassPriority(continued.state.priority_player_id))
                    first = replay_from_log(dump_replay(continued))
                    second = replay_from_log(dump_replay(first))
                    self.assertIs(second.semantics, EngineSemantics.LEGACY_019)
                    self.assertEqual(state_digest(second), state_digest(continued))
                    self.assertEqual(_observables(first), _observables(continued))
                    self.assertEqual(_observables(second), _observables(continued))
                    document = json.loads(dump_replay(second))
                    self.assertEqual(document["body"]["engine_version"], "0.19.0")

    def test_legacy_regressions_survive_snapshot_match_stores(self) -> None:
        # El conjunto incluye las regresiones históricas de Drenaje, ambos
        # Desafíos y la habilidad de Señor, además del ataque relacionado.
        for name in EXPECTED:
            source = (ARTIFACTS / name).read_text(encoding="utf-8")
            for store_name, store in (
                ("memory", InMemoryMatchStore()),
                ("sqlite", SQLiteMatchStore(":memory:")),
            ):
                with self.subTest(name=name, store=store_name):
                    engine = replay_from_log(source)
                    before = _observables(engine)
                    store.create(name, engine)
                    restored = store.load(name).engine
                    self.assertIs(restored.semantics, EngineSemantics.LEGACY_019)
                    self.assertEqual(_observables(restored), before)
                    self.assertEqual(state_digest(restored), EXPECTED[name])

                    command = PassPriority(engine.state.priority_player_id)
                    engine.execute(command)
                    restored.execute(command)
                    self.assertEqual(_observables(restored), _observables(engine))
                if isinstance(store, SQLiteMatchStore):
                    store.close()

    def test_live_drainage_still_requires_effects_phase(self) -> None:
        engine = GameEngine()
        engine.new_match({"A": test_deck("A"), "B": test_deck("B")}, seed=201)
        while engine.state.phase is not Phase.COMBAT:
            for _ in engine.state.turn_order:
                engine.execute(PassPriority(engine.state.priority_player_id))
            engine.execute(AdvancePhase("A"))
        with self.assertRaisesRegex(IllegalAction, "Fase Activa"):
            engine.execute(DrainSteps("A", 1))

    def test_020_replay_never_enables_legacy_mode(self) -> None:
        engine = GameEngine(RuleSet(version="0.20.9"))
        engine.new_match({"A": test_deck("A"), "B": test_deck("B")}, seed=202)
        restored = replay_from_log(dump_replay(engine))
        self.assertIs(restored.semantics, EngineSemantics.CURRENT)

    def test_unknown_replay_version_is_rejected_explicitly(self) -> None:
        engine = GameEngine(RuleSet(version="9.9.9"))
        engine.new_match({"A": test_deck("A"), "B": test_deck("B")}, seed=203)
        with self.assertRaisesRegex(ValueError, "no compatible"):
            replay_from_log(dump_replay(engine))
