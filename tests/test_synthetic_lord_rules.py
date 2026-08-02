import unittest
from copy import deepcopy

from card_duel_engine import GameEngine, RuleSet
from card_duel_engine.domain import (
    AbilityDefinition, CardDefinition, CardKind, CompositeCost, EffectDefinition,
    EffectDuration, EffectKind, Keyword, LordDomain, Phase, TargetMode, Zone,
)
from card_duel_engine.domain.errors import IllegalAction
from card_duel_engine.engine import (
    ActivateAbility, DeclareAttackers, DeclareBlockers, DeclareChallenge, PassPriority,
    ResolveCombat,
)
from card_duel_engine.persistence import dump_replay, replay_from_log
from card_duel_engine.persistence.snapshot import dump_snapshot, load_snapshot, state_digest
from fixtures import test_deck


def put(engine, definition_id, player, zone=Zone.BATTLEFIELD):
    card_id = next(i for i, c in engine.state.cards.items()
                   if c.definition_id == definition_id and c.owner_id == player)
    for state_player in engine.state.players.values():
        for cards in state_player.zones.values():
            if card_id in cards:
                cards.remove(card_id)
    engine.state.players[player].zones[zone].append(card_id)
    card = engine.state.cards[card_id]
    card.zone = zone
    card.controller_id = player
    return card_id


def engine_with(a=(), b=(), seed=1):
    engine = GameEngine(RuleSet())
    engine.new_match({"A": [*a, *test_deck(f"a{seed}", 12)],
                      "B": [*b, *test_deck(f"b{seed}", 12)]}, seed=seed)
    engine.state.phase = Phase.EFFECTS
    engine.state.priority_player_id = "A"
    engine.state.phase_priority_complete = True
    return engine


def close_window(engine):
    engine.execute(PassPriority(engine.state.priority_player_id))
    engine.execute(PassPriority(engine.state.priority_player_id))


class SyntheticLordContract:
    DOMAIN = None

    def make_lord(self):
        return CardDefinition(
            f"synthetic-{self.DOMAIN.name.lower()}", "Unidad sintética", CardKind.LORD, 7,
            lord_domain=self.DOMAIN,
            abilities=(AbilityDefinition(
                "consume", (EffectDefinition(EffectKind.DEAL_DAMAGE, 1,
                                              TargetMode.CHOSEN_PERMANENT),),
                CompositeCost(strength=2),
            ),),
        )

    def test_permanent_strength_targeting_depletion_and_active_timing(self):
        lord = self.make_lord()
        target = CardDefinition("synthetic-target", "Objetivo sintético", CardKind.CREATURE,
                                0, base_strength=3)
        engine = engine_with((lord,), (target,))
        lord_id = put(engine, lord.card_id, "A")
        target_id = put(engine, target.card_id, "B")
        self.assertTrue(lord.permanent)
        self.assertEqual(engine._current_strength(lord_id), lord.cost)
        self.assertTrue(engine._card_can_be_targeted(target, lord_id, False))
        self.assertFalse(engine._is_creature(lord_id))
        engine.execute(ActivateAbility("A", lord_id, "consume", chosen_card_ids=(target_id,)))
        self.assertEqual(engine._current_strength(lord_id), 5)
        engine.state.phase = Phase.COMBAT
        engine.state.priority_player_id = "A"
        with self.assertRaises(IllegalAction):
            engine.execute(ActivateAbility("A", lord_id, "consume", chosen_card_ids=(target_id,)))
        engine.state.phase = Phase.EFFECTS
        engine.state.priority_player_id = "A"
        engine.state.cards[lord_id].strength_modifier = -7
        engine._run_state_based_actions()
        self.assertIn(lord_id, engine.state.players["A"].zones[Zone.DISCARD])


class TestSyntheticAbyss(SyntheticLordContract, unittest.TestCase):
    DOMAIN = LordDomain.ABYSS


class TestSyntheticElysium(SyntheticLordContract, unittest.TestCase):
    DOMAIN = LordDomain.ELYSIUM


class TestSyntheticMagic(SyntheticLordContract, unittest.TestCase):
    DOMAIN = LordDomain.MAGIC


