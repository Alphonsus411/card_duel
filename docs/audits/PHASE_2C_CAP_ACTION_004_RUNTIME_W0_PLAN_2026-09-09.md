# Plan runtime W0 de `CAP-ACTION-004` — 2026-09-09

## A. Estado real

- **HECHO OBSERVADO — baseline:** la revisión auditada es `7ae37497ed6aa5d69fb16ac42a715998e63141b4`, su tree SHA es `642867e95a633148eadcac90c9aebfa681c6b117`, la fecha Git es `2026-09-09T11:38:57+02:00`, la versión es `0.20.1` y la rama local examinada es `work`.
- **HECHO OBSERVADO — alcance:** este documento es un plan W0; no modifica runtime, schema, datos, API, tests funcionales ni versión.
- **HECHO OBSERVADO — fase:** Fase 2C sigue `IN_PROGRESS` y Fase 3 sigue `PENDING` en el baseline.
- **HECHO OBSERVADO — capability objetivo:** `CAP-ACTION-004` está `MISSING`, gate `READY`, riesgo `CRITICAL`, prioridad `P0` y wave propuesta `W1`; `READY` sólo corresponde al contrato, no equivale a implementación.
- **HECHO OBSERVADO — prerequisites:** `CAP-ACTION-002` y `CAP-PRIVACY-001` están `SUPPORTED / CLOSED`; son los dos prerequisites directos de `CAP-ACTION-004`.
- **HECHO OBSERVADO — dependientes:** `CAP-SECRET-002` y `CAP-TIME-002` son los dos dependientes directos de `CAP-ACTION-004`.
- **HECHO OBSERVADO — timing:** `CAP-TIME-002` está `PARTIAL / WAIT-PREREQ`, riesgo `HIGH`, prioridad `P1`, wave `W2`; `CAP-TIME-005` está `MISSING / WAIT-PREREQ`, riesgo `CRITICAL`, prioridad `P0`, wave `W1`.
- **HECHO OBSERVADO — corpus:** `CAP-ACTION-004` acredita 0 entradas directas y alcance indirecto potencial sobre 431 entradas, compuestas por 386 identidades y 45 variantes, sin promoción ni suma automática.
- **HECHO OBSERVADO — censo de capabilities:** `docs/ENGINE_CAPABILITY_MATRIX.csv` contiene exactamente 64 filas: 28 `SUPPORTED`, 20 `PARTIAL`, 10 `MISSING` y 6 `BLOCKED`; sus gates son 28 `CLOSED`, 17 `WAIT-PREREQ`, 12 `NORM-BLOCKED` y 7 `READY`.
- **HECHO OBSERVADO — contraste de cifras:** los valores 2 `SUPPORTED`, 245 `PARTIAL`, 143 `MISSING`, 41 `AMBIGUOUS` y 0 `CONFLICT` publicados al inicio del roadmap describen las 431 entradas del corpus, no las 64 capabilities; no deben compararse como si fueran el mismo censo.

## B. Veredicto

- **CONTRATO APROBADO — autorización:** W0 queda listo para planificación detallada únicamente si conserva los prerequisites, invariantes, compatibilidad y gates de este documento; no queda autorizada una implementación runtime por este archivo.
- **CONTRATO APROBADO — límite:** el primitive universal cubre identidad, elector, audiencia, opciones opacas, estado, vínculo de versión, persistencia, snapshot, replay y CAS exactamente una vez.
- **CONTRATO APROBADO — exclusiones:** candidatos de cartas, cardinalidad compleja, ordenación, selección compuesta, `simultaneous reveal` y semántica de búsquedas quedan fuera y permanecen en `CAP-SECRET-002` u otras especializaciones.
- **HECHO OBSERVADO — mulligan:** este veredicto no desbloquea `CAP-TIME-002`; continúan abiertos `CAP-ACTION-004`, `CAP-TIME-005` y las preguntas normativas de mulligan.

## C. Mapa arquitectónico

