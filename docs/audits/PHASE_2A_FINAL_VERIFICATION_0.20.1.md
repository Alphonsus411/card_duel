# Verificación final de Fase 2-A — 0.20.1

## IMPLEMENTATION SUMMARY

Fase 2-A incorpora una microcolección declarativa, su presentación editorial,
manifiesto, registro y catálogo público, junto con pruebas integrales y
documentación. El rango propio de la fase es
`a3b164f7735f55f37b53808160a56ad54861c7c9..HEAD`; el rango autoritativo total
parte de `0c0f405a77204b6fef046c320f1444f5f0795261`.

## BASE SET SIZE

**8 cartas**, todas criaturas permanentes de rango estándar.

## CARD LIST

`base-c001` Ember Initiate; `base-c002` Grove Sentinel; `base-c003` Skyline
Duelist; `base-c004` Stoneback Warden; `base-c005` Ashen Vanguard; `base-c006`
Verdant Colossus; `base-c007` First Arena Champion; `base-c008` Ancient Grove
Keeper.

## TOKEN SCHEME

Tokens editoriales explícitos, estables y correlativos `BASE-001`…`BASE-008`;
no se derivan de la posición del elemento en el corpus.

## MECHANICAL COVERAGE

Se cubren criaturas ordinarias con costes 1…8, Fuerza base, subtipos y la
keyword general ya existente `CAN_CHALLENGE` en dos cartas. `CardDefinition`
permanece como única autoridad mecánica.

## PRESENTATION COVERAGE

Las ocho definiciones tienen exactamente una `CardPresentation`; tokens e IDs
son únicos, los textos describen sólo mecánicas declaradas y `art` permanece
vacío en todo el corpus.

## MANIFEST RESULT

**PASS.** `BASE_SET_MANIFEST` publica `collection_id="base"`, revisión 1,
versión mínima 0.20.1 y las ocho definiciones, con round-trip sin pérdidas.

## REGISTRY RESULT

**PASS.** El registro publica corpus y procedencia de forma atómica y conserva
su snapshot completo ante una colisión de un lote posterior.

## PUBLIC CATALOG RESULT

**PASS.** El catálogo público une las fuentes mecánica y editorial por
`card_id`, entrega las ocho cartas de forma determinista y produce datos JSON
seguros sin permitir que variantes editoriales alteren las reglas.

## REAL MATCH SMOKE TEST

**PASS.** Las pruebas construyen y validan un mazo real de 40 cartas antes de
crear una partida, y crean otra partida con el manifiesto base a través del
límite público autenticado de aplicación/servicio.

## MECHANICAL GAPS FOUND

**Ninguno.** Las ocho cartas sólo consumen capacidades generales existentes; no
se añadió ningún efecto, resolutor, keyword, persistencia o replay nuevo.

## ENGINE CHANGES

**FAIL de alcance.** El diff autoritativo no toca `engine/`, `application.py`,
`persistence/`, `replay` ni `transport`, pero sí modifica
`rules/__init__.py`, `rules/deck.py`, `domain/models.py`, `service.py` y la
exportación raíz `src/card_duel_engine/__init__.py`. En particular modifica la documentación contractual de
`CardDefinition` para fijar la semántica de puntos y añade políticas/validación
de puntos de mazo en reglas y servicio. Por tanto no es cierto, para el rango completo
solicitado, que Fase 2-A sólo añada contenido, tests y documentación con el único
ajuste permitido en `content/__init__.py`.

## TEST RESULTS

**PASS tras una corrección mínima de test.** La primera ejecución descubrió
una expectativa obsoleta (`points.exceeded`) frente al contrato ya usado
`deck.points_exceeded`: 1 fallo, 685 aprobadas, 1 omitida y 816 subtests. Se
corrigió únicamente esa expectativa. La ejecución final de
`uv run python -m pytest -q` obtuvo **687 passed y 816 subtests passed** en
107,12 s; coverage repitió las 687 pruebas y 816 subtests sin fallos.
`git diff --check` terminó con código 0.

