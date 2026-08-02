from __future__ import annotations

import unittest

from card_duel_engine import (
    CardCatalog,
    InMemoryMatchStore,
    MatchService,
    classic_deck_policy,
    mythic_deck_policy,
)
from card_duel_engine.domain.enums import CardKind, CardRank
from card_duel_engine.domain.models import CardDefinition
from card_duel_engine.service import DeckValidationFailure


def card(card_id: str, *, cost: int = 5, rank: CardRank = CardRank.STANDARD, set_id: str = "new") -> CardDefinition:
    return CardDefinition(card_id, card_id, CardKind.EVENT, cost, rank=rank, set_id=set_id)


def legal_cards(size: int, *, set_id: str = "new") -> list[CardDefinition]:
    return [card(f"c-{index // 5}", set_id=set_id) for index in range(size)]


class DeckConstructionPolicyTests(unittest.TestCase):
    def test_mythic_size_boundaries(self):
        policy = mythic_deck_policy(allowed_set_ids=frozenset({"new"}))
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
        for cost, set_id, valid in ((0, "old", False), (4, "myth", False), (5, "myth", True), (50, "myth", True), (51, "myth", False), (4, "old", True)):
            with self.subTest(cost=cost, set_id=set_id):
                deck = legal_cards(39) + [card("edge", cost=cost, set_id=set_id)]
                self.assertEqual(policy.validate(deck).is_valid, valid)

    def test_set_allowlist_and_predicate_are_injected(self):
        allowed = mythic_deck_policy(allowed_set_ids=frozenset({"new"}))
        predicate = mythic_deck_policy(set_predicate=lambda value: value.startswith("season-"))
        self.assertTrue(allowed.validate(legal_cards(40, set_id="new")).is_valid)
        self.assertFalse(allowed.validate(legal_cards(40, set_id="old")).is_valid)
        self.assertTrue(predicate.validate(legal_cards(40, set_id="season-7")).is_valid)

    def test_classic_old_sets_require_explicit_authorization(self):
        closed = classic_deck_policy(allowed_set_ids=frozenset({"current"}))
        open_old = classic_deck_policy(allowed_set_ids=frozenset({"current", "old"}))
        self.assertFalse(closed.validate([card("x", set_id="old")]).is_valid)
        self.assertTrue(open_old.validate([card("x", set_id="old")]).is_valid)

    def test_classic_zero_cost_limits(self):
        policy = classic_deck_policy()
        distinct_six = [card(f"z-{index}", cost=0) for index in range(6)]
        self.assertTrue(policy.validate(distinct_six).is_valid)
        self.assertFalse(policy.validate(distinct_six + [card("seventh", cost=0)]).is_valid)
        self.assertFalse(policy.validate([card("same", cost=0), card("same", cost=0)]).is_valid)

    def test_classic_general_copy_limits_are_only_opt_in(self):
        repeated = [card("same")] * 9
        self.assertTrue(classic_deck_policy().validate(repeated).is_valid)
        self.assertFalse(classic_deck_policy(max_standard_copies=8).validate(repeated).is_valid)

    def test_factories_have_no_default_points_budget_n_points_01(self):
        self.assertIsNone(mythic_deck_policy().point_budget)
        self.assertIsNone(classic_deck_policy().point_budget)
        self.assertFalse(classic_deck_policy(point_budget=4).validate([card("x", cost=5)]).is_valid)

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
        policy = mythic_deck_policy(allowed_set_ids=frozenset({"new"}), mythic_set_ids=frozenset({"bad"}))
        deck = [card("z", cost=0, set_id="bad")] * 6
        first = policy.validate(deck).issues
        second = policy.validate(iter(deck)).issues
        self.assertEqual(first, second)
        self.assertEqual([issue.code for issue in first], ["deck.too_small", "copies.exceeded", "set.not_allowed", "cost.zero_forbidden", "mythic.cost_range"])

    def test_service_rejection_happens_before_engine_or_catalog_mutation(self):
        catalog = CardCatalog()
        calls = 0

        def factory():
            nonlocal calls
            calls += 1
            raise AssertionError("no debe construirse el motor")

        service = MatchService(InMemoryMatchStore(), engine_factory=factory, deck_policy=mythic_deck_policy())
        before = catalog.definitions()
        with self.assertRaises(DeckValidationFailure):
            service.create_match("rejected", {"A": legal_cards(39), "B": legal_cards(40)})
        self.assertEqual(calls, 0)
        self.assertEqual(catalog.definitions(), before)


if __name__ == "__main__":
    unittest.main()