| Capa | Estado auditado | Destino W0 | Etiqueta |
|---|---|---|---|
| `domain/models.py` | `GameState` contiene `pending_search` y `pending_move_replacement`, pero no un registro universal. | Añadir el tipo de decisión y un campo opcional sin sustituir los modelos especializados. | **PROPUESTA** |
| `domain/enums.py` | No hay discriminadores universales de familia, estado o audiencia. | Añadir enums cerrados y versionados sólo si el codec preserva rechazo de desconocidos. | **PROPUESTA** |
| `engine/commands.py` | Existen comandos especializados y el historial acepta un conjunto cerrado. | Añadir un comando tipado de cierre con `decision_id`, token opaco y `expected_version` en la frontera apropiada. | **PROPUESTA** |
| `engine/actions.py` y `engine/options.py` | Enumeran/revalidan acciones y producen opciones remotas opacas, no decisiones persistidas. | Exponer sólo al elector una opción legal para cerrar la decisión vigente. | **PROPUESTA** |
| `engine/game.py` | Ejecuta con copia/rollback y valida invariantes; no posee lifecycle universal. | Crear/cerrar la decisión dentro de la transacción de dominio, sin ejecutar la mecánica especializada al cerrarla. | **PROPUESTA** |
| `application.py` | Autentica actores y traduce option IDs ligados a actor/versión. | Resolver token de transporte sin convertirlo en autoridad ni filtrar el payload. | **PROPUESTA** |
| `service.py` | Carga, ejecuta y guarda con `expected_version`. | Mantener una sola operación de guardado CAS y errores públicos uniformes. | **PROPUESTA** |
| `persistence/codec.py` | Serializa dataclasses/enums mediante discriminadores cerrados. | Registrar los tipos nuevos y rechazar discriminadores o versiones desconocidos. | **PROPUESTA** |
| `persistence/snapshot.py` | Escribe schema `2`, checksum y `state_digest`. | Elevar schema al primer número disponible y decodificar schema `2` con ausencia explícita. | **PROPUESTA** |
| `persistence/replay.py` | Escribe schema `2` y reconstruye desde setup, mulligans y comandos. | Elevar schema junto con snapshot y conservar lifecycle/observables deterministas. | **PROPUESTA** |
| `persistence/migrations.py` | Migra explícitamente schema `1 → 2`; no adivina rutas ausentes. | Añadir migraciones explícitas al nuevo schema, puras e idempotentes a nivel de resultado. | **PROPUESTA** |
| `storage/base.py` y `storage/sqlite.py` | Persisten el snapshot completo y ya ofrecen CAS. | Reutilizar el CAS; no crear una segunda tabla autoritativa de decisiones en W0. | **PROPUESTA** |
| `presentation.py` y DTO de servicio | Proyectan estado según actor, pero no este primitive. | Añadir vistas separadas para elector, adversario, público y motor. | **PROPUESTA** |

- **HECHO OBSERVADO — reutilización:** `PendingSearch`, `PendingMoveReplacement`, targets, orden de triggers, orden de replacements y action option IDs muestran fragmentos útiles, pero ninguno satisface el contrato universal completo.
- **CONTRATO APROBADO — independencia:** los modelos especializados permanecen independientes en la primera implementación; sólo podrán migrarse con equivalencia demostrada de snapshot, eventos, observables y replay.

## D. Modelo autoritativo

| Campo | Regla | Etiqueta |
|---|---|---|
| `decision_id` | Identidad estable, inmutable y determinista a partir del origen y su posición canónica. | **CONTRATO APROBADO** |
| `semantic_family` | Familia y versión de semántica; nunca `card_id`. | **CONTRATO APROBADO** |
| `authorized_elector` | Único actor que puede solicitar el cierre. | **CONTRATO APROBADO** |
| `audience` | Política autoritativa de existencia y campos visibles. | **CONTRATO APROBADO** |
| `authorized_opaque_options` | Conjunto congelado de tokens únicos, opacos y no reversibles. | **CONTRATO APROBADO** |
| `state_version` | Vínculo exacto a la versión que autoriza la decisión. | **CONTRATO APROBADO** |
| `origin` | Referencia estable al hecho creador. | **CONTRATO APROBADO** |
| `status` | Sólo `pending` o `closed`; `closed` es terminal. | **CONTRATO APROBADO** |
| `selected_option` | `None` en `pending`; exactamente una opción autorizada en `closed`. | **CONTRATO APROBADO** |

