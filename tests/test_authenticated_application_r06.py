"""Pruebas de contrato del adaptador de aplicación autenticado de R-06.

Estas pruebas viven deliberadamente fuera de ``test_service_v0110.py``: la
autorización es responsabilidad de la frontera de aplicación, no del motor ni
del servicio interno.
"""

import inspect
import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from card_duel_engine import (
    AccessDenied,
    AuthenticatedMatchApplication,
    AuthenticationRequired,
    CardCatalog,
    CommandRejected,
    ExternalIdentity,
    InMemoryIdentityAuthorization,
    InMemoryMatchStore,
    InternalLoadFailure,
    InvalidDeck,
    InvalidIdentity,
    InvalidMatchId,
    MalformedCommand,
    MatchService,
    OptionRejected,
    ResourceNotFound,
    SQLiteMatchStore,
    WriteConflict,
)
from card_duel_engine.application import Capability, PublicMatchView
from card_duel_engine.domain.enums import Zone
from card_duel_engine.domain.models import GameState
from card_duel_engine.engine.commands import Concede, PassPriority
from card_duel_engine.engine.game import GameEngine
from card_duel_engine.persistence.snapshot import state_digest
from card_duel_engine.storage import MatchNotFound
from fixtures import test_deck


class AuthenticatedApplicationR06Contract:
    """Batería común ejecutada sin cambios sobre ambos almacenes CAS."""

    store_kind = ""

    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        if self.store_kind == "memory":
            self.store = InMemoryMatchStore()
        elif self.store_kind == "sqlite":
            path = Path(self.temporary_directory.name) / "r06.db"
            self.store = SQLiteMatchStore(path)
            self.addCleanup(self.store.close)
        else:  # pragma: no cover - protege nuevas subclases mal configuradas
            raise AssertionError("La batería R-06 necesita un almacén")

        self.catalog = CardCatalog()
        self.service = MatchService(self.store, catalog=self.catalog)
        self.authorization = InMemoryIdentityAuthorization()
        self.app = AuthenticatedMatchApplication(self.service, self.authorization)
        self.identities = {
            "alice": ExternalIdentity("https://issuer.example", "alice"),
            "bob": ExternalIdentity("https://issuer.example", "bob"),
            "carol": ExternalIdentity("https://issuer.example", "carol"),
            "dave": ExternalIdentity("https://issuer.example", "dave"),
        }
        # Fixture mínima exigida: dos partidas y dos participantes distintos en
        # cada una. Las asociaciones tampoco se comparten entre partidas.
        for index, match_id in enumerate(("one", "two"), start=1):
            self.service.create_match(
                match_id,
                {
                    "A": test_deck(f"{match_id}-A"),
                    "B": test_deck(f"{match_id}-B"),
                },
                seed=index,
            )
        for identity, match_id, player_id in (
            ("alice", "one", "A"),
            ("bob", "one", "B"),
            ("carol", "two", "A"),
            ("dave", "two", "B"),
        ):
            self.authorization.bind_player(
                self.identities[identity], match_id, player_id
            )

    def fingerprint(self, match_id):
        stored = self.service.get_match(match_id)
        return stored.version, state_digest(stored.engine)

    def assert_rejected_without_mutation(self, error, operation, match_id):
        before = self.fingerprint(match_id)
        with self.assertRaises(error):
            operation()
        self.assertEqual(self.fingerprint(match_id), before)

    def corrupt_snapshot(self, match_id, payload):
        if self.store_kind == "memory":
            version, _ = self.store._records[match_id]
            self.store._records[match_id] = (version, payload)
        else:
            with self.store._connect() as connection:
                connection.execute(
                    "UPDATE matches SET snapshot = ? WHERE match_id = ?",
                    (payload, match_id),
                )

    def test_fixture_contains_two_matches_and_two_players_per_match(self):
        for match_id in ("one", "two"):
            stored = self.service.get_match(match_id)
            self.assertEqual(set(stored.engine.state.players), {"A", "B"})
            self.assertEqual(stored.version, 1)

    def test_malformed_match_ids_have_stable_public_error_without_side_effects(self):
        alice = self.identities["alice"]
        self.authorization.grant_global(alice, Capability.CREATE_MATCH)
        self.authorization.grant_match(alice, "one", Capability.ADMINISTER)
        invalid_ids = (
            "",
            "   ",
            " leading",
            "trailing ",
            "line\nbreak",
            "nul\0",
            "x" * 129,
        )

        for match_id in invalid_ids:
            operations = (
                lambda value=match_id: self.app.create_match(
                    alice,
                    value,
                    {"A": test_deck("bad-A"), "B": test_deck("bad-B")},
                ),
                lambda value=match_id: self.app.view(alice, value),
                lambda value=match_id: self.app.submit(
                    alice, value, PassPriority("A"), expected_version=1
                ),
                lambda value=match_id: self.app.administrative_version(alice, value),
            )
            for operation in operations:
                with self.subTest(match_id=repr(match_id), operation=operation):
                    with (
                        patch.object(
                            self.store, "create", wraps=self.store.create
                        ) as create,
                        patch.object(self.store, "load", wraps=self.store.load) as load,
                        patch.object(
                            self.authorization,
                            "allows_global",
                            wraps=self.authorization.allows_global,
                        ) as allows_global,
                        patch.object(
                            self.authorization,
                            "player_for",
                            wraps=self.authorization.player_for,
                        ) as player_for,
                        patch.object(
                            self.authorization,
                            "allows_match",
                            wraps=self.authorization.allows_match,
                        ) as allows_match,
                    ):
                        with self.assertRaises(InvalidMatchId) as caught:
                            operation()
                    self.assertEqual(caught.exception.code, "invalid_match_id")
                    self.assertEqual(
                        caught.exception.args, (InvalidMatchId.public_message,)
                    )
                    if match_id:
                        self.assertNotIn(match_id, str(caught.exception))
                    create.assert_not_called()
                    load.assert_not_called()
                    allows_global.assert_not_called()
                    player_for.assert_not_called()
                    allows_match.assert_not_called()

        self.assertEqual(self.fingerprint("one")[0], 1)

    def test_missing_revoked_and_invalid_credentials_do_not_mutate(self):
        credentials = (
            (AuthenticationRequired, None),
            # Un token revocado/expirado no supera el autenticador del adaptador
            # y, por tanto, nunca constituye una identidad autenticada.
            (
                InvalidIdentity,
                ExternalIdentity(
                    "https://issuer.example", "revoked", authenticated=False
                ),
            ),
            (InvalidIdentity, ExternalIdentity("", "alice")),
            (InvalidIdentity, ExternalIdentity("https://issuer.example", "")),
            (InvalidIdentity, ExternalIdentity("https://issuer.example", "alice", 1)),
            (
                InvalidIdentity,
                ExternalIdentity("https://issuer.example", "alice", "true"),
            ),
            (InvalidIdentity, ExternalIdentity(None, "alice")),
            (InvalidIdentity, ExternalIdentity("https://issuer.example", None)),
            (InvalidIdentity, ExternalIdentity(123, "alice")),
            (InvalidIdentity, ExternalIdentity("https://issuer.example", 123)),
        )
        for error, credential in credentials:
            with self.subTest(error=error.__name__, credential=credential):
                before = self.fingerprint("one")
                with self.assertRaises(error) as caught:
                    self.app.view(credential, "one")
                self.assertEqual(self.fingerprint("one"), before)
                self.assertEqual(caught.exception.args, (error.public_message,))
                self.assertIsNone(caught.exception.__cause__)

    def test_identity_match_resolved_player_and_command_author_matrix(self):
        # La columna resolved_player documenta el jugador obtenido de la política;
        # no es un parámetro seleccionable de la API pública.
        matrix = (
            ("alice", "one", "A", "A", True),
            ("alice", "one", "A", "B", False),
            ("bob", "one", "B", "A", False),
            ("bob", "one", "B", "B", True),
            ("carol", "two", "A", "A", True),
            ("carol", "two", "A", "B", False),
            ("dave", "two", "B", "A", False),
            ("dave", "two", "B", "B", True),
            ("alice", "two", None, "A", False),
            ("alice", "two", None, "B", False),
            ("carol", "one", None, "A", False),
            ("carol", "one", None, "B", False),
        )
        for identity_name, match_id, resolved_player, author, allowed in matrix:
            with self.subTest(
                identity=identity_name,
                match=match_id,
                resolved_player=resolved_player,
                author=author,
            ):
                identity = self.identities[identity_name]
                before = self.fingerprint(match_id)
                command = (
                    self.service.view(match_id, author).legal_actions[0]
                    if allowed
                    else Concede(author)
                )

                def operation():
                    return self.app.submit(
                        identity,
                        match_id,
                        command,
                        expected_version=before[0],
                    )

                if allowed:
                    response = operation()
                    self.assertEqual(response.observation.player_id, resolved_player)
                    self.assertEqual(response.version, before[0] + 1)
                else:
                    self.assert_rejected_without_mutation(
                        AccessDenied, operation, match_id
                    )

    def test_player_cannot_be_selected_on_view_or_submit(self):
        self.assertNotIn(
            "player_id",
            inspect.signature(AuthenticatedMatchApplication.view).parameters,
        )
        self.assertNotIn(
            "player_id",
            inspect.signature(AuthenticatedMatchApplication.submit).parameters,
        )
        self.assertEqual(
            self.app.view(self.identities["alice"], "one").observation.player_id,
            "A",
        )

    def test_capabilities_are_independent_and_denials_do_not_mutate(self):
        alice = self.identities["alice"]
        before = self.fingerprint("one")

        # La asociación inicial concede observar y enviar, pero no las
        # capacidades global y administrativa, que son independientes.
        with self.assertRaises(AccessDenied):
            self.app.create_match(
                alice,
                "three",
                {"A": test_deck("three-A"), "B": test_deck("three-B")},
            )
        with self.assertRaises(AccessDenied):
            self.app.administrative_version(alice, "one")
        self.assertEqual(self.fingerprint("one"), before)

        self.authorization.grant_match(alice, "one", Capability.ADMINISTER)
        self.assertEqual(self.app.administrative_version(alice, "one"), before[0])
        # Administrar no concede observación en otra partida.
        self.authorization.grant_match(alice, "two", Capability.ADMINISTER)
        with self.assertRaises(AccessDenied):
            self.app.view(alice, "two")

        self.authorization.grant_global(alice, Capability.CREATE_MATCH)
        self.assertEqual(
            self.app.create_match(
                alice,
                "three",
                {"A": test_deck("three-A"), "B": test_deck("three-B")},
            ),
            1,
        )

    def test_observe_and_submit_bindings_are_independent(self):
        observer = ExternalIdentity("https://issuer.example", "observer")
        sender = ExternalIdentity("https://issuer.example", "sender")
        self.authorization.bind_player(
            observer, "one", "A", capabilities=(Capability.OBSERVE,)
        )
        self.authorization.bind_player(
            sender, "one", "A", capabilities=(Capability.SUBMIT_COMMAND,)
        )
        self.assertEqual(self.app.view(observer, "one").observation.player_id, "A")
        with self.assertRaises(AccessDenied):
            self.app.submit(
                observer,
                "one",
                self.service.view("one", "A").legal_actions[0],
                expected_version=1,
            )
        with self.assertRaises(AccessDenied):
            self.app.view(sender, "one")

        command = self.service.view("one", "A").legal_actions[0]
        self.assertEqual(
            self.app.submit(sender, "one", command, expected_version=1).version,
            2,
        )

    def test_unauthorized_existing_and_missing_match_are_indistinguishable(self):
        identity = self.identities["alice"]
        before = {match_id: self.fingerprint(match_id) for match_id in ("one", "two")}
        errors = []
        for match_id in ("two", "does-not-exist"):
            with self.subTest(match_id=match_id):
                with self.assertRaises(AccessDenied) as caught:
                    self.app.view(identity, match_id)
                errors.append((caught.exception.code, caught.exception.args))
        self.assertEqual(errors[0], errors[1])
        self.assertEqual(
            errors[0],
            ("access_denied", ("La identidad no está autorizada para esta operación",)),
        )
        self.assertEqual(
            {match_id: self.fingerprint(match_id) for match_id in ("one", "two")},
            before,
        )

    def test_authorized_missing_match_uses_safe_not_found_error(self):
        identity = self.identities["alice"]
        self.authorization.bind_player(identity, "missing", "A")
        with self.assertRaises(ResourceNotFound) as caught:
            self.app.view(identity, "missing")
        self.assertEqual(caught.exception.args, ("El recurso solicitado no existe",))

    def test_illegal_command_and_stale_version_preserve_version_and_digest(self):
        alice = self.identities["alice"]
        bob = self.identities["bob"]
        self.assert_rejected_without_mutation(
            CommandRejected,
            lambda: self.app.submit(bob, "one", PassPriority("B"), expected_version=1),
            "one",
        )
        command = self.service.view("one", "A").legal_actions[0]
        self.app.submit(alice, "one", command, expected_version=1)
        self.assert_rejected_without_mutation(
            WriteConflict,
            lambda: self.app.submit(alice, "one", command, expected_version=1),
            "one",
        )

    def test_incompatible_decks_have_a_safe_specific_public_error(self):
        alice = self.identities["alice"]
        self.authorization.grant_global(alice, Capability.CREATE_MATCH)
        original = test_deck("duplicate")[0]
        incompatible = replace(original, name=f"{original.name} (interno secreto)")
        catalog_before = self.catalog.definitions()

        with self.assertRaises(InvalidDeck) as caught:
            self.app.create_match(
                alice,
                "invalid-decks",
                {"A": (original,), "B": (incompatible,)},
            )

        self.assertEqual(caught.exception.code, "invalid_deck")
        self.assertEqual(caught.exception.args, (InvalidDeck.public_message,))
        self.assertNotIn("interno secreto", str(caught.exception))
        with self.assertRaises(MatchNotFound):
            self.service.get_match("invalid-decks")
        self.assertEqual(self.catalog.definitions(), catalog_before)

    def test_unexpected_engine_errors_propagate_without_side_effects(self):
        alice = self.identities["alice"]
        self.authorization.grant_global(alice, Capability.CREATE_MATCH)

        for error_type in (TypeError, AttributeError, RuntimeError, ValueError):
            match_id = f"unexpected-{error_type.__name__}"
            catalog_before = self.catalog.definitions()
            with self.subTest(error_type=error_type):
                with patch.object(
                    GameEngine,
                    "new_match",
                    side_effect=error_type("detalle interno accidental"),
                ):
                    with self.assertRaises(error_type) as caught:
                        self.app.create_match(
                            alice,
                            match_id,
                            {
                                "A": test_deck(f"{match_id}-A"),
                                "B": test_deck(f"{match_id}-B"),
                            },
                        )

                self.assertNotIsInstance(caught.exception, InvalidDeck)
                with self.assertRaises(MatchNotFound):
                    self.service.get_match(match_id)
                self.assertEqual(self.catalog.definitions(), catalog_before)

    def test_malformed_commands_have_a_safe_specific_public_error(self):
        before = self.fingerprint("one")
        with self.assertRaises(MalformedCommand) as caught:
            self.app.submit(
                self.identities["alice"], "one", object(), expected_version=1
            )
        self.assertEqual(caught.exception.code, "malformed_command")
        self.assertEqual(caught.exception.args, (MalformedCommand.public_message,))
        self.assertNotIn("object", str(caught.exception))
        self.assertEqual(self.fingerprint("one"), before)

    def test_unreadable_snapshot_has_a_safe_internal_load_error(self):
        version, _ = self.fingerprint("one")
        self.corrupt_snapshot("one", "texto interno que no es JSON")

        with self.assertRaises(InternalLoadFailure) as caught:
            self.app.view(self.identities["alice"], "one")

        self.assertEqual(caught.exception.code, "internal_load_failure")
        self.assertEqual(
            caught.exception.args, (InternalLoadFailure.public_message,)
        )
        self.assertNotIn("texto interno", str(caught.exception))
        if self.store_kind == "memory":
            self.assertEqual(self.store._records["one"][0], version)
        else:
            with self.store._connect() as connection:
                persisted = connection.execute(
                    "SELECT version, snapshot FROM matches WHERE match_id = 'one'"
                ).fetchone()
            self.assertEqual(persisted, (version, "texto interno que no es JSON"))

    def test_two_authorized_requests_with_same_version_have_one_cas_winner(self):
        alice = self.identities["alice"]
        command = self.service.view("one", "A").legal_actions[0]

        def submit():
            try:
                self.app.submit(alice, "one", command, expected_version=1)
                return "winner"
            except WriteConflict:
                return "conflict"

        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(lambda _: submit(), range(2)))
        self.assertCountEqual(outcomes, ("winner", "conflict"))
        self.assertEqual(self.service.get_match("one").version, 2)

    def test_public_options_distinguish_same_action_type_without_command_fields(self):
        internal = self.service.view("one", "A")
        duplicated = replace(
            internal,
            legal_actions=(Concede("A"), Concede("A")),
        )
        with patch.object(self.service, "view", return_value=duplicated):
            payload = self.app.view(self.identities["alice"], "one").to_dict()

        first, second = payload["legal_actions"]
        self.assertEqual(first["action"], second["action"])
        self.assertNotEqual(first["id"], second["id"])
        self.assertEqual(set(first), {"id", "action"})
        self.assertEqual(set(second), {"id", "action"})
        forbidden = {
            "player_id", "card_id", "chosen_player_ids", "chosen_card_ids",
            "target", "cost_option_index", "discard_card_ids",
            "sacrifice_card_ids", "x_value",
        }
        self.assertTrue(forbidden.isdisjoint(first))
        self.assertTrue(forbidden.isdisjoint(second))

    def test_valid_public_option_executes_the_exact_authoritative_alternative(self):
        alice = self.identities["alice"]
        view = self.app.view(alice, "one")
        selected = next(
            option for option in view.legal_actions if option.action == "PassPriority"
        )

        result = self.app.submit_option(
            alice, "one", selected.option_id, expected_version=view.version
        )

        self.assertEqual(result.version, 2)
        self.assertEqual(self.service.get_match("one").engine.state.status.name, "RUNNING")

    def test_every_emitted_option_can_be_submitted_with_its_authoritative_context(self):
        alice = self.identities["alice"]
        option_count = len(self.app.view(alice, "one").legal_actions)

        for index in range(option_count):
            with self.subTest(index=index):
                match_id = f"option-roundtrip-{index}"
                self.service.create_match(
                    match_id,
                    {
                        "A": test_deck(f"{match_id}-A"),
                        "B": test_deck(f"{match_id}-B"),
                    },
                    seed=1,
                )
                self.authorization.bind_player(alice, match_id, "A")
                view = self.app.view(alice, match_id)

                result = self.app.submit_option(
                    alice,
                    match_id,
                    view.legal_actions[index].option_id,
                    expected_version=view.version,
                )

                self.assertEqual(result.version, view.version + 1)

    def test_public_view_rejects_actions_without_authoritative_identifiers(self):
        view = self.service.view("one", "A")
        self.assertTrue(view.legal_actions)

        with self.assertRaisesRegex(
            ValueError, "acciones legales requieren identificadores autoritativos"
        ):
            PublicMatchView.from_view(view)

    def test_foreign_fabricated_and_stale_options_are_safe_and_do_not_mutate(self):
        alice = self.identities["alice"]
        alice_view = self.app.view(alice, "one")
        bob_option = self.app.view(self.identities["bob"], "one").legal_actions[0]
        self.assert_rejected_without_mutation(
            OptionRejected,
            lambda: self.app.submit_option(
                alice, "one", bob_option.option_id, expected_version=1
            ),
            "one",
        )

        self.authorization.bind_player(alice, "two", "A")
        other_match_option = self.app.view(alice, "two").legal_actions[0]
        self.assert_rejected_without_mutation(
            OptionRejected,
            lambda: self.app.submit_option(
                alice, "one", other_match_option.option_id, expected_version=1
            ),
            "one",
        )
        original = alice_view.legal_actions[0].option_id
        replacement = "1" if original[-1] == "0" else "0"
        tampered = original[:-1] + replacement
        self.assertNotEqual(tampered, original)
        for invalid in ("invented", tampered):
            self.assert_rejected_without_mutation(
                OptionRejected,
                lambda invalid=invalid: self.app.submit_option(
                    alice, "one", invalid, expected_version=1
                ),
                "one",
            )

        valid = alice_view.legal_actions[0].option_id
        self.app.submit_option(alice, "one", valid, expected_version=1)
        self.assert_rejected_without_mutation(
            WriteConflict,
            lambda: self.app.submit_option(
                alice, "one", valid, expected_version=1
            ),
            "one",
        )

    def test_tampered_option_id_transformation_always_changes_original(self):
        for original in ("option0", "optiona"):
            with self.subTest(original=original):
                replacement = "1" if original[-1] == "0" else "0"
                tampered = original[:-1] + replacement

                self.assertNotEqual(tampered, original)

    def test_two_public_option_writes_with_same_cas_have_one_winner(self):
        alice = self.identities["alice"]
        view = self.app.view(alice, "one")
        option_id = view.legal_actions[0].option_id

        def submit():
            try:
                self.app.submit_option(
                    alice, "one", option_id, expected_version=view.version
                )
                return "winner"
            except WriteConflict:
                return "conflict"

        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(lambda _: submit(), range(2)))
        self.assertCountEqual(outcomes, ("winner", "conflict"))
        self.assertEqual(self.service.get_match("one").version, 2)

    def test_public_dto_excludes_internal_and_opponent_private_state(self):
        response = self.app.view(self.identities["alice"], "one")
        payload = response.to_dict()
        encoded = json.dumps(payload)
        forbidden_keys = {
            "engine",
            "state",
            "snapshot",
            "deck",
            "opponent_hand",
            "chosen_card_ids",
            "discard_card_ids",
            "sacrifice_card_ids",
        }

        def inspect_value(value):
            self.assertNotIsInstance(value, (GameEngine, GameState))
            if isinstance(value, dict):
                self.assertTrue(forbidden_keys.isdisjoint(value))
                for nested in value.values():
                    inspect_value(nested)
            elif isinstance(value, (list, tuple)):
                for nested in value:
                    inspect_value(nested)

        inspect_value(payload)
        stored = self.service.get_match("one")
        opponent_hidden = {
            *stored.engine.state.players["B"].zones[Zone.HAND],
            *stored.engine.state.players["B"].zones[Zone.DECK],
        }
        self.assertTrue(opponent_hidden)
        self.assertTrue(all(card_id not in encoded for card_id in opponent_hidden))


class InMemoryAuthenticatedApplicationR06Tests(
    AuthenticatedApplicationR06Contract, unittest.TestCase
):
    store_kind = "memory"


class SQLiteAuthenticatedApplicationR06Tests(
    AuthenticatedApplicationR06Contract, unittest.TestCase
):
    store_kind = "sqlite"


if __name__ == "__main__":
    unittest.main()
