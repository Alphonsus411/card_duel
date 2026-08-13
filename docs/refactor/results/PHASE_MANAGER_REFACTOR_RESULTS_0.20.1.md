# Resultados del refactor de `PhaseManager` — 0.20.1

## Identificación

- Fecha UTC: **2026-08-13**.
- Rama: **`work`**.
- SHA inicial: **`e491ebb4881b1fa16f35f2ca88965fbb0be4e91d`**.
- SHA de implementación: **`98d598b350609d1b5a57dc0253c6d1f73e029529`**.
- SHA del commit documental que contiene esta línea: se obtiene sólo después de
  confirmar el documento y, por tanto, se informa fuera del propio commit; no se
  afirma una autorreferencia imposible.
- Estado: **GO**; la verificación de wheel se repitió sobre el commit de
  implementación.

## Archivos modificados antes de los informes

```text
pyproject.toml
scripts/verify_release.py
src/card_duel_engine/engine/game.py
src/card_duel_engine/engine/phases.py
tests/test_phase_manager_parity.py
tests/test_release_metadata.py
uv.lock
```

Se añaden además los dos informes de esta tarea bajo `docs/refactor/`.

## Diff stat previo a los informes

`git diff --stat HEAD` terminó con código 0 y mostró:

```text
7 files changed, 289 insertions(+), 46 deletions(-)
```

El stat definitivo se registra antes del commit en la sección de revisión.

## Comandos y resultados reales

| Orden | Comando literal | Código | Resultado real |
|---:|---|---:|---|
| 1 | `uv run pytest -q tests/test_phase_manager_parity.py` | 0 | `10 passed in 0.15s` (ejecución final). |
| 2 | `uv sync --locked --extra dev` | 0 | 16 paquetes resueltos; 15 auditados. |
| 3 | `uv run python -m mypy` | 0 | Sin incidencias en 39 archivos fuente. |
| 4 | `uv run python -m compileall -q src tests` | 0 | Sin salida. |
| 5 | `uv run python -m unittest discover -s tests -v` | 0 | `Ran 396 tests in 68.064s`; `OK`. |
| 6 | `uv run python scripts/verify_release.py --profile runtime` | 0 | `OK: perfil runtime completado`. |
| 7 | `uv run python scripts/verify_release.py --profile full --json dist/release-verification.json` | 0 | Estado `ok`; 8 etapas; cobertura 89 %; wheel instalado en Python 3.11, 3.12 y 3.13. |
| 8 | `uv run python scripts/verify_reproducible_wheel.py` | 0 | 2 builds binariamente idénticos; auditoría e integridad RECORD correctas. |
| 9 | `sha256sum 'Fantasy Tokens.pdf' 'Fantasy Tokens Edicion Mitica.pdf'` | 0 | Ambos hashes coinciden con `docs/RULES_SOURCES.json`. |

## Intentos fallidos conservados

| Comando | Código | Diagnóstico y resolución |
|---|---:|---|
| `uv run pytest -q tests/test_phase_manager_parity.py` antes de implementar | 4 | El archivo aún no existía; 0 pruebas. Se creó la prueba, sin alterar artefactos. |
| Primera `uv run python -m unittest discover -s tests -v` | 1 | 396 pruebas, 1 fallo y 1 omitida: el módulo nuevo aún no aparecía entre archivos rastreados usados por la política del wheel. Se añadió al índice; no se cambió snapshot ni expectativa. |
| Primer `uv run python scripts/verify_release.py --profile full --json dist/release-verification.json` | 2 | La CLI rechazaba la ruta literal exigida. Se autorizó sólo `dist/release-verification.json`, manteniendo el rechazo de otras rutas/versiones, y se añadió prueba. |

## Evidencia JSON

`dist/release-verification.json` es evidencia efímera no versionada. Registra
`status=ok`, perfil `full`, etapas `metadata`, `lockfile`, `security`, `quality`,
`rules-sources`, `simulations`, `persistence` y `package`; cobertura total 89 %.

## PDFs normativos

| Archivo | SHA-256 calculado | SHA-256 registrado | Estado |
|---|---|---|---|
| `Fantasy Tokens.pdf` | `1c51dabe2023626ad532368e2567d2084c47ec137c7a738bd8c0e0b707f86b21` | mismo | coincide |
| `Fantasy Tokens Edicion Mitica.pdf` | `61243b30d219dd12d8897a206ed664d95a5e3c38b6670a818933f6d90904af36` | mismo | coincide |

## Observación sobre el wheel antes del commit

El verificador reproducible construye deliberadamente desde un worktree
separado de `HEAD`. Antes del commit informó `source_commit=e491ebb...`, por lo
que acredita el mecanismo y la base, no todavía los bytes nuevos que estaban en
el índice. Tras crear el commit de implementación se repetirá el comando y se
registrará su SHA y resultado en un segundo commit exclusivamente documental,
sin afirmar una autorreferencia imposible.

## Evidencia postcommit de implementación

Sobre `HEAD=98d598b350609d1b5a57dc0253c6d1f73e029529` se repitieron, ambos con
código 0:

- `uv run pytest -q tests/test_phase_manager_parity.py`: `10 passed in 0.16s`.
- `uv run python scripts/verify_reproducible_wheel.py`: dos builds idénticos,
  **43 archivos** (incluido `card_duel_engine/engine/phases.py`), RECORD íntegro,
  `source_tree_clean=true`, `source_commit=98d598b...` y SHA-256 del wheel
  **`a497c8dc0881af750413de213b93856e26764f632638a67439f1e59ff68f1ae7`**.

## Revisión previa al commit

Los cuatro controles terminaron con código 0. `git diff --check HEAD` no produjo
salida; `git diff --stat HEAD` registró **9 archivos, 502 inserciones y 46
eliminaciones**; `git status --short` mostró los dos documentos y los dos
módulos/pruebas nuevos, junto con cinco archivos modificados, todos esperados.
Se leyó el diff completo con `git diff --cached --no-ext-diff --unified=3`; no
aparecieron snapshots, fixtures, PDF ni artefactos de `dist` versionados.
