from __future__ import annotations

import ast
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
PACKAGE = ROOT / "src" / "card_duel_engine"
TRACEABILITY = DOCS / "RULES_TRACEABILITY.md"
LEGACY_REPLAY_README = ROOT / "tests" / "artifacts" / "0.19.0" / "README.md"

TRACEABILITY_DECISIONS = {
    "ya cumple",
    "requiere prueba",
    "requiere corrección",
    "bloqueada",
    "sólo documentación",
}


def traceability_decisions() -> dict[str, str]:
    text = TRACEABILITY.read_text(encoding="utf-8")
    matrix = text.split("## Matriz de decisiones base–Mítica (R-03B)", 1)[1]
    matrix = matrix.split("\n## ", 1)[0]
    rows: dict[str, str] = {}
    for line in matrix.splitlines():
        if not (
            line.startswith("| R-")
            or line.startswith("| N-")
            or line.startswith("| M-")
        ):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        rows[cells[0]] = cells[-1]
    return rows


STALE_DOCUMENTATION = {
    "ausencia del PDF Mítico": re.compile(
        r"(?:PDF|reglamento)[^\n.]{0,40}M[ií]tic[oa][^\n.]{0,50}"
        r"(?:no (?:est[aá]|se encuentra)|ausente|no disponible)",
        re.IGNORECASE,
    ),
    "referencia Mítica sin paginación física/interna": re.compile(
        r"(?:M[ií]tic[oa]|PDF M[ií]tico)[^\n]{0,50}"
        r"(?:p\.|página)\s*\d+",
        re.IGNORECASE,
    ),
    "presupuesto de puntos presentado como definitivo": re.compile(
        r"(?:mazo|baraja)[^\n.]{0,60}"
        r"(?:es|ser[aá]|debe (?:tener|sumar))\s+(?:de\s+)?(?:200|300|400)\s+puntos",
        re.IGNORECASE,
    ),
    "cartas Míticas declaradas parte del paquete": re.compile(
        r"(?:paquete|card_duel_engine)[^\n.]{0,60}"
        r"(?:incluye|contiene|incorpora|trae)[^\n.]{0,30}cartas? M[ií]ticas?",
        re.IGNORECASE,
    ),
    "Desafío actual restringido exclusivamente a Reinos": re.compile(
        r"(?:actualmente|backend actual)[^\n.]{0,80}"
        r"(?:exige|requiere)[^\n.]{0,30}(?:dominio )?Reinos",
        re.IGNORECASE,
    ),
}


def stale_claims(text: str) -> list[str]:
    return [label for label, pattern in STALE_DOCUMENTATION.items() if pattern.search(text)]


class MythicDocumentationTests(unittest.TestCase):
    def test_traceability_decision_column_uses_closed_vocabulary(self):
        decisions = traceability_decisions()
        self.assertTrue(decisions)
        self.assertEqual(
            {identifier: value for identifier, value in decisions.items()
             if value not in TRACEABILITY_DECISIONS},
            {},
        )

    def test_traceability_includes_replay_and_keeps_debts_blocked(self):
        decisions = traceability_decisions()
        self.assertEqual(decisions["R-COMPAT-019-REPLAY"], "ya cumple")
        self.assertEqual(decisions["N-POINTS-01"], "bloqueada")
        self.assertEqual(decisions["M-LORD-EVENT-01"], "bloqueada")

    def test_detector_recognizes_each_obsolete_claim(self):
        examples = {
            "El PDF Mítico no está disponible en este repositorio.",
            "Según el reglamento Mítico, p. 3, cambia la inmunidad.",
            "La baraja debe tener 300 puntos.",
            "El paquete incluye las cartas Míticas.",
            "Actualmente Desafío exige dominio Reinos.",
        }
        detected = {claim for example in examples for claim in stale_claims(example)}
        self.assertEqual(detected, set(STALE_DOCUMENTATION))

    def test_repository_documentation_has_no_obsolete_mythic_claims(self):
        failures: list[str] = []
        for path in sorted(
            (*DOCS.glob("*.md"), ROOT / "README.md", LEGACY_REPLAY_README)
        ):
            for claim in stale_claims(path.read_text(encoding="utf-8")):
                failures.append(f"{path.relative_to(ROOT)}: {claim}")
        self.assertEqual(failures, [])

    def test_production_package_contains_no_concrete_card_definitions(self):
        calls: list[str] = []
        for path in sorted(PACKAGE.rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and (
                    isinstance(node.func, ast.Name) and node.func.id == "CardDefinition"
                    or isinstance(node.func, ast.Attribute)
                    and node.func.attr == "CardDefinition"
                ):
                    calls.append(f"{path.relative_to(ROOT)}:{node.lineno}")
        self.assertEqual(calls, [], "Las cartas concretas deben llegar como datos de colección")

    def test_production_package_bundles_no_catalog_data_files(self):
        catalog_suffixes = {".csv", ".json", ".pdf", ".tsv", ".yaml", ".yml"}
        data_files = [
            str(path.relative_to(ROOT))
            for path in sorted(PACKAGE.rglob("*"))
            if path.is_file() and path.suffix.lower() in catalog_suffixes
        ]
        self.assertEqual(data_files, [], "No se deben empaquetar catálogos concretos")


if __name__ == "__main__":
    unittest.main()
