from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MECHANICAL_GAPS = ROOT / "docs" / "PHASE_2_MECHANICAL_GAPS.md"
DECK_POINTS_CONFORMANCE = ROOT / "docs" / "PHASE_2_DECK_POINTS_CONFORMANCE.md"
REQUIRED_HEADINGS = (
    "CARD",
    "DESIRED BEHAVIOR",
    "CURRENT ENGINE LIMITATION",
    "IS GENERAL CAPABILITY?",
    "EVIDENCE",
    "PROPOSED FOLLOW-UP",
    "Conformidad de construcción de mazos",
)
DECK_POINTS_HEADINGS = (
    "Normativa confirmada",
    "Implementación existente",
    "Cambios introducidos",
    "N-POINTS-01",
    "Cost vs deck points",
    "Reglas relacionales",
    "Límites",
)


class Phase2MechanicalGapsDocumentationTests(unittest.TestCase):
    def test_document_exists_and_declares_each_required_heading(self):
        self.assertTrue(MECHANICAL_GAPS.is_file())

        headings = tuple(
            line.removeprefix("## ").strip()
            for line in MECHANICAL_GAPS.read_text(encoding="utf-8").splitlines()
            if line.startswith("## ")
        )

        self.assertEqual(headings, REQUIRED_HEADINGS)

    def test_deck_points_conformance_records_normative_and_technical_boundaries(self):
        self.assertTrue(DECK_POINTS_CONFORMANCE.is_file())
        content = DECK_POINTS_CONFORMANCE.read_text(encoding="utf-8")
        headings = tuple(
            line.removeprefix("## ").strip()
            for line in content.splitlines()
            if line.startswith("## ")
        )

        self.assertEqual(headings, DECK_POINTS_HEADINGS)
        for conclusion in (
            "`CardDefinition.cost` es la fuente\nautoritativa",
            "`classic_deck_policy()` y `mythic_deck_policy()`",
            "`min_points=50`",
            "fuera de\n`DeckConstructionPolicy`",
            "sólo cuando el\nformato la solicita",
            "**`N-POINTS-01` sigue abierto y bloqueado.**",
            "no elige **200, 300, 400 ni ninguna otra cifra Mítica**",
            "físicas 3 y 5",
            "física 2 / interna 1",
        ):
            with self.subTest(conclusion=conclusion):
                self.assertIn(conclusion, content)

    def test_mechanical_gaps_summarizes_deck_conformance(self):
        content = MECHANICAL_GAPS.read_text(encoding="utf-8")
        for conclusion in (
            "ya existía\nde forma embebida",
            "API reusable\n`deck_points()`",
            "necesitaba modelado declarativo",
            "validación separada",
            "ambigüedad normativa, no un defecto de software",
            "`N-POINTS-01`",
        ):
            with self.subTest(conclusion=conclusion):
                self.assertIn(conclusion, content)


if __name__ == "__main__":
    unittest.main()
