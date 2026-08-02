import tempfile
import unittest
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor
from dataclasses import MISSING, fields
from pathlib import Path
from types import UnionType
from typing import get_args, get_origin

from card_duel_engine import (
    InMemoryMatchStore,
    MatchService,
    SQLiteMatchStore,
    VersionConflict,
)
from card_duel_engine.domain.errors import IllegalAction
from card_duel_engine.catalog import CardCatalog
from card_duel_engine.engine.game import GameEngine
from card_duel_engine.domain.enums import MatchStatus
from card_duel_engine.engine import commands as command_module
from card_duel_engine.engine.commands import (
    EXECUTABLE_COMMAND_TYPES,
    Concede,
    GameCommand,
    PassPriority,
)
from card_duel_engine.persistence.snapshot import state_digest
from card_duel_engine.service import MalformedGameCommand
from fixtures import test_deck


class MatchIdValidationContract:
    """Contrato común de claves para todos los almacenes de partidas."""

    store_kind = ""

    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        if self.store_kind == "memory":
            self.store = InMemoryMatchStore()
        elif self.store_kind == "sqlite":
            self.store = SQLiteMatchStore(
                Path(self.temporary_directory.name) / "match-ids.db"
            )
            self.addCleanup(self.store.close)
        else:  # pragma: no cover
            raise AssertionError("La batería necesita un almacén")

        service = MatchService(self.store)
        service.create_match(
            "existing", {"A": test_deck("id-A"), "B": test_deck("id-B")}
        )
        self.engine = self.store.load("existing").engine

    def test_create_load_and_save_reject_the_same_invalid_ids(self):
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
            for operation in (
                lambda value=match_id: self.store.create(value, self.engine),
                lambda value=match_id: self.store.load(value),
                lambda value=match_id: self.store.save(
                    value, self.engine, expected_version=1
                ),
            ):
                with self.subTest(match_id=repr(match_id), operation=operation):
                    with self.assertRaises(ValueError):
                        operation()

        self.assertEqual(self.store.load("existing").version, 1)

    def test_unicode_without_control_characters_preserves_exact_identity(self):
        match_id = "partida-Ñ-棋-🙂"
        self.assertEqual(self.store.create(match_id, self.engine), 1)
        stored = self.store.load(match_id)
        self.assertEqual(stored.match_id, match_id)
        self.assertEqual(
            self.store.save(match_id, stored.engine, expected_version=stored.version), 2
        )
        self.assertEqual(self.store.load(match_id).match_id, match_id)


class InMemoryMatchIdValidationTests(MatchIdValidationContract, unittest.TestCase):
    store_kind = "memory"


class SQLiteMatchIdValidationTests(MatchIdValidationContract, unittest.TestCase):
    store_kind = "sqlite"


