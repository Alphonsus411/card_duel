from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from card_duel_engine import GameEngine, RuleSet
from card_duel_engine.domain import Phase
from card_duel_engine.domain.errors import IllegalAction
from card_duel_engine.engine import AdvancePhase, DrainSteps, PassPriority
from card_duel_engine.engine.game import ReplayCompatibilityMode
from card_duel_engine.persistence import dump_replay, replay_from_log, state_digest
from card_duel_engine.persistence.codec import canonical_json

from fixtures import test_deck


ARTIFACTS = Path(__file__).parent / "artifacts" / "0.19.0"
EXPECTED = {
    "drainage-outside-effects.replay-v2.json": "f216145cb50c9cd8648debce523581f6f537d801558ee6e8a05497a85fa06110",
    "challenge-combat.replay-v2.json": "044970d424cc449607164dc3df955df3f04d4e8ebdef28670f7348c09edddd31",
    "attackers-declared.replay-v2.json": "1f2f8124a44f4d599587be89b564fea84d8d53b8513dab3e01bbdcb679be117a",
    "challenge-non-realms.replay-v2.json": "ec7f638d0c8897d0549e639731bf13634513a78f3ed1345897fc8895e41f9b6e",
}


def _rechecksum(document: dict) -> str:
    document["sha256"] = hashlib.sha256(
        canonical_json(document["body"]).encode("utf-8")
    ).hexdigest()
    return json.dumps(document)


class Legacy019ReplayTests(unittest.TestCase):
    def test_legacy_replays_preserve_digest_and_observables(self) -> None:
        for name, digest in EXPECTED.items():
            with self.subTest(name=name):
                engine = replay_from_log((ARTIFACTS / name).read_text(encoding="utf-8"))
                self.assertEqual(state_digest(engine), digest)
                self.assertIs(engine.state.phase, Phase.COMBAT)
                self.assertIs(engine._replay_compatibility_mode, ReplayCompatibilityMode.NORMAL)
                event = engine.state.event_log[-1]
                self.assertNotIn("turn_serial", event.payload)
                if name.startswith("drainage"):
                    player = engine.state.players["A"]
                    self.assertEqual((player.wounds, player.steps), (6, 8))
                    self.assertEqual(player.drainage_used_turn_serial, 1)
                    self.assertEqual(event.event_type, "DRAINAGE_USED")
                else:
                    self.assertEqual(
                        [(p.wounds, p.steps) for p in engine.state.players.values()],
                        [(0, 10), (0, 5)],
                    )
                    self.assertTrue(
                        all(len(player.zones) == 6 for player in engine.state.players.values())
                    )

    def test_mode_is_restored_when_legacy_replay_raises(self) -> None:
        document = json.loads(
            (ARTIFACTS / "drainage-outside-effects.replay-v2.json").read_text()
        )
        document["body"]["final_digest"] = "0" * 64
        captured: list[GameEngine] = []
        real_engine = GameEngine

        def capture(*args, **kwargs):
            engine = real_engine(*args, **kwargs)
            captured.append(engine)
            return engine

        with patch("card_duel_engine.persistence.replay.GameEngine", side_effect=capture):
            with self.assertRaisesRegex(ValueError, "diverge"):
                replay_from_log(_rechecksum(document))
        self.assertIs(
            captured[0]._replay_compatibility_mode, ReplayCompatibilityMode.NORMAL
        )

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
        self.assertIs(
            restored._replay_compatibility_mode, ReplayCompatibilityMode.NORMAL
        )

    def test_unknown_replay_version_is_rejected_explicitly(self) -> None:
        engine = GameEngine(RuleSet(version="9.9.9"))
        engine.new_match({"A": test_deck("A"), "B": test_deck("B")}, seed=203)
        with self.assertRaisesRegex(ValueError, "no compatible"):
            replay_from_log(dump_replay(engine))
