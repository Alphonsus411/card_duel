import importlib.util
from pathlib import Path
import re
import json
import subprocess
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch
import zipfile

import card_duel_engine
from card_duel_engine.rules.config import RuleSet


ROOT = Path(__file__).resolve().parents[1]
HISTORICAL_0200_COMMIT = "006534eb9acc3b0e2fc67e409938ec5724e99077"
RELEASE_RESULT_NAMES = {
    "full-python-3.13.json",
    "runtime-python-3.11.json",
    "runtime-python-3.12.json",
    "runtime-python-3.13.json",
}


def project_version():
    with (ROOT / "pyproject.toml").open("rb") as stream:
        return tomllib.load(stream)["project"]["version"]


class ReleaseMetadataTests(unittest.TestCase):
    def test_archived_release_results_are_valid_and_match_their_directory(self):
        results = ROOT / "docs" / "release-results"
        self.assertEqual({path.name for path in results.iterdir() if path.is_dir()}, {"0.20.0", "0.20.1"})
        for directory in sorted(path for path in results.iterdir() if path.is_dir()):
            self.assertEqual({path.name for path in directory.glob("*.json")}, RELEASE_RESULT_NAMES)
            for path in directory.glob("*.json"):
                with self.subTest(path=path.relative_to(ROOT)):
                    document = json.loads(path.read_bytes())
                    self.assertEqual(document["version"], directory.name)
                    if document["profile"] == "full":
                        expected = f"card_duel_engine-{directory.name}-py3-none-any.whl"
                        package = document["package"]
                        self.assertEqual(package["audit"]["filename"], expected)
                        if "wheel" in package:
                            self.assertEqual(package["wheel"], expected)

    def test_0200_results_are_the_exact_bytes_from_the_last_matching_commit(self):
        for name in sorted(RELEASE_RESULT_NAMES):
            with self.subTest(name=name):
                historical = subprocess.run(
                    ["git", "show", f"{HISTORICAL_0200_COMMIT}:docs/release-results/{name}"],
                    cwd=ROOT,
                    check=True,
                    capture_output=True,
                ).stdout
                self.assertEqual(
                    (ROOT / "docs" / "release-results" / "0.20.0" / name).read_bytes(),
                    historical,
                )

    def test_release_verifier_rejects_another_version_result_directory(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        try:
            import verify_release
        finally:
            sys.path.pop(0)
        accepted = verify_release.release_result_path(
            f"docs/release-results/{project_version()}/runtime-python-3.13.json"
        )
        self.assertEqual(accepted.parent.name, project_version())
        with self.assertRaisesRegex(ValueError, project_version()):
            verify_release.release_result_path(
                "docs/release-results/0.20.0/runtime-python-3.13.json"
            )

    def test_public_and_rules_versions_are_in_sync(self):
        self.assertEqual(card_duel_engine.__version__, project_version())
        self.assertEqual(RuleSet().version, card_duel_engine.__version__)

    def test_release_version_is_consistent_across_declared_surfaces(self):
        expected = project_version()
        lock = (ROOT / "uv.lock").read_text(encoding="utf-8")
        package = re.search(
            r'\[\[package\]\]\nname = "card-duel-engine"\nversion = "([^"]+)"',
            lock,
        )
        self.assertIsNotNone(package)
        assert package is not None
        self.assertEqual(package.group(1), expected)

        documents = {
            "README.md": f"## Alcance de la versión {expected}",
            "CHANGELOG.md": f"## {expected}",
            f"docs/VALIDATION_{expected}.md": (
                f"# Validación candidata de la entrega {expected}"
            ),
        }
        for relative, marker in documents.items():
            with self.subTest(document=relative):
                self.assertIn(marker, (ROOT / relative).read_text(encoding="utf-8"))

    def test_built_wheel_filename_and_metadata_match_project_version(self):
        expected = project_version()
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            subprocess.run(
                [sys.executable, "-m", "build", "--wheel", "--outdir", str(output)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            wheels = list(output.glob("*.whl"))
            self.assertEqual(
                [wheel.name for wheel in wheels],
                [f"card_duel_engine-{expected}-py3-none-any.whl"],
            )
            with zipfile.ZipFile(wheels[0]) as archive:
                metadata_names = [
                    name for name in archive.namelist() if name.endswith(".dist-info/METADATA")
                ]
                self.assertEqual(len(metadata_names), 1)
                metadata = archive.read(metadata_names[0]).decode("utf-8")
            self.assertIn("Name: card-duel-engine\n", metadata)
            self.assertIn(f"Version: {expected}\n", metadata)

    def resolve_from_tree(self, root, pyproject=None, *, installed="0.18.0"):
        from card_duel_engine import _version

        source_file = root / "src" / "card_duel_engine" / "_version.py"
        source_file.parent.mkdir(parents=True)
        source_file.touch()
        if pyproject is not None:
            (root / "pyproject.toml").write_text(pyproject, encoding="utf-8")

        with (
            patch.object(_version, "__file__", str(source_file)),
            patch.object(_version.metadata, "version", return_value=installed) as metadata_version,
        ):
            result = _version.resolve_version()
        return result, metadata_version

    def test_checkout_version_is_preferred_over_installed_metadata(self):
        with tempfile.TemporaryDirectory() as temporary:
            result, installed = self.resolve_from_tree(
                Path(temporary), '[project]\nversion = "0.19.0"\n'
            )

        self.assertEqual(result, "0.19.0")
        installed.assert_not_called()

    def test_wheel_install_without_pyproject_uses_distribution_metadata(self):
        with tempfile.TemporaryDirectory() as temporary:
            result, installed = self.resolve_from_tree(Path(temporary))

        self.assertEqual(result, "0.18.0")
        installed.assert_called_once_with("card-duel-engine")

    def test_missing_checkout_and_distribution_propagates_package_not_found(self):
        from card_duel_engine import _version

        with tempfile.TemporaryDirectory() as temporary:
            wheel_file = Path(temporary) / "site-packages" / "card_duel_engine" / "_version.py"
            wheel_file.parent.mkdir(parents=True)
            wheel_file.touch()
            with (
                patch.object(_version, "__file__", str(wheel_file)),
                patch.object(
                    _version.metadata,
                    "version",
                    side_effect=_version.metadata.PackageNotFoundError("card-duel-engine"),
                ),
                self.assertRaises(_version.metadata.PackageNotFoundError),
            ):
                _version.resolve_version()

    def test_invalid_checkout_toml_is_not_hidden(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(tomllib.TOMLDecodeError):
                self.resolve_from_tree(Path(temporary), "[project\nversion =")

    def test_checkout_requires_project_version(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(RuntimeError, "project.version"):
                self.resolve_from_tree(Path(temporary), "[project]\nname = 'example'\n")

    def test_checkout_rejects_non_textual_project_version(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "debe ser texto"):
                self.resolve_from_tree(Path(temporary), "[project]\nversion = 19\n")

    def test_unexpected_metadata_errors_are_not_hidden(self):
        from card_duel_engine._version import resolve_version

        with (
            patch("card_duel_engine._version.Path.is_file", return_value=False),
            patch("card_duel_engine._version.metadata.version", side_effect=RuntimeError("metadata")),
            self.assertRaisesRegex(RuntimeError, "metadata"),
        ):
            resolve_version()

    def test_all_release_version_consumers_read_current_project_version(self):
        expected = project_version()
        self.assertEqual(project_version(), expected)
        self.assertEqual(card_duel_engine.__version__, expected)
        self.assertEqual(RuleSet().version, expected)

        sys.path.insert(0, str(ROOT / "scripts"))
        try:
            from project_metadata import read_project_version
            import verify_release
            import verify_reproducible_wheel
        finally:
            sys.path.pop(0)

        self.assertEqual(read_project_version(ROOT), expected)
        self.assertEqual(verify_release.VERSION, expected)
        self.assertEqual(verify_reproducible_wheel.policy_for(ROOT).version, expected)

    def test_wheel_audit_targets_the_universal_release_wheel(self):
        path = ROOT / "scripts" / "verify_reproducible_wheel.py"
        spec = importlib.util.spec_from_file_location("wheel_audit", path)
        self.assertIsNotNone(spec)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.path.insert(0, str(ROOT / "scripts"))
        try:
            spec.loader.exec_module(module)
        finally:
            sys.path.pop(0)
        self.assertEqual(
            module.policy_for(ROOT).wheel_name,
            f"card_duel_engine-{project_version()}-py3-none-any.whl",
        )

    def test_current_documents_agree_on_completed_roadmap_deliveries(self):
        roadmap = (ROOT / "docs" / "ROADMAP.md").read_text(encoding="utf-8")
        completed_section = roadmap.split("## Entregas completadas", 1)[1].split(
            "## Pendientes normativos bloqueados", 1
        )[0]
        completed_deliveries = set(
            re.findall(r"^### (R-\d{2}(?:\.\d+)?)\b", completed_section, re.MULTILINE)
        )
        self.assertTrue(completed_deliveries)

        traceability = (ROOT / "docs" / "RULES_TRACEABILITY.md").read_text(
            encoding="utf-8"
        )
        # Las secciones numeradas son fotografías históricas de cada versión, no
        # declaraciones del estado actual de la hoja de ruta.
        current_traceability = re.sub(
            r"^## Trazabilidad \d.*?(?=^## |\Z)",
            "",
            traceability,
            flags=re.DOTALL | re.MULTILINE,
        )
        current_documents = {
            "README.md": (ROOT / "README.md").read_text(encoding="utf-8"),
            "docs/ROADMAP.md": roadmap,
            "docs/RULES_TRACEABILITY.md": current_traceability,
        }

        for delivery in completed_deliveries:
            milestone = rf"{re.escape(delivery)}(?![\d.])"
            contradictory_status = re.compile(
                rf"(?:{milestone}.{{0,80}}\b(?:queda|sigue|continúa|trabajo|tarea|"
                rf"incremento)\b.{{0,40}}\b(?:pendiente|futur[oa]|habilitad[oa]|"
                rf"siguiente)\b|\b(?:pendiente|futur[oa]|habilitad[oa]|siguiente)"
                rf"\b.{{0,40}}{milestone})",
                re.DOTALL | re.IGNORECASE,
            )
            for document, content in current_documents.items():
                with self.subTest(delivery=delivery, document=document):
                    self.assertNotRegex(content, contradictory_status)

        # R-07.2 es el cierre que debe declarar de forma coincidente cada fuente
        # de estado vigente; el changelog se excluye porque conserva historia.
        self.assertIn("R-07.2", completed_deliveries)
        completion = re.compile(
            r"R-07\.2.{0,160}\b(?:completad[ao]s?|cerrad[ao]s?)\b|"
            r"\b(?:completad[ao]s?|cerrad[ao]s?)\b.{0,160}R-07\.2",
            re.DOTALL | re.IGNORECASE,
        )
        for document, content in current_documents.items():
            with self.subTest(delivery="R-07.2", document=document, state="completed"):
                self.assertRegex(content, completion)


if __name__ == "__main__":
    unittest.main()
