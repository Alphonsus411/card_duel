import unittest
from copy import deepcopy
from typing import NoReturn

from card_duel_engine import GameEngine
from card_duel_engine.domain.enums import CardKind, Phase, Zone
from card_duel_engine.domain.errors import IllegalAction
from card_duel_engine.domain.models import CardDefinition, GameState, MoveReplacementDefinition
from card_duel_engine.engine.combat import CombatManager
from card_duel_engine.engine.commands import (
    DeclareAttackers,
    DeclareBlockers,
    DeclareChallenge,
    ResolveCombat,
)
from card_duel_engine.rules.config import RuleSet

from fixtures import test_deck


class MinimalCombatContext:
    """Adaptador que expone al combate solo su contrato estructural."""

    def __init__(self, engine: GameEngine, *, fail_on_emit: bool = False) -> None:
        self.engine = engine
        self.fail_on_emit = fail_on_emit

    def _require_running_state(self) -> GameState:
        return self.engine._require_running_state()

    def _is_ready_creature(self, card_id: str) -> bool:
        return self.engine._is_ready_creature(card_id)

    def _is_lord_creature(self, card_id: str) -> bool:
        return self.engine._is_lord_creature(card_id)

    def _is_creature(self, card_id: str) -> bool:
        return self.engine._is_creature(card_id)

    @property
    def _combat_action_enumeration_limit(self) -> int:
        return self.engine.rules.legal_action_enumeration_limit

    def _current_strength(self, card_id: str) -> int:
        return self.engine._current_strength(card_id)

    def _deal_damage(
        self, card_id: str, amount: int, source_card_id: str | None = None
    ) -> None:
        self.engine._deal_damage(card_id, amount, source_card_id)

    def _deal_wounds(
        self, player_id: str, amount: int, source_card_id: str | None = None
    ) -> None:
        self.engine._deal_wounds(player_id, amount, source_card_id)

    def _run_state_based_actions(self) -> None:
        self.engine._run_state_based_actions()

    def _emit(
        self,
        event_type: str,
        player_id: str | None = None,
        card_id: str | None = None,
        payload: dict[str, object] | None = None,
    ) -> None:
        if self.fail_on_emit:
            raise RuntimeError("fallo inyectado después de mutar el combate")
        self.engine._emit(event_type, player_id, card_id, payload)