class TestSyntheticRealms(unittest.TestCase):
    def make_engine(self, seed=1):
        lord = CardDefinition("synthetic-realms", "Unidad de reinos", CardKind.LORD, 8,
                              lord_domain=LordDomain.REALMS)
        victim = CardDefinition("synthetic-creature", "Unidad contraria", CardKind.CREATURE,
                                0, base_strength=3)
        other_lord = CardDefinition("synthetic-other", "Unidad no autorizada", CardKind.LORD, 4,
                                    lord_domain=LordDomain.ABYSS)
        engine = engine_with((lord, other_lord), (victim,), seed)
        ids = (put(engine, lord.card_id, "A"), put(engine, victim.card_id, "B"),
               put(engine, other_lord.card_id, "A"))
        return engine, ids

    def test_temporary_transformation_preserves_identity_state_and_restores(self):
        engine, (lord_id, _, _) = self.make_engine()
        card = engine.state.cards[lord_id]
        card.counters["synthetic"] = 2
        card.attached_to = "stable-attachment-reference"
        before_order = tuple(engine.state.players["A"].zones[Zone.BATTLEFIELD])
        card.transformed_as_creature = True
        card.creature_form_expires_turn_serial = engine.state.turn_serial
        self.assertTrue(engine._is_ready_creature(lord_id))
        engine._cleanup_end_of_turn()
        self.assertFalse(card.transformed_as_creature)
        self.assertEqual(card.instance_id, lord_id)
        self.assertEqual(card.owner_id, "A")
        self.assertEqual(card.counters, {"synthetic": 2})
        self.assertEqual(card.attached_to, "stable-attachment-reference")
        self.assertEqual(tuple(engine.state.players["A"].zones[Zone.BATTLEFIELD]), before_order)

    def test_authorized_transformation_can_attack_and_block(self):
        attacker_game, (lord_id, _, _) = self.make_engine()
        attacker_game.state.cards[lord_id].transformed_as_creature = True
        attacker_game.state.phase = Phase.COMBAT
        attacker_game.execute(DeclareAttackers("A", (lord_id,), "B"))
        self.assertEqual(attacker_game.state.combat.attackers, (lord_id,))

        blocker_game, (blocker_id, victim_id, _) = self.make_engine()
        # Se invierten control y jugador activo solo para construir un bloqueo sintético.
        blocker_game._set_controller(blocker_id, "B")
        blocker_game._set_controller(victim_id, "A")
        blocker_game.state.cards[blocker_id].transformed_as_creature = True
        blocker_game.state.phase = Phase.COMBAT
        blocker_game.state.priority_player_id = "A"
        blocker_game.execute(DeclareAttackers("A", (victim_id,), "B"))
        blocker_game.execute(DeclareBlockers("B", ((victim_id, (blocker_id,)),)))
        self.assertEqual(blocker_game.state.combat.blockers[victim_id], (blocker_id,))

    def test_challenge_validation_closed_damage_snapshot_and_rollback(self):
        for seed in (3, 19, 71):
            with self.subTest(seed=seed):
                engine, (lord_id, victim_id, other_id) = self.make_engine(seed)
                command = DeclareChallenge("A", lord_id, victim_id, "B")
                for bad_phase in (Phase.DRAW, Phase.COMBAT):
                    engine.state.phase = bad_phase
                    before = deepcopy(engine.state)
                    with self.assertRaises(IllegalAction):
                        engine.execute(command)
                    self.assertEqual(engine.state, before)
                engine.state.phase = Phase.EFFECTS
                before = deepcopy(engine.state)
                with self.assertRaises(IllegalAction):
                    engine.execute(command)  # Señor todavía no transformado
                self.assertEqual(engine.state, before)
                engine.state.cards[other_id].transformed_as_creature = True
                with self.assertRaises(IllegalAction):
                    engine.execute(DeclareChallenge("A", other_id, victim_id, "B"))
                engine.state.cards[lord_id].transformed_as_creature = True
                engine.execute(command)
                self.assertTrue(engine.state.combat.is_challenge)
                restored = load_snapshot(dump_snapshot(engine))
                self.assertTrue(restored.state.combat.is_challenge)
                self.assertEqual(state_digest(restored), state_digest(engine))
                close_window(engine)
                engine.execute(ResolveCombat("A"))
                self.assertIn(victim_id, engine.state.players["B"].zones[Zone.DISCARD])
                self.assertIn(lord_id, engine.state.players["A"].zones[Zone.BATTLEFIELD])
                self.assertEqual(engine.state.players["B"].wounds, 0)
                engine.state.combat = None
                with self.assertRaises(IllegalAction):
                    engine.execute(command)
                engine.state.phase = Phase.COMBAT
                engine.state.phase_priority_complete = True
                with self.assertRaises(IllegalAction):
                    engine.execute(DeclareAttackers("A", (lord_id,), "B"))

    def test_noncreature_target_and_normal_combat_exclude_challenge(self):
        lord = CardDefinition("synthetic-realms-object-test", "Unidad de reinos", CardKind.LORD,
                              8, lord_domain=LordDomain.REALMS)
        artifact = CardDefinition("synthetic-object", "Objeto sintético", CardKind.ARTIFACT, 0)
        engine = engine_with((lord,), (artifact,))
        lord_id = put(engine, lord.card_id, "A")
        victim_id = put(engine, artifact.card_id, "B")
        engine.state.cards[lord_id].transformed_as_creature = True
        with self.assertRaises(IllegalAction):
            engine.execute(DeclareChallenge("A", lord_id, victim_id, "B"))


