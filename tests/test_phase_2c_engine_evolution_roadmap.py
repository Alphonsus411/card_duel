from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROADMAP = ROOT / "docs" / "PHASE_2C_ENGINE_EVOLUTION_ROADMAP.md"


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
            else content.index("## Diferencias justificadas", start)
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
