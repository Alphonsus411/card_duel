from __future__ import annotations

import pickle
import unittest
from decimal import Decimal
from unittest.mock import patch

from card_duel_engine import (
    CardCatalog,
    DeckConstructionPolicy,
    InMemoryMatchStore,
    MatchService,
    classic_deck_policy,
    mythic_deck_policy,
)
from card_duel_engine.domain.enums import CardKind, CardRank
from card_duel_engine.domain.models import CardDefinition
from card_duel_engine.service import DeckValidationFailure
from card_duel_engine.storage import MatchNotFound


def set_id_starts_with_season(set_id: str) -> bool:
    return set_id.startswith("season-")


def card(card_id: str, *, cost: int = 5, rank: CardRank = CardRank.STANDARD, set_id: str = "new") -> CardDefinition:
    return CardDefinition(card_id, card_id, CardKind.EVENT, cost, rank=rank, set_id=set_id)


def legal_cards(size: int, *, set_id: str = "new") -> list[CardDefinition]:
    return [card(f"c-{index // 5}", set_id=set_id) for index in range(size)]


class DeckConstructionPolicyTests(unittest.TestCase):
    def test_equivalent_mythic_policies_have_equal_hashes_and_pickle_roundtrip(self):
        first = mythic_deck_policy()
        second = mythic_deck_policy()

        self.assertEqual(first, second)
        self.assertEqual(hash(first), hash(second))
        self.assertEqual(pickle.loads(pickle.dumps(first)), first)

    def test_isolated_and_explicitly_empty_mythic_classifiers_are_distinct(self):
        isolated = mythic_deck_policy()
        empty = mythic_deck_policy(mythic_set_ids=())

        self.assertNotEqual(isolated, empty)
        self.assertFalse(empty._is_mythic("any-set"))
        self.assertTrue(isolated._is_mythic("any-set"))
        self.assertEqual(pickle.loads(pickle.dumps(empty)), empty)

    def test_nonempty_mythic_ids_are_the_authority_without_a_predicate(self):
        first = mythic_deck_policy(mythic_set_ids={"myth"})
        second = mythic_deck_policy(mythic_set_ids={"myth"})

        self.assertIsNone(first.mythic_set_predicate)
        self.assertEqual(first, second)
        self.assertEqual(hash(first), hash(second))

    def test_custom_predicate_preserves_normal_callable_equality(self):
        same_callable = mythic_deck_policy(
            mythic_set_predicate=set_id_starts_with_season
        )
        same_callable_again = mythic_deck_policy(
            mythic_set_predicate=set_id_starts_with_season
        )
        different_callable = mythic_deck_policy(
            mythic_set_predicate=lambda set_id: set_id.startswith("season-")
        )

        self.assertEqual(same_callable, same_callable_again)
        self.assertEqual(hash(same_callable), hash(same_callable_again))
        self.assertNotEqual(same_callable, different_callable)
        self.assertEqual(
            pickle.loads(pickle.dumps(same_callable)), same_callable
        )

    def test_all_numeric_limits_require_exact_int(self):
        fields = (
            "min_cards", "max_cards", "max_standard_copies",
            "max_legendary_copies", "max_zero_cost_copies",
            "max_zero_cost_total", "mythic_min_cost", "mythic_max_cost",
            "point_budget",
        )

        class IntLike:
            def __int__(self):
                return 1

        invalid_values = (
            True, 1.0, "1", [1], (1,), {1}, {"value": 1},
            Decimal("1"), IntLike(),
        )
        for field in fields:
            for value in invalid_values:
                with self.subTest(field=field, value_type=type(value).__name__):
                    with self.assertRaises(TypeError):
                        DeckConstructionPolicy(**{field: value})

    def test_numeric_relationships_and_nonnegative_limits_are_preserved(self):
        for arguments in (
            {"min_cards": -1},
            {"min_cards": 2, "max_cards": 1},
            {"mythic_min_cost": 6, "mythic_max_cost": 5,
             "mythic_set_ids": {"myth"}},
        ):
            with self.subTest(arguments=arguments):
                with self.assertRaises(ValueError):
                    DeckConstructionPolicy(**arguments)

    def test_collection_ids_and_predicates_are_strictly_validated(self):
        for field in ("allowed_set_ids", "mythic_set_ids"):
            for ids in (("",), (1,), (None,), ("ok", False)):
                with self.subTest(field=field, ids=ids):
                    with self.assertRaises(TypeError):
                        DeckConstructionPolicy(**{field: ids})
        for field in ("set_predicate", "mythic_set_predicate"):
            for value in (False, 1, "callable", []):
                with self.subTest(field=field, value=value):
                    with self.assertRaises(TypeError):
                        DeckConstructionPolicy(**{field: value})

    def test_collection_generators_are_consumed_once(self):
        iterations = {"allowed": 0, "mythic": 0}

        def ids(kind, values):
            iterations[kind] += 1
            if iterations[kind] > 1:
                raise AssertionError("segunda iteración")
            yield from values

        policy = DeckConstructionPolicy(
            allowed_set_ids=ids("allowed", ("base", "myth")),
            mythic_set_ids=ids("mythic", ("myth",)),
            mythic_min_cost=5,
            mythic_max_cost=50,
        )
        self.assertEqual(iterations, {"allowed": 1, "mythic": 1})
        self.assertEqual(policy.allowed_set_ids, frozenset({"base", "myth"}))
        self.assertEqual(policy.mythic_set_ids, frozenset({"myth"}))

    def test_explicit_mythic_sets_must_be_allowed(self):
        with self.assertRaisesRegex(ValueError, "Míticas.*permitidas"):
            mythic_deck_policy(
                allowed_set_ids={"current"}, mythic_set_ids={"future"}
            )

    def test_general_collection_filter_requires_explicit_mythic_classifier(self):
        for arguments in (
            {"allowed_set_ids": (value for value in ("current",))},
            {"set_predicate": lambda _set_id: True},
        ):
            with self.subTest(filter=next(iter(arguments))):
                with self.assertRaisesRegex(ValueError, "configuración de colecciones"):
                    mythic_deck_policy(**arguments)

    def test_mythic_ids_must_satisfy_general_predicate(self):
        with self.assertRaisesRegex(ValueError, "configuración de colecciones"):
            mythic_deck_policy(
                set_predicate=lambda set_id: set_id == "current",
                mythic_set_ids=(set_id for set_id in ("private-mythic",)),
            )

    def test_factory_materializes_id_generators_once_and_future_sets_are_not_mythic(self):
        iterations = {"allowed": 0, "mythic": 0}

        def one_shot(kind, values):
            iterations[kind] += 1
            if iterations[kind] > 1:
                raise AssertionError("segunda iteración")
            yield from values

        policy = mythic_deck_policy(
            allowed_set_ids=one_shot("allowed", ("myth", "future")),
            mythic_set_ids=one_shot("mythic", ("myth",)),
        )
        self.assertEqual(iterations, {"allowed": 1, "mythic": 1})
        for cost in (4, 60):
            with self.subTest(cost=cost):
                future_deck = legal_cards(39, set_id="future") + [
                    card("future-edge", cost=cost, set_id="future")
                ]
                mythic_deck = legal_cards(39, set_id="future") + [
                    card("mythic-edge", cost=cost, set_id="myth")
                ]
                self.assertTrue(policy.validate(future_deck).is_valid)
                self.assertFalse(policy.validate(mythic_deck).is_valid)

    def test_general_predicate_accepts_explicit_mythic_ids(self):
        policy = mythic_deck_policy(
            set_predicate=lambda set_id: set_id in {"myth", "future"},
            mythic_set_ids=(set_id for set_id in ("myth",)),
        )
        self.assertTrue(policy.validate(legal_cards(40, set_id="future")).is_valid)

    def test_mythic_factory_rejects_non_callable_predicates_first(self):
        for field in ("set_predicate", "mythic_set_predicate"):
            with self.subTest(field=field):
                with self.assertRaisesRegex(TypeError, "invocable") as caught:
                    mythic_deck_policy(**{field: "private predicate"})
                self.assertNotIn("private predicate", str(caught.exception))

    def test_mythic_limits_require_an_applicable_classifier(self):
        with self.assertRaisesRegex(ValueError, "clasificación aplicable"):
            DeckConstructionPolicy(mythic_min_cost=5, mythic_max_cost=50)

    def test_mythic_size_boundaries(self):
        policy = mythic_deck_policy(
            allowed_set_ids=frozenset({"new"}), mythic_set_ids=frozenset({"new"})
        )
        for size, valid in ((39, False), (40, True), (60, True), (61, False)):
            with self.subTest(size=size):
                self.assertEqual(policy.validate(legal_cards(size)).is_valid, valid)

    def test_mythic_copy_limits_use_canonical_rank(self):
        policy = mythic_deck_policy()
        base = legal_cards(40)
        for repeated, valid in (
            ([card("ordinary")] * 5, True),
            ([card("ordinary")] * 6, False),
            ([card("legend", rank=CardRank.LEGENDARY)] * 4, True),
            ([card("legend", rank=CardRank.LEGENDARY)] * 5, False),
        ):
            with self.subTest(copies=len(repeated), rank=repeated[0].rank):
                deck = repeated + base[len(repeated):]
                self.assertEqual(policy.validate(deck).is_valid, valid)

    def test_mythic_zero_and_identified_mythic_cost_interval(self):
        policy = mythic_deck_policy(mythic_set_ids=frozenset({"myth"}))
        for cost, set_id, valid in ((0, "old", False), (4, "myth", False), (5, "myth", True), (50, "myth", True), (60, "myth", False), (4, "old", True), (60, "old", True)):
            with self.subTest(cost=cost, set_id=set_id):
                deck = legal_cards(39) + [card("edge", cost=cost, set_id=set_id)]
                self.assertEqual(policy.validate(deck).is_valid, valid)

    def test_isolated_mythic_profile_applies_cost_interval_to_every_card(self):
        policy = mythic_deck_policy()
        for cost, valid in ((4, False), (5, True), (50, True), (60, False)):
            with self.subTest(cost=cost):
                deck = legal_cards(39) + [card("edge", cost=cost)]
                self.assertEqual(policy.validate(deck).is_valid, valid)

    def test_set_allowlist_and_predicate_are_injected(self):
        allowed = mythic_deck_policy(
            allowed_set_ids=frozenset({"new"}), mythic_set_ids=frozenset({"new"})
        )
        predicate = mythic_deck_policy(
            set_predicate=lambda value: value.startswith("season-"),
            mythic_set_predicate=lambda value: value == "season-mythic",
        )
        self.assertTrue(allowed.validate(legal_cards(40, set_id="new")).is_valid)
        self.assertFalse(allowed.validate(legal_cards(40, set_id="old")).is_valid)
        self.assertTrue(predicate.validate(legal_cards(40, set_id="season-7")).is_valid)

    def test_classic_old_sets_require_explicit_authorization(self):
        closed = classic_deck_policy(allowed_set_ids=frozenset({"current"}))
        open_old = classic_deck_policy(allowed_set_ids=frozenset({"current", "old"}))
        old_deck = legal_cards(40, set_id="old")
        self.assertFalse(closed.validate(old_deck).is_valid)
        self.assertTrue(open_old.validate(old_deck).is_valid)

    def test_classic_zero_cost_limits(self):
        policy = classic_deck_policy()
        base = legal_cards(34)
        distinct_six = base + [card(f"z-{index}", cost=0) for index in range(6)]
        self.assertTrue(policy.validate(distinct_six).is_valid)
        self.assertFalse(policy.validate(distinct_six + [card("seventh", cost=0)]).is_valid)
        self.assertFalse(policy.validate(base + [card("same", cost=0), card("same", cost=0)] + legal_cards(4)).is_valid)

    def test_classic_exact_general_size_and_copy_limits(self):
        policy = classic_deck_policy()
        for size, valid in ((39, False), (40, True), (60, True), (61, False)):
            with self.subTest(size=size):
                self.assertEqual(policy.validate(legal_cards(size)).is_valid, valid)
        base = legal_cards(40)
        for repeated, valid in (
            ([card("ordinary")] * 5, True),
            ([card("ordinary")] * 6, False),
            ([card("legend", rank=CardRank.LEGENDARY)] * 4, True),
            ([card("legend", rank=CardRank.LEGENDARY)] * 5, False),
        ):
            deck = repeated + base[len(repeated):]
            self.assertEqual(policy.validate(deck).is_valid, valid)

    def test_factories_have_no_default_points_budget_n_points_01(self):
        self.assertIsNone(mythic_deck_policy().point_budget)
        self.assertIsNone(classic_deck_policy().point_budget)
        self.assertFalse(classic_deck_policy(point_budget=4).validate(legal_cards(40)).is_valid)

    def test_one_shot_generator_is_materialized_once_and_returned(self):
        iterations = 0
        source = legal_cards(40)

        def one_shot():
            nonlocal iterations
            iterations += 1
            if iterations > 1:
                raise AssertionError("segunda iteración")
            yield from source

        result = mythic_deck_policy().validate(one_shot())
        self.assertEqual(iterations, 1)
        self.assertEqual(result.cards, tuple(source))

    def test_issue_order_is_deterministic(self):
        policy = mythic_deck_policy(
            set_predicate=lambda set_id: set_id == "new",
            mythic_set_predicate=lambda set_id: set_id == "bad",
        )
        deck = [card("z", cost=0, set_id="bad")] * 6
        first = policy.validate(deck).issues
        second = policy.validate(iter(deck)).issues
        self.assertEqual(first, second)
        self.assertEqual([issue.code for issue in first], ["deck.too_small", "copies.exceeded", "set.not_allowed", "cost.zero_forbidden", "mythic.cost_range"])

    def test_invalid_policy_configuration_prevents_game_engine_construction(self):
        with patch("card_duel_engine.engine.game.GameEngine") as engine_class:
            with self.assertRaises(ValueError):
                policy = mythic_deck_policy(allowed_set_ids={"current"})
                engine_class(deck_policy=policy)
        engine_class.assert_not_called()

    def test_service_rejection_happens_before_engine_or_catalog_mutation(self):
        catalog = CardCatalog()
        store = InMemoryMatchStore()
        calls = 0

        def factory():
            nonlocal calls
            calls += 1
            raise AssertionError("no debe construirse el motor")

        service = MatchService(store, engine_factory=factory, deck_policy=mythic_deck_policy())
        before = catalog.definitions()
        with self.assertRaises(DeckValidationFailure) as caught:
            service.create_match("rejected", {"A": legal_cards(39), "B": legal_cards(40)})
        self.assertEqual(calls, 0)
        self.assertEqual(catalog.definitions(), before)
        self.assertIsNone(caught.exception.__cause__)
        self.assertEqual(str(caught.exception), "")
        with self.assertRaises(MatchNotFound):
            store.load("rejected")


if __name__ == "__main__":
    unittest.main()
