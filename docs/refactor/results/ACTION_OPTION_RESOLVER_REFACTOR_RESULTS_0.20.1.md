# Resultados del refactor de `ActionOptionResolver` — 0.20.1

## Identificación

- Fecha UTC: **2026-08-13**.
- Rama de cierre: **`refactor/action-option-resolver`**.
- SHA base de la verificación de cierre: **`8538dcdd57dfa8c741e5f058ffb69eb4cb5f6494`**.
- SHA de extracción de implementación: **`5e3b7b9af0907d997515676c733e8a76ac729ce4`**.
- SHA de paridad final de implementación: **`2c8a18789d742c242017a8df9afb209b94c1e0d4`**.
- SHA de cierre documental: se registra tras crear el commit final de evidencia, ya
  que el documento no puede contener de forma autorreferente el SHA del commit que
  lo incorpora. Ambos identificadores se distinguen también en la pull request.
- Decisión: **GO**.

## Archivos cambiados y frontera

La iniciativa de extracción quedó idealmente limitada a:

```text
src/card_duel_engine/engine/options.py
src/card_duel_engine/engine/game.py
tests/test_action_option_resolver_parity.py
docs/refactor/ACTION_OPTION_RESOLVER_DIAGNOSTIC_0.20.1.md
docs/refactor/ACTION_OPTION_RESOLVER_REFACTOR_0.20.1.md
docs/refactor/results/ACTION_OPTION_RESOLVER_REFACTOR_RESULTS_0.20.1.md
```

En esta verificación de cierre, el árbol partió limpio en el merge `8538dcd`; la
implementación, las pruebas y los informes ya estaban integrados. La corrección de
evidencia no toca snapshots, fixtures, PDF, codec, replay ni persistencia.

## `git diff --stat`

Tras añadir los documentos al índice, `git diff --cached --stat HEAD` terminó con
código 0 y mostró:

```text
2 files changed, 283 insertions(+)
```

## Comandos y resultados exactos

| Orden | Comando literal | Código | Resultado observado |
|---:|---|---:|---|
| 1 | `git status --short --branch` | 0 | `## work`; árbol inicial limpio. |
| 2 | `git rev-parse HEAD` | 0 | `ac9bb1db3b6749dde21ed8ebb536f65c04daec0f`. |
| 3 | `sha256sum 'Fantasy Tokens.pdf' 'Fantasy Tokens Edicion Mitica.pdf'` | 0 | Los dos hashes coinciden con la línea base (tabla inferior). |
| 4 | `uv run pytest -q tests/test_action_option_resolver_parity.py` | 2 | Falló en colección: `ModuleNotFoundError: No module named 'card_duel_engine'`; 1 error en 0.25 s. |
| 5 | `uv sync --locked --extra dev` | 0 | 16 paquetes resueltos; 14 preparados e instalados. |
| 6 | `uv run pytest -q tests/test_action_option_resolver_parity.py` | 0 | `93 passed in 1.26s`. |
| 7 | `uv run coverage erase && uv run coverage run --branch -m pytest -q tests/test_action_option_resolver_parity.py && uv run coverage report --format=total` | 2 | Las 93 pruebas pasaron en 2.54 s; cobertura aislada 38 %, inferior al `fail-under=88`. |
| 8 | `uv run python scripts/verify_release.py --profile full --json dist/action-option-resolver-verification.json` | 2 | La CLI rechazó la ruta: la evidencia debe estar bajo `docs/release-results/0.20.1` o ser `dist/release-verification.json`. |
| 9 | `uv run python scripts/verify_release.py --profile full --json dist/release-verification.json` | 0 | `status=ok`; 8 etapas; cobertura 89 %; 300 simulaciones, 54 000 comandos, 84 000 eventos y 30 roundtrips. |

## Cobertura

La cobertura aislada de la prueba diferencial fue **38 %**, una medición esperable
para un único módulo pero insuficiente para la política global; se registra como
intento fallido y no como cobertura del proyecto. El perfil full ejecutó la suite de
calidad bajo branch coverage y registró **89 %**, por encima del mínimo de 88 %.
Mypy y compileall también terminaron correctamente.

## Matriz Python y paquete

| Python | Instalación del wheel | Resultado |
|---|---|---|
| 3.11 | ejecutada por el perfil full | OK |
| 3.12 | ejecutada por el perfil full | OK |
| 3.13 | ejecutada por el perfil full | OK |

