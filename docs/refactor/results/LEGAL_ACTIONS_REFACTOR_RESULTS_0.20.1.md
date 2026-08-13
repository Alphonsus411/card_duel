# Evidencia del refactor de acciones legales — 0.20.1

Fecha de ejecución: **2026-08-12 (UTC)**. Todos los resultados de este informe
proceden de ejecuciones nuevas en el checkout actual. No se dedujo ningún dato
de `docs/release-results/`.

Las secciones desde **Base y árbol inicial** hasta **Comprobaciones ausentes**
son la fotografía histórica tomada en `0d28bb8cbb664f9a7353b512667e539e9d80ff1f`,
antes de redactar e integrar los informes. Sus comandos, salidas, códigos y
conteos se conservan literalmente; no describen por sí solos el diff definitivo
de toda la refactorización. La sección **Estado final post-merge** documenta por
separado la situación después de integrar el commit documental.

## Base y árbol inicial

| Comando literal | Código de salida | Resultado/conteo literal |
|---|---:|---|
| `git merge-base --is-ancestor 952b1759371eb9c591c7601d906547de4f508449 HEAD` | 0 | La base sí es ancestro. |
| `git rev-parse HEAD` | 0 | `0d28bb8cbb664f9a7353b512667e539e9d80ff1f` |
| `git status --short` | 0 | 0 líneas; árbol limpio antes de redactar estos informes. |

## Archivos cambiados desde la base validada

El comando literal
`git diff --name-only 952b1759371eb9c591c7601d906547de4f508449..HEAD`
terminó con código **0** y devolvió **4 archivos**:

```text
docs/refactor/LEGAL_ACTIONS_REFACTOR_0.20.1.md
src/card_duel_engine/engine/actions.py
src/card_duel_engine/engine/game.py
tests/test_legal_action_enumerator_parity.py
```

El comando literal
`git diff --stat 952b1759371eb9c591c7601d906547de4f508449..HEAD`
terminó con código **0** y registró **4 archivos cambiados, 1011 inserciones y
125 eliminaciones**:

```text
 docs/refactor/LEGAL_ACTIONS_REFACTOR_0.20.1.md |  43 ++
 src/card_duel_engine/engine/actions.py         | 200 +++++++
 src/card_duel_engine/engine/game.py            | 150 +----
 tests/test_legal_action_enumerator_parity.py   | 743 +++++++++++++++++++++++++
 4 files changed, 1011 insertions(+), 125 deletions(-)
```

Tras redactar la evidencia se añaden además, en el commit documental, estos
archivos cambiados: `docs/refactor/LEGAL_ACTIONS_DIAGNOSTIC_0.20.1.md`,
`docs/refactor/LEGAL_ACTIONS_REFACTOR_0.20.1.md` y
`docs/refactor/results/LEGAL_ACTIONS_REFACTOR_RESULTS_0.20.1.md`.

## Conteo de líneas inspeccionado

`wc -l src/card_duel_engine/engine/actions.py src/card_duel_engine/engine/game.py tests/test_legal_action_enumerator_parity.py`
terminó con código **0**:

```text
   200 src/card_duel_engine/engine/actions.py
  2446 src/card_duel_engine/engine/game.py
   743 tests/test_legal_action_enumerator_parity.py
  3389 total
```

## Comprobaciones aprobadas

| Comando literal | Código | Resultado literal |
|---|---:|---|
| `uv sync --locked --extra dev` | 0 | 10 paquetes instalados. |
| `env PYTHONPATH=src uv run --with pytest pytest -q tests/test_legal_action_enumerator_parity.py` | 0 | `36 passed in 0.34s` |
| `env PYTHONPATH=src uv run --with pytest pytest -q` | 0 | `432 passed, 711 subtests passed in 74.27s (0:01:14)` |
| `uv run mypy src` | 0 | `Success: no issues found in 38 source files` |
| `uv run python -m compileall -q src tests` | 0 | Sin salida. |

## Intentos fallidos (no ocultados)

| Comando literal | Código | Resultado literal |
|---|---:|---|
| `uv run python -m unittest tests.test_legal_action_enumerator_parity` | 1 | 1 prueba intentada; error de importación: `No module named 'pytest'`. |
| `uv run pytest -q tests/test_legal_action_enumerator_parity.py` | 2 | Recolección interrumpida; `No module named 'card_duel_engine'`. |
| `uv run python -m unittest discover -s tests` (antes de sincronizar el extra dev) | 1 | `Ran 393 tests in 20.934s`; 3 errores y 1 omitida. |
| `uv run python -m unittest discover -s tests` (después de sincronizar el extra dev) | 1 | `Ran 397 tests in 74.356s`; 1 error (`pytest` no importable por unittest) y 1 omitida. |

Los dos problemas de entorno/importación se resolvieron para la comprobación
válida usando el ejecutor pytest explícito, dependencia efímera `--with pytest`
y `PYTHONPATH=src`; no se reinterpretaron los intentos fallidos como aprobados.

## Comprobaciones ausentes

- `uv run python scripts/verify_release.py --profile runtime`: **NO EJECUTADO**.
- `uv run python scripts/verify_release.py --profile full`: **NO EJECUTADO**.
- Matriz separada Python 3.11/3.12/3.13: **NO EJECUTADO**.
- Construcción reproducible del wheel como comando independiente: **NO EJECUTADO**.
- Simulaciones headless como comando independiente: **NO EJECUTADO**.
- Persistencia/roundtrips como comando independiente: **NO EJECUTADO**.
- Captura visual: **NO APLICA**; la refactorización no modifica interfaces visuales.

## Estado final post-merge

Después de integrar `ff08956` mediante el merge `c6d614e`, el historial real
desde la base validada
`952b1759371eb9c591c7601d906547de4f508449` deja finalmente integrados estos
seis archivos:

```text
docs/refactor/LEGAL_ACTIONS_DIAGNOSTIC_0.20.1.md
docs/refactor/LEGAL_ACTIONS_REFACTOR_0.20.1.md
docs/refactor/results/LEGAL_ACTIONS_REFACTOR_RESULTS_0.20.1.md
src/card_duel_engine/engine/actions.py
src/card_duel_engine/engine/game.py
tests/test_legal_action_enumerator_parity.py
```

Esta lista post-merge es la que representa el diff final de la refactorización;
la lista de cuatro archivos anterior pertenece exclusivamente a la fotografía
intermedia registrada antes de crear los informes.
