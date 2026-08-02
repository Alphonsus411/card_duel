import unittest
from copy import deepcopy
from unittest.mock import patch

from card_duel_engine import GameEngine, RuleSet
from card_duel_engine.domain import (
    AbilityDefinition,
    CardDefinition,
    CardKind,
    CardRank,
    CompositeCost,
    ContinuousEffectDefinition,
    EffectDefinition,
    EffectDuration,
    EffectKind,
    LordDomain,
    Phase,
    TargetMode,
    TriggerKind,
    Zone,
)
from card_duel_engine.domain.errors import IllegalAction
from card_duel_engine.engine import (
    ActivateAbility,
    AdvancePhase,
    DeclareChallenge,
    DrainSteps,
    OrderTriggeredAbilities,
    PassPriority,
    PlayCard,
    ResolveCombat,
    TransmutePermanent,
)

from fixtures import test_deck
from card_duel_engine.persistence.replay import dump_replay, replay_from_log
from card_duel_engine.persistence.snapshot import (
    SNAPSHOT_SCHEMA_VERSION,
    dump_snapshot,
    load_snapshot,
    state_digest,
)


def force_zone(engine, definition_id, player_id, zone):
    card_id = next(
        card_id
        for card_id, instance in engine.state.cards.items()
        if instance.definition_id == definition_id and instance.owner_id == player_id
    )
    instance = engine.state.cards[card_id]
    for player in engine.state.players.values():
        for cards in player.zones.values():
            if card_id in cards:
                cards.remove(card_id)
    if card_id in engine.state.resolution:
        engine.state.resolution.remove(card_id)
    engine.state.players[player_id].zones[zone].append(card_id)
    instance.zone = zone
    instance.controller_id = player_id
    return card_id


def resolve_one(engine):
    engine.execute(PassPriority(engine.state.priority_player_id))
    engine.execute(PassPriority(engine.state.priority_player_id))


