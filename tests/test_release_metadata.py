import importlib.util
from pathlib import Path
import unittest

import card_duel_engine
from card_duel_engine.rules.config import RuleSet


ROOT = Path(__file__).resolve().parents[1]


class ReleaseMetadataTests(unittest.TestCase):
    def test_public_and_rules_versions_are_in_sync(self):
        self.assertEqual(card_duel_engine.__version__, "0.18.2")
        self.assertEqual(RuleSet().version, card_duel_engine.__version__)

    def test_wheel_audit_targets_the_universal_release_wheel(self):
        path = ROOT / "scripts" / "verify_reproducible_wheel.py"
        spec = importlib.util.spec_from_file_location("wheel_audit", path)
        self.assertIsNotNone(spec)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.WHEEL_NAME, "card_duel_engine-0.18.2-py3-none-any.whl")


if __name__ == "__main__":
    unittest.main()