- **CONTRATO APROBADO — autoridad única:** debe existir una sola representación persistida; cachés, snapshots serializados, replay, DTO y proyecciones no son autoridades alternativas.
- **CONTRATO APROBADO — derivados:** validez, acciones legales, vistas redactadas e índices abiertos se recalculan y no se persisten como otra verdad.
- **CONTRATO APROBADO — transitorios:** request IDs, locks, leases, sesiones, cachés, reintentos, wall-clock y tokens de transporte no forman parte del modelo.
- **CONTRATO APROBADO — lifecycle:** sólo existe `pending → closed`; no se introducen estados `expired` o `cancelled`. La invalidación ocurre por revalidación/versionado y un rechazo no muta.
- **PROPUESTA — forma:** introducir una dataclass inmutable `PendingDecision` o nombre equivalente y una colección indexada por `decision_id`; el nombre y si la cardinalidad inicial es una o varias decisiones deben cerrarse antes de código.
- **PREGUNTA ABIERTA — cardinalidad de infraestructura:** el contrato no fija si `GameState` admite exactamente una decisión universal simultánea o un mapa ordenado de varias; la decisión debe basarse en casos W1 sin absorber selección compuesta.

## E. Integración con `GameState`

- **HECHO OBSERVADO — estado actual:** `GameState` persiste `pending_search`, `pending_move_replacement`, `pending_triggers`, `event_log`, `command_history` y `setup_mulligans`; no existe `pending_decision`.
- **PROPUESTA — cambio aditivo:** añadir `pending_decision: PendingDecision | None = None` al final de los campos con default, preservando construcción posicional histórica y sin eliminar campos existentes.
- **CONTRATO APROBADO — invariantes:** `validate_invariants()` debe comprobar elector existente, tokens únicos/no vacíos conforme a la familia, coherencia `status/selected_option`, origen resoluble, identidad estable y vínculo de versión.
- **CONTRATO APROBADO — rollback:** creación y cierre se realizan dentro del snapshot transaccional existente de `GameEngine.execute`; cualquier error restaura estado, historial, eventos y contadores.
- **CONTRATO APROBADO — no duplicación:** ningún handler puede mantener la misma decisión viva simultáneamente en el campo universal y en un pending especializado.
- **PROPUESTA — eventos:** crear eventos tipados de creación y cierre con payload interno completo, más una proyección redactada; no emitir un evento de cierre antes de que la transacción y el CAS puedan confirmarse.
- **PREGUNTA ABIERTA — publicación del evento:** hay que fijar si el evento de dominio se acumula antes del `save` y sólo se publica fuera de proceso después del CAS, o si no existe bus externo; W0 debe impedir observables fantasma del perdedor CAS.

## F. Snapshot

- **HECHO OBSERVADO — formato:** snapshot usa `SNAPSHOT_SCHEMA_VERSION = "2"`, sobre `{body, sha256}`, JSON canónico, `state_digest`, versión de motor, semántica, reglas, catálogo, estado y contadores.
- **PROPUESTA — versión:** el primer writer con decisión universal elevará `SNAPSHOT_SCHEMA_VERSION` de `2` a `3`; snapshot y replay deben cambiar en la misma entrega.
- **CONTRATO APROBADO — lectura legacy:** la migración `2 → 3` añade exactamente la ausencia compatible de decisión universal; no infiere una decisión desde `pending_search`, `pending_move_replacement`, comandos o eventos.
- **CONTRATO APROBADO — fidelidad:** el round-trip debe conservar exactamente identidad, familia, elector, audiencia, opciones, versión, origen, estado y selección, además del digest canónico.
- **CONTRATO APROBADO — rechazo cerrado:** schema, enum, discriminador o semántica desconocidos se rechazan antes de instalar estado en el motor.
- **PROPUESTA — fixtures:** conservar fixtures golden de schema `1`, `2` y `3`, incluidos estados `pending` y `closed`, checksum corrupto y discriminadores desconocidos.

## G. Replay

