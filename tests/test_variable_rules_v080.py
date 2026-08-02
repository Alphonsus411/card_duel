import unittest

from card_duel_engine import GameEngine, RuleSet
from card_duel_engine.domain import (
    AbilityDefinition,
    CardDefinition,
    CardKind,
    CostComponent,
    EffectDefinition,
    EffectKind,
    EffectPatchDefinition,
    MoveReplacementDefinition,
    TargetAllocation,
    TargetMode,
    TextPatchDefinition,
    XCostDefinition,
    Zone,
)
from card_duel_engine.domain.errors import IllegalAction, PaymentError
from card_duel_engine.engine import (
    ActivateAbility,
    PassPriority,
    PlayCard,
    ResolveMoveReplacement,
)
from card_duel_engine.persistence import dump_snapshot

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


class VariableRulesV080Tests(unittest.TestCase):
    def make_engine(self, a_specials=(), b_specials=()):
        engine = GameEngine(RuleSet())
        engine.new_match(
            {
                "A": [*a_specials, *test_deck("A8", 16)],
                "B": [*b_specials, *test_deck("B8", 16)],
            },
            seed=80,
        )
        return engine

    def test_x_cost_is_paid_and_frozen_on_the_stack(self):
        burst = CardDefinition(
            "X_BURST8",
            "Estallido variable",
            CardKind.QUICK_RESOURCE,
            20,
            permanent=False,
            transmutable=False,
            x_cost=XCostDefinition(
                CostComponent.STEPS,
                multiplier=2,
                minimum=0,
                maximum=5,
            ),
            effects=(
                EffectDefinition(
                    EffectKind.DEAL_WOUNDS,
                    1,
                    TargetMode.CHOSEN_PLAYER,
                    x_multiplier=3,
                ),
            ),
        )
        engine = self.make_engine((burst,))
        card_id = force_zone(engine, "X_BURST8", "A", Zone.HAND)
        engine.state.players["A"].steps = 6
        legal_x = {
            action.x_value
            for action in engine.legal_actions("A")
            if isinstance(action, PlayCard) and action.card_id == card_id
        }
        self.assertEqual(legal_x, {0, 1, 2, 3})

        engine.execute(
            PlayCard("A", card_id, chosen_player_ids=("B",), x_value=3)
        )
        self.assertEqual(engine.state.players["A"].steps, 0)
        self.assertEqual(engine.state.stack[-1].x_value, 3)
        # Cambiar la Reserva después del anuncio no recalcula X.
        engine.state.players["A"].steps = 50
        resolve_one(engine)
        self.assertEqual(engine.state.players["B"].wounds, 10)

    def test_invalid_x_and_invalid_x_distribution_are_atomic(self):
        divided = CardDefinition(
            "X_DIVIDE8",
            "Reparto variable",
            CardKind.QUICK_RESOURCE,
            0,
            permanent=False,
            transmutable=False,
            x_cost=XCostDefinition(CostComponent.STEPS, maximum=6),
            effects=(
                EffectDefinition(
                    EffectKind.DEAL_HARM,
                    0,
                    TargetMode.CHOSEN_ENTITY,
                    minimum_targets=1,
                    maximum_targets=2,
                    distributed=True,
                    x_multiplier=1,
                ),
            ),
        )
        engine = self.make_engine((divided,))
        card_id = force_zone(engine, "X_DIVIDE8", "A", Zone.HAND)
        engine.state.players["A"].steps = 5
        before = tuple(engine.state.players["A"].zones[Zone.HAND])
        with self.assertRaises(IllegalAction):
            engine.execute(
                PlayCard(
                    "A",
                    card_id,
                    allocations=(TargetAllocation("B", 4),),
                    x_value=5,
                )
            )
        self.assertEqual(tuple(engine.state.players["A"].zones[Zone.HAND]), before)
        self.assertEqual(engine.state.players["A"].steps, 5)
        with self.assertRaises(PaymentError):
            engine.execute(
                PlayCard(
                    "A",
                    card_id,
                    allocations=(TargetAllocation("B", 7),),
                    x_value=7,
                )
            )

    def test_activated_ability_can_use_x(self):
        source_definition = CardDefinition(
            "X_ABILITY8",
            "Canalizador",
            CardKind.CREATURE,
            2,
            base_strength=2,
            abilities=(
                AbilityDefinition(
                    "channel",
                    (
                        EffectDefinition(
                            EffectKind.DEAL_WOUNDS,
                            0,
                            TargetMode.CHOSEN_PLAYER,
                            x_multiplier=1,
                        ),
                    ),
                    x_cost=XCostDefinition(CostComponent.STEPS, maximum=5),
                ),
            ),
        )
        engine = self.make_engine((source_definition,))
        source = force_zone(engine, "X_ABILITY8", "A", Zone.BATTLEFIELD)
        engine.state.players["A"].steps = 4
        legal_x = {
            action.x_value
            for action in engine.legal_actions("A")
            if isinstance(action, ActivateAbility)
            and action.source_card_id == source
            and action.chosen_player_ids == ("B",)
        }
        self.assertEqual(legal_x, {0, 1, 2, 3, 4})
        engine.execute(
            ActivateAbility(
                "A", source, "channel", chosen_player_ids=("B",), x_value=4
            )
        )
        self.assertEqual(engine.state.players["A"].steps, 0)
        resolve_one(engine)
        self.assertEqual(engine.state.players["B"].wounds, 4)

    def test_effect_patch_changes_ability_magnitude_and_target_count(self):
        battery = CardDefinition(
            "BATTERY8",
            "Batería",
            CardKind.CREATURE,
            2,
            base_strength=2,
            abilities=(
                AbilityDefinition(
                    "pulse",
                    (
                        EffectDefinition(
                            EffectKind.DEAL_WOUNDS,
                            2,
                            TargetMode.SELF,
                        ),
                    ),
                ),
            ),
        )
        editor = CardDefinition(
            "EFFECT_EDITOR8",
            "Reescribir efecto",
            CardKind.QUICK_RESOURCE,
            0,
            permanent=False,
            transmutable=False,
            effects=(
                EffectDefinition(
                    EffectKind.MODIFY_TEXT,
                    0,
                    TargetMode.CHOSEN_PERMANENT,
                    text_patch=TextPatchDefinition(
                        effect_patches=(
                            EffectPatchDefinition(
                                effect_index=0,
                                ability_id="pulse",
                                amount_delta=3,
                                set_minimum_targets=2,
                                set_maximum_targets=2,
                                set_target=TargetMode.CHOSEN_PLAYER,
                            ),
                        ),
                    ),
                ),
            ),
        )
        engine = self.make_engine((battery, editor))
        source = force_zone(engine, "BATTERY8", "A", Zone.BATTLEFIELD)
        spell = force_zone(engine, "EFFECT_EDITOR8", "A", Zone.HAND)
        engine.execute(PlayCard("A", spell, chosen_card_ids=(source,)))
        resolve_one(engine)

        ability = engine._definition(source).abilities[0]
        self.assertEqual(ability.effects[0].amount, 5)
        self.assertEqual(ability.effects[0].minimum_targets, 2)
        self.assertEqual(ability.effects[0].maximum_targets, 2)
        engine.state.priority_player_id = "A"
        engine.execute(
            ActivateAbility(
                "A",
                source,
                "pulse",
                chosen_player_ids=("A", "B"),
            )
        )
        resolve_one(engine)
        self.assertEqual(engine.state.players["A"].wounds, 5)
        self.assertEqual(engine.state.players["B"].wounds, 5)

    def test_two_deferred_replacements_replay_one_action_without_partial_state(self):
        replacement_pair = (
            MoveReplacementDefinition(Zone.HAND),
            MoveReplacementDefinition(Zone.EXILE),
        )
        first = CardDefinition(
            "DEFER_A8",
            "Destino A",
            CardKind.CREATURE,
            3,
            base_strength=3,
            move_replacements=replacement_pair,
            deferred_replacement_choice=True,
        )
        second = CardDefinition(
            "DEFER_B8",
            "Destino B",
            CardKind.CREATURE,
            3,
            base_strength=3,
            move_replacements=replacement_pair,
            deferred_replacement_choice=True,
        )
        destroy = CardDefinition(
            "DOUBLE_DESTROY8",
            "Destrucción doble",
            CardKind.QUICK_RESOURCE,
            0,
            permanent=False,
            transmutable=False,
            effects=(
                EffectDefinition(
                    EffectKind.DESTROY,
                    0,
                    TargetMode.CHOSEN_PERMANENT,
                    minimum_targets=2,
                    maximum_targets=2,
                ),
            ),
        )
        engine = self.make_engine((destroy,), (first, second))
        spell = force_zone(engine, "DOUBLE_DESTROY8", "A", Zone.HAND)
        target_a = force_zone(engine, "DEFER_A8", "B", Zone.BATTLEFIELD)
        target_b = force_zone(engine, "DEFER_B8", "B", Zone.BATTLEFIELD)
        engine.execute(
            PlayCard("A", spell, chosen_card_ids=(target_a, target_b))
        )
        engine.execute(PassPriority("B"))
        engine.execute(PassPriority("A"))

        pending = engine.state.pending_move_replacement
        self.assertIsNotNone(pending)
        self.assertEqual(pending.card_id, target_a)
        self.assertIn(target_a, engine.state.players["B"].zones[Zone.BATTLEFIELD])
        self.assertIn(target_b, engine.state.players["B"].zones[Zone.BATTLEFIELD])
        self.assertEqual(engine.observe("A").replacement_destinations, ())
        self.assertEqual(
            engine.observe("B").replacement_destinations,
            ((0, "HAND"), (1, "EXILE")),
        )
        with self.assertRaises(IllegalAction):
            engine.execute(ResolveMoveReplacement("A", 0))

        engine.execute(ResolveMoveReplacement("B", 0))
        self.assertEqual(engine.state.pending_move_replacement.card_id, target_b)
        # La primera destrucción sigue sin estar aplicada: la acción completa se reintentará.
        self.assertIn(target_a, engine.state.players["B"].zones[Zone.BATTLEFIELD])
        engine.execute(ResolveMoveReplacement("B", 1))

        self.assertIsNone(engine.state.pending_move_replacement)
        self.assertIn(target_a, engine.state.players["B"].zones[Zone.HAND])
        self.assertIn(target_b, engine.state.players["B"].zones[Zone.EXILE])
        self.assertIn(spell, engine.state.players["A"].zones[Zone.DISCARD])
        engine.validate_invariants()

    def test_failed_replay_restores_the_complete_pending_choice_state(self):
        resilient = CardDefinition(
            "DEFER_FAILURE8",
            "Destino recuperable",
            CardKind.CREATURE,
            3,
            base_strength=3,
            move_replacements=(
                MoveReplacementDefinition(Zone.HAND),
                MoveReplacementDefinition(Zone.EXILE),
            ),
            deferred_replacement_choice=True,
        )
        destroy = CardDefinition(
            "DESTROY_FAILURE8",
            "Destrucción fallida",
            CardKind.QUICK_RESOURCE,
            0,
            permanent=False,
            transmutable=False,
            effects=(
                EffectDefinition(EffectKind.DESTROY, 0, TargetMode.CHOSEN_PERMANENT),
            ),
        )
        engine = self.make_engine((destroy,), (resilient,))
        spell = force_zone(engine, "DESTROY_FAILURE8", "A", Zone.HAND)
        target = force_zone(engine, "DEFER_FAILURE8", "B", Zone.BATTLEFIELD)
        engine.execute(PlayCard("A", spell, chosen_card_ids=(target,)))
        engine.execute(PassPriority("B"))
        engine.execute(PassPriority("A"))

        fingerprint_before = dump_snapshot(engine, indent=None)
        replay_state_before = (
            engine._replacement_replay_choices,
            engine._replacement_replay_cursor,
        )
        check_wound_limits = engine._check_wound_limits

        def fail_after_replacement():
            raise RuntimeError("fallo posterior simulado")

        engine._check_wound_limits = fail_after_replacement
        try:
            with self.assertRaisesRegex(RuntimeError, "fallo posterior simulado"):
                engine.execute(ResolveMoveReplacement("B", 0))
        finally:
            engine._check_wound_limits = check_wound_limits

        self.assertEqual(dump_snapshot(engine, indent=None), fingerprint_before)
        self.assertEqual(
            (engine._replacement_replay_choices, engine._replacement_replay_cursor),
            replay_state_before,
        )


if __name__ == "__main__":
    unittest.main()
