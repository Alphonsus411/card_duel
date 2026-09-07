import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROADMAP = ROOT / "docs" / "PHASE_2C_ENGINE_EVOLUTION_ROADMAP.md"
MATRIX = ROOT / "docs" / "ENGINE_CAPABILITY_MATRIX.csv"
DEPENDENCIES = ROOT / "docs" / "ENGINE_CAPABILITY_DEPENDENCIES.md"
CANONICAL_AUDIT = ROOT / "docs" / "FANTASY_TOKENS_BACKEND_GAP_AUDIT.md"
SOURCE_INVENTORY = ROOT / "docs" / "FANTASY_TOKENS_SOURCE_INVENTORY.csv"
READINESS_AUDIT = ROOT / "docs" / "audits" / "PHASE_2C_FIRST_SLICE_READINESS_AUDIT_2026-09-07.md"
TRACEABILITY_AUDIT = ROOT / "docs" / "audits" / "PHASE_2C_FIRST_SLICE_TRACEABILITY_2026-09-07.md"
EXPECTED_SLICE_VERDICT = "N-PHASE-02 IMPLEMENTATION BLOCKED"


def _matrix_rows() -> list[dict[str, str]]:
    with MATRIX.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, strict=True)
        assert reader.fieldnames is not None
        rows = list(reader)
    assert all(None not in row for row in rows), "fila CSV con columnas sobrantes"
    assert all(all(value is not None for value in row.values()) for row in rows)
    return rows


def _first_slice_section(content: str) -> str:
    return content.split("## primer slice", 1)[1].split(
        "## Definition of Done de Phase 2C", 1
    )[0]


def _parse_first_slice(content: str) -> dict[str, str | list[dict[str, str]]]:
    """Parse the deliberately small, machine-readable YAML subset in the roadmap."""
    match = re.search(r"```yaml\n(?P<body>.*?)\n```", content, flags=re.DOTALL)
    assert match, "falta el bloque YAML del primer slice"
    result: dict[str, str | list[dict[str, str]]] = {}
    current_list: list[dict[str, str]] | None = None
    current_item: dict[str, str] | None = None
    for line in match.group("body").splitlines():
        scalar = re.fullmatch(r"([a-z_]+):\s*(\S.*)", line)
        list_start = re.fullmatch(r"([a-z_]+):", line)
        item_start = re.fullmatch(r"  - ([a-z_]+):\s*(\S.*)", line)
        item_field = re.fullmatch(r"    ([a-z_]+):\s*(\S.*)", line)
        if scalar:
            result[scalar.group(1)] = scalar.group(2)
            current_list = None
        elif list_start:
            current_list = []
            result[list_start.group(1)] = current_list
        elif item_start and current_list is not None:
            current_item = {item_start.group(1): item_start.group(2)}
            current_list.append(current_item)
        elif item_field and current_item is not None:
            current_item[item_field.group(1)] = item_field.group(2)
        else:
            raise AssertionError(f"línea YAML no parseable: {line!r}")
    return result


def _capability_gates(content: str) -> dict[str, str]:
    return dict(
        re.findall(
            r"^\| `(CAP-[A-Z]+-\d{3})`[^|]*\| `(?:SUPPORTED|PARTIAL|MISSING|BLOCKED)` \| `(CLOSED|READY|WAIT-PREREQ|NORM-BLOCKED)` \|",
            content,
            flags=re.MULTILINE,
        )
    )


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


def test_first_slice_contract_matches_matrix_and_enforces_authorization_gate() -> None:
    content = ROADMAP.read_text(encoding="utf-8")
    contract = _parse_first_slice(content)
    required = {
        "slice_id", "capability_id", "normative_rule_id", "authorization",
        "status", "gate", "prerequisites", "blockers", "verdict",
    }
    assert required <= contract.keys()

    rows = {row["capability_id"]: row for row in _matrix_rows()}
    gates = _capability_gates(content)
    capability_id = str(contract["capability_id"])
    capability = rows[capability_id]
    assert contract["slice_id"] == contract["normative_rule_id"] == "N-PHASE-02"
    assert contract["normative_rule_id"] in capability["normative_refs"].split(";")
    assert contract["status"] == capability["status"]
    assert contract["gate"] == capability["gate"] == gates[capability_id]
    assert contract["verdict"] == EXPECTED_SLICE_VERDICT

    prerequisites = contract["prerequisites"]
    blockers = contract["blockers"]
    assert isinstance(prerequisites, list) and isinstance(blockers, list)
    expected_prerequisites = capability["prerequisites"].split(";")
    assert [item["capability_id"] for item in prerequisites] == expected_prerequisites
    for prerequisite in prerequisites:
        matrix_row = rows[prerequisite["capability_id"]]
        assert prerequisite["status"] == matrix_row["status"]
        assert prerequisite["gate"] == matrix_row["gate"]
        if prerequisite["capability_id"] in gates:
            assert prerequisite["gate"] == gates[prerequisite["capability_id"]]

    open_prerequisites = {
        item["capability_id"] for item in prerequisites
        if item["status"] != "SUPPORTED" or item["gate"] != "CLOSED"
    }
    technical_blockers = {
        item["blocker_id"] for item in blockers if item["kind"] == "technical"
    }
    normative_blockers = [item for item in blockers if item["kind"] == "normative"]
    assert technical_blockers == open_prerequisites
    assert all(item["status"] == "OPEN" and item["gate"] == "NORM-BLOCKED" for item in normative_blockers)

    authorization = contract["authorization"]
    if authorization == "READY":
        assert not open_prerequisites
        assert not normative_blockers
        assert contract["gate"] == "READY"
    elif authorization == "BLOCKED":
        assert open_prerequisites or normative_blockers
        assert not re.search(
            r"(?im)^\s*(?:se|queda)\s+autoriza(?:do|da)?\s+(?:a\s+)?(?:implementar|modificar\s+el\s+runtime)",
            _first_slice_section(content),
        )
    else:
        raise AssertionError(f"authorization desconocida: {authorization}")


