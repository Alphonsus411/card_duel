# CAP-ACTION-004 contract audit — 2026-09-07

## Executive summary

Esta auditoría documental congela el contrato de planificación de
`CAP-ACTION-004` sin implementar runtime. La capability continúa **`MISSING`**;
su `contract_status` es **`READY`**, lo que autoriza únicamente la planificación
posterior de implementación. La versión permanece `0.20.1`, Phase 2C permanece
`IN PROGRESS`, Phase 3 permanece `PENDING` y `runtime_authorization` es
**`FORBIDDEN`**.

El análisis forense encuentra un lifecycle común en decisiones ya existentes,
pero no un primitive universal ejecutable. El contrato futuro fija una fuente
autoritativa, un único elector, opciones opacas, audiencia, cierre exactly-once,
snapshot, replay, privacidad y CAS. Las semánticas de búsqueda, targeting,
ordenación y replacements permanecen en sus modelos especializados.

## Audit identity and baseline

```yaml
audit_date: 2026-09-07
execution_date: 2026-09-08
capability: CAP-ACTION-004
version: 0.20.1
phase_2c: IN_PROGRESS
phase_3: PENDING
status: MISSING
gate: READY
contract_status: READY
runtime_authorization: FORBIDDEN
initial_sha: f80bc858221c8842dbe9ce0542e8a93b2141bfb6
final_audited_sha: f80bc858221c8842dbe9ce0542e8a93b2141bfb6
```

`initial_sha` es el `HEAD` capturado antes de editar. `final_audited_sha` es el
último SHA de código y documentación fuente auditado antes del commit de esta
entrega; coincide porque sólo se añaden/modifican los dos informes indicados en
la sección de cambios. El SHA del commit que contiene el propio documento no se
autorrefiere para evitar una identidad circular.

Baseline comprobado: `pyproject.toml` y `uv.lock` declaran `0.20.1`; los dos
roadmaps conservan Phase 2C `IN PROGRESS` y Phase 3 `PENDING`; la matriz declara
`CAP-ACTION-004` como `MISSING`, riesgo `CRITICAL`, prioridad `P0`, wave `W1` y
gate `READY`. `READY` no significa `PARTIAL`, `SUPPORTED` ni autorización de
runtime.

## Forensic matrix of existing mechanisms

La inspección sigue creación → estado → enumeración → validación/resolución →
snapshot/replay → proyección → CAS. “Exactly-once” describe una única
confirmación para una versión aceptada, no idempotencia global de transporte.

| Mecanismo auditado | Actor/opciones | Invalidación y cierre | Snapshot/replay | Privacidad/CAS | Estrategia contractual |
|---|---|---|---|---|---|
| `PendingSearch` | `chooser_id`, IDs elegibles, min/max, zona y destino persistidos. | Revalida actor, unicidad, cardinalidad, elegibilidad y presencia; borra antes de continuar con rollback. | Pending y cursor viven en snapshot; comando originador y `ResolveSearchChoice` reconstruyen replay. | Candidatos sólo al elector; IDs finales sólo si la regla revela; CAS en frontera. | Conservar payload y continuación especializados; adoptar sólo el sobre universal. |
| `PendingMoveReplacement` | Elector, carta, razón, índices/destinos, comando original y prefijo elegido. | Restaura el comando, publica pending y reejecuta transaccionalmente con el índice; un pending consumido no se reutiliza. | Snapshot incluye comando/prefijo; replay reinserta elecciones en orden. | Opciones sólo al elector, existencia/carta hoy parcialmente pública; CAS en submit/store. | Conservar rollback/reejecución e índices especializados; adoptar sólo lifecycle. |
| Targets de play/ability | Target heterogéneo queda congelado en comando/`StackItem`; universo legal regenerado. | Legalidad al anunciar y fizzle/revalidación al resolver. | Comandos y pila sobreviven por snapshot/replay. | Transporte remoto opaco; observables dependen del efecto; CAS existente. | Tipos, cardinalidad, inmunidad y asignaciones no migran al primitive. |
| Targets de triggers | Controlador e `item_id`; opciones se regeneran hasta bloquear targets. | Debe coincidir con comando legal vigente; el lock sólo ocurre una vez. | `pending_triggers` y `ChooseTriggeredTargets` son reproducibles. | Lote visible y payload remoto redactado. | Sólo reutilizar autorización/lifecycle; mantener targeting especializado. |
| Orden de triggers | Lote simultáneo y permutaciones de `item_id`. | Exige permutación exacta y vacía el lote una vez. | Snapshot del lote y replay de `OrderTriggeredAbilities`. | Alternativas completas sólo internas; submit usa CAS. | Mantener simultaneidad y LIFO en stack. |
| `SetReplacementOrder` | Actor en comando; orden persistido en `CardInstance`. | Configuración mutable y repetible, no pending exactly-once. | Estado y comando son serializables/reproducibles. | Acción remota opaca y versionada. | No convertir en decisión pendiente. |
| Action option IDs | HMAC efímero ligado a match, actor, versión e índice; opciones no persistidas. | Reenumera y valida MAC/versión; reinicio invalida el secreto. | No pertenece a snapshot ni replay. | Oculta payload y usa CAS, pero no registra consumo. | Referencia pública útil; no es la identidad autoritativa futura. |

