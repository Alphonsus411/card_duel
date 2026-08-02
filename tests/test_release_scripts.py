from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
import unittest
import base64
import csv
import hashlib
import io
import re
from unittest.mock import patch
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]


def project_version():
    with (ROOT / "pyproject.toml").open("rb") as stream:
        return tomllib.load(stream)["project"]["version"]


def active_packaging_versions(workflow: str) -> set[str]:
    """Devuelve versiones literales solo del bloque activo de subida del job full."""
    full_job = workflow.split("\n  full:\n", 1)[1]
    upload = full_job.split("actions/upload-artifact@", 1)[1]
    return set(re.findall(r"(?<![A-Za-z0-9])([0-9]+\.[0-9]+\.[0-9]+)(?![A-Za-z0-9])", upload))


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
             patch.object(self.release, "_rules_sources", return_value={"status": "ok"}), \
             patch.object(self.release, "_package", return_value={"status": "ok"}):
            result = self.release.verify("full")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["version"], project_version())
        self.assertIn("rules-sources", result["executed_stages"])
        self.assertEqual(self.release.render(result), self.release.render(json.loads(self.release.render(result))))

    def test_runtime_profile_skips_expensive_stages(self):
        with patch.object(self.release, "_lockfile", return_value={"status": "ok"}), \
             patch.object(self.release, "_quality", return_value={"status": "ok"}), \
             patch.object(self.release, "verify_simulations") as simulations, \
             patch.object(self.release, "verify_persistence") as persistence, \
             patch.object(self.release, "_rules_sources") as rules_sources, \
             patch.object(self.release, "_package") as package:
            result = self.release.verify("runtime")
        self.assertEqual(result["profile"], "runtime")
        self.assertEqual(result["executed_stages"], ["lockfile", "quality"])
        simulations.assert_not_called(); persistence.assert_not_called(); rules_sources.assert_not_called(); package.assert_not_called()

    def test_runtime_never_invokes_build_or_wheel_auditor(self):
        commands = []
        def runner(command, **kwargs):
            commands.append(command)
            output = "90" if "--format=total" in command else ""
            return subprocess.CompletedProcess(command, 0, output, "")
        with patch.object(self.release, "verify_simulations"), \
             patch.object(self.release, "verify_persistence"):
            self.release.verify("runtime", runner=runner)
        flattened = [part for command in commands for part in command]
        self.assertNotIn("build", flattened)
        self.assertNotIn("scripts/verify_reproducible_wheel.py", flattened)

    def test_command_errors_propagate(self):
        def failing(*args, **kwargs):
            return subprocess.CompletedProcess(["mypy"], 2, "type output", "type error")
        with self.assertRaises(self.release.VerificationStageError) as raised:
            self.release._run(["mypy"], stage="quality:mypy", runner=failing)
        self.assertEqual(raised.exception.returncode, 2)
        self.assertIn("quality:mypy", raised.exception.diagnostic())
        self.assertIn("type output", raised.exception.diagnostic())
        self.assertIn("type error", raised.exception.diagnostic())

    def test_release_workflow_derives_active_package_paths_from_project_version(self):
        workflow = (ROOT / ".github" / "workflows" / "tests.yml").read_text(encoding="utf-8")
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        version = project["project"]["version"]

        self.assertIn("id: package", workflow)
        self.assertIn("from scripts.project_metadata import read_project_version", workflow)
        self.assertIn("version = read_project_version(Path.cwd())", workflow)
        self.assertIn('output.write(f"version={version}\\n")', workflow)
        self.assertIn('output.write(f"wheel=card_duel_engine-{version}-py3-none-any.whl\\n")', workflow)
        self.assertIn("name: card-duel-engine-${{ steps.package.outputs.version }}-release", workflow)
        self.assertIn("dist/${{ steps.package.outputs.wheel }}", workflow)
        self.assertEqual(active_packaging_versions(workflow), set())

        # Una mención histórica fuera del bloque de subida no es empaquetado activo.
        historical = f"# test_historical_release_0.1.0\n{workflow}"
        self.assertEqual(active_packaging_versions(historical), set())
        mismatched = workflow.replace(
            "dist/${{ steps.package.outputs.wheel }}",
            "dist/card_duel_engine-9.99.9-py3-none-any.whl",
        )
        self.assertEqual(active_packaging_versions(mismatched), {"9.99.9"})

        full_job = workflow.split("\n  full:\n", 1)[1]
        upload = full_job.split("actions/upload-artifact@", 1)[1]
        expected_paths = {
            "dist/${{ steps.package.outputs.wheel }}",
            "dist/SHA256SUMS",
            "dist/wheel-audit.json",
            "dist/release-verification.json",
        }
        upload_lines = {line.strip() for line in upload.splitlines()}
        uploaded = {line for line in upload_lines if line.startswith("dist/")}
        self.assertEqual(uploaded, expected_paths)
        self.assertIn("if-no-files-found: error", upload)
        self.assertIn("--json dist/release-verification.json", full_job)

        verifier = (ROOT / "scripts" / "verify_release.py").read_text(encoding="utf-8")
        wheel_audit = (ROOT / "scripts" / "verify_reproducible_wheel.py").read_text(encoding="utf-8")
        self.assertIn('(ROOT / "dist" / "wheel-audit.json").read_text', verifier)
        self.assertIn('(destination / "SHA256SUMS").write_text', wheel_audit)
        self.assertIn('(destination / "wheel-audit.json").write_text', wheel_audit)
        self.assertIn("destination / WHEEL_NAME", wheel_audit)

        # La selección/copia precede al checksum y a ambos informes; el perfil
        # completo no vuelve a construir después de producir su JSON.
        self.assertLess(wheel_audit.index("shutil.copyfile(first, final_wheel)"),
                        wheel_audit.index('(destination / "SHA256SUMS").write_text'))
        self.assertLess(wheel_audit.index('(destination / "SHA256SUMS").write_text'),
                        wheel_audit.index('(destination / "wheel-audit.json").write_text'))
        self.assertEqual(verifier.count("scripts/verify_reproducible_wheel.py"), 1)

    def test_validation_document_does_not_claim_a_manual_sha_is_final(self):
        validation = (ROOT / "docs" / "VALIDATION_0.20.1.md").read_text(encoding="utf-8")
        sha = r"[0-9a-f]{64}"
        forbidden = re.compile(
            rf"(?:hash final|artefacto definitivo).{{0,160}}{sha}|"
            rf"{sha}.{{0,160}}(?:hash final|artefacto definitivo)",
            re.IGNORECASE | re.DOTALL,
        )
        self.assertNotRegex(validation, forbidden)
        self.assertIn("candidato local", validation)


class WheelAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wheel = load("wheel_audit_tests", "verify_reproducible_wheel.py")
        temporary = tempfile.NamedTemporaryFile(suffix=".whl", delete=False)
        temporary.close()
        cls.original = Path(temporary.name)
        content = {}
        for name in cls.wheel.CANONICAL_ORDER:
            if name == f"{cls.wheel.DIST_INFO}/METADATA":
                data = f"Metadata-Version: 2.4\nName: card-duel-engine\nVersion: {cls.wheel.VERSION}\nLicense-Expression: Apache-2.0\n".encode()
            elif name == f"{cls.wheel.DIST_INFO}/WHEEL":
                data = b"Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n"
            elif name == f"{cls.wheel.DIST_INFO}/top_level.txt":
                data = b"card_duel_engine\n"
            elif name.endswith("/RECORD"):
                continue
            else:
                data = (ROOT / "src" / name).read_bytes()
            content[name] = data
        record = io.StringIO(newline="")
        writer = csv.writer(record, lineterminator="\n")
        for name in cls.wheel.CANONICAL_ORDER:
            if name.endswith("/RECORD"):
                writer.writerow((name, "", "")); continue
            data = content[name]
            digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
            writer.writerow((name, f"sha256={digest}", len(data)))
        content[f"{cls.wheel.DIST_INFO}/RECORD"] = record.getvalue().encode()
        with ZipFile(cls.original, "w", ZIP_DEFLATED) as archive:
            for name in cls.wheel.CANONICAL_ORDER:
                from zipfile import ZipInfo
                info = ZipInfo(name); info.external_attr = 0o644 << 16
                archive.writestr(info, content[name])
        cls.wheel.audit(cls.original)

    @classmethod
    def tearDownClass(cls):
        cls.original.unlink(missing_ok=True)

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

    def test_package_policy_matches_tracked_python_modules(self):
        tracked = subprocess.check_output(
            ["git", "ls-files", "--", "src/card_duel_engine"],
            cwd=ROOT,
            text=True,
        ).splitlines()
        package_prefix = "src/card_duel_engine/"
        python_modules = {
            path.removeprefix("src/")
            for path in tracked
            if path.startswith(package_prefix)
            and path.endswith(".py")
            and ".." not in Path(path).parts
            and "\\" not in path
        }
        self.assertIsInstance(self.wheel.PACKAGE_FILES, frozenset)
        self.assertEqual(python_modules, self.wheel.PACKAGE_FILES)
        self.assertIn("card_duel_engine/application.py", self.wheel.PACKAGE_FILES)
        self.assertIn("card_duel_engine/content/signature.py", self.wheel.PACKAGE_FILES)

    def test_altered_wheel_and_corrupt_record_are_rejected(self):
        record = f"{self.wheel.DIST_INFO}/RECORD"
        self.assert_rejected(lambda es: [(n, b"altered" if n == record else d) for n, d in es], "RECORD")

    def test_dangerous_path_is_rejected(self):
        self.assert_rejected(lambda es: es + [("../escape.py", b"x")], "Ruta peligrosa")

    def test_unexpected_entry_is_rejected(self):
        self.assert_rejected(lambda es: es + [("card_duel_engine/extra.py", b"x")], "Contenido divergente")

    def test_test_module_is_rejected(self):
        self.assert_rejected(lambda es: es + [("card_duel_engine/tests/test_extra.py", b"x")], "Ruta peligrosa")

    def test_database_is_rejected(self):
        self.assert_rejected(lambda es: es + [("card_duel_engine/data.sqlite", b"x")], "Ruta peligrosa")

    def test_both_primary_rule_pdfs_are_rejected(self):
        for filename in ("Fantasy Tokens.pdf", "Fantasy Tokens Edicion Mitica.pdf"):
            with self.subTest(filename=filename):
                self.assert_rejected(
                    lambda entries, name=filename: entries
                    + [(f"card_duel_engine/{name}", b"not packaged")],
                    "Ruta peligrosa",
                )

    def test_secret_is_rejected(self):
        target = "card_duel_engine/__init__.py"
        secret = b"-----BEGIN PRIVATE KEY-----"
        self.assert_rejected(
            lambda es: [(name, secret if name == target else data) for name, data in es],
            "Posible secreto",
        )

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

    def test_audit_has_mandatory_release_evidence(self):
        report = self.wheel.audit(self.original)
        required = {
            "version", "filename", "sha256", "files", "record_integrity",
            "runtime_dependencies", "tag", "root_is_purelib", "pdfs_absent",
            "fixtures_absent", "production_cards_absent",
        }
        self.assertTrue(required.issubset(report))
        self.assertEqual(report["version"], project_version())
        self.assertEqual(report["runtime_dependencies"], [])
        self.assertEqual(set(report["pdfs_absent"]), {
            "Fantasy Tokens.pdf", "Fantasy Tokens Edicion Mitica.pdf"
        })


if __name__ == "__main__":
    unittest.main()
