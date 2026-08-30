# Validación final de acciones legales — 0.20.1

## Identificación de la ejecución

- **SHA evaluado:** `d7de285010712c23de4cadbefc3e1b26ed5ab39b`.
- **Rama:** `work`.
- **Fecha UTC:** `2026-08-13T06:51:12Z`.
- **Base histórica de la extracción:**
  `952b1759371eb9c591c7601d906547de4f508449`.
- `git merge-base --is-ancestor
  952b1759371eb9c591c7601d906547de4f508449 HEAD` terminó con código **0**:
  la base histórica es ancestro del SHA evaluado.

La secuencia se ejecutó desde la raíz del repositorio y se detuvo de inmediato
al primer fallo, según el criterio solicitado. Ninguna comprobación no
ejecutada se presenta como satisfactoria.

## Comandos ejecutados y códigos de salida

| Orden | Comando exacto | Código | Resumen verificable de la salida real |
|---:|---|---:|---|
| 1 | `uv sync --locked --extra dev` | 0 | Resolución de 12 paquetes; preparación e instalación de 10 paquetes. Entre los instalados figuran `build==1.5.0`, `coverage==7.15.2` y `mypy==2.3.0`; no se instaló `pytest`. |
| 2 | `uv run python -m mypy` | 0 | `Success: no issues found in 38 source files`. |
| 3 | `uv run python -m compileall -q src tests` | 0 | Sin salida de diagnóstico; terminó con código cero. |
| 4 | `uv run python -m unittest discover -s tests -v` | 1 | `Ran 397 tests in 102.633s` y `FAILED (errors=1, skipped=1)`. El único error fue la importación de `test_legal_action_enumerator_parity`: `ModuleNotFoundError: No module named 'pytest'`. |

No cambió ninguno de los comandos oficiales solicitados: el bloque
**Desarrollo reproducible** de `README.md` contiene literalmente y en el mismo
orden los siete comandos de esta validación. Por ello no se aplicó ningún
reemplazo de comando.

## Resultado de las pruebas

La salida real de `unittest`, y no un conteo de archivos, registra un total de
**397 tests**. El desglose es:

- **395 superados**: total 397 menos 1 error y 1 omitido;
- **0 fallidos por aserción**;
- **1 error de carga/importación**;
- **1 omitido**.

El conjunto de pruebas, como comprobación global, **no es satisfactorio** porque
el proceso terminó con código 1.

## Mypy y compilación de bytecode

- **mypy: satisfactorio**; código 0, sin incidencias en 38 archivos fuente.
- **compileall: satisfactorio**; código 0 y sin salida de error para `src` y
  `tests`.

## Verificaciones de release

| Comprobación | Comando exacto | Estado |
|---|---|---|
| Runtime | `uv run python scripts/verify_release.py --profile runtime` | **NO EJECUTADA** por la regla de parada tras el fallo de `unittest`. |
| Full/JSON | `uv run python scripts/verify_release.py --profile full --json dist/release-verification.json` | **NO EJECUTADA** por la regla de parada. No se generó evidencia JSON nueva. |
| Wheel reproducible | `uv run python scripts/verify_reproducible_wheel.py` | **NO EJECUTADA** por la regla de parada. |

En consecuencia, no se atribuye un resultado satisfactorio a las verificaciones
runtime, full ni de reproducibilidad del wheel.

## Archivos modificados frente a la base histórica

Antes de crear este informe,
`git diff --name-only
952b1759371eb9c591c7601d906547de4f508449..HEAD` terminó con código 0 y mostró
estos seis archivos integrados desde la base:

```text
docs/refactor/LEGAL_ACTIONS_DIAGNOSTIC_0.20.1.md
docs/refactor/LEGAL_ACTIONS_REFACTOR_0.20.1.md
docs/refactor/results/LEGAL_ACTIONS_REFACTOR_RESULTS_0.20.1.md
src/card_duel_engine/engine/actions.py
src/card_duel_engine/engine/game.py
tests/test_legal_action_enumerator_parity.py
```

El `git diff --stat` correspondiente registró **6 archivos cambiados, 1285
inserciones y 125 eliminaciones**. Este informe añade como séptimo archivo
documental
`docs/refactor/results/LEGAL_ACTIONS_FINAL_VALIDATION_0.20.1.md`; no modifica la
implementación evaluada.

## Incidencia y clasificación

La incidencia es **funcional/de configuración del repositorio**, no una
limitación exclusivamente ambiental demostrable:

1. `tests/test_legal_action_enumerator_parity.py` contiene un `import pytest` a
   nivel de módulo.
2. El extra oficial `dev` de `pyproject.toml` declara solamente `build`,
   `coverage` y `mypy`.
3. `uv.lock` confirma esos mismos tres componentes para el extra `dev`.
4. La sincronización oficial terminó correctamente, pero la ejecución oficial
   con `unittest` no pudo importar el módulo de pruebas por la ausencia de
   `pytest`.

No se instaló una dependencia adicional ni se cambió de ejecutor para convertir
el fallo en un aprobado. Hacerlo habría dejado de validar la secuencia oficial
exacta.

## Estado final del repositorio y trabajo no iniciado

Al comenzar la validación, `git status --short` no produjo líneas y la rama era
`work`. La única modificación deliberada de esta tarea es el presente informe;
los comandos ejecutados no modificaron archivos versionados. Tras registrar y
confirmar este documento, el árbol debe quedar limpio en la misma rama.

No se inició ningún diagnóstico implementable de `PhaseManager`. El fallo de la
secuencia permanece sin resolver y ha sido identificado como no exclusivamente
ambiental, por lo que se mantiene expresamente el bloqueo solicitado.

## Comprobaciones no ejecutadas

Además de las tres verificaciones de release detalladas arriba, no se ejecutaron
comandos alternativos con `pytest`, no se repitió `unittest` con dependencias
efímeras y no se inició ninguna prueba o modificación de `PhaseManager`. La
parada después del código 1 fue intencional.
