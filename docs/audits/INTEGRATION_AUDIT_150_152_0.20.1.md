# Auditoría de integración de los PR #150, #151 y #152 — 0.20.1

## A. Identidad

| Campo | Valor |
| --- | --- |
| Repositorio | `Alphonsus411/card_duel` |
| SHA base de `origin/main` | `10cb87ff8cb49b27b3e2a5cf3754b96243d747eb` |
| Rama de auditoría | `work` |
| SHA de contenido auditado | `05cfc78821b97dd630fb73a4010d34ee11b01dcc` |
| SHA final previsto | El `HEAD` del commit documental que incorpora esta línea; verificable con `git rev-parse HEAD` sin autorreferencia. |
| Versión | `0.20.1` |
| Fecha UTC | `2026-08-28` |

El clon entregado no conserva un remoto configurado ni
`refs/remotes/origin/main`. El SHA base se fijó al `HEAD` inicial
`10cb87ff8cb49b27b3e2a5cf3754b96243d747eb`, cuyo asunto es el merge del PR
#160 y que constituye la instantánea de `main` suministrada para esta tarea. La
ausencia de la referencia remota impide un `fetch` nuevo y queda declarada como
limitación de consulta; no se inventó una referencia. No se alteró código de
producción, reglas, versión, tag ni release.

**Estrategia de identidad del commit.** El campo se dejó inicialmente como
«se completa tras el commit». La auditoría quedó fijada en el primer commit de
contenido `05cfc78821b97dd630fb73a4010d34ee11b01dcc`; este segundo commit,
exclusivamente documental, sustituye la leyenda por ese SHA inmutable. Su SHA
final queda verificable con `git rev-parse HEAD`. Así se evita la autorreferencia
imposible y una cadena infinita de reescrituras.

## B. PR #150 — rechazo de cartas no registradas

**Estado: `SUPERSEDED`.**

* **Diff original inspeccionado:** base
  `d7455cbb3e360c822756180660b7a27ce212318b`, head
  `9c627ed6b94cebdc1408f5e6033e9b209d5d5fb0`, un commit
  (`Reject unregistered cards from collection registries`), 17 inserciones en
  `src/card_duel_engine/engine/game.py` y `tests/test_collection_registry.py`.
  Se inspeccionó con `git diff d7455cb...9c627ed`.
* **Cambio original:** si `GameEngine` usa `CollectionRegistry`, una definición
  ausente del catálogo autoritativo provoca `ValueError` y no se auto-registra;
  el test exigía además catálogo intacto y cero llamadas a la política.
* **Diferencias frente a `origin/main`:** `git cherry origin/main 9c627ed`
  muestra `+`, por lo que el parche literal no está integrado. El motor actual
  ya centraliza la prevalidación y aplica la misma prohibición en la ruta
  evolucionada de `new_match`. El commit de reconciliación
  `83e2daf525bae4fec0bc1daf3e2e0ff8a4854411` añadió una prueba más fuerte: usa
  una carta registrada y otra desconocida, compara snapshots completos antes y
  después, comprueba la ausencia de la carta y verifica que la política no se
  invoca.
* **Equivalencia semántica:** **sí**, con cobertura estrictamente superior. La
  definición desconocida se rechaza, el registro autoritativo no muta y no se
  vuelve a validar confianza. La diferencia textual deriva de la evolución del
  motor y del test, no de una relajación del contrato.
* **Decisión por cambio:** no portar las cuatro líneas antiguas del motor, para
  no duplicar la prevalidación actual; conservar la prueba reforzada ya presente.
* **Justificación:** portar el parche original sobre la arquitectura actual
  introduciría lógica redundante. La conducta solicitada queda demostrada en el
  punto autoritativo y por invariantes de snapshot más completos.
* **Tests y resultados:**
  `tests/test_collection_registry.py` quedó incluido en las pruebas dirigidas
  (**36 tests y 114 subtests, todos pasan**, junto con los otros dos archivos),
  en pytest completo y en unittest completo.

## C. PR #151 — descubrimiento unittest de la paridad del caché

**Estado: `PRESENT`.**

* **Diff original inspeccionado:** base
  `565c5abe4fa0973a7ed8ca4bbba781c4a27879a1`, head
  `20248530cbeaefc52b44d9adfbc8bb7d82cb7422`, un commit, 62 inserciones y 61
  eliminaciones en `tests/test_targeting_local_cache_parity.py`; se inspeccionó
  con `git diff 565c5ab...2024853`.
* **Cambio original:** convertir las pruebas de paridad parametrizadas para que
  también las descubra `unittest`, preservando escenarios, caché local y
  comparación entre rutas.
* **Diferencias frente a `origin/main`:** ninguna en el archivo (`git diff
  2024853 origin/main -- tests/test_targeting_local_cache_parity.py` no produjo
  salida). `git cherry origin/main 2024853` devolvió `-`, prueba de equivalencia
  por parche. El mismo cambio está registrado en main mediante
  `1ba7da1bfa7e84e95ba6ecbaf945a0bb69f9e1c5`.
