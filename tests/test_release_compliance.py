from __future__ import annotations

import json
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str, filename: str):
    sys.path.insert(0, str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


class ReleaseMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.metadata = load_script("release_metadata_compliance", "verify_release_metadata.py")

    def make_repository(self, version: str = "0.20.1") -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        (root / "docs").mkdir()
        (root / "pyproject.toml").write_text(
            f'[project]\nname = "card-duel-engine"\nversion = "{version}"\n', encoding="utf-8"
        )
        (root / "uv.lock").write_text(
            f'[[package]]\nname = "card-duel-engine"\nversion = "{version}"\n', encoding="utf-8"
        )
        (root / "CHANGELOG.md").write_text(f"# Changelog\n\n## {version}\n", encoding="utf-8")
        (root / "docs" / f"VALIDATION_{version}.md").write_text(
            f"# Validación candidata {version}\n", encoding="utf-8"
        )
        (root / "README.md").write_text(
            f"# Proyecto\n\n## Alcance de la versión {version}\n\n"
            "Referencia histórica legítima: 0.19.0 y 0.20.0.\n",
            encoding="utf-8",
        )
        return root

    def test_accepts_matching_normative_versions_and_historical_references(self):
        values = self.metadata.verify(self.make_repository())
        self.assertEqual(set(values.values()), {"0.20.1"})
        self.assertEqual(
            set(values),
            {"pyproject", "uv_lock", "changelog", "validation", "readme_scope"},
        )

    def test_rejects_lockfile_drift(self):
        root = self.make_repository()
        (root / "uv.lock").write_text(
            '[[package]]\nname = "card-duel-engine"\nversion = "9.9.9"\n', encoding="utf-8"
        )
        with self.assertRaisesRegex(ValueError, "uv_lock=9.9.9"):
            self.metadata.verify(root)

    def test_rejects_readme_scope_drift(self):
        root = self.make_repository()
        (root / "README.md").write_text(
            "# Proyecto\n\n## Alcance de la versión 0.20.0\n", encoding="utf-8"
        )
        with self.assertRaisesRegex(ValueError, "readme_scope=0.20.0"):
            self.metadata.verify(root)


class RepositorySecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.security = load_script("repository_security_compliance", "verify_repository_security.py")

    def make_rules(self, root: Path) -> Path:
        rules = root / "rules.json"
        rules.write_text(json.dumps({
            "allowed_shell_true": [],
            "excluded_paths": [],
            "secret_patterns": {"private_key": "-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----"},
        }), encoding="utf-8")
        return rules

    def test_accepts_safe_python_and_reports_counts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "safe.py"; source.write_text("value = 1\n", encoding="utf-8")
            with patch.object(self.security, "_tracked_files", return_value=[source]):
                result = self.security.verify(root, self.make_rules(root))
        self.assertEqual(result, {"tracked_files_scanned": 1, "python_files_analyzed": 1})

    def test_rejects_secret_dynamic_execution_and_shell(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "unsafe.py"
            private_key = "-----BEGIN " + "PRIVATE KEY-----"
            source.write_text(
                f'secret = "{private_key}"\n'
                'eval("1")\n'
                'run(["echo"], shell=True)\n',
                encoding="utf-8",
            )
            with patch.object(self.security, "_tracked_files", return_value=[source]), \
                 self.assertRaises(ValueError) as raised:
                self.security.verify(root, self.make_rules(root))
        message = str(raised.exception)
        self.assertIn("secreto potencial", message)
        self.assertIn("ejecución dinámica", message)
        self.assertIn("shell=True", message)


class RollbackProcedureTests(unittest.TestCase):
    def test_procedure_is_non_destructive_and_preserves_persistence(self):
        procedure = (ROOT / "docs" / "RELEASE_ROLLBACK.md").read_text(encoding="utf-8")
        self.assertIn("sha256sum --check SHA256SUMS", procedure)
        self.assertIn("función de *yank*", procedure)
        self.assertIn("versión nueva", procedure)
        self.assertIn("Ningún replay, snapshot, manifiesto", procedure)
        self.assertNotIn("git push --force", procedure)
        self.assertNotIn("rm dist/", procedure)
