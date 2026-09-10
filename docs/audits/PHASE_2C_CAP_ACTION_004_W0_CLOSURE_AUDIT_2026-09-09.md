# Auditoría de cierre W0 de `CAP-ACTION-004` — 2026-09-09

> **Veredicto:** **CAP-ACTION-004 W0 NO CERRADO — REQUIERE CORRECCIÓN**.
>
> Esta auditoría no declara **`CAPABILITY CLOSED`**. W1 —comandos, eventos,
> creación/cierre ejecutable, proyecciones y recorrido de servicio— continúa
> expresamente fuera de alcance. Además, la evidencia verde disponible
> corresponde al `HEAD` de entrada, no al commit que incorpora este informe.

## 1. HEAD inicial

El checkout estaba limpio al comenzar. El `HEAD` inicial y SHA exacto sobre el
que se hicieron las verificaciones locales de esta auditoría fue
`40e7dfe79561357d3ab3d278fb233883b1fbf54a` (`work`), merge de PR #280. El
baseline inmediatamente anterior al runtime W0 fue
`a8b3e26acf95bc50e6bda4aa1ccdb0bab05e6932`; el commit que introdujo W0 fue
`73e769a8293e9dfbd0018ac3d01e358e254a3036` y entró en `main` mediante
`2832b94ae61e7aa7c913cdd5207a212fed3de8b8`.

El **SHA del cambio auditado** es el commit que contiene este archivo. Por la
imposibilidad de que un archivo incluya su propio SHA sin modificarlo de nuevo,
este informe no inventa ese valor: las ejecuciones se atribuyen al SHA exacto
realmente ejecutado y el gate exige CI nuevo sobre el tip del cambio.

## 2. Problemas encontrados

1. El primer runtime W0 convirtió `state_digest()` en una función dependiente de
   la versión de reglas: con reglas `0.19.0` omitía `pending_decision`, aunque el
   campo ya era parte del estado autoritativo.
2. El CI del commit de implementación quedó rojo en sus cuatro jobs.
3. La evidencia documental anterior cerraba calidad usando un SHA anterior. Esa
   evidencia sigue siendo histórica, pero no prueba el commit de este informe.
4. W0 proporciona infraestructura persistente, no el lifecycle público. No hay
   todavía comando/evento universal de creación o cierre ni proyección por
   audiencia; atribuirle el cierre de toda la capability sería incorrecto.

## 3. Causa del CI rojo