- **HECHO OBSERVADO — formato:** replay usa `REPLAY_SCHEMA_VERSION = "2"`, conserva setup, mulligans, inicio, comandos, conteo y digest final; acepta el escape histórico de digest sólo para `0.20.0` y `0.20.1`.
- **PROPUESTA — versión:** elevar replay a schema `3` y representar la creación/cierre mediante comandos/eventos deterministas suficientes para reconstruir la misma decisión.
- **CONTRATO APROBADO — identidad:** `decision_id` no puede depender de UUID aleatorio, wall-clock, orden de diccionario no canónico ni secreto de proceso.
- **CONTRATO APROBADO — semántica histórica:** un replay schema `1/2` no gana decisiones retroactivas; se ejecuta con su semántica declarada y conserva sus bytes como artefacto histórico.
- **CONTRATO APROBADO — resultado:** replay nuevo debe reproducir estado, selección, orden observable de eventos y `final_digest`; una versión desconocida falla sin fallback.
- **PROPUESTA — golden pair:** para cada caso nuevo, guardar un golden pre-W0 legible y otro schema `3`, y comprobar determinismo byte a byte cuando el formato lo garantice y equivalencia semántica mediante digest.

## H. Migraciones

- **HECHO OBSERVADO — mecanismo:** `migrate_document()` copia el body y recorre una tabla explícita; hoy sólo hay rutas `snapshot/replay/manifest 1 → 2`.
- **PROPUESTA — rutas:** añadir `("snapshot", "2")` y `("replay", "2")` hacia `3`; no cambiar las funciones `1 → 2`, para mantener composición histórica `1 → 2 → 3`.
- **CONTRATO APROBADO — propiedades:** migración determinista, no destructiva, transaccional en storage, repetible sin cambiar el resultado y con rollback operativo documentado.
- **CONTRATO APROBADO — desconocidos:** ausencia de ruta, ciclo o versión no textual produce error; queda prohibido adivinar defaults salvo el `None` legacy aprobado.
- **PROPUESTA — despliegue:** desplegar reader `1/2/3` antes o junto al writer `3`; no permitir que un binario viejo reescriba snapshots `3`.
- **PREGUNTA ABIERTA — rollback de despliegue:** debe elegirse entre compatibilidad de writer dual temporal o rollback sólo hacia delante; no hay autoridad en los documentos auditados para writer dual.

## I. Storage/SQLite

- **HECHO OBSERVADO — diseño:** `SQLiteMatchStore` mantiene una fila por partida con `match_id`, `version`, `snapshot` y `updated_at`; la autoridad de dominio está dentro del snapshot.
- **CONTRATO APROBADO — unidad:** W0 no crea tabla de decisiones ni columna JSON paralela; hacerlo produciría dos autoridades y violaría `CAP-ACTION-004-INV-01`.
- **PROPUESTA — migración:** si sólo cambia el payload, no hace falta DDL; el reader migra el snapshot en memoria y el siguiente CAS confirmado escribe schema `3`.
- **CONTRATO APROBADO — atomicidad:** una actualización confirmada debe incluir conjuntamente snapshot con decisión cerrada, historial, eventos y nueva `version`.
- **PROPUESTA — operabilidad:** medir tamaño de snapshot y latencia de carga/guardado antes y después; documentar backup y restauración sobre una copia real de SQLite.
- **PREGUNTA ABIERTA — persistencia eager:** decidir si los snapshots schema `2` se actualizan mediante job transaccional o sólo al siguiente write; la opción recomendada es lazy migration para evitar una mutación masiva sin necesidad.

## J. CAS

- **HECHO OBSERVADO — contrato vigente:** stores validan `expected_version` como entero positivo; SQLite usa `BEGIN IMMEDIATE` y `UPDATE ... WHERE match_id = ? AND version = ?`.
- **CONTRATO APROBADO — cierre único:** dos cierres con la misma versión compiten por un único CAS; sólo uno persiste `closed`, selección, eventos, historial y versión incrementada.
- **CONTRATO APROBADO — perdedor:** el perdedor recibe `stale-version`/`VersionConflict` y no reintenta automáticamente con la versión nueva ni simula éxito.
- **CONTRATO APROBADO — reintento:** una petición posterior puede leer el estado terminal, pero no reabrir, repetir efectos ni añadir otro cierre.
- **PROPUESTA — servicio:** ejecutar sobre la copia cargada y publicar cualquier observable externo únicamente después de `store.save`; el fallo de CAS descarta la copia candidata.
- **PROPUESTA — prueba crítica:** barrera de dos clientes sobre SQLite, misma decisión/token/versión, exactamente un éxito, una versión final incrementada una vez y un solo evento de cierre.

