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
import shutil
import threading
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


class RepositorySecretPatternTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.security = load("repository_secret_pattern_tests", "verify_repository_security.py")
        cls.rules = ROOT / "config" / "security-rules.json"

    @staticmethod
    def synthetic_fine_grained_token(
        identifier_length: int = 22, secret_length: int = 59
    ) -> bytes:
        """Patrón sintético con forma válida que nunca contiene un secreto real."""
        identifier = "0" * identifier_length
        marker = "INVALIDTESTTOKEN"
        secret = (marker + "X" * secret_length)[:secret_length]
        return ("github" + "_pat_" + identifier + "_" + secret).encode()

    def verify_content(self, content: bytes) -> dict[str, int]:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = root / "candidate.txt"
            candidate.write_bytes(content)
            with patch.object(self.security, "_tracked_files", return_value=[candidate]):
                return self.security.verify(root, self.rules)

    def test_github_fine_grained_token_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "github_fine_grained_token"):
            self.verify_content(self.synthetic_fine_grained_token())

    def test_github_fine_grained_token_with_legitimate_separators_is_rejected(self):
        token = self.synthetic_fine_grained_token()
        for content in (b"(" + token + b")", b"token=" + token + b"\n", token + b","):
            with self.subTest(content=content), \
                 self.assertRaisesRegex(ValueError, "github_fine_grained_token"):
                self.verify_content(content)

    def test_github_pat_prefix_without_credential_shape_is_accepted(self):
        result = self.verify_content(
            b"Documentation mentions github_pat_ but contains no credential.\n"
        )
        self.assertEqual(result["tracked_files_scanned"], 1)

    def test_github_pat_with_short_or_long_segments_is_accepted(self):
        lengths = ((21, 59), (23, 59), (22, 58), (22, 60))
        for identifier_length, secret_length in lengths:
            with self.subTest(
                identifier_length=identifier_length, secret_length=secret_length
            ):
                malformed = self.synthetic_fine_grained_token(
                    identifier_length, secret_length
                )
                result = self.verify_content(malformed)
                self.assertEqual(result["tracked_files_scanned"], 1)

    def test_github_pat_token_with_underscore_suffix_is_accepted_whole(self):
        extended = self.synthetic_fine_grained_token() + b"_extra"
        result = self.verify_content(extended)
        self.assertEqual(result["tracked_files_scanned"], 1)

    def test_synthetic_token_inserted_in_historical_fixture_is_detected(self):
        historical = ROOT / "tests" / "artifacts" / "0.19.0" / "replay-v2.json"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixture = root / historical.relative_to(ROOT)
            fixture.parent.mkdir(parents=True)
            fixture.write_bytes(historical.read_bytes() + self.synthetic_fine_grained_token())
            with patch.object(self.security, "_tracked_files", return_value=[fixture]), \
                 self.assertRaisesRegex(ValueError, "github_fine_grained_token"):
                self.security.verify(root, self.rules)


class ReleaseVerifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.release = load("release_verifier_tests", "verify_release.py")

    def test_correct_results_and_deterministic_json(self):
        with patch.object(self.release, "_lockfile", return_value={"status": "ok"}), \
             patch.object(self.release, "_metadata", return_value={"status": "ok"}), \
             patch.object(self.release, "_security", return_value={"status": "ok"}), \
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
             patch.object(self.release, "_metadata", return_value={"status": "ok"}), \
             patch.object(self.release, "_security", return_value={"status": "ok"}), \
             patch.object(self.release, "_quality", return_value={"status": "ok"}), \
             patch.object(self.release, "verify_simulations") as simulations, \
             patch.object(self.release, "verify_persistence") as persistence, \
             patch.object(self.release, "_rules_sources") as rules_sources, \
             patch.object(self.release, "_package") as package:
            result = self.release.verify("runtime")
        self.assertEqual(result["profile"], "runtime")
        self.assertEqual(result["executed_stages"], ["metadata", "lockfile", "security", "quality"])
        simulations.assert_not_called(); persistence.assert_not_called(); rules_sources.assert_not_called(); package.assert_not_called()

    def test_runtime_never_invokes_build_or_wheel_auditor(self):
        commands: list[list[str]] = []
        forbidden = ("build", "verify_reproducible_wheel", "uv pip install", ".whl", "wheel")

        def runner(command, **kwargs):
            commands.append(command)
            rendered = " ".join(str(part) for part in command).lower()
            for fragment in forbidden:
                if fragment in rendered:
                    self.fail(f"El perfil runtime ejecutó una operación de paquete: {rendered}")
            output = "90" if "--format=total" in command else ""
            return subprocess.CompletedProcess(command, 0, output, "")

        with patch.object(self.release, "_metadata", return_value={"status": "ok"}), \
             patch.object(self.release, "_security", return_value={"status": "ok"}), \
             patch.object(self.release, "verify_simulations") as simulations, \
             patch.object(self.release, "verify_persistence") as persistence, \
             patch.object(self.release, "_package") as package:
            result = self.release.verify("runtime", runner=runner)

        self.assertTrue(commands)
        self.assertEqual(result["executed_stages"], ["metadata", "lockfile", "security", "quality"])
        simulations.assert_not_called()
        persistence.assert_not_called()
        package.assert_not_called()

    def test_full_profile_preserves_package_stage(self):
        stage_result = {"status": "ok"}
        with patch.object(self.release, "_metadata", return_value=stage_result), \
             patch.object(self.release, "_lockfile", return_value=stage_result), \
             patch.object(self.release, "_security", return_value=stage_result), \
             patch.object(self.release, "_quality", return_value=stage_result), \
             patch.object(self.release, "_rules_sources", return_value=stage_result), \
             patch.object(self.release, "verify_simulations", return_value=stage_result), \
             patch.object(self.release, "verify_persistence", return_value=stage_result), \
             patch.object(self.release, "_package", return_value=stage_result) as package:
            result = self.release.verify("full")

        package.assert_called_once()
        self.assertEqual(result["executed_stages"][-1], "package")

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
        self.assertIn("destination / policy.wheel_name", wheel_audit)

        # La selección/copia precede al checksum y a ambos informes; el perfil
        # completo no vuelve a construir después de producir su JSON.
        self.assertLess(wheel_audit.index("shutil.copyfile(first, final_wheel)"),
                        wheel_audit.index('(destination / "SHA256SUMS").write_text'))
        self.assertLess(wheel_audit.index('(destination / "SHA256SUMS").write_text'),
                        wheel_audit.index('(destination / "wheel-audit.json").write_text'))
        self.assertEqual(verifier.count("scripts/verify_reproducible_wheel.py"), 1)

    def test_validation_document_does_not_claim_a_manual_sha_is_final(self):
        validation = (
            ROOT / "docs" / f"VALIDATION_{project_version()}.md"
        ).read_text(encoding="utf-8")
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
        cls.policy = cls.wheel.policy_for(ROOT)
        cls.temporary = tempfile.TemporaryDirectory()
        cls.original = Path(cls.temporary.name) / cls.policy.wheel_name
        content = {}
        for name in cls.policy.canonical_order:
            if name == f"{cls.policy.dist_info}/METADATA":
                data = (
                    f"Metadata-Version: 2.4\nName: card-duel-engine\n"
                    f"Version: {cls.policy.version}\nLicense-Expression: Apache-2.0\n\n"
                    f"## Alcance de la versión {cls.policy.version}\n"
                ).encode()
            elif name == f"{cls.policy.dist_info}/WHEEL":
                data = b"Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n"
            elif name == f"{cls.policy.dist_info}/top_level.txt":
                data = b"card_duel_engine\n"
            elif name.endswith("/RECORD"):
                continue
            else:
                data = (ROOT / "src" / name).read_bytes()
            content[name] = data
        record = io.StringIO(newline="")
        writer = csv.writer(record, lineterminator="\n")
        for name in cls.policy.canonical_order:
            if name.endswith("/RECORD"):
                writer.writerow((name, "", "")); continue
            data = content[name]
            digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
            writer.writerow((name, f"sha256={digest}", len(data)))
        content[f"{cls.policy.dist_info}/RECORD"] = record.getvalue().encode()
        with ZipFile(cls.original, "w", ZIP_DEFLATED) as archive:
            for name in cls.policy.canonical_order:
                from zipfile import ZipInfo
                info = ZipInfo(name); info.external_attr = 0o644 << 16
                archive.writestr(info, content[name])
        cls.wheel.audit(cls.original, cls.policy)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

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
            self.wheel.audit(self.mutate(transform), self.policy)

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
        self.assertIsInstance(self.policy.package_files, frozenset)
        self.assertEqual(python_modules, self.policy.package_files)
        self.assertIn("card_duel_engine/application.py", self.policy.package_files)
        self.assertIn("card_duel_engine/content/signature.py", self.policy.package_files)

    def test_altered_wheel_and_corrupt_record_are_rejected(self):
        record = f"{self.policy.dist_info}/RECORD"
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
        secret = b"-----BEGIN " + b"PRIVATE KEY-----"
        self.assert_rejected(
            lambda es: [(name, secret if name == target else data) for name, data in es],
            "Posible secreto",
        )

    def test_runtime_dependency_is_rejected(self):
        metadata = f"{self.policy.dist_info}/METADATA"
        self.assert_rejected(lambda es: [(n, d + b"Requires-Dist: danger\\n" if n == metadata else d) for n, d in es], "dependencias")

    def test_wrong_version_or_license_is_rejected(self):
        metadata = f"{self.policy.dist_info}/METADATA"
        self.assert_rejected(lambda es: [(n, d.replace(b"Apache-2.0", b"MIT") if n == metadata else d) for n, d in es], "Licencia incorrecta")

    def test_built_wheel_metadata_contains_version_and_current_scope_heading(self):
        report = self.wheel.audit(self.original, self.policy)
        self.assertEqual(report["version"], self.policy.version)

    def test_metadata_without_exact_version_is_rejected(self):
        metadata = f"{self.policy.dist_info}/METADATA"
        expected = f"Version: {self.policy.version}".encode()
        self.assert_rejected(
            lambda entries: [
                (name, data.replace(expected, b"Version: 9.99.9") if name == metadata else data)
                for name, data in entries
            ],
            "versión exacta",
        )

    def test_packed_readme_without_current_scope_heading_is_rejected(self):
        metadata = f"{self.policy.dist_info}/METADATA"
        heading = f"## Alcance de la versión {self.policy.version}".encode()
        self.assert_rejected(
            lambda entries: [
                (name, data.replace(heading, b"## Alcance obsoleto") if name == metadata else data)
                for name, data in entries
            ],
            "README empacado",
        )

    def test_divergent_zip_order_is_rejected(self):
        self.assert_rejected(lambda es: list(reversed(es)), "Orden ZIP divergente")

    def test_explicit_manifest_rejects_extra_content(self):
        self.assert_rejected(lambda es: es[:-1], "Contenido divergente")

    def test_audit_has_mandatory_release_evidence(self):
        report = self.wheel.audit(self.original, self.policy)
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


