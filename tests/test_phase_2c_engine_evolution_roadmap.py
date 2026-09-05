import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROADMAP = ROOT / "docs" / "PHASE_2C_ENGINE_EVOLUTION_ROADMAP.md"
MATRIX = ROOT / "docs" / "ENGINE_CAPABILITY_MATRIX.csv"
DEPENDENCIES = ROOT / "docs" / "ENGINE_CAPABILITY_DEPENDENCIES.md"
CANONICAL_AUDIT = ROOT / "docs" / "FANTASY_TOKENS_BACKEND_GAP_AUDIT.md"
SOURCE_INVENTORY = ROOT / "docs" / "FANTASY_TOKENS_SOURCE_INVENTORY.csv"


def _matrix_rows() -> list[dict[str, str]]:
    with MATRIX.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, strict=True)
        assert reader.fieldnames is not None
        rows = list(reader)
    assert all(None not in row for row in rows), "fila CSV con columnas sobrantes"
    assert all(all(value is not None for value in row.values()) for row in rows)
    return rows


def _strongly_connected_components(graph: dict[str, set[str]]) -> list[set[str]]:
    """Return non-trivial Tarjan SCCs without adding a graph dependency."""
    counter = 0
    indices: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    stack: list[str] = []
    on_stack: set[str] = set()
    components: list[set[str]] = []

    def visit(node: str) -> None:
        nonlocal counter
        indices[node] = lowlinks[node] = counter
        counter += 1
        stack.append(node)
        on_stack.add(node)
        for adjacent in graph[node]:
            if adjacent not in indices:
                visit(adjacent)
                lowlinks[node] = min(lowlinks[node], lowlinks[adjacent])
            elif adjacent in on_stack:
                lowlinks[node] = min(lowlinks[node], indices[adjacent])
        if lowlinks[node] == indices[node]:
            component: set[str] = set()
            while node not in component:
                popped = stack.pop()
                on_stack.remove(popped)
                component.add(popped)
            if len(component) > 1:
                components.append(component)

    for node in graph:
        if node not in indices:
            visit(node)
    return components


def test_master_document_has_exact_required_sections_and_phase_status() -> None:
    content = ROADMAP.read_text(encoding="utf-8")
    headings = re.findall(r"^## ([^#].*)$", content, flags=re.MULTILINE)
    assert headings == [
        "Executive summary",
        "estado actual",
        "principios arquitectónicos",
        "capabilities",
        "dependency graph",
        "priorización",
        "waves definitivas",
        "invariantes",
        "ambigüedades/bloqueos",
        "compatibilidad/migración",
        "primer slice",
        "Definition of Done de Phase 2C",
        "condiciones para abrir Phase 3",
    ]
    assert "Phase 2C: `IN PROGRESS`" in content
    assert "Phase 3: `PENDING`" in content
    assert "planificación derivada" in content
    assert "no implementación ni release" in content


def test_capability_csv_ids_states_references_and_traceability() -> None:
    rows = _matrix_rows()
    identifiers = [row["capability_id"] for row in rows]
    assert len(identifiers) == len(set(identifiers))
    assert all(re.fullmatch(r"CAP-[A-Z]+-\d{3}", item) for item in identifiers)
    assert {row["status"] for row in rows} <= {
        "SUPPORTED",
        "PARTIAL",
        "MISSING",
        "BLOCKED",
    }

    audit = CANONICAL_AUDIT.read_text(encoding="utf-8")
    normative_ids = set(re.findall(r"(?<![A-Z0-9-])N-[A-Z]+-\d{2}(?![A-Z0-9-])", audit))
    assert len(normative_ids) == 39
    for row in rows:
        assert row["description"] and row["source_refs"] and row["unlock_basis"]
        assert row["affected_rules"] and row["corpus_direct"] and row["corpus_indirect"]
        assert "docs/" in row["source_refs"]
        for reference in row["normative_refs"].split(";"):
            match = re.fullmatch(r"(N-[A-Z]+-)(\d{2})(?:\.\.(\d{2}))?", reference)
            assert match, f"referencia normativa no parseable: {reference}"
            prefix, start, end = match.groups()
            expanded = {f"{prefix}{number:02d}" for number in range(int(start), int(end or start) + 1)}
            assert expanded <= normative_ids


def test_capability_dependencies_are_existing_reciprocal_and_cycles_explained() -> None:
    rows = _matrix_rows()
    by_id = {row["capability_id"]: row for row in rows}
    graph: dict[str, set[str]] = {}
    for capability_id, row in by_id.items():
        prerequisites = set(filter(None, row["prerequisites"].split(";")))
        dependents = set(filter(None, row["dependents"].split(";")))
        assert prerequisites <= by_id.keys()
        assert dependents <= by_id.keys()
        for prerequisite in prerequisites:
            assert capability_id in by_id[prerequisite]["dependents"].split(";")
        for dependent in dependents:
            assert capability_id in by_id[dependent]["prerequisites"].split(";")
        graph[capability_id] = prerequisites

    assert _strongly_connected_components(graph) == [
        {"CAP-TIME-003", "CAP-TIME-004", "CAP-STACK-001"}
    ]
    explanation = ROADMAP.read_text(encoding="utf-8")
    assert "componente fuertemente conexo (SCC)" in explanation
    assert "`CAP-TIME-003 ↔ CAP-TIME-004 ↔ CAP-STACK-001`" in explanation


