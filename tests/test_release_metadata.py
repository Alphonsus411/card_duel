import importlib.util
from pathlib import Path
import re
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