El wheel reproducible `card_duel_engine-0.20.1-py3-none-any.whl` produjo dos builds
binariamente idénticos, 44 archivos, RECORD íntegro y ausencia de fixtures, cartas de
producción y PDF. SHA-256 final del wheel:
`94943da745b602cd1ed82c9125935f5638c309b28eff9ff35e222c2375e8d636`.
La comprobación posterior al commit documental construyó desde el `HEAD` limpio
`0466303d4aa60957ba085df64e3e798cceb432b4`; informó
`binary_identical_builds=true`, `builds_compared=2`, `source_tree_clean=true` y
`source_commit=0466303d4aa60957ba085df64e3e798cceb432b4`. La inspección independiente
del ZIP confirmó `card_duel_engine/engine/options.py`, 44 entradas y la ausencia de
`Fantasy Tokens.pdf` y `Fantasy Tokens Edicion Mitica.pdf`.

## Hashes de PDF

| Archivo | SHA-256 | Estado |
|---|---|---|
| `Fantasy Tokens.pdf` | `1c51dabe2023626ad532368e2567d2084c47ec137c7a738bd8c0e0b707f86b21` | coincide; no modificado |
| `Fantasy Tokens Edicion Mitica.pdf` | `61243b30d219dd12d8897a206ed664d95a5e3c38b6670a818933f6d90904af36` | coincide; no modificado |

## Fallos, omisiones y resolución

1. **Entorno sin sincronizar:** el primer pytest no pudo importar el paquete. Se
   ejecutó `uv sync --locked --extra dev` y la repetición pasó; no se cambió código.
2. **Cobertura aislada insuficiente:** el 38 % no representa la suite integral. No se
   relajó el umbral; se ejecutó el perfil full, que obtuvo 89 %.
3. **Ruta JSON inválida:** el primer perfil full se rechazó por política antes de
   verificar. Se repitió con la ruta permitida exacta, sin modificar la política.
4. **Omisiones:** no se ejecutó una matriz pytest separada por intérprete; la matriz
   solicitada está acreditada por la instalación del wheel del perfil full. No se
   realizó una prueba manual/UI porque el cambio es documentación interna y no hay
   cambio perceptible en una aplicación web.
5. `dist/release-verification.json` es evidencia efímera ignorada y no se incluye en
   el commit.

## Replay, legacy, privacidad y persistencia

El perfil full aprobó las etapas `simulations` y `persistence`, incluidos 30
roundtrips, y la suite integral ejercitó replay, perfiles históricos y privacidad.
La prueba diferencial específica parametriza `CURRENT` y `LEGACY_019`, compara el
estado serializado antes/después de las consultas y protege el orden exacto de
acciones legales. `ActionOptionResolver` sólo conserva `_context`, usa el mismo
`GameState` y no participa en snapshots, codec, replay ni persistencia.

## Revisión final previa al commit

`git diff --check HEAD` terminó con código 0 y sin salida. Después de añadir los dos
documentos, `git diff --cached --stat HEAD` registró **2 archivos y 283 inserciones**;
`git status --short` mostró exactamente
`A  docs/refactor/ACTION_OPTION_RESOLVER_REFACTOR_0.20.1.md` y
`A  docs/refactor/results/ACTION_OPTION_RESOLVER_REFACTOR_RESULTS_0.20.1.md`. Se leyó
el diff indexado completo; no contiene código, snapshots, fixtures, PDF ni artefactos
de `dist`. El SHA resultante no se escribe retroactivamente aquí: se informa en el
chat y en la metainformación de la pull request.


## Cierre reproducible posterior al commit de procedencia

1. El commit descriptivo previo a construir el wheel fue
   `780765c467c5ca9e3952a1836961813fefd6de69`; corrigió la procedencia histórica sin
   alterar el código de producción.
2. El primer intento de `uv run python scripts/verify_reproducible_wheel.py` terminó
   con código 1 porque `.venv` no contenía el módulo `build`; no fue un fallo del
   código ni modificó archivos versionados.
3. `uv sync --locked --extra dev` terminó con código 0 e instaló las dependencias
   bloqueadas de desarrollo.
4. La repetición exacta anterior al cierre terminó con código 0. Tras el commit
   documental se repitió de nuevo con código 0: dos wheels binariamente idénticos y SHA-256
   `94943da745b602cd1ed82c9125935f5638c309b28eff9ff35e222c2375e8d636`.
5. Una construcción independiente con el mismo `SOURCE_DATE_EPOCH` y una lectura con
   `zipfile` reprodujeron el hash, confirmaron `card_duel_engine/engine/options.py` y
   que ninguno de los dos PDF aparece entre las 44 entradas.
6. El SHA de código de la extracción conservadora es
   `5e3b7b9af0907d997515676c733e8a76ac729ce4`, con paridad final en
   `2c8a18789d742c242017a8df9afb209b94c1e0d4`. El commit que incorpora esta sección
   será el **SHA de cierre documental** y se registra externamente para evitar una
   referencia circular.
