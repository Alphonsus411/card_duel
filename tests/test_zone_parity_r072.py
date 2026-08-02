"""Paridad de la frontera de movimientos cerrada en R-07.2."""

import unittest
from copy import deepcopy
from types import SimpleNamespace

from card_duel_engine import GameEngine
from card_duel_engine.domain.enums import CardKind, MatchStatus, MoveReason, Phase, Zone
from card_duel_engine.domain.errors import IllegalAction
from card_duel_engine.domain.models import (
    CardDefinition,
    CardInstance,
    GameEvent,
    GameState,
    MoveReplacementDefinition,
    PlayerState,
)
from card_duel_engine.engine.commands import SetReplacementOrder
from card_duel_engine.engine.zones import MoveReplacementChoiceRequired, ZoneContext, ZoneManager
from card_duel_engine.rules.config import RuleSet


class MinimalZoneContext:
    """Implementación independiente que contiene exactamente el contrato de zonas."""

    def __init__(self, *, rules: RuleSet | None = None) -> None:
        self.rules = rules or RuleSet()
        self.state = GameState(
            ruleset_id="base",
            ruleset_version="R-07.2",
            players={"A": PlayerState("A"), "B": PlayerState("B")},
            turn_order=("A", "B"),
            cards={},
            priority_player_id="A",
            phase=Phase.EFFECTS,
            status=MatchStatus.RUNNING,
            random_seed=722,
        )
        self.definitions: dict[str, CardDefinition] = {}
        self.replay_choices: tuple[int, ...] = ()
        self.replay_cursor = 0
        # Testigos de que el gestor no toca servicios del coordinador.
        self.next_instance = 17
        self.next_stack_item = 23

    def add(self, card_id: str, zone: Zone, player_id: str = "A", definition: CardDefinition | None = None) -> None:
        definition = definition or CardDefinition(card_id, card_id, CardKind.CREATURE, 0, base_strength=3)
        self.definitions[card_id] = definition
        self.state.cards[card_id] = CardInstance(card_id, definition.card_id, player_id, player_id, zone)
        if zone is Zone.RESOLUTION:
            self.state.resolution.append(card_id)
        elif zone is Zone.VOID:
            self.state.void.append(card_id)
        else:
            self.state.players[player_id].zones[zone].append(card_id)

    def _require_state(self) -> GameState:
        return self.state

    def _require_running_state(self) -> GameState:
        if self.state.status is not MatchStatus.RUNNING:
            raise IllegalAction("La partida no está en ejecución")
        return self.state

    def _definition(self, card_id: str) -> CardDefinition:
        return self.definitions[self.state.cards[card_id].definition_id]

    def _current_strength(self, card_id: str) -> int:
        definition = self._definition(card_id)
        return (definition.base_strength or 0) + self.state.cards[card_id].strength_modifier

    def _consume_replacement_replay_choice(self) -> int | None:
        if self.replay_cursor == len(self.replay_choices):
            return None
        choice = self.replay_choices[self.replay_cursor]
        self.replay_cursor += 1
        return choice

    def _emit(self, event_type: str, player_id: str | None = None, card_id: str | None = None, payload: dict[str, object] | None = None) -> None:
        self.state.event_log.append(GameEvent(len(self.state.event_log) + 1, event_type, player_id, card_id, payload or {}))