class DetachedWorktreeBuildTests(unittest.TestCase):
    """Las mutaciones locales nunca cruzan la frontera del worktree de HEAD."""

    @classmethod
    def setUpClass(cls):
        cls.script = ROOT / "scripts" / "verify_reproducible_wheel.py"
        cls.version = project_version()
        cls.wheel_path = ROOT / "dist" / f"card_duel_engine-{cls.version}-py3-none-any.whl"
        cls.commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip()
        cls.epoch = int(subprocess.check_output(
            ["git", "show", "-s", "--format=%ct", cls.commit], cwd=ROOT, text=True
        ).strip())
        cls.baseline_report, cls.baseline_bytes = cls.run_build()

    @classmethod
    def run_build(cls):
        before = subprocess.check_output(
            ["git", "worktree", "list", "--porcelain"], cwd=ROOT, text=True
        )
        completed = subprocess.run(
            [sys.executable, str(cls.script)], cwd=ROOT, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
        )
        after = subprocess.check_output(
            ["git", "worktree", "list", "--porcelain"], cwd=ROOT, text=True
        )
        if before != after:
            raise AssertionError("el script dejó registrado un worktree temporal")
        report = json.loads(completed.stdout.splitlines()[-1])
        return report, cls.wheel_path.read_bytes()

    def assert_immutable_result(self, report, wheel_bytes):
        self.assertEqual(wheel_bytes, self.baseline_bytes)
        for field in ("version", "source_date_epoch", "source_commit", "sha256"):
            self.assertEqual(report[field], self.baseline_report[field])
        self.assertEqual(report["build_source"], "detached-worktree")
        self.assertIs(report["source_tree_clean"], True)
        self.assertIs(report["binary_identical_builds"], True)

    def test_clean_tree_produces_identical_builds_checksum_and_full_audit(self):
        report = self.baseline_report
        self.assertEqual(report["source_commit"], self.commit)
        self.assertEqual(report["source_date_epoch"], self.epoch)
        self.assertEqual(report["runtime_dependencies"], [])
        self.assertTrue(report["record_integrity"])
        self.assertTrue(report["fixtures_absent"])
        self.assertTrue(report["production_cards_absent"])
        self.assertEqual(len(report["pdfs_absent"]), 2)
        checksum = (ROOT / "dist" / "SHA256SUMS").read_text(encoding="utf-8")
        self.assertEqual(checksum, f"{hashlib.sha256(self.baseline_bytes).hexdigest()}  {self.wheel_path.name}\n")
        self.assertEqual(
            json.loads((ROOT / "dist" / "wheel-audit.json").read_text(encoding="utf-8")),
            report,
        )

    def test_modified_tracked_file_does_not_change_release(self):
        target = ROOT / "src" / "card_duel_engine" / "application.py"
        original = target.read_bytes()
        try:
            target.write_bytes(original + b"\n# local tracked mutation\n")
            self.assert_immutable_result(*self.run_build())
        finally:
            target.write_bytes(original)

    def test_modified_pyproject_does_not_change_release_version(self):
        target = ROOT / "pyproject.toml"
        original = target.read_bytes()
        try:
            current = f'version = "{self.version}"'.encode()
            target.write_bytes(original.replace(current, b'version = "9.99.9"'))
            self.assert_immutable_result(*self.run_build())
        finally:
            target.write_bytes(original)

    def test_untracked_source_file_does_not_enter_release(self):
        target = ROOT / "src" / "card_duel_engine" / "local_untracked.py"
        self.assertFalse(target.exists())
        try:
            target.write_text("raise RuntimeError('must not be packaged')\n", encoding="utf-8")
            self.assert_immutable_result(*self.run_build())
        finally:
            target.unlink(missing_ok=True)