class MythicV040Tests(unittest.TestCase):
    def make_engine(self, a_specials=(), b_specials=()):
        engine = GameEngine(RuleSet())
        engine.new_match(
            {
                "A": [*a_specials, *test_deck("A", 12)],
                "B": [*b_specials, *test_deck("B", 12)],
            },
            seed=40,
        )
        return engine

    def prepare_drainage(self):
        engine = self.make_engine()
        for _ in range(2):
            resolve_one(engine)
            engine.execute(AdvancePhase("A"))
        self.assertIs(engine.state.phase, Phase.EFFECTS)
        return engine

    def test_drainage_steps_and_wounds_table(self):
        for amount, wounds in ((1, 0), (2, 3), (3, 6), (4, 9), (5, 12)):
            with self.subTest(amount=amount):
                engine = self.prepare_drainage()
                before_steps = engine.state.players["A"].steps
                engine.execute(DrainSteps("A", amount))
                self.assertEqual(engine.state.players["A"].steps, before_steps + amount)
                self.assertEqual(engine.state.players["A"].wounds, wounds)

    def test_drainage_rejects_non_strict_integer_and_out_of_range_without_changes(self):
        for amount in (0, -1, 6, True, 1.0):
            with self.subTest(amount=amount):
                engine = self.prepare_drainage()
                before = deepcopy(engine.state)
                counters = (engine._next_instance, engine._next_stack_item)
                with self.assertRaises(IllegalAction):
                    engine.execute(DrainSteps("A", amount))
                self.assertEqual(engine.state, before)
                self.assertEqual((engine._next_instance, engine._next_stack_item), counters)

    def test_drainage_rejects_second_use_passive_player_and_wrong_phase(self):
        second = self.prepare_drainage()
        second.execute(DrainSteps("A", 1))
        second.state.priority_player_id = "A"
        passive = self.prepare_drainage()
        passive.state.priority_player_id = "B"
        wrong_phase = self.prepare_drainage()
        wrong_phase.state.phase = Phase.COMBAT
        for engine, command in (
            (second, DrainSteps("A", 1)),
            (passive, DrainSteps("B", 1)),
            (wrong_phase, DrainSteps("A", 1)),
        ):
            before = deepcopy(engine.state)
            with self.assertRaises(IllegalAction):
                engine.execute(command)
            self.assertEqual(engine.state, before)

    def test_drainage_rolls_back_every_observable_when_publication_fails(self):
        engine = self.prepare_drainage()
        before = deepcopy(engine.state)
        counters = (engine._next_instance, engine._next_stack_item)
        with patch.object(engine, "_emit", side_effect=RuntimeError("fallo inducido")):
            with self.assertRaises(RuntimeError):
                engine.execute(DrainSteps("A", 5))
        self.assertEqual(engine.state, before)
        self.assertEqual((engine._next_instance, engine._next_stack_item), counters)

    def test_drainage_resets_by_turn_serial_and_roundtrips_without_schema_change(self):
        engine = self.prepare_drainage()
        engine.execute(DrainSteps("A", 3))
        snapshot = dump_snapshot(engine)
        replay = dump_replay(engine)
        used_serial = engine.state.turn_serial
        self.assertEqual(load_snapshot(snapshot).state.players["A"].drainage_used_turn_serial, used_serial)
        self.assertEqual(replay_from_log(replay).state.players["A"].drainage_used_turn_serial, used_serial)
        self.assertEqual(SNAPSHOT_SCHEMA_VERSION, "2")
        engine.state.turn_serial += 1
        engine.state.priority_player_id = "A"
        engine.execute(DrainSteps("A", 1))

    def test_legendary_rank_is_independent_from_kind_and_permanence(self):
        cards = (
            CardDefinition("LC", "Criatura", CardKind.CREATURE, 5, rank=CardRank.LEGENDARY, base_strength=5),
            CardDefinition("LE", "Evento", CardKind.EVENT, 5, rank=CardRank.LEGENDARY, permanent=False),
            CardDefinition("LA", "Artefacto", CardKind.ARTIFACT, 5, rank=CardRank.LEGENDARY),
        )
        self.assertEqual([card.kind for card in cards], [CardKind.CREATURE, CardKind.EVENT, CardKind.ARTIFACT])
        self.assertEqual([card.permanent for card in cards], [True, False, True])
        self.assertTrue(all("IMMUNE_EVENT" not in card.keywords for card in cards))

    def test_one_effect_can_target_multiple_permanents(self):
        sweep = CardDefinition(
            "SWEEP", "Barrido", CardKind.QUICK_RESOURCE, 0,
            permanent=False, transmutable=False,
            effects=(EffectDefinition(
                EffectKind.DEAL_DAMAGE,
                2,
                TargetMode.CHOSEN_PERMANENT,
                minimum_targets=2,
                maximum_targets=3,
            ),),
        )
        engine = self.make_engine((sweep,))
        spell = force_zone(engine, "SWEEP", "A", Zone.HAND)
        first = force_zone(engine, "A-001", "A", Zone.BATTLEFIELD)
        second = force_zone(engine, "B-001", "B", Zone.BATTLEFIELD)
        engine.execute(PlayCard("A", spell, (), (first, second)))
        resolve_one(engine)
        self.assertEqual(engine.state.cards[first].damage, 2)
        self.assertEqual(engine.state.cards[second].damage, 2)

    def test_divine_is_immune_to_quick_event_and_abilities_but_transmutable(self):
        divine = CardDefinition(
            "DIVINE", "Deidad", CardKind.CREATURE, 9,
            rank=CardRank.DIVINE, base_strength=9,
        )
        destroy = CardDefinition(
            "QUICK", "Rápido", CardKind.QUICK_RESOURCE, 0,
            permanent=False, transmutable=False,
            effects=(EffectDefinition(
                EffectKind.DESTROY, 1, TargetMode.CHOSEN_PERMANENT
            ),),
        )
        engine = self.make_engine((divine, destroy))
        divine_id = force_zone(engine, "DIVINE", "A", Zone.BATTLEFIELD)
        quick_id = force_zone(engine, "QUICK", "A", Zone.HAND)
        with self.assertRaises(IllegalAction):
            engine.execute(PlayCard("A", quick_id, (), (divine_id,)))
        engine.execute(TransmutePermanent("A", divine_id))
        self.assertIn(divine_id, engine.state.players["A"].zones[Zone.DISCARD])
        self.assertEqual(engine.state.players["A"].steps, 9)

    def divine_and_effect_source(self, kind, *, ability=False):
        divine = CardDefinition("DIV", "Divino", CardKind.CREATURE, 7, rank=CardRank.DIVINE, base_strength=7)
        effect = EffectDefinition(EffectKind.DESTROY, 1, TargetMode.CHOSEN_PERMANENT)
        source = CardDefinition(
            "SRC", "Fuente", kind, 0,
            base_strength=2 if kind is CardKind.CREATURE else None,
            permanent=ability,
            transmutable=False,
            effects=() if ability else (effect,),
            abilities=(AbilityDefinition("hit", (effect,)),) if ability else (),
        )
        engine = self.make_engine((divine, source))
        return engine, force_zone(engine, "DIV", "A", Zone.BATTLEFIELD), source

    def test_divine_blocks_event(self):
        engine, divine_id, _ = self.divine_and_effect_source(CardKind.EVENT)
        source_id = force_zone(engine, "SRC", "A", Zone.HAND)
        with self.assertRaises(IllegalAction):
            engine.execute(PlayCard("A", source_id, (), (divine_id,)))

    def test_divine_blocks_quick_resource(self):
        engine, divine_id, _ = self.divine_and_effect_source(CardKind.QUICK_RESOURCE)
        source_id = force_zone(engine, "SRC", "A", Zone.HAND)
        with self.assertRaises(IllegalAction):
            engine.execute(PlayCard("A", source_id, (), (divine_id,)))

    def test_divine_blocks_ability_from_permanent_creature(self):
        engine, divine_id, _ = self.divine_and_effect_source(CardKind.CREATURE, ability=True)
        source_id = force_zone(engine, "SRC", "A", Zone.BATTLEFIELD)
        with self.assertRaises(IllegalAction):
            engine.execute(ActivateAbility("A", source_id, "hit", (), (divine_id,)))

    def test_divine_allows_ability_from_noncreature_permanent(self):
        engine, divine_id, _ = self.divine_and_effect_source(CardKind.ARTIFACT, ability=True)
        source_id = force_zone(engine, "SRC", "A", Zone.BATTLEFIELD)
        engine.execute(ActivateAbility("A", source_id, "hit", (), (divine_id,)))
        self.assertEqual(engine.state.stack[-1].chosen_card_ids, (divine_id,))

    def test_divine_allows_own_ability(self):
        effect = EffectDefinition(EffectKind.UNTAP, 1, TargetMode.CHOSEN_PERMANENT)
        divine = CardDefinition(
            "SELF", "Divino", CardKind.CREATURE, 7, rank=CardRank.DIVINE,
            base_strength=7, abilities=(AbilityDefinition("self", (effect,)),),
        )
        engine = self.make_engine((divine,))
        divine_id = force_zone(engine, "SELF", "A", Zone.BATTLEFIELD)
        engine.execute(ActivateAbility("A", divine_id, "self", (), (divine_id,)))
        self.assertEqual(engine.state.stack[-1].chosen_card_ids, (divine_id,))

    def test_divine_transmutation_is_atomic(self):
        divine = CardDefinition("DIV", "Divino", CardKind.CREATURE, 7, rank=CardRank.DIVINE, base_strength=7)
        engine = self.make_engine((divine,))
        divine_id = force_zone(engine, "DIV", "A", Zone.BATTLEFIELD)
        before = deepcopy(engine.state)
        with patch.object(engine, "_emit", side_effect=RuntimeError("fallo inducido")):
            with self.assertRaises(RuntimeError):
                engine.execute(TransmutePermanent("A", divine_id))
        self.assertEqual(engine.state, before)

    def test_rejected_divine_target_does_not_change_replay(self):
        engine, divine_id, _ = self.divine_and_effect_source(CardKind.EVENT)
        source_id = force_zone(engine, "SRC", "A", Zone.HAND)
        before_replay = dump_replay(engine)
        before_digest = state_digest(engine)
        with self.assertRaises(IllegalAction):
            engine.execute(PlayCard("A", source_id, (), (divine_id,)))
        self.assertEqual(dump_replay(engine), before_replay)
        self.assertEqual(state_digest(engine), before_digest)

    def test_divine_has_no_automatic_immunity_to_sacrifice_cost(self):
        divine = CardDefinition("DIV", "Divino", CardKind.CREATURE, 7, rank=CardRank.DIVINE, base_strength=7)
        source = CardDefinition(
            "ALTAR", "Altar", CardKind.ARTIFACT, 0,
            abilities=(AbilityDefinition("offer", (), CompositeCost(sacrifice_count=1)),),
        )
        engine = self.make_engine((divine, source))
        divine_id = force_zone(engine, "DIV", "A", Zone.BATTLEFIELD)
        source_id = force_zone(engine, "ALTAR", "A", Zone.BATTLEFIELD)
        engine.execute(ActivateAbility("A", source_id, "offer", sacrifice_card_ids=(divine_id,)))
        self.assertIn(divine_id, engine.state.players["A"].zones[Zone.DISCARD])

    def test_continuous_layer_filters_by_subtype_and_disappears_with_source(self):
        lord = CardDefinition(
            "LORD", "Señor", CardKind.CREATURE, 20,
            lord_domain=LordDomain.REALMS,
            continuous_effects=(ContinuousEffectDefinition(
                strength_delta=5,
                grant_keywords=frozenset({"IMMUNE_EVENT"}),
                affected_kinds=frozenset({CardKind.CREATURE}),
                affected_subtypes=frozenset({"ELF"}),
                excludes_source=True,
            ),),
        )
        elf = CardDefinition(
            "ELF", "Elfo", CardKind.CREATURE, 5,
            base_strength=5, subtypes=frozenset({"ELF"}),
        )
        engine = self.make_engine((lord, elf))
        lord_id = force_zone(engine, "LORD", "A", Zone.BATTLEFIELD)
        elf_id = force_zone(engine, "ELF", "A", Zone.BATTLEFIELD)
        self.assertEqual(engine._current_strength(lord_id), 20)
        self.assertEqual(engine._current_strength(elf_id), 10)
        self.assertIn("IMMUNE_EVENT", engine._effective_keywords(elf_id))
        engine._move_card(lord_id, Zone.DISCARD, "A")
        self.assertEqual(engine._current_strength(elf_id), 5)
        self.assertNotIn("IMMUNE_EVENT", engine._effective_keywords(elf_id))

    def test_strength_cost_can_deplete_a_lord(self):
        lord = CardDefinition(
            "LORD", "Señor", CardKind.CREATURE, 10,
            lord_domain=LordDomain.ABYSS,
            abilities=(AbilityDefinition(
                "last_power", (), CompositeCost(strength=10)
            ),),
        )
        engine = self.make_engine((lord,))
        lord_id = force_zone(engine, "LORD", "A", Zone.BATTLEFIELD)
        engine.execute(ActivateAbility("A", lord_id, "last_power"))
        self.assertIn(lord_id, engine.state.players["A"].zones[Zone.DISCARD])
        self.assertEqual(len(engine.state.stack), 1)

    def test_challenge_replaces_combat_and_never_overflows_to_player(self):
        lord = CardDefinition(
            "DUELIST", "Señor Duelista", CardKind.CREATURE, 6,
            lord_domain=LordDomain.REALMS,
        )
        victim = CardDefinition("VICTIM", "Rival", CardKind.CREATURE, 4, base_strength=4)
        engine = self.make_engine((lord,), (victim,))
        challenger = force_zone(engine, "DUELIST", "A", Zone.BATTLEFIELD)
        challenged = force_zone(engine, "VICTIM", "B", Zone.BATTLEFIELD)
        engine.state.phase = Phase.COMBAT
        engine.state.priority_player_id = "A"
        engine.state.phase_priority_complete = True
        engine.execute(DeclareChallenge("A", challenger, challenged, "B"))
        resolve_one(engine)
        engine.execute(ResolveCombat("A"))
        self.assertIn(challenger, engine.state.players["A"].zones[Zone.BATTLEFIELD])
        self.assertIn(challenged, engine.state.players["B"].zones[Zone.DISCARD])
        self.assertEqual(engine.state.players["B"].wounds, 0)
        self.assertFalse(engine.state.cards[challenger].exhausted)

    def test_simultaneous_triggers_wait_for_controller_order(self):
        herald = CardDefinition(
            "HERALD", "Heraldo", CardKind.CREATURE, 0, base_strength=1,
            abilities=(
                AbilityDefinition(
                    "first", (EffectDefinition(EffectKind.GAIN_STEPS, 1),),
                    trigger=TriggerKind.ON_ENTER_BATTLEFIELD,
                ),
                AbilityDefinition(
                    "second", (EffectDefinition(EffectKind.GAIN_STEPS, 2),),
                    trigger=TriggerKind.ON_ENTER_BATTLEFIELD,
                ),
            ),
        )
        engine = self.make_engine((herald,))
        card_id = force_zone(engine, "HERALD", "A", Zone.HAND)
        engine.state.phase = Phase.EFFECTS
        engine.state.priority_player_id = "A"
        engine.execute(PlayCard("A", card_id))
        resolve_one(engine)
        self.assertEqual(len(engine.state.pending_triggers), 2)
        chosen = tuple(item.item_id for item in reversed(engine.state.pending_triggers))
        engine.execute(OrderTriggeredAbilities("A", chosen))
        self.assertEqual(engine.state.stack[-1].item_id, chosen[0])
        resolve_one(engine)
        resolve_one(engine)
        self.assertEqual(engine.state.players["A"].steps, 3)

    def test_lord_can_become_creature_until_end_of_turn(self):
        lord = CardDefinition(
            "ARCANE_LORD", "Señor de la Magia", CardKind.LORD, 15,
            lord_domain=LordDomain.MAGIC,
            abilities=(AbilityDefinition(
                "manifest",
                (EffectDefinition(
                    EffectKind.BECOME_CREATURE,
                    0,
                    TargetMode.SOURCE,
                    EffectDuration.END_OF_TURN,
                ),),
                CompositeCost(strength=5),
            ),),
        )
        engine = self.make_engine((lord,))
        lord_id = force_zone(engine, "ARCANE_LORD", "A", Zone.BATTLEFIELD)
        engine.execute(ActivateAbility("A", lord_id, "manifest"))
        resolve_one(engine)
        self.assertTrue(engine._is_lord_creature(lord_id))
        self.assertEqual(engine._current_strength(lord_id), 10)
        engine._cleanup_end_of_turn()
        self.assertFalse(engine._is_creature(lord_id))


if __name__ == "__main__":
    unittest.main()
