from __future__ import annotations

import unittest

from card_duel_engine import GameEngine
from card_duel_engine.catalog import CardCatalog
from card_duel_engine.domain.enums import (
    CardKind,
    DamageCause,
    EffectKind,
    MatchStatus,
    Phase,
    TargetMode,
    Zone,
)
from card_duel_engine.domain.models import (
    CardDefinition,
    CardInstance,
    CombatState,
    EffectDefinition,
    GameState,
    PlayerState,
    StackItem,
)
from card_duel_engine.engine.damage_prevention import reserve_damage_prevention
from card_duel_engine.persistence import dump_snapshot, load_snapshot, state_digest


class DamagePreventionCharacterizationTests(unittest.TestCase):
    def make_engine(self) -> tuple[GameEngine, str, str]:
        source = CardDefinition("source", "Fuente", CardKind.ARTIFACT, 0)
        creature = CardDefinition(
            "creature", "Criatura", CardKind.CREATURE, 1, base_strength=5
        )
        engine = GameEngine(catalog=CardCatalog({"source": source, "creature": creature}))
        source_id = "source-i"
        creature_id = "creature-i"
        state = GameState(
            ruleset_id=engine.rules.ruleset_id,
            ruleset_version=engine.rules.version,
            players={"A": PlayerState("A"), "B": PlayerState("B")},
            turn_order=("A", "B"),
            cards={
                source_id: CardInstance(
                    source_id, "source", "A", "A", Zone.BATTLEFIELD
                ),
                creature_id: CardInstance(
                    creature_id, "creature", "B", "B", Zone.BATTLEFIELD
                ),
            },
            phase=Phase.EFFECTS,
            priority_player_id="A",
            status=MatchStatus.RUNNING,
        )
        state.players["A"].zones[Zone.BATTLEFIELD].append(source_id)
        state.players["B"].zones[Zone.BATTLEFIELD].append(creature_id)
        engine.state = state
        return engine, source_id, creature_id

    def test_effects_add_the_current_scalar_reserves(self) -> None:
        engine, source_id, creature_id = self.make_engine()
        state = engine._require_running_state()
        item = StackItem("stack-1", "A", source_id, ())

        engine._effects.apply(EffectDefinition(EffectKind.PREVENT_WOUNDS, 3), item)
        engine._effects.apply(
            EffectDefinition(
                EffectKind.PREVENT_DAMAGE, 2, TargetMode.CHOSEN_PERMANENT
            ),
            item,
            creature_id,
        )

        self.assertEqual(state.players["A"].wound_prevention, 3)
        self.assertEqual(state.cards[creature_id].damage_prevention, 2)
        self.assertEqual(
            [event.event_type for event in state.event_log],
            ["WOUND_PREVENTION_ADDED", "DAMAGE_PREVENTION_ADDED"],
        )

    def test_scalar_reserves_partially_consume_and_roundtrip_snapshot(self) -> None:
        engine, _, creature_id = self.make_engine()
        state = engine._require_running_state()
        state.players["A"].wound_prevention = 4
        state.cards[creature_id].damage_prevention = 5

        engine._deal_wounds("A", 3)
        engine._deal_damage(creature_id, 2)
        restored = load_snapshot(dump_snapshot(engine, indent=None))
        restored_state = restored._require_running_state()

        self.assertEqual(state.players["A"].wounds, 0)
        self.assertEqual(state.players["A"].wound_prevention, 1)
        self.assertEqual(state.cards[creature_id].damage, 0)
        self.assertEqual(state.cards[creature_id].damage_prevention, 3)
        self.assertEqual(restored_state, state)
        self.assertEqual(state_digest(restored), state_digest(engine))

    def test_normal_combat_and_challenge_share_current_scalar_damage_path(self) -> None:
        for is_challenge in (False, True):
            with self.subTest(is_challenge=is_challenge):
                engine, source_id, creature_id = self.make_engine()
                state = engine._require_running_state()
                state.cards[source_id].definition_id = "creature"
                state.cards[source_id].damage_prevention = 1
                state.cards[creature_id].damage_prevention = 2
                state.combat = CombatState(
                    attacking_player_id="A",
                    defending_player_id="B",
                    attackers=(source_id,),
                    blockers={source_id: (creature_id,)},
                    blockers_declared=True,
                    is_challenge=is_challenge,
                )
                state.phase_priority_complete = True

                engine._combat._resolve_combat("A")

                self.assertEqual(state.cards[source_id].damage_prevention, 0)
                self.assertEqual(state.cards[source_id].damage, 4)
                self.assertEqual(state.cards[creature_id].damage_prevention, 0)
                self.assertEqual(state.cards[creature_id].damage, 3)

    def test_normal_combat_and_challenge_consume_the_same_typed_reservation(self) -> None:
        for is_challenge in (False, True):
            with self.subTest(is_challenge=is_challenge):
                engine, source_id, creature_id = self.make_engine()
                state = engine._require_running_state()
                state.cards[source_id].definition_id = "creature"
                state.cards[source_id].damage_prevention_reservations = (
                    reserve_damage_prevention(DamageCause.COMBAT, 1),
                )
                state.cards[creature_id].damage_prevention_reservations = (
                    reserve_damage_prevention(DamageCause.COMBAT, 2),
                )
                state.combat = CombatState(
                    attacking_player_id="A",
                    defending_player_id="B",
                    attackers=(source_id,),
                    blockers={source_id: (creature_id,)},
                    blockers_declared=True,
                    is_challenge=is_challenge,
                )
                state.phase_priority_complete = True

                engine._combat._resolve_combat("A")

                self.assertEqual(state.cards[source_id].damage, 4)
                self.assertEqual(state.cards[source_id].damage_prevention_reservations, ())
                self.assertEqual(state.cards[creature_id].damage, 3)
                self.assertEqual(state.cards[creature_id].damage_prevention_reservations, ())

    def test_combat_wounds_consume_only_the_combat_reservation(self) -> None:
        engine, source_id, _ = self.make_engine()
        state = engine._require_running_state()
        state.cards[source_id].definition_id = "creature"
        state.players["B"].wound_prevention_reservations = (
            reserve_damage_prevention(DamageCause.COMBAT, 3),
        )
        state.combat = CombatState(
            attacking_player_id="A",
            defending_player_id="B",
            attackers=(source_id,),
            blockers_declared=True,
        )
        state.phase_priority_complete = True

        engine._combat._resolve_combat("A")

        self.assertEqual(state.players["B"].wounds, 2)
        self.assertEqual(state.players["B"].wound_prevention_reservations, ())

    def test_combat_preserves_legacy_prevention_precedence_before_typed(self) -> None:
        engine, _, creature_id = self.make_engine()
        state = engine._require_running_state()
        state.cards[creature_id].damage_prevention = 2
        state.cards[creature_id].damage_prevention_reservations = (
            reserve_damage_prevention(DamageCause.COMBAT, 3),
        )

        engine._deal_combat_damage(creature_id, 4)

        self.assertEqual(state.cards[creature_id].damage, 0)
        self.assertEqual(state.cards[creature_id].damage_prevention, 0)
        self.assertEqual(
            state.cards[creature_id].damage_prevention_reservations,
            (reserve_damage_prevention(DamageCause.COMBAT, 1),),
        )

    def test_non_combat_damage_leaves_typed_combat_reservations_intact(self) -> None:
        engine, _, creature_id = self.make_engine()
        state = engine._require_running_state()
        card_reservation = reserve_damage_prevention(DamageCause.COMBAT, 2)
        wound_reservation = reserve_damage_prevention(DamageCause.COMBAT, 3)
        state.cards[creature_id].damage_prevention_reservations = (card_reservation,)
        state.players["A"].wound_prevention_reservations = (wound_reservation,)

        engine._deal_damage(creature_id, 2)
        engine._deal_wounds("A", 3)

        self.assertEqual(state.cards[creature_id].damage, 2)
        self.assertEqual(state.cards[creature_id].damage_prevention_reservations, (card_reservation,))
        self.assertEqual(state.players["A"].wounds, 3)
        self.assertEqual(state.players["A"].wound_prevention_reservations, (wound_reservation,))

    def test_cleanup_and_battlefield_exit_clear_current_scalar_reserves(self) -> None:
        engine, _, creature_id = self.make_engine()
        state = engine._require_running_state()
        state.players["A"].wound_prevention = 2
        state.cards[creature_id].damage_prevention = 3

        engine._cleanup_end_of_turn()
        self.assertEqual(state.players["A"].wound_prevention, 0)
        self.assertEqual(state.cards[creature_id].damage_prevention, 0)

        state.cards[creature_id].damage_prevention = 3
        engine._move_card(creature_id, Zone.DISCARD, "B")
        self.assertEqual(state.cards[creature_id].damage_prevention, 0)


if __name__ == "__main__":
    unittest.main()
