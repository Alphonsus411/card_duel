import unittest

from card_duel_engine import GameEngine, RuleSet
from card_duel_engine.domain import (
    AbilityDefinition,
    CardDefinition,
    CardKind,
    ContinuousEffectDefinition,
    EffectDefinition,
    EffectDuration,
    EffectKind,
    MoveReason,
    MoveReplacementDefinition,
    Phase,
    TargetAllocation,
    TargetMode,
    TriggerKind,
    Zone,
    ZoneTarget,
)
from card_duel_engine.engine import (
    AdvancePhase,
    ChooseTriggeredTargets,
    OrderTriggeredAbilities,
    PassPriority,
    PlayCard,
)
from card_duel_engine.domain.errors import IllegalAction

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


class ResolutionV050Tests(unittest.TestCase):
    def make_engine(self, a_specials=(), b_specials=()):
        engine = GameEngine(RuleSet())
        engine.new_match(
            {
                "A": [*a_specials, *test_deck("A", 14)],
                "B": [*b_specials, *test_deck("B", 14)],
            },
            seed=50,
        )
        return engine

    def test_zone_target_moves_top_cards_without_exposing_selection(self):
        mill = CardDefinition(
            "MILL", "Vaciar", CardKind.QUICK_RESOURCE, 0,
            permanent=False,
            transmutable=False,
            effects=(EffectDefinition(
                EffectKind.MOVE_CARDS,
                3,
                TargetMode.CHOSEN_ZONE,
                destination_zone=Zone.DISCARD,
            ),),
        )
        engine = self.make_engine((mill,))
        spell = force_zone(engine, "MILL", "A", Zone.HAND)
        deck_before = len(engine.state.players["B"].zones[Zone.DECK])
        discard_before = len(engine.state.players["B"].zones[Zone.DISCARD])
        engine.execute(
            PlayCard(
                "A",
                spell,
                chosen_zone_targets=(ZoneTarget("B", Zone.DECK),),
            )
        )
        resolve_one(engine)
        self.assertEqual(len(engine.state.players["B"].zones[Zone.DECK]), deck_before - 3)
        self.assertEqual(
            len(engine.state.players["B"].zones[Zone.DISCARD]), discard_before + 3
        )

    def test_damage_can_be_distributed_between_player_and_creature(self):
        blast = CardDefinition(
            "BLAST", "Llamarada", CardKind.QUICK_RESOURCE, 0,
            permanent=False,
            transmutable=False,
            effects=(EffectDefinition(
                EffectKind.DEAL_HARM,
                10,
                TargetMode.CHOSEN_ENTITY,
                minimum_targets=1,
                maximum_targets=3,
                distributed=True,
            ),),
        )
        giant = CardDefinition("GIANT", "Gigante", CardKind.CREATURE, 20, base_strength=20)
        engine = self.make_engine((blast,), (giant,))
        spell = force_zone(engine, "BLAST", "A", Zone.HAND)
        creature = force_zone(engine, "GIANT", "B", Zone.BATTLEFIELD)
        engine.execute(
            PlayCard(
                "A",
                spell,
                allocations=(
                    TargetAllocation("B", 4),
                    TargetAllocation(creature, 6),
                ),
            )
        )
        resolve_one(engine)
        self.assertEqual(engine.state.players["B"].wounds, 4)
        self.assertEqual(engine.state.cards[creature].damage, 6)

    def test_invalid_distribution_is_rejected_before_payment(self):
        blast = CardDefinition(
            "BAD_SPLIT", "Reparto", CardKind.QUICK_RESOURCE, 2,
            permanent=False,
            transmutable=False,
            effects=(EffectDefinition(
                EffectKind.DEAL_HARM,
                10,
                TargetMode.CHOSEN_ENTITY,
                maximum_targets=2,
                distributed=True,
            ),),
        )
        engine = self.make_engine((blast,))
        spell = force_zone(engine, "BAD_SPLIT", "A", Zone.HAND)
        engine.state.players["A"].steps = 2
        with self.assertRaises(IllegalAction):
            engine.execute(
                PlayCard(
                    "A",
                    spell,
                    allocations=(TargetAllocation("B", 9),),
                )
            )
        self.assertEqual(engine.state.players["A"].steps, 2)
        self.assertIn(spell, engine.state.players["A"].zones[Zone.HAND])

    def test_combinatorial_legal_actions_are_bounded(self):
        blast = CardDefinition(
            "BOUNDED", "Acotado", CardKind.QUICK_RESOURCE, 0,
            permanent=False,
            transmutable=False,
            effects=(EffectDefinition(
                EffectKind.DEAL_HARM,
                12,
                TargetMode.CHOSEN_ENTITY,
                maximum_targets=4,
                distributed=True,
            ),),
        )
        engine = GameEngine(RuleSet(legal_action_enumeration_limit=7))
        engine.new_match(
            {"A": [blast, *test_deck("A", 14)], "B": test_deck("B", 14)},
            seed=51,
        )
        spell = force_zone(engine, "BOUNDED", "A", Zone.HAND)
        proposals = [
            action
            for action in engine.legal_actions("A")
            if isinstance(action, PlayCard) and action.card_id == spell
        ]
        self.assertEqual(len(proposals), 7)

    def test_automatic_trigger_waits_for_targets_then_order(self):
        herald = CardDefinition(
            "HERALD_TARGET", "Heraldo", CardKind.CREATURE, 0, base_strength=1,
            abilities=(AbilityDefinition(
                "arrival_hit",
                (EffectDefinition(
                    EffectKind.DEAL_WOUNDS, 3, TargetMode.CHOSEN_PLAYER
                ),),
                trigger=TriggerKind.ON_ENTER_BATTLEFIELD,
            ),),
        )
        engine = self.make_engine((herald,))
        card_id = force_zone(engine, "HERALD_TARGET", "A", Zone.HAND)
        engine.state.phase = Phase.EFFECTS
        engine.state.priority_player_id = "A"
        engine.execute(PlayCard("A", card_id))
        resolve_one(engine)
        item = engine.state.pending_triggers[0]
        self.assertFalse(item.targets_locked)
        engine.execute(
            ChooseTriggeredTargets("A", item.item_id, chosen_player_ids=("B",))
        )
        engine.execute(OrderTriggeredAbilities("A", (item.item_id,)))
        resolve_one(engine)
        self.assertEqual(engine.state.players["B"].wounds, 3)

    def test_move_replacement_can_return_destroyed_card_to_hand(self):
        survivor = CardDefinition(
            "SURVIVOR", "Superviviente", CardKind.CREATURE, 4, base_strength=4,
            move_replacement=MoveReplacementDefinition(Zone.HAND),
        )
        engine = self.make_engine((survivor,))
        card_id = force_zone(engine, "SURVIVOR", "A", Zone.BATTLEFIELD)
        destroyed = engine._destroy_permanent(card_id, MoveReason.DESTROY)
        self.assertFalse(destroyed)
        self.assertIn(card_id, engine.state.players["A"].zones[Zone.HAND])

    def test_replacement_can_return_with_less_strength_until_exhausted(self):
        revenant = CardDefinition(
            "REVENANT", "Retornado", CardKind.CREATURE, 2, base_strength=2,
            move_replacement=MoveReplacementDefinition(
                Zone.BATTLEFIELD,
                strength_delta=-1,
                enters_exhausted=True,
                minimum_strength_after=1,
            ),
        )
        engine = self.make_engine((revenant,))
        card_id = force_zone(engine, "REVENANT", "A", Zone.BATTLEFIELD)
        engine._destroy_permanent(card_id, MoveReason.DESTROY)
        self.assertEqual(engine._current_strength(card_id), 1)
        self.assertTrue(engine.state.cards[card_id].exhausted)
        engine._destroy_permanent(card_id, MoveReason.DESTROY)
        self.assertIn(card_id, engine.state.players["A"].zones[Zone.DISCARD])

    def test_regeneration_is_consumed_before_move_replacement(self):
        creature = CardDefinition(
            "REGEN", "Regenerable", CardKind.CREATURE, 5, base_strength=5,
            move_replacement=MoveReplacementDefinition(Zone.HAND),
        )
        ward = CardDefinition(
            "WARD", "Regenerar", CardKind.QUICK_RESOURCE, 0,
            permanent=False,
            transmutable=False,
            effects=(EffectDefinition(
                EffectKind.ADD_REGENERATION,
                1,
                TargetMode.CHOSEN_PERMANENT,
            ),),
        )
        engine = self.make_engine((creature, ward))
        card_id = force_zone(engine, "REGEN", "A", Zone.BATTLEFIELD)
        ward_id = force_zone(engine, "WARD", "A", Zone.HAND)
        engine.execute(PlayCard("A", ward_id, chosen_card_ids=(card_id,)))
        resolve_one(engine)
        engine.state.cards[card_id].damage = 4
        engine._destroy_permanent(card_id, MoveReason.DESTROY)
        self.assertIn(card_id, engine.state.players["A"].zones[Zone.BATTLEFIELD])
        self.assertEqual(engine.state.cards[card_id].damage, 0)
        self.assertEqual(engine.state.cards[card_id].regeneration_shields, 0)
        engine._destroy_permanent(
            card_id, MoveReason.DESTROY, allows_regeneration=False
        )
        self.assertIn(card_id, engine.state.players["A"].zones[Zone.HAND])

    def test_next_draw_phase_can_be_suppressed(self):
        denial = CardDefinition(
            "DENIAL", "Pacto", CardKind.QUICK_RESOURCE, 0,
            permanent=False,
            transmutable=False,
            effects=(EffectDefinition(
                EffectKind.SKIP_PHASE,
                0,
                TargetMode.CHOSEN_PLAYER,
                EffectDuration.NEXT_OCCURRENCE,
                phase=Phase.DRAW,
            ),),
        )
        engine = self.make_engine((denial,))
        spell = force_zone(engine, "DENIAL", "A", Zone.HAND)
        engine.execute(PlayCard("A", spell, chosen_player_ids=("B",)))
        resolve_one(engine)
        hand_before = len(engine.state.players["B"].zones[Zone.HAND])
        engine.state.phase = Phase.DISCARD
        engine.state.phase_priority_complete = True
        engine.state.priority_player_id = "A"
        while len(engine.state.players["A"].zones[Zone.HAND]) > engine.rules.hand_limit:
            discarded = engine.state.players["A"].zones[Zone.HAND][-1]
            engine._move_card(
                discarded, Zone.DISCARD, "A", reason=MoveReason.DISCARD
            )
        engine.execute(AdvancePhase("A"))
        self.assertEqual(engine.state.active_player_id, "B")
        self.assertEqual(engine.state.phase, Phase.MAINTENANCE)
        self.assertEqual(len(engine.state.players["B"].zones[Zone.HAND]), hand_before)

    def test_continuous_effect_can_remove_combat_phase(self):
        pacifist = CardDefinition(
            "PACIFIST", "Pacifista", CardKind.ARTIFACT, 1,
            continuous_effects=(ContinuousEffectDefinition(
                suppressed_phases=frozenset({Phase.COMBAT}),
            ),),
        )
        engine = self.make_engine((pacifist,))
        force_zone(engine, "PACIFIST", "A", Zone.BATTLEFIELD)
        engine.state.phase = Phase.EFFECTS
        engine.state.phase_priority_complete = True
        engine.state.priority_player_id = "A"
        engine.execute(AdvancePhase("A"))
        self.assertEqual(engine.state.phase, Phase.LEGENDARY)
        self.assertEqual(engine.state.event_log[-2].event_type, "PHASE_SKIPPED")


if __name__ == "__main__":
    unittest.main()
