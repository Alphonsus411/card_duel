# Auditoría de contrato de CAP-ACTION-004 — 2026-09-07

## Fase 1 — Baseline

### Evidencia Git previa a la edición

La inspección se realizó antes de crear este documento. El punto de partida
esperado y el observado coinciden:

| Comprobación | Evidencia observada |
| --- | --- |
| SHA esperado | `9543806234a1b5af47dc1e40514323b2c5fc4324` |
| `HEAD` real | `9543806234a1b5af47dc1e40514323b2c5fc4324` |
| Rama activa | `work` |
| Referencia local `main` | No existe `refs/heads/main` en este checkout. |
| Referencia remota `origin/main` | No existe `refs/remotes/origin/main`; el checkout tampoco tiene remotos configurados. |
| Árbol de trabajo inicial | Limpio (`git status --porcelain=v1` no produjo entradas). |

Se consultaron explícitamente tanto la referencia local como la remota antes de
editar. Al no existir ninguna referencia `main`, no hay un extremo adicional
contra el que enumerar `9543806...main`. Como comprobación local equivalente,
`git rev-list --count 9543806234a1b5af47dc1e40514323b2c5fc4324..HEAD`
devolvió `0`; por tanto, la lista de commits intermedios es **vacía** y no hay
ningún commit posterior que evaluar por impacto sobre CAP-ACTION-004.

### Versión y metadatos

La comprobación estática confirma la versión **`0.20.1`**:

- `pyproject.toml` declara `project.version = "0.20.1"`.
- La entrada `card-duel-engine` de `uv.lock` declara `version = "0.20.1"`.
- `card_duel_engine.__version__` se asigna mediante `resolve_version()`; en un
  checkout, ese resolvedor lee y devuelve de forma explícita
  `project.version` desde `pyproject.toml`. No existe un segundo literal de
  versión del paquete que contradiga el metadato canónico.
- `CHANGELOG.md` conserva la sección de release `0.20.1`.

### Estados de planificación

La lectura estática de las dos fuentes solicitadas confirma los mismos estados:

| Documento | Phase 2C | Phase 3 |
| --- | --- | --- |
| `docs/PHASE_2C_ENGINE_EVOLUTION_ROADMAP.md` | `IN PROGRESS` | `PENDING` |
| `docs/ROADMAP.md` | `IN PROGRESS` | `PENDING` |

### Estado de CAP-ACTION-004

La fila `CAP-ACTION-004` de `docs/ENGINE_CAPABILITY_MATRIX.csv` conserva:

- estado de soporte: **`MISSING`**;
- estado de readiness: **`READY`**.

La fila sigue describiendo el contrato universal de decisión pendiente y no
presenta la capability como implementada.

### Veredicto de baseline

**`BASELINE VALID`**

El SHA real coincide exactamente con el esperado, no hay commits intermedios,
la versión y los metadatos permanecen en `0.20.1`, las fases conservan sus
estados y CAP-ACTION-004 continúa `MISSING / READY`. La ausencia de referencias
`main` se registra como una limitación del checkout, no como drift sustantivo:
el propio `HEAD` es exactamente el punto de partida exigido y el árbol inicial
estaba limpio. En consecuencia, no corresponde emitir **`CAP-ACTION-004
CONTRACT BLOCKED`** por la Fase 1.
