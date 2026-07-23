from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, filename: str):
    sys.path.insert(0, str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


class ReleaseVerifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.release = load("release_verifier_tests", "verify_release.py")

    def test_correct_results_and_deterministic_json(self):
        with patch.object(self.release, "_lockfile", return_value={"status": "ok"}), \
             patch.object(self.release, "_quality", return_value={"status": "ok"}), \
             patch.object(self.release, "verify_simulations", return_value={"simulations": 300}), \
             patch.object(self.release, "verify_persistence", return_value={"roundtrips": 30}), \
             patch.object(self.release, "_package", return_value={"status": "ok"}):
            result = self.release.verify()
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["version"], "0.16.0")
        self.assertEqual(self.release.render(result), self.release.render(json.loads(self.release.render(result))))

    def test_command_errors_propagate(self):
        error = subprocess.CalledProcessError(2, ["mypy"])
        def failing(*args, **kwargs):
            raise error
        with self.assertRaises(subprocess.CalledProcessError) as raised:
            self.release._run(["mypy"], runner=failing)
        self.assertIs(raised.exception, error)


class WheelAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wheel = load("wheel_audit_tests", "verify_reproducible_wheel.py")
        subprocess.run(["uv", "run", "python", "scripts/verify_reproducible_wheel.py"], cwd=ROOT, check=True, capture_output=True)
        cls.original = ROOT / "dist" / cls.wheel.WHEEL_NAME
        cls.wheel.audit(cls.original)

    def mutate(self, transform):
        temporary = tempfile.NamedTemporaryFile(suffix=".whl", delete=False)
        temporary.close()
        destination = Path(temporary.name)
        with ZipFile(self.original) as source, ZipFile(destination, "w", ZIP_DEFLATED) as target:
            entries = [(info.filename, source.read(info.filename)) for info in source.infolist()]
            for name, data in transform(entries):
                from zipfile import ZipInfo
                info = ZipInfo(name)
                info.external_attr = 0o644 << 16
                target.writestr(info, data)
        self.addCleanup(destination.unlink, missing_ok=True)
        return destination

    def assert_rejected(self, transform, message):
        with self.assertRaisesRegex(SystemExit, message):
            self.wheel.audit(self.mutate(transform))

    def test_altered_wheel_and_corrupt_record_are_rejected(self):
        record = f"{self.wheel.DIST_INFO}/RECORD"
        self.assert_rejected(lambda es: [(n, b"altered" if n == record else d) for n, d in es], "RECORD")

    def test_dangerous_and_unexpected_paths_are_rejected(self):
        self.assert_rejected(lambda es: es + [("../secret.key", b"x")], "Contenido divergente")

    def test_runtime_dependency_is_rejected(self):
        metadata = f"{self.wheel.DIST_INFO}/METADATA"
        self.assert_rejected(lambda es: [(n, d + b"Requires-Dist: danger\\n" if n == metadata else d) for n, d in es], "dependencias")

    def test_wrong_version_or_license_is_rejected(self):
        metadata = f"{self.wheel.DIST_INFO}/METADATA"
        self.assert_rejected(lambda es: [(n, d.replace(b"Apache-2.0", b"MIT") if n == metadata else d) for n, d in es], "Versi.n o licencia")

    def test_divergent_zip_order_is_rejected(self):
        self.assert_rejected(lambda es: list(reversed(es)), "Orden ZIP divergente")

    def test_explicit_manifest_rejects_extra_content(self):
        self.assert_rejected(lambda es: es[:-1], "Contenido divergente")


if __name__ == "__main__":
    unittest.main()