## K. Privacidad

| Audiencia | Máximo observable | Etiqueta |
|---|---|---|
| Elector | Identidad pública, lifecycle y tokens opacos vigentes. | **CONTRATO APROBADO** |
| Adversario | Sólo existencia, estado o resultado que la familia declare públicos. | **CONTRATO APROBADO** |
| Público | Subconjunto público estable, sin privilegios de participante. | **CONTRATO APROBADO** |
| Motor | Registro autoritativo completo. | **CONTRATO APROBADO** |

- **CONTRATO APROBADO — opacidad:** tokens no son reversibles ni correlacionables con IDs ocultos y deben ligarse a partida, elector, decisión y versión.
- **CONTRATO APROBADO — errores:** decisión invisible, actor ajeno, token inexistente o malformado exponen la misma forma pública; `stale-version` puede distinguirse porque sólo revela CAS.
- **CONTRATO APROBADO — observabilidad:** logs, trazas, métricas, excepciones y replay público redactan candidatos, cardinalidad, IDs internos, payloads y tokens de otras audiencias.
- **PROPUESTA — pruebas:** comparar serializaciones y errores de dos mundos que sólo difieren en datos secretos para probar no interferencia.

## L. Compatibilidad histórica

- **HECHO OBSERVADO — ventana:** el baseline conserva semántica `LEGACY_019` y una excepción limitada de digest para replay `0.20.0/0.20.1`.
- **CONTRATO APROBADO — inmutabilidad:** no reescribir, regenerar ni enriquecer snapshots/replays históricos con decisiones o eventos retroactivos.
- **CONTRATO APROBADO — default:** documentos anteriores al nuevo schema cargan con decisión universal ausente; una búsqueda/replacement pendiente histórica conserva sólo su modelo propio.
- **CONTRATO APROBADO — IDs:** los IDs `CAP-ACTION-004-INV-01` a `CAP-ACTION-004-INV-14`, `decision_id`, opciones y orden de eventos nuevos no se renumeran ni reciclan.
- **PROPUESTA — soporte:** declarar explícitamente la matriz de readers/writers y mantener fixtures de todas las versiones soportadas en CI.

## M. Matriz de compatibilidad

| Productor | Lector W0 futuro | Resultado exigido | Escritura posterior | Etiqueta |
|---|---|---|---|---|
| Snapshot schema `1` | Reader `3` | Migra `1 → 2 → 3`; decisión ausente. | Writer `3` sólo tras CAS exitoso. | **PROPUESTA** |
| Snapshot schema `2` | Reader `3` | Migra `2 → 3`; decisión ausente. | Writer `3` sólo tras CAS exitoso. | **PROPUESTA** |
| Snapshot schema `3` | Reader `3` | Restaura `pending`/`closed` fielmente. | Writer `3`. | **PROPUESTA** |
| Snapshot schema `3` | Reader `2` | Incompatible; debe fallar, nunca degradar. | Ninguna. | **CONTRATO APROBADO** |
| Replay schema `1` | Reader `3` | Migra y reproduce semántica histórica sin decisión. | No reescribe el artefacto. | **PROPUESTA** |
| Replay schema `2` (`0.20.0/0.20.1`) | Reader `3` | Conserva compatibilidad de digest limitada existente. | No reescribe el artefacto. | **CONTRATO APROBADO** |
| Replay schema `3` | Reader `3` | Reconstruye lifecycle, observables y digest. | No aplica. | **PROPUESTA** |
| Schema o discriminador desconocido | Cualquier reader | Rechazo sin mutación ni fallback. | Ninguna. | **CONTRATO APROBADO** |
| In-memory store | Servicio nuevo | Misma semántica CAS que SQLite. | Snapshot schema `3`. | **PROPUESTA** |
| SQLite existente con payload `2` | Servicio nuevo | Lazy decode/migration; fila intacta hasta write. | Actualización única bajo CAS. | **PROPUESTA** |