* **Equivalencia semántica:** **sí, exacta** tanto por contenido como por
  patch-id.
* **Decisión por cambio:** conservar; no portar ni editar.
* **Justificación:** una segunda aplicación sería duplicada y no aportaría
  cobertura.
* **Tests y resultados:** el archivo pasó en la ejecución dirigida; el
  descubrimiento completo de unittest ejecutó **400 tests, todos correctos**, lo
  que prueba específicamente el objetivo de integración del PR.

## D. PR #152 — baselines opcionales y diagnóstico medido

**Estado: `REINTEGRATED`.**

* **Diff original inspeccionado:** base
  `309ac648e3db53149afbe79eb67bf2528407df63`, head
  `e706d3baee4ed3612485d7c47d2e209732f76d7f`, un commit, 35 inserciones y 22
  eliminaciones en `benchmarks/benchmark_action_options.py` y
  `tests/test_benchmark_scenarios.py`; se inspeccionó con `git diff
  309ac64...e706d3b`.
* **Cambios originales:** usar `.get()` para baselines no disponibles, emitir
  `None`/listas vacías en vez de fallar, y derivar el texto de diagnóstico de la
  categoría dominante realmente medida.
* **Diferencias frente a `origin/main`:** `git cherry origin/main e706d3b`
  devuelve `+`; no es el mismo parche. El commit de reconciliación
  `985bef1dbcb6ec9492477a66fd9824c63e74c90d` porta la conducta y añade dos
  aserciones: `baseline_sources == []` cuando no hay baseline, y `dominant ==
  categories[0]`. La comparación conserva diferencias textuales acumuladas en
  el benchmark, no diferencias de resultado en este cambio.
* **Equivalencia semántica:** **sí**, y las aserciones adicionales hacen
  explícitos el origen vacío y la ordenación dominante.
* **Decisión por cambio:** aceptar la reintegración refinada; no aplicar el
  commit original.
* **Justificación:** la versión reintegrada satisface ambos casos opcionales y
  evita un diagnóstico estático que podría contradecir la medición, con contrato
  de salida más preciso.
* **Tests y resultados:** `tests/test_benchmark_scenarios.py` pasó en la tanda
  dirigida, pytest completo y unittest completo; mypy también validó los 40
  archivos fuente del paquete.

### Matriz consolidada de decisiones

| PR | cambio | presente en main | equivalente | necesita portar | acción |
| --- | --- | --- | --- | --- | --- |
| #150 | Rechazar definiciones desconocidas con registro autoritativo | Sí, mediante implementación evolucionada y prueba reforzada | Sí | No | `SUPERSEDED`: conservar la prevalidación y el test de snapshot actuales |
| #151 | Hacer descubribles por unittest las pruebas de paridad del caché | Sí, parche exacto | Sí, exacto | No | `PRESENT`: ninguna modificación |
| #152 | Admitir baselines opcionales | Sí, reintegrado | Sí | No | `REINTEGRATED`: conservar `.get()`, `None` y fuentes vacías |
| #152 | Basar el diagnóstico en la categoría dominante medida | Sí, reintegrado | Sí | No | `REINTEGRATED`: conservar diagnóstico dinámico y aserción de orden |

## E. Lista completa de archivos modificados

Respecto del SHA base suministrado, el único archivo modificado en el alcance de esta
auditoría es:

* `docs/audits/INTEGRATION_AUDIT_150_152_0.20.1.md` (actualización documental).

No se modificaron los cinco archivos de código/test examinados, la versión, el
lockfile ni fuentes normativas. Los productos bajo `dist/` son artefactos
ignorados y no forman parte del commit.

## F. Validación

El entorno se preparó con `uv sync --locked --extra dev`. Una primera
tentativa sin dependencias falló correctamente; una tentativa paralela posterior
interfirió en el registro de worktrees temporales. Después de `git worktree
prune`, pytest y unittest se repitieron secuencialmente. Sólo las ejecuciones
canónicas aisladas y exitosas de la tabla sustentan el veredicto. Una tentativa
de runtime con una ruta JSON no autorizada también fue rechazada por el propio
script y se repitió con la ruta canónica.

