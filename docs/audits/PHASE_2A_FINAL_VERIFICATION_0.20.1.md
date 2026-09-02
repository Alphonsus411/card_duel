# Verificación final de Fase 2-A — 0.20.1

## IMPLEMENTATION SUMMARY

Fase 2-A incorpora una microcolección declarativa, su presentación editorial,
manifiesto, registro y catálogo público, junto con pruebas integrales y
documentación. El rango histórico e inmutable propio de la fase es
`a3b164f7735f55f37b53808160a56ad54861c7c9..82a6b5b433b623590d7c21ad9e6d41a56ab0fc1`;
el rango autoritativo total parte de
`0c0f405a77204b6fef046c320f1444f5f0795261`.

Ese rango real de implementación de 2-A contiene `docs/BASE_CARD_SET.md`, la
documentación de gaps y del baseline, `src/card_duel_engine/content/`, las
pruebas de contenido y los cambios documentales asociados. El commit
`82a6b5b433b623590d7c21ad9e6d41a56ab0fc1` fija el baseline de cierre de 2-A;
ningún cambio posterior se usa para juzgar su alcance histórico.

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

**PASS de alcance para 2-A.** El rango inmutable
`a3b164f7735f55f37b53808160a56ad54861c7c9..82a6b5b433b623590d7c21ad9e6d41a56ab0fc1`
no toca `engine/`, `application.py`, `persistence/`, `replay`, `transport`,
reglas, dominio ni servicio. Sus cambios de código quedan dentro de
`src/card_duel_engine/content/`; el resto corresponde a pruebas y documentación
de la microcolección y de sus gaps mecánicos.

## CAMBIOS POSTERIORES DE FASE 2-B

El rango posterior, también inmutable,
`82a6b5b433b623590d7c21ad9e6d41a56ab0fc1..74389c66f1c51b53ff9a93b819dc360b668d8ac2`
mantiene visibles cambios de Fase 2-B en `rules/deck.py`, `rules/__init__.py`,
`domain/models.py`, `service.py`, `src/card_duel_engine/__init__.py` y sus
pruebas y documentación asociadas. Estos cambios fijan semántica y validación
de puntos de mazo, pero son posteriores al baseline de 2-A: se registran para
conservar la trazabilidad y **no se utilizan para evaluar el alcance histórico
de Fase 2-A**.

## TEST RESULTS

**PASS registrado en la verificación que culminó en `74389c6`.** La primera
ejecución descubrió una expectativa obsoleta (`points.exceeded`) frente al
contrato ya usado `deck.points_exceeded`: 1 fallo, 685 aprobadas, 1 omitida y
816 subtests. Se corrigió únicamente esa expectativa. La ejecución final de
`uv run python -m pytest -q` obtuvo **687 passed y 816 subtests passed** en
107,12 s; coverage repitió las 687 pruebas y 816 subtests sin fallos.
`git diff --check` terminó con código 0. Estas cifras son evidencia histórica
ya registrada: no se atribuyen al SHA documental creado por esta corrección.

**PASS de la ejecución final de esta corrección documental.** Tras sincronizar
el extra de desarrollo bloqueado, `uv run python -m pytest -q` obtuvo **686
passed, 1 skipped y 816 subtests passed** en 108,69 s. Esta es la única cifra de
pytest atribuida a la ejecución que acompaña al nuevo SHA documental.

Los resultados de mypy, coverage, matrices de Python y CI que siguen son la
evidencia ya registrada en la verificación de `74389c6`; se conservan por
trazabilidad y no se presentan como nuevas ejecuciones del SHA documental.

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
`docs/release-results/0.20.1/`. Separados éstos, el rango propio de 2-A incluye
los cambios de contenido, pruebas y documentación enumerados en
`IMPLEMENTATION SUMMARY`. Los cambios posteriores de reglas, dominio, servicio
y exportaciones permanecen expresamente visibles en `CAMBIOS POSTERIORES DE
FASE 2-B`; no se ocultan ni se reclasifican como preexistentes o como 2-A.

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

**GO — PHASE 2-A COMPLETE.** Los controles técnicos pasan y el rango histórico
inmutable de 2-A respeta su alcance. Los cambios posteriores de 2-B se conservan
en este informe únicamente como trazabilidad y no alteran este veredicto.

## PHASE 2 VERDICT

**PHASE 2 — IN PROGRESS.**