## N. Tests

| Grupo | Casos mínimos | Gate | Etiqueta |
|---|---|---|---|
| Modelo | Campos, inmutabilidad, tokens únicos, coherencia de estado, origen y elector. | Todos pasan. | **PROPUESTA** |
| Invariantes | Una prueba/property por cada `CAP-ACTION-004-INV-01`–`14`. | 14/14 cubiertos nominalmente. | **CONTRATO APROBADO** |
| Snapshot | Round-trip `pending/closed`, schema `1/2/3`, checksum/digest corruptos, unknown version. | Sin pérdida ni fallback. | **PROPUESTA** |
| Replay | Golden legacy/nuevo, identidad estable, eventos ordenados, digest final, ejecución repetida. | Resultado determinista. | **PROPUESTA** |
| Migración | `1 → 2 → 3`, `2 → 3`, input no mutado, doble aplicación equivalente, ruta ausente. | Todos pasan. | **PROPUESTA** |
| Autorización | Elector correcto/incorrecto, partida/decisión cruzadas, opción ajena/malformada. | Rechazos sin mutación. | **PROPUESTA** |
| Privacidad | Vistas de cuatro audiencias, logs/excepciones, no interferencia. | Cero fuga. | **PROPUESTA** |
| CAS | Dos clientes en memoria y SQLite; mismo y distinto token. | Un cierre y un incremento. | **PROPUESTA** |
| Servicio | Error uniforme, no auto-retry, no publicación antes de CAS. | Paridad entre stores. | **PROPUESTA** |
| Regresión | Suite completa, test documental de roadmap y perfil full. | Sin regresiones. | **CONTRATO APROBADO** |

- **PROPUESTA — comandos de aceptación:** ejecutar `uv run pytest -q tests/test_phase_2c_engine_evolution_roadmap.py`, tests focalizados nuevos, `uv run pytest -q` y `uv run python scripts/verify_release.py --profile full`.
- **CONTRATO APROBADO — evidencia:** ningún test futuro permite reclasificar `CAP-ACTION-004` hasta demostrar recorrido público, persistente, replayable, privado y de servicio completo.

## O. Secuencia por archivos

1. **PROPUESTA — `domain/enums.py` y `domain/models.py`:** definir discriminadores, registro y validación local sin integrar especializaciones.
2. **PROPUESTA — `persistence/codec.py`:** registrar tipos con dispatch cerrado; añadir tests negativos antes de writers.
3. **PROPUESTA — `persistence/migrations.py`:** implementar rutas `2 → 3` y tests de composición histórica.
4. **PROPUESTA — `persistence/snapshot.py`:** elevar versión, escribir/restaurar el registro y añadir goldens.
5. **PROPUESTA — `engine/commands.py`:** añadir comando de cierre al conjunto ejecutable y codec.
6. **PROPUESTA — `engine/game.py`:** creación, revalidación, cierre y rollback; cerrar sólo registra opción.
7. **PROPUESTA — `persistence/replay.py`:** elevar versión y demostrar reconstrucción determinista.
8. **PROPUESTA — `engine/actions.py` y `engine/options.py`:** paridad entre enumeración y ejecución.
9. **PROPUESTA — `presentation.py`, `application.py` y `service.py`:** audiencias, autenticación, error uniforme y un único CAS.
10. **PROPUESTA — `storage/base.py` y `storage/sqlite.py`:** evitar cambios salvo los necesarios para pruebas/observabilidad; preservar el UPDATE CAS actual.
11. **PROPUESTA — `tests/`:** propiedades, goldens, privacidad, carreras y paridad de stores.
12. **PROPUESTA — `docs/`:** actualizar matriz, dependencias, roadmap y auditoría sólo después de evidencia; no promover por intención.

- **CONTRATO APROBADO — disciplina:** cada paso debe mantener verde el reader histórico; ningún commit intermedio puede escribir schema `3` sin poder leerlo y restaurarlo.

## P. Riesgos