def test_first_slice_supported_transition_cannot_cross_an_open_prerequisite() -> None:
    content = ROADMAP.read_text(encoding="utf-8")
    contract = _parse_first_slice(content)
    prerequisites = contract["prerequisites"]
    assert isinstance(prerequisites, list)
    assert contract["status"] in {"MISSING", "PARTIAL"}
    assert "de `PARTIAL` a\n`SUPPORTED`" in _first_slice_section(content)
    assert "todos sus prerequisites están `CLOSED`" in content

    # A promotion candidate is valid only after every direct edge has reached
    # both the matrix support state and the roadmap's closed gate.
    can_promote = all(
        item["status"] == "SUPPORTED" and item["gate"] == "CLOSED"
        for item in prerequisites
    )
    assert can_promote is (contract["authorization"] == "READY")


def test_dated_first_slice_reports_exist_and_have_the_exact_verdict() -> None:
    contract = _parse_first_slice(ROADMAP.read_text(encoding="utf-8"))
    for report in (READINESS_AUDIT, TRACEABILITY_AUDIT):
        assert report.is_file()
        content = report.read_text(encoding="utf-8")
        verdicts = re.findall(r"^\*\*([^*]+ IMPLEMENTATION (?:READY|BLOCKED))\*\*$", content, re.MULTILINE)
        assert verdicts == [EXPECTED_SLICE_VERDICT]
        assert f"verdict: {EXPECTED_SLICE_VERDICT}" in content
        assert _parse_first_slice(content) == contract


def test_pending_decision_capability_has_minimal_boundary_and_reciprocal_edges() -> None:
    by_id = {row["capability_id"]: row for row in _matrix_rows()}
    decision = by_id["CAP-ACTION-004"]

    assert decision["capability"] == "Decisión pendiente autorizada"
    assert decision["prerequisites"].split(";") == [
        "CAP-ACTION-002",
        "CAP-PRIVACY-001",
    ]
    assert set(decision["dependents"].split(";")) == {
        "CAP-SECRET-002",
        "CAP-TIME-002",
    }
    assert by_id["CAP-TIME-002"]["prerequisites"].split(";") == [
        "CAP-ACTION-004",
        "CAP-TIME-005",
    ]
    assert "CAP-SECRET-002" not in by_id["CAP-TIME-002"]["prerequisites"]
    assert "CAP-ACTION-004" in by_id["CAP-SECRET-002"]["prerequisites"].split(";")

    contract = " ".join((decision["description"], decision["notes"])).lower()
    for required in (
        "decision_id",
        "elector",
        "audiencia",
        "opciones opacas",
        "pendiente/resuelto",
        "autorización",
        "expiración",
        "invalidación por versión",
        "exactamente una vez",
        "persistencia",
        "snapshot",
        "replay",
        "cas",
    ):
        assert required in contract
    for excluded in (
        "candidatos de cartas",
        "cardinalidad",
        "ordenación",
        "selección compuesta",
        "simultaneous reveal",
        "semántica de búsquedas",
    ):
        assert excluded in contract

    roadmap = ROADMAP.read_text(encoding="utf-8")
    dependencies = DEPENDENCIES.read_text(encoding="utf-8")
    for document in (roadmap, dependencies):
        assert "CAP-ACTION-004" in document
        assert "domain/models.py" in document
        assert "persistence/" in document
        assert "application.py" in document
        assert "service.py" in document


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
    generic_contracts = "\n".join(" ".join(row.values()) for row in _matrix_rows())
    assert not re.search(
        r"(?:implementar|handler|dispatch)\s+(?:por|de)?\s*"
        r"(?:card_id|definition_id|identidad)",
        generic_contracts,
        re.I,
    )

    first_slice = _first_slice_section(roadmap)
    assert "no usa defaults normativos" in first_slice
    for forbidden_default in (
        r"prioridad\s+(?:por defecto|default)",
        r"(?:simultaneidad|simultáneo|simultánea)\s+(?:por defecto|default)",
        r"orden\s+multijugador\s+(?:por defecto|default)",
    ):
        assert not re.search(forbidden_default, first_slice, re.I)


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