class ZoneParityR072Tests(unittest.TestCase):
    def _pair(self, prepare=None) -> tuple[MinimalZoneContext, MinimalZoneContext, ZoneManager, object]:
        direct = MinimalZoneContext()
        if prepare:
            prepare(direct)
        facade = deepcopy(direct)
        manager = ZoneManager(direct)
        adapter = SimpleNamespace(_zones=ZoneManager(facade))
        return direct, facade, manager, adapter

    @staticmethod
    def _fingerprint(context: MinimalZoneContext) -> tuple[object, ...]:
        state = context.state
        return (
            deepcopy(state), tuple(deepcopy(state.event_log)),
            tuple(deepcopy(state.command_history)), state.random_seed,
            context.replay_choices, context.replay_cursor,
            context.next_instance, context.next_stack_item,
            deepcopy(state.pending_move_replacement),
        )

    def _assert_parity(self, direct: MinimalZoneContext, facade: MinimalZoneContext) -> None:
        self.assertEqual(self._fingerprint(direct), self._fingerprint(facade))

    def test_normal_draw_and_empty_deck(self) -> None:
        for amount in (1, 2):
            direct, facade, manager, adapter = self._pair(lambda c: c.add("c1", Zone.DECK))
            manager._draw("A", amount)
            GameEngine._draw(adapter, "A", amount)  # type: ignore[arg-type]
            self._assert_parity(direct, facade)
        self.assertEqual([event.event_type for event in direct.state.event_log], ["CARD_DRAWN", "DRAW_FAILED"])

    def test_recycling_shuffle_is_seeded_and_reproducible(self) -> None:
        def prepare(context: MinimalZoneContext) -> None:
            for card in ("c1", "c2", "c3", "c4"):
                context.add(card, Zone.DISCARD)
        direct, facade, manager, adapter = self._pair(prepare)
        manager._draw("A", 2)
        GameEngine._draw(adapter, "A", 2)  # type: ignore[arg-type]
        self._assert_parity(direct, facade)
        repeat = MinimalZoneContext()
        prepare(repeat)
        ZoneManager(repeat)._draw("A", 2)
        self.assertEqual(self._fingerprint(direct), self._fingerprint(repeat))
        self.assertEqual(direct.state.random_seed, 722)

    def test_move_between_every_storable_zone(self) -> None:
        stored = (Zone.DECK, Zone.HAND, Zone.BATTLEFIELD, Zone.DISCARD, Zone.EXILE, Zone.REVEAL, Zone.RESOLUTION, Zone.VOID)
        for source in stored:
            for destination in stored:
                direct, facade, manager, adapter = self._pair(lambda c, source=source: c.add("c", source))
                manager._move_card("c", destination, "B")
                GameEngine._move_card(adapter, "c", destination, "B")  # type: ignore[arg-type]
                self._assert_parity(direct, facade)

    def test_equipment_detaches_and_instance_state_is_cleared(self) -> None:
        def prepare(context: MinimalZoneContext) -> None:
            context.add("unit", Zone.BATTLEFIELD)
            context.add("gear", Zone.BATTLEFIELD, definition=CardDefinition("gear", "gear", CardKind.EQUIPMENT, 0))
            unit, gear = context.state.cards["unit"], context.state.cards["gear"]
            gear.attached_to = "unit"
            unit.exhausted = True; unit.damage = 2; unit.strength_modifier = 4
            unit.damage_prevention = 3; unit.activated_this_turn.add("x")
            unit.transformed_as_creature = True; unit.regeneration_shields = 2
            unit.replacement_order = (0,)
        direct, facade, manager, adapter = self._pair(prepare)
        manager._move_card("unit", Zone.HAND, "A")
        GameEngine._move_card(adapter, "unit", Zone.HAND, "A")  # type: ignore[arg-type]
        self._assert_parity(direct, facade)
        self.assertIsNone(direct.state.cards["gear"].attached_to)
        self.assertEqual(direct.state.cards["unit"], CardInstance("unit", "unit", "A", "A", Zone.HAND))

    def test_priority_and_player_selected_replacement_order(self) -> None:
        replacements = (
            MoveReplacementDefinition(Zone.EXILE, priority=1),
            MoveReplacementDefinition(Zone.HAND, priority=9),
        )
        definition = CardDefinition("c", "c", CardKind.CREATURE, 0, base_strength=3, move_replacements=replacements, player_orders_replacements=True)
        direct, facade, manager, adapter = self._pair(lambda c: c.add("c", Zone.BATTLEFIELD, definition=definition))
        self.assertEqual(manager._ordered_replacements("c", definition), (replacements[1], replacements[0]))
        self.assertEqual(GameEngine._ordered_replacements(adapter, "c", definition), (replacements[1], replacements[0]))  # type: ignore[arg-type]
        command = SetReplacementOrder("A", "c", (1, 0))
        manager._set_replacement_order(command)
        GameEngine._set_replacement_order(adapter, command)  # type: ignore[arg-type]
        self._assert_parity(direct, facade)
        manager._move_card("c", Zone.DISCARD, "A", reason=MoveReason.DESTROY)
        GameEngine._move_card(adapter, "c", Zone.DISCARD, "A", reason=MoveReason.DESTROY)  # type: ignore[arg-type]
        self._assert_parity(direct, facade)
        self.assertEqual(direct.state.cards["c"].zone, Zone.HAND)

    def test_default_replacement_uses_priority(self) -> None:
        definition = CardDefinition("c", "c", CardKind.CREATURE, 0, base_strength=3, move_replacements=(MoveReplacementDefinition(Zone.EXILE, priority=1), MoveReplacementDefinition(Zone.HAND, priority=9)))
        direct, facade, manager, adapter = self._pair(lambda c: c.add("c", Zone.BATTLEFIELD, definition=definition))
        manager._move_card("c", Zone.DISCARD, "A")
        GameEngine._move_card(adapter, "c", Zone.DISCARD, "A")  # type: ignore[arg-type]
        self._assert_parity(direct, facade)
        self.assertEqual(direct.state.cards["c"].zone, Zone.HAND)

    def test_deferred_choice_and_replayed_choice_have_parity(self) -> None:
        definition = CardDefinition("c", "c", CardKind.CREATURE, 0, base_strength=3, move_replacements=(MoveReplacementDefinition(Zone.EXILE), MoveReplacementDefinition(Zone.HAND)), deferred_replacement_choice=True)
        direct, facade, manager, adapter = self._pair(lambda c: c.add("c", Zone.BATTLEFIELD, definition=definition))
        before_direct, before_facade = self._fingerprint(direct), self._fingerprint(facade)
        for call in (lambda: manager._move_card("c", Zone.DISCARD, "A"), lambda: GameEngine._move_card(adapter, "c", Zone.DISCARD, "A")):  # type: ignore[arg-type]
            with self.assertRaises(MoveReplacementChoiceRequired): call()
        self.assertEqual(self._fingerprint(direct), before_direct)
        self.assertEqual(self._fingerprint(facade), before_facade)
        direct.replay_choices = facade.replay_choices = (1,)
        manager._move_card("c", Zone.DISCARD, "A")
        GameEngine._move_card(adapter, "c", Zone.DISCARD, "A")  # type: ignore[arg-type]
        self._assert_parity(direct, facade)
        self.assertEqual(direct.state.cards["c"].zone, Zone.HAND)

    def test_illegal_command_and_exception_leave_no_partial_mutation(self) -> None:
        definition = CardDefinition("c", "c", CardKind.CREATURE, 0, base_strength=3, move_replacements=(MoveReplacementDefinition(Zone.HAND), MoveReplacementDefinition(Zone.EXILE)), player_orders_replacements=True)
        direct, facade, manager, adapter = self._pair(lambda c: c.add("c", Zone.BATTLEFIELD, definition=definition))
        before_direct, before_facade = self._fingerprint(direct), self._fingerprint(facade)
        bad = SetReplacementOrder("A", "c", (0, 0))
        for call in (lambda: manager._set_replacement_order(bad), lambda: GameEngine._set_replacement_order(adapter, bad)):  # type: ignore[arg-type]
            with self.assertRaises(IllegalAction): call()
        self.assertEqual(self._fingerprint(direct), before_direct)
        self.assertEqual(self._fingerprint(facade), before_facade)
        for call in (lambda: manager._move_card("c", Zone.REVEAL, "missing", allow_replacement=False), lambda: GameEngine._move_card(adapter, "c", Zone.REVEAL, "missing", allow_replacement=False)):  # type: ignore[arg-type]
            with self.assertRaises(ValueError): call()
        self.assertEqual(self._fingerprint(direct), before_direct)
        self.assertEqual(self._fingerprint(facade), before_facade)

    def test_minimal_context_structurally_satisfies_zone_context(self) -> None:
        context: ZoneContext = MinimalZoneContext()
        self.assertIsInstance(ZoneManager(context), ZoneManager)


if __name__ == "__main__":
    unittest.main()