El SHA `73e769a8293e9dfbd0018ac3d01e358e254a3036` tuvo `failure` en
`runtime (3.11)`, `runtime (3.12)`, `runtime (3.13)` y `full` en las ejecuciones
[34353063201](https://github.com/Alphonsus411/card_duel/actions/runs/34353063201)
y [34353066655](https://github.com/Alphonsus411/card_duel/actions/runs/34353066655).
La causa funcional fue mezclar dos conceptos: la huella autoritativa actual y
la huella histórica de replays 0.19. La omisión global de `pending_decision`
hacía que dos estados runtime distintos pudieran compartir digest. La corrección
`12a958e845a784b533e7047b23e3f59cf9cdfd2f` volvió a incluir todos los campos
autoritativos en `state_digest()` y aisló la excepción como
`legacy_019_state_digest()`, activada sólo para documentos 0.19 históricos.

## 4. Cobertura antes y después

| Corte | SHA exacto | Collected | Passed | Failed | Skipped | Cobertura |
|---|---|---:|---:|---:|---:|---:|
| Antes de corregir | `73e769a8293e9dfbd0018ac3d01e358e254a3036` | No acreditado como suite válida | No acreditado | CI rojo | No acreditado | **No acreditada**: el perfil no completó; no se reutiliza un porcentaje de otro SHA. |
| Después, suite local de entrada | `40e7dfe79561357d3ab3d278fb233883b1fbf54a` | **782** | **781** | **0** | **1** | Sin instrumentación en esta ejecución. |
| Después, cobertura local intentada | `40e7dfe79561357d3ab3d278fb233883b1fbf54a` | **782** | **775** | **7** | **0 acreditados** | **91 % parcial e inválido** porque hubo fallos. |
| Después, perfil remoto válido | `40e7dfe79561357d3ab3d278fb233883b1fbf54a` | **782** | **781** | **0** | **1** | **89.0 %**, branch/line, artefacto del perfil de calidad. |

Los **816 subtests passed** se registran aparte y no se suman artificialmente a
`collected`. No se presenta como “antes” el 89 % de una release anterior: ante
una ejecución interrumpida, la cobertura correcta es “no acreditada”.

## 5. Correcciones realizadas

- `12a958e845a784b533e7047b23e3f59cf9cdfd2f`: separó digest autoritativo y
  compatibilidad 0.19, estrechó la detección del documento histórico y añadió
  regresiones que demuestran que una decisión cambia el digest incluso con
  reglas 0.19.
- `15975e2aee93c78c9c2db2a5f6fa476edfb03e41`: amplió ramas negativas de
  validación de `PendingDecision`.
- `db0e69a`: endureció migración snapshot v2 y rechazo de documentos inválidos.
- `11d8c71`: neutralizó fixtures W0 para que los casos sin decisión expresen
  ausencia canónica y no creen semántica W1 accidental.
- Este cambio añade la auditoría de cierre sin alterar runtime ni falsear
  resultados de CI.

## 6. Auditoría del digest runtime

`state_digest()` calcula ahora la huella del estado canónico completo, incluido
`GameState.pending_decision`. Los estados idénticos salvo decisión producen
digests distintos. La única omisión de ese campo vive en
`legacy_019_state_digest()` y sirve exclusivamente para verificar la huella que
ya estaba grabada en replays 0.19 anteriores. El fallback se condiciona a:

- schema original `1` o `2`;
- ausencia original de `engine_semantics`;
- `engine_version == "0.19.0"`; y
- semántica restaurada `LEGACY_019`.

Un documento moderno que declare explícitamente esa semántica no obtiene el
escape. Así, compatibilidad no debilita la autoridad del digest runtime.

## 7. Ruta explícita de compatibilidad legacy

La compatibilidad se divide sin heurísticas:

1. snapshot `1 → 2 → 3` mediante entradas explícitas de migración;
2. snapshot `2 → 3` inserta exactamente `pending_decision = None` y recalcula
   `state_digest` sobre el estado migrado;
3. replay permanece en schema `2` durante W0;
4. replays históricos 0.19 se verifican con `legacy_019_state_digest()` sólo si
   cumplen las cuatro condiciones de la sección 6;
5. replays 0.20.0/0.20.1 conservan únicamente su excepción histórica separada
   por `ability_source_profile`;
6. una versión, tipo o discriminador desconocido falla de forma cerrada.

No se infiere una decisión desde `pending_search`,
`pending_move_replacement`, comandos o eventos legacy.

## 8. Snapshot v3

El reader/writer usa `SNAPSHOT_SCHEMA_VERSION = "3"`. El documento conserva el
sobre `{body, sha256}`; valida primero el checksum del original, migra el body y
valida el digest del estado codificado antes de instalarlo. El campo opcional
`pending_decision` vive dentro de `GameState`, por lo que queda bajo el mismo
snapshot autoritativo que historial, eventos y resto del agregado. Hay
round-trip para ausencia, `pending` y `closed`.

## 9. Migración 2→3

La función `snapshot 2 → 3` copia la entrada, añade al `GameState` codificado la
ausencia canónica (`None`), establece schema `3` y recalcula el digest. La cadena
es determinista, no muta el documento de entrada y volver a pedir destino `3`
produce el mismo resultado canónico. Snapshot v2 con una decisión inyectada,
digest incoherente, versión sin ruta o estructura inválida se rechaza; jamás se
promueve contenido ambiguo.

## 10. CAS

W0 no crea otra tabla ni otra autoridad. In-memory y SQLite guardan el snapshot
completo mediante `save(..., expected_version=...)`; SQLite efectúa un único
`UPDATE ... WHERE version = expected_version`.

- **CAS de persistencia del snapshot W0 — IMPLEMENTADO Y PROBADO:** en ambos
  stores, dos escrituras del snapshot completo con el mismo `expected_version`
  producen exactamente un éxito, un `VersionConflict` y un solo incremento. La
  instantánea final coincide íntegramente con uno de los dos candidatos —incluidos
  campos independientes—, por lo que el estado perdedor no se mezcla parcialmente
  con el ganador.
- **CAS del cierre público y ausencia de evento fantasma — PENDIENTE DE W1:** W0
  no tiene comandos de cierre, eventos lifecycle ni publicación
  application/service. Demostrar la carrera de dos cierres y que el perdedor no
  publica observables exige ese recorrido W1; no se simula como evidencia W0.

Por ello, el gate global de CAS se clasifica **PARCIAL**: la capa de persistencia
está acreditada, pero la parte de lifecycle todavía no puede demostrarse sin
ampliar el alcance.

## 11. Goldens neutrales

`tests/artifacts/pending-decision-w0/` contiene cuatro documentos neutrales:
snapshot v2 sin decisión y snapshots v3 con ausencia, decisión pendiente y
decisión cerrada. “Neutral” significa que prueban el contenedor W0 sin asignar
semántica de carta, mulligan, búsqueda ni selección compuesta. Los fixtures
legacy permanecen inmutables; se cargan, no se regeneran para hacerlos coincidir
con el runtime actual.

## 12. Documentación sincronizada

El plan W0 distingue baseline documental y evidencia posterior; la matriz y las
dependencias mantienen `CAP-ACTION-004` sin `CAPABILITY CLOSED`; replay v3 y el
lifecycle público quedan en W1. Esta auditoría prevalece sólo para el veredicto
de cierre aquí examinado y no convierte un `success` histórico en evidencia del
SHA que contiene este documento.

## 13. Tests locales

Todas las ejecuciones de esta tabla se hicieron sobre
`40e7dfe79561357d3ab3d278fb233883b1fbf54a`:

| Comando | Exit | Resultado exacto |
|---|---:|---|
| `uv sync --locked --extra dev` | 0 | Entorno resuelto desde lock; extra dev instalado. |
| `uv run python -m pytest -q` | 0 | **782 collected; 781 passed; 0 failed; 1 skipped; 816 subtests passed.** |
| `uv run python -m mypy` | 0 | **Success: no issues found in 44 source files.** |
| `uv run python -m coverage run --branch -m pytest -q` + `uv run python -m coverage report` | 1 | **782 collected; 775 passed; 7 failed; 0 skipped acreditados; 793 subtests passed.** El reporte parcial indicó **91 %**, pero se invalida como cobertura de aceptación. Hubo un fallo de wheel reproducible y seis `sqlite3.OperationalError: disk I/O error`; no se ocultan ni se convierten en PASS. |
| `uv run python scripts/verify_release.py --profile full --json dist/release-verification.json` | 1 | **perfil `full`: FAIL en `quality:tests`**; `Ran 478 tests`, **43 errors**, por `sqlite3.OperationalError: disk I/O error` y fallos derivados de build; no se creó JSON y no se atribuye cobertura válida. |

La suite pytest y mypy prueban el SHA de entrada; los dos intentos instrumentados
registran además sus fallos ambientales en vez de ocultarlos. El CI remoto de la
sección 14 aporta el perfil válido para ese mismo SHA de entrada. Nada de ello
prueba el commit documental posterior y, por tanto, no basta para cerrar
`W0-GATE-QUALITY` en este cambio.

## 14. CI remoto

La ejecución remota [tests #34452239359](https://github.com/Alphonsus411/card_duel/actions/runs/34452239359)
está vinculada exactamente a
`40e7dfe79561357d3ab3d278fb233883b1fbf54a`:

| Job | Resultado | Finalización UTC |
|---|---|---|
| `runtime (3.11)` | `success` | `2026-09-10T07:54:54Z` |
| `runtime (3.12)` | `success` | `2026-09-10T07:55:17Z` |
| `runtime (3.13)` | `success` | `2026-09-10T07:55:22Z` |
| `full` | `success` | `2026-09-10T07:56:45Z` |

**No se copia esa declaración verde al SHA de este cambio.** Para el commit que
contiene esta auditoría, los cuatro resultados son **NO CONSTA / PENDIENTE**
hasta que CI publique `success` para ese mismo SHA.

## 15. Riesgos restantes

- El tip documental aún no dispone de los cuatro checks remotos exigidos.
- W1 debe definir comandos/eventos, exactly-once de cierre, proyecciones por
  audiencia, errores no interferentes y publicación sólo después del CAS.
- Replay sigue correctamente en v2; elevarlo antes del primer lifecycle W1
  inventaría semántica. Al elevarlo habrá que añadir migración/goldens v3.
- El fallback histórico exige vigilancia para no ampliar sus condiciones.
- Falta medir crecimiento de payload y latencia SQLite con carga representativa.
- Mulligan y otros modelos especializados no se integran automáticamente.

## 16. Estado de cada gate

| Gate | Estado | Justificación |
|---|---|---|
| `W0.1-GATE-CARDINALITY` | **CERRADO** | Slot único opcional; no hay lista mutable ni simultaneidad anticipada. |
| `W0-GATE-SCHEMA` | **CERRADO** | Snapshot reader/writer v3, codec cerrado y migración explícita. |
| `W0-GATE-DIGEST` | **CERRADO** | Digest autoritativo incluye la decisión; fallback 0.19 queda aislado y estrecho. |
| `W0-GATE-HISTORY` | **CERRADO** | Snapshots 1/2 migran; fixtures legacy no se reescriben; replay sigue v2. |
| `W0-GATE-GOLDENS` | **CERRADO** | v2-none y v3-none/pending/closed, sin mecánica W1. |
| `W0-GATE-CAS` | **PARCIAL** | CAS de persistencia del snapshot W0 implementado y probado en InMemory y SQLite, con ganador íntegro; CAS del cierre público y ausencia de evento fantasma pendientes de W1. |
| `W0-GATE-DOCS` | **CERRADO** | Alcance W0/W1 y compatibilidad quedan diferenciados. |
| `W0-GATE-QUALITY` | **NO CERRADO** | No constan `runtime (3.11)`, `runtime (3.12)`, `runtime (3.13)` y `full` como `success` para el SHA del commit que contiene esta auditoría. |

Por aplicación estricta del gate de calidad, el resultado final es:

> **CAP-ACTION-004 W0 NO CERRADO — REQUIERE CORRECCIÓN**

Incluso si una ejecución posterior cerrase W0 para el SHA del cambio, no se
deberá declarar **`CAPABILITY CLOSED`**: W1 continúa fuera de alcance.

## 17. Adenda de revalidación local — 2026-09-10

Esta adenda registra una ejecución nueva sobre el checkout limpio con SHA exacto
`a11a0d1c7071da3db400af60dd68cda5abd8b4d5`. Ese SHA es el objeto realmente
probado; no se sustituye por el SHA posterior que incorpora esta documentación.

### 17.1 Contadores y cobertura de aceptación

| Comando | Exit | Collected | Passed | Failed | Skipped | Resultado adicional |
|---|---:|---:|---:|---:|---:|---|
| `uv sync --locked --extra dev` | 0 | N/A | N/A | N/A | N/A | Lock respetado y extra `dev` instalado. |
| `uv run pytest -q tests/test_pending_decision_w0.py` | 0 | **58** | **58** | **0** | **0** | 100 % de la selección. |
| `uv run pytest -q tests/test_replay_legacy_019.py tests/test_replay_legacy_020_profile.py tests/test_persistence_v090.py tests/test_expected_version_contract.py` | 0 | **43** | **43** | **0** | **0** | **159 subtests passed**. |
| `uv run pytest -q tests/test_phase_2c_engine_evolution_roadmap.py` | 0 | **15** | **15** | **0** | **0** | 100 % de la selección. |
| `uv run coverage erase && uv run coverage run -m pytest -q` | 0 | **783** | **782** | **0** | **1** | **816 subtests passed**. |
| `uv run coverage report -m` | 0 | N/A | N/A | N/A | N/A | **91 %** total: 4.590 statements, 314 missed, 1.656 branches y 253 ramas parciales; supera `fail_under = 88` por 3 puntos. |

El porcentaje exacto publicado por `coverage report -m` es **91 %**. No se
cambió `fail_under`, no se añadieron omisiones, exclusiones ni
`pragma: no cover`, y la suite instrumentada no tuvo fallos.

### 17.2 Perfil de release completo

`uv run python scripts/verify_release.py --profile full` terminó con exit 0 y
`OK: perfil full completado`. Sus etapas, en el orden ejecutado por el script,
quedaron así:

| Etapa | Estado | Evidencia registrada |
|---|---|---|
| `metadata` | **PASS** | Versión `0.20.1` coherente en changelog, pyproject, README, lock y validación. |
| `lockfile` | **PASS** | `uv lock --check`, diff vacío de `uv.lock` y hash sin cambios. |
| `security` | **PASS** | 114 archivos Python analizados y 225 archivos versionados escaneados. |
| `quality:mypy` | **PASS** | `Success: no issues found in 44 source files`. |
| `quality:compileall` | **PASS** | Compilación de `src`, `tests` y `scripts` sin error. |
| `quality:tests` | **PASS** | Discovery `unittest` completo bajo cobertura de ramas sin error. |
| `quality:coverage` | **PASS** | **88 %** en el corpus ejecutado internamente por el perfil; satisface el `fail_under = 88` del proyecto. |
| `rules-sources` | **PASS** | Dos fuentes PDF verificadas. |
| `simulations` | **PASS** | 300 simulaciones, 54.000 comandos y 84.000 eventos. |
| `persistence` | **PASS** | 30 round-trips. |
| `package:build-audit` | **PASS** | Dos builds binariamente idénticos; wheel puro con 48 archivos, sin fixtures, PDF ni cartas de producción. |
| `package:artifact-coherence` | **PASS** | `card_duel_engine-0.20.1-py3-none-any.whl`, SHA-256 `738cc71dba85cdb37cfa5c85d71ff4f9251b71eceb82dae7e060e5b8395e1b91`. |
| `package:python-3.11`, `package:install-3.11`, `package:import-3.11` | **PASS** | Instalación aislada e import de versión `0.20.1`. |
| `package:python-3.12`, `package:install-3.12`, `package:import-3.12` | **PASS** | Instalación aislada e import de versión `0.20.1`. |
| `package:python-3.13`, `package:install-3.13`, `package:import-3.13` | **PASS** | Instalación aislada e import de versión `0.20.1`. |

Una consulta auxiliar posterior invocó inicialmente
`verify_rules_sources.verify()` con un argumento incorrecto y recibió
`RulesSourceError`; no era un control del perfil ni un fallo del repositorio. La
invocación canónica `uv run python scripts/verify_rules_sources.py` se repitió y
pasó para ambas fuentes. Se conserva aquí el incidente de operador para que el
registro no oculte resultados.

### 17.3 Estado actualizado del gate

La evidencia local del SHA `a11a0d1c7071da3db400af60dd68cda5abd8b4d5`
queda íntegramente verde. Sin embargo, el commit que contiene esta adenda tendrá
otro SHA y todavía no puede tener, antes de publicarse, resultados remotos
`runtime (3.11)`, `runtime (3.12)`, `runtime (3.13)` y `full` asociados a ese
mismo objeto Git. Por la regla de identidad de evidencia aplicada en esta
auditoría:

> **`W0-GATE-QUALITY`: PENDIENTE de CI para el SHA del commit documental.**

No se clasifica como `BLOQUEADO`: no falló ningún control canónico local. Tampoco
se declara `CAPABILITY CLOSED`; W1 y el tramo de lifecycle de
`W0-GATE-CAS` permanecen fuera del alcance de esta revalidación.
