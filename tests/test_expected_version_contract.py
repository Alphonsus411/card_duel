import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from card_duel_engine import (
    AuthenticatedMatchApplication,
    ExternalIdentity,
    InMemoryMatchStore,
    InvalidExpectedVersion,
    MatchService,
    SQLiteMatchStore,
    VersionConflict,
)
from card_duel_engine.engine.commands import PassPriority
from card_duel_engine.storage import validate_expected_version
from fixtures import test_deck


INVALID_VERSIONS = (True, False, 0, -1, 1.0, "1", None, [], {})


class ExpectedVersionDomainTests(unittest.TestCase):
    def test_exact_type_and_range_contract(self):
        for value in INVALID_VERSIONS:
            with self.subTest(type=type(value).__name__):
                with self.assertRaises(ValueError) as caught:
                    validate_expected_version(value)
                self.assertEqual(
                    str(caught.exception),
                    "La versión esperada debe ser un entero positivo",
                )
                self.assertNotIn(repr(value), str(caught.exception))

        for value in (1, 2, 99):
            with self.subTest(value=value):
                self.assertEqual(validate_expected_version(value), value)


class ExpectedVersionStoreContract:
    store_kind = ""

    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        if self.store_kind == "memory":
            self.store = InMemoryMatchStore()
        else:
            self.store = SQLiteMatchStore(
                Path(self.temporary_directory.name) / "versions.db"
            )
            self.addCleanup(self.store.close)
        service = MatchService(self.store)
        service.create_match(
            "match", {"A": test_deck("version-A"), "B": test_deck("version-B")}
        )
        self.engine = self.store.load("match").engine

    def test_invalid_versions_never_write(self):
        for value in INVALID_VERSIONS:
            with self.subTest(type=type(value).__name__):
                with self.assertRaises(ValueError):
                    self.store.save("match", self.engine, expected_version=value)
                self.assertEqual(self.store.load("match").version, 1)

    def test_one_and_higher_versions_are_accepted(self):
        self.assertEqual(self.store.save("match", self.engine, expected_version=1), 2)
        self.assertEqual(self.store.save("match", self.engine, expected_version=2), 3)

    def test_valid_but_stale_version_remains_a_conflict(self):
        self.store.save("match", self.engine, expected_version=1)
        with self.assertRaises(VersionConflict):
            self.store.save("match", self.engine, expected_version=1)


class InMemoryExpectedVersionTests(ExpectedVersionStoreContract, unittest.TestCase):
    store_kind = "memory"


class SQLiteExpectedVersionTests(ExpectedVersionStoreContract, unittest.TestCase):
    store_kind = "sqlite"


class MatchServiceExpectedVersionTests(unittest.TestCase):
    def test_invalid_version_does_not_read_write_or_execute(self):
        store = Mock()
        service = MatchService(store)
        service.validate_command = Mock(wraps=service.validate_command)
        command = Mock()
        for value in INVALID_VERSIONS:
            with self.subTest(type=type(value).__name__):
                store.reset_mock()
                command.reset_mock()
                service.validate_command.reset_mock()
                with self.assertRaises(ValueError):
                    service.submit("match", command, expected_version=value)
                store.load.assert_not_called()
                store.save.assert_not_called()
                service.validate_command.assert_not_called()


class AuthenticatedApplicationExpectedVersionTests(unittest.TestCase):
    def setUp(self):
        self.service = Mock()
        self.authorization = Mock()
        self.application = AuthenticatedMatchApplication(
            self.service, self.authorization
        )
        self.identity = ExternalIdentity("issuer", "subject")

    def test_both_submit_boundaries_reject_before_membership_or_service(self):
        source = Mock()
        operations = (
            lambda value: self.application.submit(
                self.identity,
                "match",
                PassPriority("A"),
                expected_version=value,
            ),
            lambda value: self.application.submit_from(
                self.identity, "match", source, expected_version=value
            ),
        )
        for operation in operations:
            for value in INVALID_VERSIONS:
                with self.subTest(operation=operation, type=type(value).__name__):
                    self.service.reset_mock()
                    self.authorization.reset_mock()
                    source.reset_mock()
                    with self.assertRaises(InvalidExpectedVersion) as caught:
                        operation(value)
                    self.assertEqual(caught.exception.code, "invalid_expected_version")
                    self.assertEqual(
                        caught.exception.args,
                        (InvalidExpectedVersion.public_message,),
                    )
                    self.assertNotIn(repr(value), str(caught.exception))
                    self.assertIsNone(caught.exception.__cause__)
                    self.assertTrue(caught.exception.__suppress_context__)
                    self.authorization.player_for.assert_not_called()
                    self.service.assert_not_called()
                    source.choose_action.assert_not_called()


if __name__ == "__main__":
    unittest.main()
