"""T0 mantiene explícito el bloqueo del lifecycle de setup."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "audits" / "CAP_TIME_005_T0_SETUP_LIFECYCLE_CONTRACT_2026-10-26.md"


def test_t0_contract_preserves_setup_and_mulligan_boundaries() -> None:
    content = CONTRACT.read_text(encoding="utf-8")

    assert "CAP-TIME-005 / T0" in content
    assert "MISSING / WAIT-PREREQ" in content
    assert "N-PHASE-02" in content
    assert "IMPLEMENTATION BLOCKED" in content
    assert "No se implementa `KEEP`/`REPLACE`" in content
    assert "No se decide orden, alternancia ni simultaneidad" in content
    assert "No se revela decisión" in content
    assert "No se conserva, elige o redetermina jugador inicial" in content
