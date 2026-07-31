import importlib.util
from pathlib import Path
import re
import tomllib
import unittest

import card_duel_engine
from card_duel_engine.rules.config import RuleSet


ROOT = Path(__file__).resolve().parents[1]


class ReleaseMetadataTests(unittest.TestCase):
    def test_public_and_rules_versions_are_in_sync(self):
        self.assertEqual(card_duel_engine.__version__, "0.19.0")
        self.assertEqual(RuleSet().version, card_duel_engine.__version__)

    def test_wheel_audit_targets_the_universal_release_wheel(self):
        path = ROOT / "scripts" / "verify_reproducible_wheel.py"
        spec = importlib.util.spec_from_file_location("wheel_audit", path)
        self.assertIsNotNone(spec)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.WHEEL_NAME, "card_duel_engine-0.19.0-py3-none-any.whl")

    def test_completed_roadmap_deliveries_are_not_described_as_next(self):
        roadmap = (ROOT / "docs" / "ROADMAP.md").read_text(encoding="utf-8")
        completed_section = roadmap.split("## Entregas completadas", 1)[1].split(
            "## Pendientes normativos bloqueados", 1
        )[0]
        completed_deliveries = set(re.findall(r"^### (R-\d{2})\b", completed_section, re.MULTILINE))
        self.assertTrue(completed_deliveries)

        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        current_version = project["project"]["version"]
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        current_changelog = changelog.split(f"## {current_version}", 1)[1].split("\n## ", 1)[0]
        current_metadata = "\n".join(
            ((ROOT / "README.md").read_text(encoding="utf-8"), current_changelog)
        )

        for delivery in completed_deliveries:
            with self.subTest(delivery=delivery):
                described_as_next = re.compile(
                    rf"(?:{delivery}.{{0,120}}\bsiguiente\b|\bsiguiente\b.{{0,120}}{delivery})",
                    re.DOTALL | re.IGNORECASE,
                )
                self.assertNotRegex(current_metadata, described_as_next)


if __name__ == "__main__":
    unittest.main()