## Universal pending-decision contract

Cada decisión futura tendrá **una sola representación autoritativa persistida**.
Los campos normativos son:

| Campo | Contrato |
|---|---|
| `decision_id` | Identidad estable e inmutable, derivada determinísticamente del origen y su posición canónica. |
| `semantic_family` | Discriminador versionado por familia, nunca por `card_id`. |
| `authorized_elector` | Único actor autorizado a cerrar. |
| `audience` | Política que determina existencia y campos observables por audiencia. |
| `authorized_opaque_options` | Conjunto congelado de tokens únicos, opacos y no reversibles. |
| `state_version` | Vínculo exacto al estado y precondición CAS. |
| `origin` | Referencia autoritativa estable al hecho que creó la decisión. |
| `status` | Sólo `pending` o `closed`; `closed` es terminal. |
| `selected_option` | Ausente en `pending`; exactamente una opción autorizada al cerrar. |

La secuencia de creación se deriva de la posición canónica de `origin`, no se
duplica como autoridad. Son derivados y recalculables: validez, acciones
legales, vistas redactadas, representación API e índices abiertos. Son
transitorios y descartables: tokens de transporte, trace/request IDs, locks,
leases, cachés, reintentos, sesiones y wall-clock.

El lifecycle cerrado es `pending → closed`. No existen `expired` ni
`cancelled`. La transacción revalida decisión pendiente, origen, elector,
opción, versión, partida no terminada y CAS; sólo entonces escribe conjuntamente
`closed` y `selected_option`. Un rechazo no muta nada. Cerrar registra la
elección, pero no ejecuta la mecánica especializada.

Exclusiones normativas: el primitive no representa candidatos de cartas,
cardinalidad compleja, ordenación, selección compuesta, simultaneous reveal ni
search semantics.

## Fourteen invariants

| ID | Invariante contractual | Superficie futura |
|---|---|---|
| `CAP-ACTION-004-INV-01` | Una sola fuente autoritativa persistida por decisión. | Modelo, persistencia, snapshot, replay |
| `CAP-ACTION-004-INV-02` | `decision_id` estable en modelos, comandos, eventos, API y reconstrucciones. | Modelo, API, replay |
| `CAP-ACTION-004-INV-03` | Sólo `authorized_elector` solicita el cierre. | Enumeración, comandos, servicio |
| `CAP-ACTION-004-INV-04` | Sólo puede elegirse un token de `authorized_opaque_options`. | Validación, aplicación, API |
| `CAP-ACTION-004-INV-05` | `pending → closed` sucede exactamente una vez. | Transacción, persistencia, replay |
| `CAP-ACTION-004-INV-06` | Todo rechazo deja estado y decisión sin mutación. | Aplicación, servicio, storage |
| `CAP-ACTION-004-INV-07` | El perdedor de CAS se rechaza sin mutación. | Storage, concurrencia |
| `CAP-ACTION-004-INV-08` | Cada proyección respeta `audience` sin fugas. | API, eventos, observabilidad |
| `CAP-ACTION-004-INV-09` | Snapshot restaura todos y sólo los datos autoritativos. | Snapshot, codec, migración |
| `CAP-ACTION-004-INV-10` | Replay preserva identidad, autoridad, audiencia, opciones, versión y cierre. | Eventos, replay, golden fixtures |
| `CAP-ACTION-004-INV-11` | Versión desconocida se rechaza sin fallback ni mutación. | Codec, servicio, replay |
| `CAP-ACTION-004-INV-12` | Wall-clock nunca autoriza, invalida ni cierra una decisión. | Servicio, jobs, storage, replay |
| `CAP-ACTION-004-INV-13` | `semantic_family` despacha familias versionadas, nunca cartas concretas. | Handlers, aplicación, catálogo |
| `CAP-ACTION-004-INV-14` | El cierre sólo registra la opción y no ejecuta mecánicas ajenas. | Aplicación, eventos, composición |

