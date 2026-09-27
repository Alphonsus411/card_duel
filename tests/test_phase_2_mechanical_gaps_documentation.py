from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MECHANICAL_GAPS = ROOT / "docs" / "PHASE_2_MECHANICAL_GAPS.md"
REQUIRED_HEADINGS = (
    "CARD",
    "DESIRED BEHAVIOR",
    "CURRENT ENGINE LIMITATION",
    "IS GENERAL CAPABILITY?",
    "EVIDENCE",
    "PROPOSED FOLLOW-UP",
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

    def test_challenge_gap_is_explicit_and_phase_is_not_claimed_complete(self):
        gap_text = MECHANICAL_GAPS.read_text(encoding="utf-8")
        roadmap = (ROOT / "docs" / "FRONTEND_AND_CONTENT_ROADMAP.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("un gap requerido", gap_text)
        self.assertIn("devuelve `False` antes de consultar `CAN_CHALLENGE`", gap_text)
        self.assertIn("Fase 2-A — IN PROGRESS", roadmap)
        self.assertNotIn("Fase 2-A — COMPLETE", roadmap)


if __name__ == "__main__":
    unittest.main()