| Riesgo | Impacto | Mitigación | Etiqueta |
|---|---|---|---|
| Dos fuentes autoritativas | Split-brain entre `GameState` y tabla/modelo especializado. | Un único registro; especializaciones independientes. | **CONTRATO APROBADO** |
| ABA o ID inestable | Cierre de otra decisión tras replay/reconexión. | Derivación canónica y tests golden. | **CONTRATO APROBADO** |
| Fuga por opciones/errores | Revelación de mano, candidatos o cardinalidad. | Tokens opacos, proyección y no interferencia. | **CONTRATO APROBADO** |
| Evento fantasma tras CAS perdido | Cliente observa un cierre no persistido. | Publicación post-CAS y copia candidata descartable. | **PROPUESTA** |
| Migración irreversible | Partidas ilegibles o rollback imposible. | Reader previo, backup, lazy migration y fixtures. | **PROPUESTA** |
| Inferencia legacy | Reapertura o reinterpretación histórica. | Default `None`, sin heurísticas. | **CONTRATO APROBADO** |
| Acoplar mecánica al cierre | Efectos dobles o atomicidad falsa. | Cierre sólo registra opción; continuación separada. | **CONTRATO APROBADO** |
| Promoción prematura de mulligan | Se ignoran setup y dudas normativas. | Mantener `CAP-TIME-002 / CAP-TIME-005` abiertos. | **CONTRATO APROBADO** |
| Crecimiento del snapshot | Latencia y contención SQLite. | Benchmark de payload/CAS y límites explícitos. | **PROPUESTA** |

## Q. Gates

| Gate | Criterio de entrada/salida | Estado en este plan | Etiqueta |
|---|---|---|---|
| `W0-GATE-BASELINE` | SHA/tree/fecha/versión/rama y fixtures históricos fijados. | Listo. | **HECHO OBSERVADO** |
| `W0-GATE-CONTRACT` | Campos, exclusiones e invariantes `01`–`14` sin contradicción. | Listo con preguntas de forma no semántica. | **CONTRATO APROBADO** |
| `W0-GATE-SCHEMA` | Numeración, readers, writers, migraciones y unknown-version tests. | Pendiente de implementación. | **PROPUESTA** |
| `W0-GATE-PRIVACY` | Proyecciones y no interferencia para cuatro audiencias. | Pendiente de implementación. | **PROPUESTA** |
| `W0-GATE-CAS` | Carrera real en memoria/SQLite con un único ganador y sin evento fantasma. | Pendiente de implementación. | **PROPUESTA** |
| `W0-GATE-HISTORY` | Goldens schema `1/2/3`, replay/digest y rollback operativo. | Pendiente de implementación. | **PROPUESTA** |
| `W0-GATE-QUALITY` | Suite completa y perfil full verdes. | Pendiente de la futura entrega runtime. | **PROPUESTA** |
| `CAP-ACTION-004 CLOSED` | Recorrido completo público, persistente, replayable, privado y de servicio. | No alcanzado; sigue `MISSING / READY`. | **HECHO OBSERVADO** |
| `CAP-TIME-002 READY` | `CAP-ACTION-004` y `CAP-TIME-005` cerradas y autorización expresa posterior. | No alcanzado; sigue `PARTIAL / WAIT-PREREQ`. | **HECHO OBSERVADO** |

## R. Deudas