Los IDs son permanentes y no pueden reutilizarse ni renumerarse.

## Dependency edges

| Arista | Tipo | Evidencia y efecto |
|---|---|---|
| `CAP-ACTION-002 → CAP-ACTION-004` | prerequisite | La enumeración/revalidación existente precede al primitive. |
| `CAP-PRIVACY-001 → CAP-ACTION-004` | prerequisite | La proyección por audiencia es condición previa. |
| `CAP-ACTION-004 → CAP-SECRET-002` | dependent | Las elecciones secretas/compuestas especializan el núcleo. |
| `CAP-ACTION-004 → CAP-TIME-002` | dependent/blocker | Mulligan requiere decisión pendiente y continúa bloqueado. |

Las cuatro aristas son recíprocas entre matriz y documento de dependencias y no
introducen ciclos. `CAP-TIME-005` continúa siendo además prerequisite separado
de `CAP-TIME-002`; este informe no lo cierra.

## Existing-model strategy

`PendingSearch` y `PendingMoveReplacement` permanecen **independientes** durante
la primera implementación. No se migran, fusionan ni componen sólo por parecido
estructural. Una migración posterior requiere equivalencia demostrada de
snapshot restaurado, eventos/observables/digest de replay y un beneficio medible
superior al riesgo. Targets, trigger ordering y replacement ordering mantienen
sus tipos y validadores. Action option IDs pueden inspirar tokens públicos, pero
no `decision_id` ni almacenamiento autoritativo.

## W0 impact matrix

| Superficie | Clasificación W0 | Obligación futura |
|---|---|---|
| `GameState` | cambio aditivo interno compatible | `pending_decision` opcional; no sustituir pending especializados. |
| Comandos | cambio aditivo público compatible | Resolución tipada con identidad, opción opaca y versión. |
| Eventos | cambio aditivo público compatible | Crear/elegir/cerrar con redacción por audiencia. |
| Snapshot | nueva versión de schema/replay | Decoder legacy produce exactamente `pending_decision = None`. |
| Replay | nueva versión de schema/replay | Lifecycle y observables completos y deterministas. |
| Codec | cambio aditivo interno compatible | Dispatch cerrado y rechazo de discriminador desconocido. |
| SQLite/stores | migración explícita | Migración transaccional e idempotente; preservar CAS. |
| `application` | cambio aditivo público compatible | Autenticar, traducir token opaco y uniformar errores. |
| `service` | cambio aditivo público compatible | Operación versionada con un único CAS. |
| DTO | cambio aditivo público compatible | Vista proyectada sin candidatos ni payload interno. |
| Proyecciones | cambio aditivo público compatible | Elector, adversario, público y motor separados. |
| CAS | sin cambio | Mantener `expected_version` y atomicidad vigente. |
| Artefactos históricos | sin cambio | Inmutables, leídos con decoder declarado. |

No se autoriza `breaking deliberado`. Cualquier desviación exige una nueva
decisión contractual antes de escribir runtime.

## Historical compatibility and migration

El primer runtime futuro que escriba decisiones debe versionar simultáneamente
snapshot y replay. Un decoder legacy sólo añade el default compatible
`pending_decision = None`; nunca infiere o reabre decisiones desde comandos,
eventos o pending especializados. Una versión desconocida se rechaza antes de
mutar, sin fallback, downgrade ni heurísticas.

El replay nuevo conserva creación/origen, opción elegida, cierre/resultado,
eventos, observables por audiencia y digest final. Los artefactos anteriores se
leen con su semántica histórica y no se reescriben, regeneran ni enriquecen con
eventos retroactivos. Toda migración de store será identificada, transaccional,
idempotente y compatible con rollback operativo.

## Privacy and audience projections

| Audiencia | Máximo observable |
|---|---|
| Elector | Identidad pública, lifecycle y tokens opacos vigentes. |
| Adversario | Sólo existencia/estado/resultado que la regla haga públicos. |
| Observador público | Subconjunto público estable, sin privilegios de jugador. |
| Motor interno | Identidad, opciones y payload autoritativos completos. |

Los tokens no derivan reversible o correlacionablemente de IDs ocultos. Opción
inexistente, token malformado, ajeno/no autorizado o decisión invisible exponen
la misma forma pública; `stale-version` puede ser distinto porque sólo revela la
precondición CAS. Logs, trazas, métricas, excepciones y replay público deben
sanear candidatos, cardinalidades, IDs, payloads y tokens de otras audiencias.

