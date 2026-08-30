from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import unittest

from card_duel_engine.domain import Zone
from card_duel_engine.persistence import (
    dump_replay,
    legacy_state_digest_without_ability_source_profile,
    replay_from_log,
    state_digest,
)
from card_duel_engine.persistence.codec import canonical_json
from card_duel_engine.persistence.replay import REPLAY_SCHEMA_VERSION


ARTIFACTS = Path(__file__).parent / "artifacts" / "0.20.x-pre-source-profile"
REPLAYS = (
    "pending-ability-source-present.replay-v2.json",
    "pending-ability-source-sacrificed.replay-v2.json",
)


def _rechecksum(document: dict) -> str:
    document["sha256"] = hashlib.sha256(
        canonical_json(document["body"]).encode("utf-8")
    ).hexdigest()
    return json.dumps(document)


class Legacy020AbilitySourceProfileReplayTests(unittest.TestCase):
    def test_authentic_historical_digests_are_accepted_without_losing_profile(self):
        metadata = json.loads((ARTIFACTS / "metadata.json").read_text())
        expected = {item["file"]: item["final_digest"] for item in metadata["artifacts"]}
        for name in REPLAYS:
            with self.subTest(name=name):
                engine = replay_from_log((ARTIFACTS / name).read_text())
                item = engine.state.stack[-1]
                self.assertEqual(
                    legacy_state_digest_without_ability_source_profile(engine),
                    expected[name],
                )
                self.assertNotEqual(state_digest(engine), expected[name])
                self.assertIsNotNone(item.ability_source_profile)
                dumped = json.loads(dump_replay(engine))
                self.assertEqual(dumped["body"]["final_digest"], state_digest(engine))
                self.assertNotEqual(dumped["body"]["final_digest"], expected[name])

    def test_legacy_digest_omits_only_profile_and_detects_other_state_changes(self):
        original = replay_from_log((ARTIFACTS / REPLAYS[0]).read_text())
        baseline = legacy_state_digest_without_ability_source_profile(original)

        mutations = {}
        zone = deepcopy(original)
        source_id = zone.state.stack[-1].source_card_id
        zone.state.cards[source_id].zone = Zone.EXILE
        mutations["zone"] = zone

        event = deepcopy(original)
        event.state.event_log[-1] = replace(
            event.state.event_log[-1], event_type="ALTERED_EVENT"
        )
        mutations["event"] = event

        counter = deepcopy(original)
        counter.state.event_log[-1] = replace(
            counter.state.event_log[-1], sequence=999
        )
        mutations["counter"] = counter

        target = deepcopy(original)
        target.state.stack[-1] = replace(
            target.state.stack[-1], chosen_player_ids=("A",)
        )
        mutations["target"] = target

        for label, engine in mutations.items():
            with self.subTest(alteration=label):
                self.assertNotEqual(
                    legacy_state_digest_without_ability_source_profile(engine), baseline
                )

    def test_versions_outside_the_historical_window_do_not_receive_fallback(self):
        for version in ("0.20.1+unknown", "0.20.2", "0.20.10"):
            with self.subTest(version=version):
                document = json.loads((ARTIFACTS / REPLAYS[0]).read_text())
                document["body"]["engine_version"] = version
                document["body"]["rules"]["fields"]["version"] = version
                with self.assertRaisesRegex(ValueError, "diverge"):
                    replay_from_log(_rechecksum(document))

    def test_replay_schema_remains_v2(self):
        self.assertEqual(REPLAY_SCHEMA_VERSION, "2")
