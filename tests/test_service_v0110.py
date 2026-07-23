import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from card_duel_engine import InMemoryMatchStore, MatchService, SQLiteMatchStore, VersionConflict
from card_duel_engine.persistence.snapshot import state_digest
from fixtures import test_deck


class MatchServiceV0110Tests(unittest.TestCase):
    def decks(self):
        return {"A": test_deck("A"), "B": test_deck("B")}

    def test_create_view_submit_and_isolation(self):
        service = MatchService(InMemoryMatchStore())
        self.assertEqual(service.create_match("match", self.decks(), seed=7), 1)
        view = service.view("match", "A")
        action = view.legal_actions[0]
        updated = service.submit("match", action, expected_version=view.version)
        self.assertEqual(updated.version, 2)
        self.assertEqual(service.get_match("match").version, 2)

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


if __name__ == "__main__":
    unittest.main()