## CAS and exactly-once

Dos cierres sobre el mismo `expected_version` compiten por **un único CAS**.
Sólo uno confirma conjuntamente el estado `closed`, `selected_option`, eventos,
historial y nueva versión. El perdedor recibe `stale-version` y no modifica
nada. Application/service no simulan éxito, no reintentan con versión nueva ni
anexan historial antes del CAS confirmado. Un retry posterior al éxito puede
leer el resultado terminal, pero no reabre ni vuelve a ejecutar la decisión.

## Implementation planning

1. **W0 schema:** diseñar tipos y discriminadores, versiones snapshot/replay,
   decoder legacy, rechazo cerrado y migración de store.
2. **W1 lifecycle:** implementar creación y cierre transaccional sin integrar
   todavía modelos especializados.
3. **Fronteras:** comandos, eventos, DTO, application/service y proyecciones
   separadas con errores uniformes.
4. **Verificación:** round-trip, golden replay legacy/nuevo, propiedades de los
   catorce invariantes, carreras CAS y pruebas de no interferencia privada.
5. **Integración posterior:** evaluar cada modelo existente individualmente;
   ninguna integración es implícita y mulligan requiere nueva autorización.

La planificación no autoriza cambios actuales bajo `src/`, `tests/` de runtime,
schema, stores, endpoints ni versión de paquete.

## Files changed and prohibited runtime scope

| Ruta | Operación | Clasificación |
|---|---|---|
| `docs/audits/PHASE_2C_CAP_ACTION_004_CONTRACT_AUDIT_2026-09-07.md` | Modificado/reemplazado | Documentación de auditoría |
| `docs/audits/PHASE_2C_CAP_ACTION_004_TRACEABILITY_2026-09-07.md` | Añadido | Trazabilidad documental |

No se modifica ningún archivo de `src/`, persistencia, storage, aplicación,
servicio, schema, fixtures ni tests de runtime. La lista anterior es exhaustiva.

## Real verification results

Resultados capturados el 2026-09-08, después de redactar ambos documentos:

| Orden | Comando real | Código | Salida capturada |
|---|---|---:|---|
| 1 | `uv run pytest -q tests/test_phase_2c_engine_evolution_roadmap.py` | `0` | `13 passed in 0.19s` |
| 2 | `uv run python scripts/verify_release.py --profile full` | `1` | Primer intento detenido en `quality:mypy`: `No module named mypy`. |
| 3 | `uv sync --extra dev` | `0` | 14 dependencias de desarrollo instaladas, incluido `mypy==2.3.0`. |
| 4 | `uv run python scripts/verify_release.py --profile full` | `0` | `OK: perfil full completado`. |

El intento 2 es una limitación inicial del entorno, no un resultado omitido ni
un fallo del contrato. El resultado oficial del perfil es la repetición 4 tras
sincronizar las dependencias declaradas. Las comprobaciones documentales de
estructura, cobertura de requisitos, rutas modificadas y última línea se
ejecutaron después de incorporar esta tabla y también finalizaron con código
`0`; se detallan en la matriz de trazabilidad.

## Remaining blockers

- `CAP-ACTION-004` continúa **`MISSING`**: este contrato `READY` no constituye
  implementación, cierre ni promoción de capability.
- No existe runtime universal de decisión pendiente: no hay todavía modelo,
  comando, evento, codec, snapshot/replay versionado, migración, endpoint ni
  recorrido application/service/storage de `CAP-ACTION-004`.
- Esta entrega **no altera los blockers de mulligan**. `CAP-TIME-002` permanece
  `PARTIAL / WAIT-PREREQ`; `CAP-TIME-005` permanece `MISSING / WAIT-PREREQ` y
  siguen abiertos `N-MULLIGAN-01.OPEN-ORDER`, `OPEN-MODE`, `OPEN-REVEAL` y
  `OPEN-STARTER`. No existe autorización transitiva para `N-PHASE-02`.
- La implementación futura debe superar W0, los catorce invariantes, privacidad,
  compatibilidad histórica y pruebas concurrentes antes de reevaluar el gate.

## Final verdict

Todas las comprobaciones documentales pasaron. El contrato queda preparado para
planificar runtime, sin autorizarlo ni alterar el estado `MISSING` o los blockers
de mulligan.

CAP-ACTION-004 CONTRACT READY FOR RUNTIME IMPLEMENTATION PLANNING