class TestDeclarativeChallengeCapability(unittest.TestCase):
    def make_case(self, domain, *, keyword=False, kind=CardKind.LORD, seed=301):
        challenger = CardDefinition(
            f"challenge-{domain.name.lower()}-{kind.name.lower()}-{keyword}",
            "Desafiante sintético", kind, 6,
            base_strength=6 if kind is CardKind.CREATURE else None,
            lord_domain=domain if kind is CardKind.LORD else None,
            keywords=frozenset({Keyword.CAN_CHALLENGE}) if keyword else frozenset(),
        )
        target = CardDefinition(
            f"challenge-target-{seed}", "Objetivo sintético", CardKind.CREATURE,
            0, base_strength=2,
        )
        engine = engine_with((challenger,), (target,), seed)
        challenger_id = put(engine, challenger.card_id, "A")
        target_id = put(engine, target.card_id, "B")
        return engine, challenger_id, target_id

    def assert_parity(self, engine, command, expected):
        self.assertEqual(command in engine.legal_actions(command.player_id), expected)
        before = deepcopy(engine.state)
        if expected:
            engine.execute(command)
        else:
            with self.assertRaises(IllegalAction):
                engine.execute(command)
            self.assertEqual(engine.state, before)

    def test_domain_identity_transformation_keyword_and_exhaustion_matrix(self):
        cases = (
            (LordDomain.REALMS, False, CardKind.LORD, True),
            (LordDomain.ABYSS, False, CardKind.LORD, False),
            (LordDomain.ABYSS, True, CardKind.LORD, True),
            (LordDomain.ELYSIUM, True, CardKind.LORD, True),
            (LordDomain.MAGIC, True, CardKind.LORD, True),
            (LordDomain.ABYSS, True, CardKind.CREATURE, False),
        )
        for seed, (domain, keyword, kind, expected) in enumerate(cases, 310):
            with self.subTest(domain=domain, keyword=keyword, kind=kind):
                engine, challenger, target = self.make_case(
                    domain, keyword=keyword, kind=kind, seed=seed
                )
                command = DeclareChallenge("A", challenger, target, "B")
                # La capacidad nunca transforma automáticamente una carta.
                self.assert_parity(engine, command, False)
                if kind is CardKind.LORD:
                    engine.state.cards[challenger].transformed_as_creature = True
                    self.assert_parity(engine, command, expected)

        engine, challenger, target = self.make_case(
            LordDomain.ABYSS, keyword=True, seed=320
        )
        engine.state.cards[challenger].transformed_as_creature = True
        engine.state.cards[challenger].exhausted = True
        self.assert_parity(
            engine, DeclareChallenge("A", challenger, target, "B"), False
        )

    def test_legal_execution_parity_and_challenge_damage_does_not_overflow(self):
        engine, challenger, target = self.make_case(
            LordDomain.ELYSIUM, keyword=True, seed=330
        )
        engine.state.cards[challenger].transformed_as_creature = True
        command = DeclareChallenge("A", challenger, target, "B")
        engine.state.phase = Phase.DRAW
        self.assert_parity(engine, command, False)
        engine.state.phase = Phase.EFFECTS
        self.assert_parity(engine, command, True)
        close_window(engine)
        engine.execute(ResolveCombat("A"))
        self.assertEqual(engine.state.players["B"].wounds, 0)
        engine.state.combat = None
        self.assert_parity(engine, command, False)  # segundo Desafío
        engine.state.phase = Phase.COMBAT
        engine.state.phase_priority_complete = True
        with self.assertRaises(IllegalAction):
            engine.execute(DeclareAttackers("A", (challenger,), "B"))

        prior_combat, prior_challenger, prior_target = self.make_case(
            LordDomain.ABYSS, keyword=True, seed=331
        )
        prior_combat.state.cards[prior_challenger].transformed_as_creature = True
        prior_combat._emit(
            "ATTACKERS_DECLARED", "A",
            payload={"turn_serial": prior_combat.state.turn_serial},
        )
        self.assert_parity(
            prior_combat,
            DeclareChallenge("A", prior_challenger, prior_target, "B"),
            False,
        )

    def test_current_snapshot_and_replay_roundtrip_keyword_generically(self):
        engine, challenger, _ = self.make_case(
            LordDomain.MAGIC, keyword=True, seed=340
        )
        restored = load_snapshot(dump_snapshot(engine))
        self.assertIn(
            Keyword.CAN_CHALLENGE,
            restored.catalog.get(restored.state.cards[challenger].definition_id).keywords,
        )
        replay_source = GameEngine(RuleSet())
        replay_source.new_match(
            {
                "A": [engine.catalog.get(engine.state.cards[challenger].definition_id),
                      *test_deck("replay-a", 12)],
                "B": test_deck("replay-b", 12),
            },
            seed=341,
        )
        replayed = replay_from_log(dump_replay(replay_source))
        self.assertEqual(state_digest(replayed), state_digest(replay_source))


if __name__ == "__main__":
    unittest.main()
