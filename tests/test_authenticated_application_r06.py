import json
import tempfile
import unittest
from pathlib import Path

from card_duel_engine import (
    AccessDenied,
    AuthenticatedMatchApplication,
    AuthenticationRequired,
    Capability,
    CommandRejected,
    ExternalIdentity,
    InMemoryIdentityAuthorization,
    InMemoryMatchStore,
    InvalidIdentity,
    MatchService,
    ResourceNotFound,
    SQLiteMatchStore,
    WriteConflict,
)
from card_duel_engine.domain.enums import Zone
from card_duel_engine.domain.models import GameState
from card_duel_engine.engine.game import GameEngine
from card_duel_engine.engine.commands import PassPriority
from card_duel_engine.persistence.snapshot import state_digest
from fixtures import test_deck


class AuthenticatedApplicationR06Tests(unittest.TestCase):
    def setUp(self):
        self.store = InMemoryMatchStore()
        self.service = MatchService(self.store)
        self.auth = InMemoryIdentityAuthorization()
        self.app = AuthenticatedMatchApplication(self.service, self.auth)
        self.creator = ExternalIdentity("https://issuer.example", "operator")
        self.alice = ExternalIdentity("https://issuer.example", "alice")
        self.bob = ExternalIdentity("https://issuer.example", "bob")
        self.auth.grant_global(self.creator, Capability.CREATE_MATCH)
        self.service.create_match(
            "one", {"A": test_deck("A"), "B": test_deck("B")}, seed=8
        )
        self.service.create_match(
            "two", {"A": test_deck("A2"), "B": test_deck("B2")}, seed=9
        )
        self.auth.bind_player(self.alice, "one", "A")
        self.auth.bind_player(self.bob, "one", "B")

    def fingerprint(self, match_id="one"):
        stored = self.service.get_match(match_id)
        return stored.version, state_digest(stored.engine)

    def assert_rejected_without_mutation(self, error, operation, match_id="one"):
        before = self.fingerprint(match_id)
        with self.assertRaises(error):
            operation()
        self.assertEqual(self.fingerprint(match_id), before)

    def test_missing_identity_is_rejected_without_mutation(self):
        self.assert_rejected_without_mutation(
            AuthenticationRequired, lambda: self.app.view(None, "one")
        )

    def test_invalid_identity_is_rejected_without_mutation(self):
        invalid = ExternalIdentity("https://issuer.example", "alice", authenticated=False)
        self.assert_rejected_without_mutation(
            InvalidIdentity, lambda: self.app.view(invalid, "one")
        )

    def test_cross_player_observation_is_not_selectable(self):
        view = self.app.view(self.alice, "one")
        self.assertEqual(view.observation.player_id, "A")
        self.assertNotIn("player_id", AuthenticatedMatchApplication.view.__annotations__)

    def test_access_to_another_match_is_rejected_without_mutation(self):
        self.assert_rejected_without_mutation(
            AccessDenied, lambda: self.app.view(self.alice, "two"), "two"
        )

    def test_command_attributed_to_another_player_is_rejected_without_mutation(self):
        self.assert_rejected_without_mutation(
            AccessDenied,
            lambda: self.app.submit(
                self.alice, "one", PassPriority("B"), expected_version=1
            ),
        )

    def test_stale_version_is_translated_without_mutation(self):
        view = self.app.view(self.alice, "one")
        command = self.service.view("one", "A").legal_actions[0]
        self.app.submit(
            self.alice, "one", command, expected_version=view.version
        )
        self.assert_rejected_without_mutation(
            WriteConflict,
            lambda: self.app.submit(
                self.alice, "one", command, expected_version=view.version
            ),
        )

    def test_public_dto_serialization_recursively_excludes_internal_state(self):
        response = self.app.view(self.alice, "one")
        payload = response.to_dict()
        encoded = json.dumps(payload)

        forbidden_keys = {
            "engine", "state", "snapshot", "deck", "opponent_hand",
            "chosen_card_ids", "discard_card_ids", "sacrifice_card_ids",
        }

        def inspect(value):
            self.assertNotIsInstance(value, (GameEngine, GameState))
            if isinstance(value, dict):
                self.assertTrue(forbidden_keys.isdisjoint(value))
                for nested in value.values():
                    inspect(nested)
            elif isinstance(value, (list, tuple)):
                for nested in value:
                    inspect(nested)

        inspect(payload)
        stored = self.service.get_match("one")
        opponent_hidden = {
            *stored.engine.state.players["B"].zones[Zone.HAND],
            *stored.engine.state.players["B"].zones[Zone.DECK],
        }
        self.assertTrue(opponent_hidden)
        self.assertTrue(all(card_id not in encoded for card_id in opponent_hidden))

    def test_each_identity_receives_only_its_own_private_observation(self):
        alice_view = self.app.view(self.alice, "one")
        bob_view = self.app.view(self.bob, "one")
        stored = self.service.get_match("one")
        alice_hand = tuple(stored.engine.state.players["A"].zones[Zone.HAND])
        bob_hand = tuple(stored.engine.state.players["B"].zones[Zone.HAND])

        self.assertEqual(alice_view.observation.own_hand, alice_hand)
        self.assertEqual(bob_view.observation.own_hand, bob_hand)
        self.assertTrue(set(alice_hand).isdisjoint(bob_view.observation.own_hand))
        self.assertTrue(set(bob_hand).isdisjoint(alice_view.observation.own_hand))
        self.assertEqual(alice_view.observation.opponent_hand_sizes, {"B": len(bob_hand)})
        self.assertEqual(bob_view.observation.opponent_hand_sizes, {"A": len(alice_hand)})

    def test_illegal_action_is_safe_and_does_not_mutate(self):
        self.assert_rejected_without_mutation(
            CommandRejected,
            lambda: self.app.submit(
                self.bob, "one", PassPriority("B"), expected_version=1
            ),
        )

    def test_not_found_is_translated_without_internal_identifier(self):
        self.auth.bind_player(self.alice, "missing", "A")
        with self.assertRaises(ResourceNotFound) as caught:
            self.app.view(self.alice, "missing")
        self.assertEqual(caught.exception.args, ("El recurso solicitado no existe",))

    def test_creation_observation_submission_and_admin_are_separate(self):
        decks = {"A": test_deck("C"), "B": test_deck("D")}
        self.assert_rejected_without_mutation(
            AccessDenied, lambda: self.app.create_match(self.alice, "new", decks)
        )
        self.assertEqual(self.app.create_match(self.creator, "new", decks), 1)
        with self.assertRaises(AccessDenied):
            self.app.administrative_version(self.creator, "new")
        self.auth.grant_match(self.creator, "new", Capability.ADMINISTER)
        self.assertEqual(self.app.administrative_version(self.creator, "new"), 1)
        with self.assertRaises(AccessDenied):
            self.app.view(self.creator, "new")


