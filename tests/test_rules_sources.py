from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load_verifier():
    spec = importlib.util.spec_from_file_location("rules_sources_tests", ROOT / "scripts" / "verify_rules_sources.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RulesSourcesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.verifier = load_verifier()

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def source(self, identifier: str, path: str, content: bytes = b"%PDF-test") -> dict[str, object]:
        destination = self.root / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
        return {
            "id": identifier, "path": path, "name": identifier,
            "sha256": hashlib.sha256(content).hexdigest(), "size": len(content), "pages": 1,
            "title": identifier, "declared_date": "2018-01-01", "normative_role": "base",
        }

    def write_manifest(self, sources: list[dict[str, object]]) -> Path:
        path = self.root / "manifest.json"
        path.write_text(json.dumps({"schema_version": 1, "sources": sources}), encoding="utf-8")
        return path

    def assert_rejected(self, source: dict[str, object], diagnostic: str) -> None:
        with self.assertRaisesRegex(self.verifier.RulesSourceError, diagnostic):
            self.verifier.verify(self.write_manifest([source]), self.root)

    def test_valid_temporary_copy(self):
        source = self.source("base", "copy.pdf")
        self.assertEqual(self.verifier.verify(self.write_manifest([source]), self.root), ["OK [base] copy.pdf"])

    def test_rejects_invalid_schema(self):
        source = self.source("base", "copy.pdf")
        manifest = self.write_manifest([source])
        manifest.write_text(json.dumps({"schema_version": 2, "sources": [source]}), encoding="utf-8")
        with self.assertRaisesRegex(self.verifier.RulesSourceError, "schema_version debe ser 1"):
            self.verifier.verify(manifest, self.root)

    def test_rejects_absolute_path(self):
        source = self.source("base", "copy.pdf"); source["path"] = str(self.root / "copy.pdf")
        self.assert_rejected(source, "ruta absoluta rechazada")

    def test_rejects_traversal(self):
        source = self.source("base", "copy.pdf"); source["path"] = "folder/../copy.pdf"
        self.assert_rejected(source, "traversal rechazado")

    def test_rejects_missing_file(self):
        source = self.source("base", "copy.pdf"); (self.root / "copy.pdf").unlink()
        self.assert_rejected(source, "archivo ausente")

    def test_rejects_wrong_hash(self):
        source = self.source("base", "copy.pdf"); source["sha256"] = "0" * 64
        self.assert_rejected(source, "SHA-256 divergente")

    def test_rejects_non_pdf_header(self):
        source = self.source("base", "copy.pdf", b"not-a-pdf")
        self.assert_rejected(source, "cabecera PDF incorrecta")

    def test_output_order_is_stable(self):
        second = self.source("z-source", "z.pdf")
        first = self.source("a-source", "a.pdf")
        output = self.verifier.verify(self.write_manifest([second, first]), self.root)
        self.assertEqual(output, ["OK [a-source] a.pdf", "OK [z-source] z.pdf"])


if __name__ == "__main__":
    unittest.main()
