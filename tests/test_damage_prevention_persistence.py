from __future__ import annotations

import hashlib
import json
import unittest
from copy import deepcopy

from card_duel_engine import GameEngine
from card_duel_engine.domain import (
    DamageCause,
    DamagePreventionProfile,
    DamagePreventionReservation,
    Zone,
)
from card_duel_engine.persistence import (
    dump_replay,
    dump_snapshot,
    load_snapshot,
    replay_from_log,
    state_digest,
)
from card_duel_engine.persistence.codec import canonical_json
from card_duel_engine.persistence.snapshot import (
    legacy_state_digest_without_damage_prevention_profiles,
)

from fixtures import test_deck


def checksum(body: dict[str, object]) -> str:
    return hashlib.sha256(canonical_json(body).encode("utf-8")).hexdigest()


class DamagePreventionPersistenceTests(unittest.TestCase):
    def make_engine(self) -> tuple[GameEngine, str]:
        engine = GameEngine()
        engine.new_match({"A": test_deck("A"), "B": test_deck("B")}, seed=250)
        state = engine._require_state()
        card_id = state.players["A"].zones[Zone.HAND][0]
        engine._move_card(card_id, Zone.BATTLEFIELD, "A")
        return engine, card_id

    def test_snapshot_v5_roundtrips_explicit_legacy_and_typed_profiles(self) -> None:
        engine, card_id = self.make_engine()
        state = engine._require_state()
        state.players["A"].wound_prevention = 2
        state.players["A"].wound_prevention_reservations = (
            DamagePreventionReservation(DamageCause.COMBAT, 3),
        )
        state.cards[card_id].damage_prevention = 1
        state.cards[card_id].damage_prevention_reservations = (
            DamagePreventionReservation(DamageCause.COMBAT, 4),
        )

        payload = dump_snapshot(engine, indent=None)
        document = json.loads(payload)
        restored = load_snapshot(payload)
        restored_state = restored._require_state()

        self.assertEqual(document["body"]["schema_version"], "5")
        self.assertEqual(restored_state, state)
        self.assertEqual(state_digest(restored), state_digest(engine))
        self.assertEqual(
            restored_state.players["A"].wound_prevention_profile,
            DamagePreventionProfile.LEGACY_UNTYPED,
        )
        self.assertEqual(
            restored_state.cards[card_id].damage_prevention_profile,
            DamagePreventionProfile.LEGACY_UNTYPED,
        )

    def test_snapshot_v4_golden_migration_preserves_legacy_scalars_without_combat_label(self) -> None:
        engine, card_id = self.make_engine()
        state = engine._require_state()
        state.players["A"].wound_prevention = 2
        state.cards[card_id].damage_prevention = 3
        document = json.loads(dump_snapshot(engine, indent=None))
        fields = document["body"]["state"]["fields"]
        for _, player in fields["players"]["$mapping"]:
            player["fields"].pop("wound_prevention_profile")
            player["fields"].pop("wound_prevention_reservations")
        for _, card in fields["cards"]["$mapping"]:
            card["fields"].pop("damage_prevention_profile")
            card["fields"].pop("damage_prevention_reservations")
        document["body"]["schema_version"] = "4"
        document["body"]["state_digest"] = hashlib.sha256(
            canonical_json(document["body"]["state"]).encode("utf-8")
        ).hexdigest()
        document["sha256"] = checksum(document["body"])

        restored = load_snapshot(document)
        restored_state = restored._require_state()

        self.assertEqual(restored_state.players["A"].wound_prevention, 2)
        self.assertEqual(restored_state.cards[card_id].damage_prevention, 3)
        self.assertEqual(
            restored_state.players["A"].wound_prevention_profile,
            DamagePreventionProfile.LEGACY_UNTYPED,
        )
        self.assertEqual(restored_state.players["A"].wound_prevention_reservations, ())
        self.assertEqual(
            restored_state.cards[card_id].damage_prevention_profile,
            DamagePreventionProfile.LEGACY_UNTYPED,
        )
        self.assertEqual(restored_state.cards[card_id].damage_prevention_reservations, ())

    def test_replay_v3_golden_digest_rebuilds_with_the_legacy_profile(self) -> None:
        engine = GameEngine()
        engine.new_match({"A": test_deck("RA"), "B": test_deck("RB")}, seed=251)
        document = json.loads(dump_replay(engine, indent=None))
        document["body"]["schema_version"] = "3"
        document["body"]["final_digest"] = (
            legacy_state_digest_without_damage_prevention_profiles(engine)
        )
        document["sha256"] = checksum(document["body"])

        replayed = replay_from_log(document)

        self.assertEqual(replayed.state, engine.state)
        self.assertEqual(state_digest(replayed), state_digest(engine))

    def test_unknown_schema_and_unknown_cause_fail_closed(self) -> None:
        engine, card_id = self.make_engine()
        state = engine._require_state()
        state.cards[card_id].damage_prevention_reservations = (
            DamagePreventionReservation(DamageCause.COMBAT, 1),
        )
        document = json.loads(dump_snapshot(engine, indent=None))
        invalid_schema = deepcopy(document)
        invalid_schema["body"]["schema_version"] = "99"
        invalid_schema["sha256"] = checksum(invalid_schema["body"])
        with self.assertRaises(ValueError):
            load_snapshot(invalid_schema)

        invalid_cause = deepcopy(document)
        fields = invalid_cause["body"]["state"]["fields"]
        for key, card in fields["cards"]["$mapping"]:
            if key == card_id:
                reservation = card["fields"]["damage_prevention_reservations"]
                reservation["$tuple"][0]["fields"]["cause"]["name"] = "OTHER"
        invalid_cause["body"]["state_digest"] = hashlib.sha256(
            canonical_json(invalid_cause["body"]["state"]).encode("utf-8")
        ).hexdigest()
        invalid_cause["sha256"] = checksum(invalid_cause["body"])
        with self.assertRaises(ValueError):
            load_snapshot(invalid_cause)


if __name__ == "__main__":
    unittest.main()