| Tipo | Comando exacto | Resultado | Recuento / duración | Evidencia |
| --- | --- | --- | --- | --- |
| Pruebas dirigidas | `uv run python -m pytest -q tests/test_collection_registry.py tests/test_targeting_local_cache_parity.py tests/test_benchmark_scenarios.py` | PASS (0) | 36 passed, 114 subtests; 3,77 s (6 s pared) | resumen pytest al 100 % |
| Pytest completo | `uv run python -m pytest -q` | PASS (0) | 559 passed, 733 subtests; 79,96 s (81 s pared) | resumen final pytest |
| Unittest completo | `uv run python -m unittest discover -s tests -q` | PASS (0) | 400 tests; 79,215 s (81 s pared) | `Ran 400 tests` / `OK` |
| mypy | `uv run python -m mypy src/card_duel_engine` | PASS (0) | 40 archivos; 5 s pared | `Success: no issues found in 40 source files` |
| compileall | `uv run python -m compileall -q src/card_duel_engine` | PASS (0) | sin errores; <1 s | ausencia de salida y código 0 |
| verify_release runtime | `uv run python scripts/verify_release.py --profile runtime --json dist/release-verification.json` | PASS (0), `status: ok` | 121 s pared; cobertura 89 %; 96 Python y 172 archivos rastreados | JSON esquema 2; metadata, lockfile, security y quality |
| verify_release full | `uv run python scripts/verify_release.py --profile full --json dist/release-verification.json` | PASS (0), `status: ok` | 320 s pared; 300 simulaciones, 54.000 comandos, 84.000 eventos, 30 roundtrips, 2 fuentes | ocho etapas; wheel instalado en Python 3.11/3.12/3.13 |
| verify_reproducible_wheel | `uv run python scripts/verify_reproducible_wheel.py` | PASS (0) | 2 builds, 44 entradas; 14 s | JSON: `binary_identical_builds: true`, RECORD íntegro y árbol limpio |
| verify_rules_sources | `uv run python scripts/verify_rules_sources.py` | PASS (0) | 2 fuentes; <1 s | `OK` para ambos PDF declarados |
| git diff --check | `git diff --check` | PASS (0) | sin diagnósticos; <1 s | salida vacía |

## G. Wheel

| Campo | Resultado |
| --- | --- |
| Filename | `card_duel_engine-0.20.1-py3-none-any.whl` |
| SHA-256 | `c3f69c8d83772e3fa452355f363419f04b1791fd9f32a0253863b0924329574c` |
| Número de entradas | 44 |
| Reproducibilidad | **Sí**: dos builds binariamente idénticos |
| Inspección de contenido | **APROBADA** |

La auditoría verificó `RECORD`, `Root-Is-Purelib`, tag `py3-none-any`, licencia
Apache-2.0, cero dependencias runtime y ausencia de fixtures, cartas de
producción y ambos PDF. El artefacto procede del worktree detached limpio de
`10cb87ff8cb49b27b3e2a5cf3754b96243d747eb` y se instaló con éxito en Python 3.11, 3.12 y 3.13.

## H. Resumen de ramas

Se actualizó el inventario tras `fetch`, sin eliminar referencias. Los dos
`codex/*` posteriores al corte del informe de ramas son ancestros probados de la
base actual, por lo que incrementan A y `SAFE_TO_DELETE` en dos sin cambiar las
demás categorías.

| Métrica | Total |
| --- | ---: |
| Ramas remotas | 161 |
| Ramas `codex/*` | 159 |
| `SAFE_TO_DELETE` | 153 |
| `REVIEW_REQUIRED` | 2 |
| `KEEP` | 5 |
| Categoría A | 153 |
| Categoría B | 2 |
| Categoría C | 0 |
| Categoría D | 4 |
| Categoría E | 1 |

No se eliminó ninguna rama. **`Bella-2.0 untouched`**: sólo se contó como
categoría E/`KEEP`; no se usó como base, inspeccionó, modificó, fusionó, rebasó
ni eliminó. El inventario, método y disposición por rama están en
[`CODEX_BRANCH_AUDIT_0.20.1.md`](CODEX_BRANCH_AUDIT_0.20.1.md). Ese documento
conserva su corte anterior (157 `codex/*`); esta sección declara de forma
explícita la actualización aritmética al corte de `origin/main` de esta auditoría.

## I. Protección observada de `main`

La consulta pública documentada devolvió `protected: false`,
`protection.enabled: false`, checks `off`, y listas vacías de rulesets y reglas
aplicables. El endpoint de protección clásica respondió **401 Requires
authentication**; por tanto no se infieren valores de campos no consultables y
`delete_branch_on_merge` tampoco pudo determinarse con esta sesión.

Recomendaciones: repetir la consulta autenticada como administrador; establecer
un ruleset para `main`; exigir PR y los checks existentes `runtime (3.11)`,
`runtime (3.12)`, `runtime (3.13)` y `full`; bloquear force-push y eliminación;
limitar cualquier bypass; y valorar rama actualizada y borrado automático tras
merge según la operativa del mantenedor. Son recomendaciones, no cambios
realizados por esta auditoría.

## J. Release readiness

**READY.** La candidata mantiene exactamente `0.20.1`; la integración de los
tres PR es semánticamente completa; pasan todas las verificaciones obligatorias;
el wheel es reproducible, íntegro e instalable; el alcance versionado es sólo
documental. No se creó ningún tag ni release. La protección de rama requiere el
seguimiento de gobierno recomendado, pero no altera la validez técnica observada
de la candidata.

## K. Veredicto global

**GO**

Justificación objetiva: no queda ningún cambio de #150–#152 por portar, no hay
cambio normativo ni divergencia de versión, todas las ejecuciones canónicas
obligatorias terminaron con código 0, y dos construcciones limpias del wheel
produjeron el mismo SHA-256 y contenido aprobado. El único cambio rastreado es
este informe de auditoría; no se crearon tags, releases ni se eliminaron ramas.