class Legacy019ReplayGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = ROOT / "tests" / "artifacts" / "0.19.0" / "generate_legacy_019_replays.py"
        spec = importlib.util.spec_from_file_location("legacy_019_generator_tests", path)
        assert spec is not None and spec.loader is not None
        cls.generator = importlib.util.module_from_spec(spec)
        sys.path.insert(0, str(ROOT / "src"))
        try:
            spec.loader.exec_module(cls.generator)
        finally:
            sys.path.pop(0)
        cls.fixture_names = (
            "drainage-outside-effects.replay-v2.json",
            "challenge-combat.replay-v2.json",
            "attackers-declared.replay-v2.json",
            "challenge-non-realms.replay-v2.json",
            "lord-ability-outside-effects.replay-v2.json",
        )

    def instrumented_runner(self, calls, barrier=None, fail=None):
        def run(command, **kwargs):
            command = tuple(map(str, command))
            calls.append(command)
            if command[:4] == ("git", "worktree", "add", "--detach"):
                worktree = Path(command[4])
                worktree.mkdir(parents=True)
                if barrier is not None:
                    barrier.wait(timeout=5)
                if fail == "add":
                    raise subprocess.CalledProcessError(1, command)
            elif command[:4] == ("git", "worktree", "remove", "--force"):
                shutil.rmtree(command[4], ignore_errors=True)
            elif command and command[0] == sys.executable:
                if fail == "worker":
                    raise subprocess.CalledProcessError(1, command)
            return subprocess.CompletedProcess(command, 0)
        return run

    def test_parallel_runs_use_distinct_paths_and_preserve_preexisting_path(self):
        calls = []
        barrier = threading.Barrier(2)
        errors = []
        preexisting = Path(tempfile.gettempdir()) / "card-duel-019"
        preexisting.mkdir(exist_ok=True)
        sentinel = preexisting / "must-survive"
        sentinel.write_bytes(b"unrelated")
        self.addCleanup(shutil.rmtree, preexisting, ignore_errors=True)

        def invoke():
            try:
                self.generator.run_historical_worker(ROOT)
            except Exception as error:  # pragma: no cover - asserted below
                errors.append(error)

        runner = self.instrumented_runner(calls, barrier)
        with patch.object(self.generator.subprocess, "run", side_effect=runner):
            threads = [threading.Thread(target=invoke) for _ in range(2)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=10)
        self.assertEqual(errors, [])
        additions = [Path(call[4]) for call in calls if call[:4] == ("git", "worktree", "add", "--detach")]
        self.assertEqual(len(additions), 2)
        self.assertNotEqual(additions[0].parent, additions[1].parent)
        self.assertTrue(all(path.name == "worktree" for path in additions))
        self.assertEqual(sentinel.read_bytes(), b"unrelated")
        self.assertTrue(all(not path.parent.exists() for path in additions))

    def test_cleanup_after_add_and_worker_errors(self):
        for failure in ("add", "worker"):
            with self.subTest(failure=failure):
                calls = []
                runner = self.instrumented_runner(calls, fail=failure)
                with patch.object(self.generator.subprocess, "run", side_effect=runner), \
                     self.assertRaises(subprocess.CalledProcessError):
                    self.generator.run_historical_worker(ROOT)
                additions = [Path(call[4]) for call in calls if call[:4] == ("git", "worktree", "add", "--detach")]
                removals = [call for call in calls if call[:4] == ("git", "worktree", "remove", "--force")]
                self.assertEqual(len(removals), 0 if failure == "add" else 1)
                self.assertIn(("git", "worktree", "prune"), calls)
                self.assertFalse(additions[0].parent.exists())

    def test_regenerated_fixtures_are_byte_identical_and_leave_no_worktree(self):
        before = subprocess.check_output(
            ["git", "worktree", "list", "--porcelain"], cwd=ROOT
        )
        artifact_dir = ROOT / "tests" / "artifacts" / "0.19.0"
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            subprocess.run(
                [sys.executable, str(artifact_dir / "generate_legacy_019_replays.py"),
                 "--output", str(output)],
                cwd=ROOT,
                check=True,
            )
            for name in self.fixture_names:
                self.assertEqual((output / name).read_bytes(), (artifact_dir / name).read_bytes())
        after = subprocess.check_output(
            ["git", "worktree", "list", "--porcelain"], cwd=ROOT
        )
        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