## MYPY RESULT

**PASS.** `uv run python -m mypy src/card_duel_engine`: sin incidencias en 43
archivos fuente, que es el path configurado por `tool.mypy.files`.

## COVERAGE RESULT

**PASS.** `uv run python -m coverage run --branch -m pytest -q` seguido de
`uv run python -m coverage report`: **90 %** sobre 4.431 statements y 1.592
branches, por encima del umbral **88 %**. El informe incluye los módulos nuevos
de contenido; `base_set.py` queda entre los 18 archivos omitidos del detalle por
tener cobertura completa.

## PYTHON 3.11 RESULT

**PASS ejecutado realmente.** `uv sync --python 3.11 --locked --extra dev` y
el perfil runtime terminaron correctamente bajo **CPython 3.11.13**.

## PYTHON 3.12 RESULT

**PASS ejecutado realmente.** `uv sync --python 3.12 --locked --extra dev` y el
perfil runtime terminaron correctamente bajo **CPython 3.12.11**.

## PYTHON 3.13 RESULT

**PASS ejecutado realmente.** `uv sync --python 3.13 --locked --extra dev` y el
perfil runtime terminaron correctamente bajo **CPython 3.13.5**.

## FULL CI RESULT

**PASS.** Se ejecutaron literalmente
`python scripts/verify_release.py --profile runtime` (mediante `uv run`, en el
entorno canónico) y `python scripts/verify_release.py --profile full`. El perfil
full en Python 3.13 terminó con `OK: perfil full completado`; incluye calidad,
fuentes, simulación headless, round-trips de persistencia y auditoría/instalación
del wheel. La matriz runtime local equivalente a CI pasó en 3.11, 3.12 y 3.13.

## VERSION CHECK

**PASS.** Se conserva `0.20.1`; no cambiaron `pyproject.toml`, `uv.lock`,
`CHANGELOG.md`, `_version.py`, dependencias ni metadatos de versión durante
Fase 2-A. No se creó tag.

## OUT-OF-SCOPE CHECK

**PASS.** No se añadieron arte final, frontend, Expo, TypeScript, HTTP,
autenticación nueva, matchmaking, economía, progresión ni despliegue. La
modificación del roadmap es sólo documentación. Una búsqueda de líneas Python
añadidas con IDs concretos y revisión AST de las pruebas halló IDs únicamente
como datos, fixtures, enlaces de catálogo y aserciones; no existe comparación,
tabla de comportamiento ni despacho mecánico basado en un ID concreto.

El baseline autoritativo contiene cinco archivos **preexistentes**, ajenos a
Fase 2-A: el informe final de Fase 1 y cuatro JSON de release bajo
`docs/release-results/0.20.1/`. Separados éstos, el rango posterior incluye los
cambios de contenido y documentación, pero también los cambios de reglas,
dominio, servicio y exportaciones enumerados en `ENGINE CHANGES`; no se los
oculta ni se los reclasifica como preexistentes.

La búsqueda de IDs concretos encontró sus declaraciones como datos y una
aserción de mensaje de error en tests, pero **ninguna comparación ni despacho
mecánico basado en IDs concretos**. Tampoco aparecieron arte final, frontend,
Expo, TypeScript, HTTP, autenticación nueva, matchmaking, economía, progresión,
despliegue, tags, dependencias o cambios de versión.

## ROADMAP STATUS

La microcolección base y su recorrido headless quedan completos, pero la Fase 2
global continúa: no se declara una colección final ni balance competitivo,
deck builder, UI o arte.

## PHASE 2-A VERDICT

**NO-GO — PHASE 2-A NOT CLOSED.** Los controles técnicos pasan, pero el control
obligatorio de alcance falla porque el diff contiene cambios de dominio, reglas,
servicio y exportación raíz fuera de la excepción permitida. En consecuencia no
se emite la frase de cierre `GO — PHASE 2-A COMPLETE`.

## PHASE 2 VERDICT

**PHASE 2 — IN PROGRESS.**