- **HECHO OBSERVADO — primitive ausente:** todavía no existen modelo, comando, evento, codec, snapshot/replay versionado, migración ni recorrido application/service universal.
- **HECHO OBSERVADO — setup:** `CAP-TIME-005` carece del lifecycle completo que crea participantes/mazos/manos, mantiene `SETUP`, registra decisiones y prepara la transición sin conceder prioridad.
- **HECHO OBSERVADO — mulligan:** `CAP-TIME-002` posee contador, restricción a setup, tamaños 5→1, reshuffle determinista, evento y persistencia/replay básicos, pero carece de KEEP/REPLACE público, pending universal, paridad legal, CAS específico, capas completas, privacidad y compatibilidad versionada.
- **PREGUNTA ABIERTA — orden:** `N-MULLIGAN-01.OPEN-ORDER` continúa abierta.
- **PREGUNTA ABIERTA — modo:** `N-MULLIGAN-01.OPEN-MODE` continúa abierta.
- **PREGUNTA ABIERTA — revelación:** `N-MULLIGAN-01.OPEN-REVEAL` continúa abierta.
- **PREGUNTA ABIERTA — jugador inicial:** `N-MULLIGAN-01.OPEN-STARTER` continúa abierta y la selección/concesión de prioridad permanece separada en `CAP-TIME-001`.
- **PREGUNTA ABIERTA — forma del registro:** resolver una decisión única frente a colección ordenada sin introducir selección compuesta.
- **PREGUNTA ABIERTA — operación:** cerrar política de rollback/forward y momento de publicación de eventos tras CAS.
- **CONTRATO APROBADO — efecto de las deudas:** estas preguntas bloquean los tramos afectados y la promoción de capabilities, pero no bloquean preparar schema, compatibilidad, privacidad y pruebas W0 conforme a este plan.

## S. Evidencias

| Evidencia contrastada en `7ae37497ed6aa5d69fb16ac42a715998e63141b4` | Resultado | Etiqueta |
|---|---|---|
| `docs/ENGINE_CAPABILITY_MATRIX.csv` | 64 capabilities; estados/gates/corpus y aristas de las tres capabilities coinciden con los registros de A. | **HECHO OBSERVADO** |
| `docs/ENGINE_CAPABILITY_DEPENDENCIES.md` | Confirma aristas `CAP-ACTION-002/CAP-PRIVACY-001 → CAP-ACTION-004 → CAP-SECRET-002/CAP-TIME-002` y `CAP-TIME-005 → CAP-TIME-002`; declara independencia entre `CAP-ACTION-004` y `CAP-TIME-005`. | **HECHO OBSERVADO** |
| `docs/PHASE_2C_ENGINE_EVOLUTION_ROADMAP.md` | Confirma las 64 capabilities, W0 de versionado/invariantes, W1 para el primitive y W2 para timing condicionado; distingue corpus de capabilities. | **HECHO OBSERVADO** |
| `docs/audits/PHASE_2C_CAP_ACTION_004_CONTRACT_AUDIT_2026-09-07.md` | Congela nueve campos, catorce invariantes, exclusiones, estrategia de modelos existentes, compatibilidad, privacidad y CAS; prohíbe runtime en aquella entrega contractual. | **HECHO OBSERVADO** |
| `docs/audits/PHASE_2C_CAP_ACTION_004_TRACEABILITY_2026-09-07.md` | Traza individualmente requisitos e invariantes y conserva `CAP-ACTION-004 MISSING`, `CAP-TIME-002 PARTIAL / WAIT-PREREQ` y `CAP-TIME-005 MISSING / WAIT-PREREQ`. | **HECHO OBSERVADO** |
| `docs/audits/PHASE_2C_FIRST_SLICE_READINESS_AUDIT_2026-09-07.md` | Mantiene `N-PHASE-02 IMPLEMENTATION BLOCKED` por prerequisites técnicos y cuatro preguntas normativas. | **HECHO OBSERVADO** |
| `src/card_duel_engine/domain/models.py` | Acredita los pending especializados y la ausencia del universal en `GameState`. | **HECHO OBSERVADO** |
| `src/card_duel_engine/persistence/{snapshot,replay,migrations}.py` | Acredita schema `2`, migraciones explícitas, checksums/digests, replay por comandos y compatibilidad histórica limitada. | **HECHO OBSERVADO** |
| `src/card_duel_engine/storage/{base,sqlite}.py` | Acredita snapshot como payload autoritativo y CAS por `expected_version`. | **HECHO OBSERVADO** |

- **HECHO OBSERVADO — consistencia:** no aparece evidencia objetiva nueva que cierre las preguntas normativas, cambie el estado de las tres capabilities o active una condición adicional de bloqueo para la planificación W0.
- **CONTRATO APROBADO — regla de actualización:** cualquier cambio de arista, estado, schema o decisión normativa obliga a reauditar conjuntamente las cuatro fuentes principales y esta evidencia antes de implementar.

CAP-ACTION-004 W0 LISTO CON PRERREQUISITOS