class MatchServiceV0110Tests(unittest.TestCase):
    def decks(self):
        return {"A": test_deck("A"), "B": test_deck("B")}

    @staticmethod
    def command_instance(command_type):
        values = {"player_id": "A"}
        for field in fields(command_type):
            if field.name in values or field.default is not MISSING:
                continue
            annotation = field.type
            origin = get_origin(annotation)
            if annotation == "int" or annotation is int:
                values[field.name] = 0
            elif annotation == "str" or annotation is str:
                values[field.name] = "value"
            elif origin is tuple or str(annotation).startswith("tuple["):
                values[field.name] = ()
            elif origin is UnionType and type(None) in get_args(annotation):
                values[field.name] = None
            else:  # pragma: no cover - obliga a ampliar la fábrica al añadir campos
                raise AssertionError(f"Campo de prueba desconocido: {field}")
        return command_type(**values)

    def test_executable_command_registry_is_complete_and_has_no_duplicates(self):
        concrete_commands = {
            value
            for value in vars(command_module).values()
            if isinstance(value, type)
            and value.__module__ == command_module.__name__
            and issubclass(value, GameCommand)
            and value is not GameCommand
        }
        self.assertEqual(set(EXECUTABLE_COMMAND_TYPES), concrete_commands)
        self.assertEqual(len(EXECUTABLE_COMMAND_TYPES), len(set(EXECUTABLE_COMMAND_TYPES)))

    def test_command_validation_uses_exact_registered_types(self):
        class InventedCommand(GameCommand):
            pass

        class InventedConcede(Concede):
            pass

        rejected = (
            object(),
            GameCommand("A"),
            InventedCommand("A"),
            InventedConcede("A"),
        )
        for command in rejected:
            with self.subTest(command=type(command).__name__):
                with self.assertRaises(MalformedGameCommand):
                    MatchService.validate_command(command)

        for command_type in EXECUTABLE_COMMAND_TYPES:
            with self.subTest(command_type=command_type.__name__):
                MatchService.validate_command(self.command_instance(command_type))

    def test_create_view_submit_and_isolation(self):
        service = MatchService(InMemoryMatchStore())
        self.assertEqual(service.create_match("match", self.decks(), seed=7), 1)
        view = service.view("match", "A")
        action = view.legal_actions[0]
        updated = service.submit("match", action, expected_version=view.version)
        self.assertEqual(updated.version, 2)
        self.assertEqual(service.get_match("match").version, 2)

    def test_late_engine_failure_never_calls_store_or_mutates_shared_catalog(self):
        class AccidentalSetupFailure(RuntimeError):
            pass

        class RecordingStore(InMemoryMatchStore):
            def __init__(self):
                super().__init__()
                self.create_calls = []

            def create(self, match_id, engine):
                self.create_calls.append((match_id, engine))
                return super().create(match_id, engine)

        catalog = CardCatalog()
        store = RecordingStore()
        service = MatchService(store, catalog=catalog)
        definitions_before = catalog.definitions()

        with patch.object(
            GameEngine,
            "_validate_candidate_invariants",
            side_effect=AccidentalSetupFailure("fallo accidental tardío"),
        ):
            with self.assertRaisesRegex(AccidentalSetupFailure, "accidental tardío"):
                service.create_match("not-created", self.decks(), seed=41)

        self.assertEqual(store.create_calls, [])
        self.assertEqual(catalog.definitions(), definitions_before)
        with self.assertRaises(KeyError):
            store.load("not-created")

    def test_stale_version_is_rejected_without_mutation(self):
        service = MatchService(InMemoryMatchStore())
        service.create_match("match", self.decks())
        view = service.view("match", "A")
        action = view.legal_actions[0]
        service.submit("match", action, expected_version=1)
        with self.assertRaises(VersionConflict):
            service.submit("match", action, expected_version=1)
        self.assertEqual(service.get_match("match").version, 2)

    def test_sqlite_service_persists_and_is_deterministic(self):
        with tempfile.TemporaryDirectory() as directory:
            service = MatchService(SQLiteMatchStore(Path(directory) / "matches.db"))
            service.create_match("one", self.decks(), seed=19)
            service.create_match("two", self.decks(), seed=19)
            self.assertEqual(
                state_digest(service.get_match("one").engine),
                state_digest(service.get_match("two").engine),
            )

    def test_sqlite_in_memory_database_survives_short_connections(self):
        store = SQLiteMatchStore(":memory:")
        self.addCleanup(store.close)
        service = MatchService(store)
        self.assertEqual(service.create_match("memory", self.decks(), seed=19), 1)
        view = service.view("memory", "A")
        updated = service.submit(
            "memory", view.legal_actions[0], expected_version=view.version
        )
        self.assertEqual(updated.version, 2)
        self.assertEqual(service.get_match("memory").version, 2)

    def test_sqlite_rejects_all_operations_after_close(self):
        store = SQLiteMatchStore(":memory:")
        service = MatchService(store)
        service.create_match("closed", self.decks(), seed=19)
        stored = store.load("closed")

        store.close()
        store.close()

        operations = (
            lambda: store.create("another", stored.engine),
            lambda: store.load("closed"),
            lambda: store.save(
                "closed", stored.engine, expected_version=stored.version
            ),
        )
        for operation in operations:
            with self.subTest(operation=operation):
                with self.assertRaisesRegex(
                    RuntimeError, "^SQLiteMatchStore está cerrado$"
                ):
                    operation()

    def test_sqlite_context_manager_closes_store_on_exit(self):
        with SQLiteMatchStore(":memory:") as store:
            service = MatchService(store)
            self.assertEqual(service.create_match("context", self.decks(), seed=19), 1)
            self.assertEqual(store.load("context").version, 1)

        with self.assertRaisesRegex(RuntimeError, "^SQLiteMatchStore está cerrado$"):
            store.load("context")

    def test_concurrent_writers_have_one_winner(self):
        service = MatchService(InMemoryMatchStore())
        service.create_match("race", self.decks())
        view = service.view("race", "A")
        action = view.legal_actions[0]

        def submit():
            try:
                service.submit("race", action, expected_version=1)
                return True
            except VersionConflict:
                return False

        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(sum(pool.map(lambda _: submit(), range(2))), 1)

    def test_submit_from_and_wrong_player_source(self):
        class Source:
            def __init__(self, wrong=False):
                self.wrong = wrong

            def choose_action(self, observation, legal_actions):
                action = legal_actions[0]
                return PassPriority("B") if self.wrong else action

        service = MatchService(InMemoryMatchStore())
        service.create_match("source", self.decks())
        self.assertEqual(service.submit_from("source", "A", Source()).version, 2)
        with self.assertRaises(ValueError):
            service.submit_from("source", "A", Source(True))
        self.assertEqual(service.get_match("source").version, 2)

    def test_invalid_command_never_persists_partial_state_for_both_stores(self):
        with tempfile.TemporaryDirectory() as directory:
            for index, store in enumerate(
                (InMemoryMatchStore(), SQLiteMatchStore(Path(directory) / "invalid.db"))
            ):
                service = MatchService(store)
                match_id = f"invalid-{index}"
                service.create_match(match_id, self.decks(), seed=4)
                before = state_digest(service.get_match(match_id).engine)
                with self.assertRaises(IllegalAction):
                    service.submit(match_id, PassPriority("B"), expected_version=1)
                stored = service.get_match(match_id)
                self.assertEqual(stored.version, 1)
                self.assertEqual(state_digest(stored.engine), before)

    def test_memory_and_sqlite_have_equivalent_submit_semantics(self):
        with tempfile.TemporaryDirectory() as directory:
            digests = []
            for index, store in enumerate(
                (
                    InMemoryMatchStore(),
                    SQLiteMatchStore(Path(directory) / "equivalent.db"),
                )
            ):
                service = MatchService(store)
                match_id = f"equivalent-{index}"
                service.create_match(match_id, self.decks(), seed=23)
                view = service.view(match_id, "A")
                service.submit(
                    match_id, view.legal_actions[0], expected_version=view.version
                )
                digests.append(state_digest(service.get_match(match_id).engine))
            self.assertEqual(digests[0], digests[1])

    def test_terminal_submit_and_later_view_for_both_stores(self):
        with tempfile.TemporaryDirectory() as directory:
            stores = (
                InMemoryMatchStore(),
                SQLiteMatchStore(Path(directory) / "terminal.db"),
            )
            for index, store in enumerate(stores):
                with self.subTest(store=type(store).__name__):
                    service = MatchService(store)
                    match_id = f"terminal-{index}"
                    service.create_match(match_id, self.decks(), seed=31)

                    terminal = service.submit(
                        match_id, Concede("A"), expected_version=1
                    )

                    self.assertEqual(terminal.version, 2)
                    self.assertEqual(terminal.legal_actions, ())
                    stored = service.get_match(match_id)
                    self.assertEqual(stored.version, 2)
                    self.assertIs(stored.engine.state.status, MatchStatus.FINISHED)
                    self.assertEqual(stored.engine.state.winner_ids, ("B",))

                    later = service.view(match_id, "A")
                    self.assertEqual(later.version, 2)
                    self.assertEqual(later.observation, terminal.observation)
                    self.assertEqual(later.legal_actions, ())


if __name__ == "__main__":
    unittest.main()