class CombatParityR071Tests(unittest.TestCase):
    _COMBAT_COMMANDS = (
        DeclareAttackers,
        DeclareBlockers,
        DeclareChallenge,
        ResolveCombat,
    )

    def _prepared_engine(self) -> tuple[GameEngine, str]:
        engine = GameEngine()
        engine.new_match({"A": test_deck("A"), "B": test_deck("B")}, seed=71)
        # Activa el snapshot transaccional del camino público sin intervenir en
        # el combate que se prueba.
        engine.catalog.register(
            CardDefinition(
                card_id="ATOMICITY-SENTINEL",
                name="Centinela de atomicidad",
                kind=CardKind.EVENT,
                cost=0,
                move_replacements=(
                    MoveReplacementDefinition(Zone.HAND),
                    MoveReplacementDefinition(Zone.EXILE),
                ),
                deferred_replacement_choice=True,
            )
        )
        state = engine._require_state()
        attacker = state.players["A"].zones[Zone.HAND][0]
        engine._move_card(attacker, Zone.BATTLEFIELD, "A")
        state.phase = Phase.COMBAT
        state.phase_priority_complete = True
        return engine, attacker

    @staticmethod
    def _fingerprint(engine: GameEngine) -> tuple[object, ...]:
        state = engine._require_state()
        return (
            deepcopy(state),
            tuple(deepcopy(state.event_log)),
            tuple(deepcopy(state.command_history)),
            engine._next_instance,
            engine._next_stack_item,
        )

    @staticmethod
    def _raise_after_mutation(
        event_type: str,
        player_id: str | None = None,
        card_id: str | None = None,
        payload: dict[str, object] | None = None,
    ) -> NoReturn:
        raise RuntimeError("fallo inyectado después de mutar el combate")

    def _run_public_pair(
        self,
        *,
        illegal: bool = False,
        fail_on_emit: bool = False,
    ) -> tuple[GameEngine, GameEngine, tuple[object, ...], tuple[object, ...]]:
        regular, regular_attacker = self._prepared_engine()
        minimal, minimal_attacker = self._prepared_engine()
        minimal._combat = CombatManager(
            MinimalCombatContext(minimal, fail_on_emit=fail_on_emit)
        )
        if fail_on_emit:
            regular._emit = self._raise_after_mutation  # type: ignore[method-assign]

        regular_before = self._fingerprint(regular)
        minimal_before = self._fingerprint(minimal)
        regular_command = DeclareAttackers(
            "A", () if illegal else (regular_attacker,), "B"
        )
        minimal_command = DeclareAttackers(
            "A", () if illegal else (minimal_attacker,), "B"
        )
        error = RuntimeError if fail_on_emit else IllegalAction if illegal else None

        for engine, command in (
            (regular, regular_command),
            (minimal, minimal_command),
        ):
            if error is None:
                engine.execute(command)
            else:
                with self.assertRaises(error):
                    engine.execute(command)

        self.assertEqual(self._fingerprint(regular), self._fingerprint(minimal))
        return regular, minimal, regular_before, minimal_before

    def test_public_path_matches_minimal_context_on_success(self) -> None:
        regular, minimal, _, _ = self._run_public_pair()
        regular_state = regular._require_state()
        minimal_state = minimal._require_state()

        self.assertEqual(regular_state.event_log[-1].event_type, "ATTACKERS_DECLARED")
        self.assertEqual(regular_state.command_history, minimal_state.command_history)

    def test_public_path_matches_minimal_context_on_illegal_command(self) -> None:
        regular, minimal, regular_before, minimal_before = self._run_public_pair(
            illegal=True
        )

        self.assertEqual(self._fingerprint(regular), regular_before)
        self.assertEqual(self._fingerprint(minimal), minimal_before)

    def test_public_path_matches_minimal_context_on_exception_without_partial_mutation(
        self,
    ) -> None:
        regular, minimal, regular_before, minimal_before = self._run_public_pair(
            fail_on_emit=True
        )

        self.assertEqual(self._fingerprint(regular), regular_before)
        self.assertEqual(self._fingerprint(minimal), minimal_before)

    def test_public_enumeration_matches_direct_manager_for_two_players(self) -> None:
        engine, _ = self._prepared_engine()
        before = self._fingerprint(engine)

        public = tuple(
            action
            for action in engine.legal_actions("A")
            if isinstance(action, self._COMBAT_COMMANDS)
        )
        direct = engine._combat.legal_actions("A")

        self.assertEqual(public, direct)
        self.assertEqual(self._fingerprint(engine), before)

    def test_public_enumeration_matches_direct_manager_for_multiple_players(self) -> None:
        engine = GameEngine()
        engine.new_match(
            {player: test_deck(player) for player in ("A", "B", "C")}, seed=72
        )
        state = engine._require_state()
        for player_id in state.turn_order:
            card_id = state.players[player_id].zones[Zone.HAND][0]
            engine._move_card(card_id, Zone.BATTLEFIELD, player_id)
        state.phase = Phase.COMBAT
        state.phase_priority_complete = True
        before = self._fingerprint(engine)

        public = tuple(
            action
            for action in engine.legal_actions(state.active_player_id)
            if isinstance(action, self._COMBAT_COMMANDS)
        )
        direct = engine._combat.legal_actions(state.active_player_id)

        self.assertEqual(public, direct)
        self.assertEqual(
            [action.defending_player_id for action in direct if isinstance(action, DeclareAttackers)],
            [player for player in state.turn_order if player != state.active_player_id],
        )
        self.assertEqual(self._fingerprint(engine), before)

    def test_limit_preserves_order_and_does_not_restrict_authoritative_command(self) -> None:
        engine = GameEngine(RuleSet(legal_action_enumeration_limit=1))
        engine.new_match({"A": test_deck("A"), "B": test_deck("B")}, seed=73)
        state = engine._require_state()
        attackers = tuple(state.players["A"].zones[Zone.HAND][:2])
        for card_id in attackers:
            engine._move_card(card_id, Zone.BATTLEFIELD, "A")
        state.phase = Phase.COMBAT
        state.phase_priority_complete = True

        direct = engine._combat.legal_actions("A")
        public = tuple(
            action
            for action in engine.legal_actions("A")
            if isinstance(action, self._COMBAT_COMMANDS)
        )
        self.assertEqual(public, direct)
        declarations = tuple(
            action for action in direct if isinstance(action, DeclareAttackers)
        )
        self.assertEqual(len(declarations), 1)

        explicit = DeclareAttackers("A", attackers, "B")
        self.assertNotIn(explicit, declarations)
        engine.execute(explicit)
        self.assertEqual(state.combat.attackers, attackers)


if __name__ == "__main__":
    unittest.main()
