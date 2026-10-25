from __future__ import annotations

import unittest
from copy import deepcopy

from card_duel_engine import GameEngine
from card_duel_engine.catalog import CardCatalog
from card_duel_engine.domain import DamageCause, DamagePreventionReservation
from card_duel_engine.domain.enums import CardKind, MatchStatus, Phase, Zone
from card_duel_engine.domain.models import CardDefinition, CardInstance, CombatState, GameState, PlayerState
from card_duel_engine.engine.commands import ResolveCombat
from card_duel_engine.persistence import dump_snapshot, load_snapshot, state_digest


class DamagePreventionP5MatrixTests(unittest.TestCase):
    def make_engine(self) -> tuple[GameEngine, str, str]:
        creature = CardDefinition(
            "creature", "Criatura", CardKind.CREATURE, 1, base_strength=5
        )
        engine = GameEngine(catalog=CardCatalog({"creature": creature}))
        attacker_id = "attacker-i"
        blocker_id = "blocker-i"
        state = GameState(
            ruleset_id=engine.rules.ruleset_id,
            ruleset_version=engine.rules.version,
            players={"A": PlayerState("A"), "B": PlayerState("B")},
            turn_order=("A", "B"),
            cards={
                attacker_id: CardInstance(
                    attacker_id, "creature", "A", "A", Zone.BATTLEFIELD
                ),
                blocker_id: CardInstance(
                    blocker_id, "creature", "B", "B", Zone.BATTLEFIELD
                ),
            },
            phase=Phase.COMBAT,
            priority_player_id="A",
            status=MatchStatus.RUNNING,
        )
        state.players["A"].zones[Zone.BATTLEFIELD].append(attacker_id)
        state.players["B"].zones[Zone.BATTLEFIELD].append(blocker_id)
        engine.state = state
        return engine, attacker_id, blocker_id

    def prepare_blocked_combat(
        self, *, is_challenge: bool
    ) -> tuple[GameEngine, str, str]:
        engine, attacker_id, blocker_id = self.make_engine()
        state = engine._require_running_state()
        state.cards[attacker_id].damage_prevention_reservations = (
            DamagePreventionReservation(DamageCause.COMBAT, 3),
        )
        state.cards[blocker_id].damage_prevention_reservations = (
            DamagePreventionReservation(DamageCause.COMBAT, 3),
        )
        state.combat = CombatState(
            attacking_player_id="A",
            defending_player_id="B",
            attackers=(attacker_id,),
            blockers={attacker_id: (blocker_id,)},
            blockers_declared=True,
            is_challenge=is_challenge,
        )
        state.phase_priority_complete = True
        return engine, attacker_id, blocker_id

    def test_insufficient_card_reservation_consumes_once_and_applies_remainder(self) -> None:
        engine, _, blocker_id = self.make_engine()
        state = engine._require_running_state()
        state.cards[blocker_id].damage_prevention_reservations = (
            DamagePreventionReservation(DamageCause.COMBAT, 2),
        )

        engine._deal_combat_damage(blocker_id, 5)

        self.assertEqual(state.cards[blocker_id].damage, 3)
        self.assertEqual(state.cards[blocker_id].damage_prevention_reservations, ())
        self.assertEqual(
            [event.payload["amount"] for event in state.event_log if event.event_type == "DAMAGE_DEALT"],
            [3],
        )

    def test_insufficient_wound_reservation_consumes_once_and_applies_remainder(self) -> None:
        engine, attacker_id, _ = self.make_engine()
        state = engine._require_running_state()
        state.players["B"].wound_prevention_reservations = (
            DamagePreventionReservation(DamageCause.COMBAT, 2),
        )
        state.combat = CombatState(
            attacking_player_id="A",
            defending_player_id="B",
            attackers=(attacker_id,),
            blockers_declared=True,
        )
        state.phase_priority_complete = True

        engine._combat._resolve_combat("A")

        self.assertEqual(state.players["B"].wounds, 3)
        self.assertEqual(state.players["B"].wound_prevention_reservations, ())
        self.assertEqual(
            [event.payload["amount"] for event in state.event_log if event.event_type == "WOUNDS_ADDED"],
            [3],
        )

    def test_snapshot_restoration_matches_direct_resolution_for_combat_and_challenge(self) -> None:
        for is_challenge in (False, True):
            with self.subTest(is_challenge=is_challenge):
                direct, _, _ = self.prepare_blocked_combat(is_challenge=is_challenge)
                restored = load_snapshot(dump_snapshot(direct, indent=None))

                direct._combat._resolve_combat("A")
                restored._combat._resolve_combat("A")

                self.assertEqual(restored.state, direct.state)
                self.assertEqual(state_digest(restored), state_digest(direct))

    def test_public_combat_failure_restores_damage_and_reservation_together(self) -> None:
        engine, _, _ = self.prepare_blocked_combat(is_challenge=False)
        before = deepcopy(engine.state)
        original_emit = engine._emit

        def fail_after_damage(
            event_type: str,
            player_id: str | None = None,
            card_id: str | None = None,
            payload: dict[str, object] | None = None,
        ) -> None:
            if event_type == "COMBAT_RESOLVED":
                raise RuntimeError("fallo inyectado después de prevenir daño")
            original_emit(event_type, player_id, card_id, payload)

        engine._emit = fail_after_damage  # type: ignore[method-assign]
        with self.assertRaisesRegex(RuntimeError, "fallo inyectado"):
            engine.execute(ResolveCombat("A"))

        self.assertEqual(engine.state, before)


if __name__ == "__main__":
    unittest.main()