class MatchStoreParityR06Tests(unittest.TestCase):
    def test_memory_and_sqlite_preserve_identical_cas_rejections(self):
        with tempfile.TemporaryDirectory() as directory:
            stores = (
                InMemoryMatchStore(),
                SQLiteMatchStore(Path(directory) / "parity.db"),
            )
            outcomes = []
            for index, store in enumerate(stores):
                service = MatchService(store)
                match_id = f"parity-{index}"
                service.create_match(
                    match_id, {"A": test_deck("PA"), "B": test_deck("PB")}, seed=12
                )
                initial = service.get_match(match_id)
                view = service.view(match_id, "A")
                updated = service.submit(
                    match_id, view.legal_actions[0], expected_version=view.version
                )
                digest = state_digest(service.get_match(match_id).engine)
                with self.assertRaises(WriteConflict):
                    app = AuthenticatedMatchApplication(service, InMemoryIdentityAuthorization())
                    identity = ExternalIdentity("issuer", "subject")
                    app._authorization.bind_player(identity, match_id, "A")
                    app.submit(identity, match_id, view.legal_actions[0], expected_version=1)
                final = service.get_match(match_id)
                outcomes.append((initial.version, updated.version, final.version, digest == state_digest(final.engine)))
                if isinstance(store, SQLiteMatchStore):
                    store.close()
            self.assertEqual(outcomes, [(1, 2, 2, True), (1, 2, 2, True)])


if __name__ == "__main__":
    unittest.main()
