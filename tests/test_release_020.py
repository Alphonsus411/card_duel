import json
from pathlib import Path
import re
import tomllib
import unittest
from zipfile import ZipFile

from card_duel_engine.catalog import CardCatalog
from card_duel_engine.persistence import load_snapshot, replay_from_log, state_digest

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "tests" / "artifacts" / "0.19.0"


class Release020PolicyTests(unittest.TestCase):
    def test_project_is_the_only_current_version_literal(self):
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        current = project["project"]["version"]
        self.assertEqual(current, "0.20.1")
        consumers = [*sorted((ROOT / "scripts").glob("*.py")), ROOT / ".github/workflows/tests.yml"]
        for path in consumers:
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertNotRegex(path.read_text(encoding="utf-8"), rf"(?<![\d.]){re.escape(current)}(?![\d.])")

    def test_production_catalog_remains_empty(self):
        self.assertEqual(CardCatalog().definitions(), ())
        package = ROOT / "src" / "card_duel_engine"
        self.assertFalse(any(path.suffix in {".json", ".yaml", ".yml"} for path in package.rglob("*")))

    def test_built_wheel_excludes_primary_pdfs_and_runtime_dependencies(self):
        wheels = sorted((ROOT / "dist").glob("*.whl"))
        if not wheels:
            self.skipTest("el wheel se inspecciona tras ejecutar el verificador de empaquetado")
        with ZipFile(wheels[-1]) as archive:
            names = set(archive.namelist())
            metadata_name = next(name for name in names if name.endswith(".dist-info/METADATA"))
            metadata = archive.read(metadata_name).decode("utf-8")
        self.assertTrue({"Fantasy Tokens.pdf", "Fantasy Tokens Edicion Mitica.pdf"}.isdisjoint(names))
        runtime = [line for line in metadata.splitlines() if line.startswith("Requires-Dist:") and 'extra == "dev"' not in line]
        self.assertEqual(runtime, [])


class Historical019CompatibilityTests(unittest.TestCase):
    @staticmethod
    def fingerprint(engine):
        state = engine.state
        assert state is not None
        return (
            state_digest(engine), tuple(state.command_history),
            tuple((player_id, player.wounds) for player_id, player in state.players.items()),
            state.turn_order, engine._next_instance, engine._next_stack_item,
            tuple(state.cards), tuple(item.stack_id for item in state.stack),
        )

    def test_v1_snapshot_and_v2_replay_keep_019_observables(self):
        snapshot_document = json.loads((ARTIFACTS / "snapshot-v1.json").read_text(encoding="utf-8"))
        replay_document = json.loads((ARTIFACTS / "replay-v2.json").read_text(encoding="utf-8"))
        self.assertEqual(snapshot_document["body"]["schema_version"], "1")
        self.assertEqual(replay_document["body"]["schema_version"], "2")
        self.assertEqual(replay_document["body"]["engine_version"], "0.19.0")

        restored = load_snapshot(snapshot_document)
        replayed = replay_from_log(replay_document)
        self.assertEqual(self.fingerprint(restored), self.fingerprint(replayed))
        self.assertEqual(restored.rules.version, "0.19.0")
        self.assertEqual(restored.state.players["A"].wounds, 2)
        self.assertEqual(len(restored.state.command_history), 3)
