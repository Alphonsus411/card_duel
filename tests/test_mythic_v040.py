import unittest

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
    DeclareChallenge,
    DrainSteps,
    OrderTriggeredAbilities,
    PassPriority,
    PlayCard,
    ResolveCombat,
    TransmutePermanent,
)

from fixtures import test_deck


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

    def test_universal_drainage_is_once_per_active_turn(self):
        engine = self.make_engine()
        engine.execute(DrainSteps("A", 5))
        self.assertEqual(engine.state.players["A"].steps, 5)
        self.assertEqual(engine.state.players["A"].wounds, 12)
        engine.state.priority_player_id = "A"
        with self.assertRaises(IllegalAction):
            engine.execute(DrainSteps("A", 1))
        engine.state.priority_player_id = "B"
        with self.assertRaises(IllegalAction):
            engine.execute(DrainSteps("B", 1))

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