def test_documented_totals_defaults_and_generic_capability_boundary() -> None:
    with SOURCE_INVENTORY.open(encoding="utf-8", newline="") as stream:
        inventory = list(csv.DictReader(stream, strict=True))
    card_entries = [
        row
        for row in inventory
        if "texto de cartas" in row["clase_contenido"]
        and row["numero_carta_token"] != "PAGE"
    ]
    assert len(card_entries) == 431

    roadmap = ROADMAP.read_text(encoding="utf-8")
    assert "39/39" in roadmap and "431/431" in roadmap
    assert "Cualquier presupuesto implícito, especialmente 200, 300 o 400" in roadmap
    assert "cero dispatch por identidad" in roadmap
    assert "reglas particulares por carta" in roadmap

    # Las cifras disputadas sólo pueden aparecer como bloqueo, nunca como default.
    for row in _matrix_rows():
        if re.search(r"\b(?:200|300|400)\b", " ".join(row.values())):
            assert row["capability_id"] == "CAP-NORM-002"
            assert row["status"] == "BLOCKED" and row["blocked_by_normative"].startswith("YES")
    assert not any(
        re.search(r"(?:implementar|handler|dispatch).{0,40}(?:card_id|definition_id)", row["description"], re.I)
        for row in _matrix_rows()
    )


def test_roadmap_defines_every_wave_and_required_review_dimension() -> None:
    content = ROADMAP.read_text(encoding="utf-8")

    expected_waves = (
        "W0 — Contractos, versionado e invariantes",
        "W1 — Acciones y costes atómicos",
        "W2 — Tiempo de juego",
        "W3 — Zonas, movimientos y privacidad",
        "W4 — Taxonomía, targeting y selectores",
        "W5 — Estado derivado y permanentes",
        "W6 — Combate y habilidades universales",
        "W7 — Conformidad masiva del corpus",
    )
    required_dimensions = (
        "**Objetivo:**",
        "**Capabilities:**",
        "**Dependencias de entrada:**",
        "**Exclusiones:**",
        "**Normativa relacionada:**",
        "**Desbloqueo directo/indirecto del corpus:**",
        "**Superficies técnicas:**",
        "**Riesgos:**",
        "**Criterios de salida:**",
        "**Categorías de tests:**",
    )

    for index, wave in enumerate(expected_waves):
        start = content.index(f"### {wave}")
        end = (
            content.index(f"### {expected_waves[index + 1]}")
            if index + 1 < len(expected_waves)
            else content.index("## invariantes", start)
        )
        section = content[start:end]
        for dimension in required_dimensions:
            assert dimension in section, f"{wave} no declara {dimension}"


def test_roadmap_keeps_graph_gates_and_release_outside_w7() -> None:
    content = ROADMAP.read_text(encoding="utf-8")

    for constraint in (
        "componente fuertemente conexo (SCC)",
        "`CAP-TIME-003 ↔ CAP-TIME-004 ↔ CAP-STACK-001`",
        "Un nodo `NORM-BLOCKED` permanece fuera",
        "cero dispatch por identidad",
    ):
        assert constraint in content

    normalized = " ".join(content.split())
    assert "no abre la Fase 3" in normalized
    assert "no autoriza publicar cartas" in normalized


def test_w0_defines_impact_matrix_and_versioned_compatibility_gates() -> None:
    content = ROADMAP.read_text(encoding="utf-8")
    w0 = content.split("## compatibilidad/migración", 1)[1].split(
        "## primer slice", 1
    )[0]

    for surface in (
        "`MatchState` / `GameState`",
        "`PlayerState`",
        "`CardDefinition`",
        "`CardInstance`",
        "Comandos",
        "Eventos",
        "Reducers / managers",
        "Stores",
        "SQLite",
        "Snapshots",
        "Replay logs",
        "JSON público",
        "Fronteras de aplicación",
    ):
        assert surface in w0

    for classification in (
        "Adición compatible mediante campo opcional y default exclusivamente técnico",
        "Cambio que requiere nueva versión de snapshot/replay/manifest",
        "Migración explícita de SQLite",
        "Ruptura deliberada y documentada",
        "Detalle interno que no debe entrar en el JSON público",
    ):
        assert classification in w0

    for gate in (
        "tests/artifacts/0.19.0/",
        "tests/artifacts/0.20.x-pre-source-profile/",
        "la semántica histórica de replay no se reinterpreta con reglas",
        "golden files",
        "migración SQLite idempotente",
        "rechazo controlado de versiones",
        "ningún campo interno nuevo aparece en JSON",
        "No diseña todavía",
        "`src/card_duel_engine/persistence/` o",
        "`src/card_duel_engine/storage/`",
    ):
        assert gate in w0
