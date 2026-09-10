# Plan runtime W0 de `CAP-ACTION-004` — 2026-09-09

> **Convención temporal (actualizada tras PR #275).** Las secciones A–T son el
> **BASELINE DOCUMENTAL ANTERIOR**: conservan deliberadamente el diagnóstico y
> las propuestas redactados antes de que existiera el runtime W0. Cuando una
> frase de esas secciones dice «no existe», «propuesta» o «futuro», describe
> ese corte histórico y no el checkout actual. La sección U es la
> **EVIDENCIA RUNTIME POSTERIOR AL PR #275** y prevalece para determinar qué
> está implementado, probado o cerrado. No se borra ni se reinterpreta el texto
> anterior como si hubiese sido escrito después del merge.

## A. Estado real

- **HECHO OBSERVADO — baseline actualizado:** después de restaurar `origin` a `https://github.com/Alphonsus411/card_duel.git` y ejecutar `git fetch --prune origin`, `git remote show origin` resolvió `main` como rama por defecto. `origin/main` es `59c07af59690aafec9f35faf6af1bb8435c41eee`, su tree SHA es `f6c2f022f9f4af3b90d651d4918e9b7425b94d60` y su fecha Git es `2026-09-09T14:14:18+02:00`. El baseline anterior `7ae37497ed6aa5d69fb16ac42a715998e63141b4` se conserva como extremo inicial del compare y la rama local examinada es `work`.
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
| `persistence/snapshot.py` | **BASELINE DOCUMENTAL:** escribía schema `2`, checksum y `state_digest`. **RUNTIME POST-#275:** reader/writer ya operan en snapshot schema `3`. | Migración explícita de snapshots `1/2 → 3`; writer `3`. | **IMPLEMENTADO W0** |
| `persistence/replay.py` | **BASELINE Y RUNTIME POST-#275:** escribe schema `2` y reconstruye desde setup, mulligans y comandos. | Mantener reader/writer v2 hasta que W1 introduzca el primer comando/evento de decisión. | **IMPLEMENTADO SIN CAMBIO DE SCHEMA** |
| `persistence/migrations.py` | Migra explícitamente schema `1 → 2`; no adivina rutas ausentes. | Añadir migraciones explícitas al nuevo schema, puras e idempotentes a nivel de resultado. | **PROPUESTA** |
| `storage/base.py` y `storage/sqlite.py` | Persisten el snapshot completo y ya ofrecen CAS. | Reutilizar el CAS; no crear una segunda tabla autoritativa de decisiones en W0. | **PROPUESTA** |
| `presentation.py` y DTO de servicio | Proyectan estado según actor, pero no este primitive. | Añadir vistas separadas para elector, adversario, público y motor. | **PROPUESTA** |

- **HECHO OBSERVADO — reutilización:** `PendingSearch`, `PendingMoveReplacement`, targets, orden de triggers, orden de replacements y action option IDs muestran fragmentos útiles, pero ninguno satisface el contrato universal completo.
- **CONTRATO APROBADO — independencia:** los modelos especializados permanecen independientes en la primera implementación; sólo podrán migrarse con equivalencia demostrada de snapshot, eventos, observables y replay.

### C.1. Decisión arquitectónica explícita: autoridad y ubicación

| Alternativa | Ventajas | Costes/riesgos | Decisión W0 |
|---|---|---|---|
| `PendingDecision` dentro de `GameState` | Participa en el mismo grafo de dominio que jugadores, pila, historial y eventos; entra en el snapshot, checksum y `state_digest`; se confirma junto al resto del estado mediante el único `save(..., expected_version=...)`. | Aumenta el snapshot y obliga a versionar codec, snapshot y replay. | **ACEPTADA PROVISIONALMENTE** como única autoridad. La cardinalidad concreta queda sometida al gate C.2 antes de W0.1. |
| Estructura persistente independiente (incluida una tabla SQLite de decisiones) | Permitiría consultas o índices SQL directos y escrituras aisladas. | Divide el agregado entre dos documentos/autoridades; exige transacción, recuperación, migración y CAS coordinados para que snapshot y decisión no diverjan ni queden huérfanos. | **RECHAZADA** en W0. El snapshot completo ya es el documento autoritativo. |
| Derivar la decisión de la arquitectura existente (`command_history`, `event_log`, pila/replay u option IDs) | Evitaría añadir un campo persistido explícito. | Historial, eventos y replay describen o reconstruyen hechos, y las opciones son proyecciones; convertir cualquiera en autoridad implícita duplica semántica, dificulta revalidación y no ofrece un lifecycle universal inequívoco. | **RECHAZADA** como autoridad. Pueden seguir siendo evidencia, reconstrucción o proyección derivada. |
| Reutilizar `PendingSearch` o `PendingMoveReplacement` como contenedor universal | Ya están alojados en `GameState` y serializados con él. | Sus contratos son mecánicos y distintos; forzar el primitive universal alteraría snapshots/replays históricos y acoplaría migraciones no autorizadas. | **RECHAZADA**. Ambos modelos quedan sin migración ni integración. |

- **DECISIÓN ARQUITECTÓNICA PROVISIONAL — autoridad única:** `GameState` es el agregado y la única autoridad de `PendingDecision`. `domain/models.py` ya concentra en él los estados pendientes especializados; `persistence/snapshot.py` codifica el `GameState` completo dentro del documento protegido por checksum y `state_digest`; `storage/base.py` persiste ese snapshot como una unidad tanto al crear como al guardar; `storage/sqlite.py` mantiene una sola fila `matches(match_id, version, snapshot, updated_at)` y reemplaza el snapshot sólo mediante `UPDATE` condicionado por versión; finalmente, `MatchService.submit` carga el agregado, rechaza una versión obsoleta antes de ejecutar y entrega la copia resultante al único `store.save` CAS. Esa cadena permite confirmar o rechazar conjuntamente decisión, historial, eventos y estado, sin una segunda autoridad que coordinar.
- **RECHAZO EXPLÍCITO — tabla SQLite:** no se añadirá una tabla `decisions` ni una columna JSON paralela. Aunque pudiera compartir una transacción SQLite, seguiría creando dos representaciones autoritativas con invariantes de sincronización, permitiría referencias huérfanas y rompería la paridad con `InMemoryMatchStore`; el snapshot completo ya es el documento autoritativo que protege el CAS.
- **ALCANCE — especializaciones existentes:** `PendingSearch` y `PendingMoveReplacement` permanecen exactamente como están durante W0.1: no se migran, no se adaptan y no se integran en `PendingDecision`. Tampoco se infieren decisiones universales desde esos campos al leer documentos legacy.

### C.2. Gate de aprobación de cardinalidad antes de W0.1

- **BLOQUEO EXPLÍCITO — aprobación humana:** antes de modificar runtime, schema, migraciones o tests de W0.1 debe quedar registrada en este informe (o en una ADR enlazada) la aprobación explícita de **exactamente una** de estas formas:
  1. `pending_decision: PendingDecision | None`, para permitir como máximo una decisión universal viva en la partida; o
  2. una colección indexada por `decision_id` (por ejemplo, `dict[str, PendingDecision]` con serialización canónica), si los casos W1 demuestran decisiones simultáneas.
- **PROHIBICIÓN ESTRUCTURAL:** no se admite `list[PendingDecision]` mutable: no impone unicidad de `decision_id`, hace costosa/ambigua la búsqueda y deja que el orden de inserción se convierta accidentalmente en semántica observable.
- **GARANTÍAS DE LA OPCIÓN 1:** el slot único hace imposible una colisión entre dos decisiones vivas y no tiene orden interno que pueda variar; crear exige que el slot sea `None`, cerrar opera sobre el mismo `decision_id` y limpiar/reemplazar exige una transición validada dentro del agregado. Así se evitan duplicados y decisiones huérfanas por construcción.
- **GARANTÍAS DE LA OPCIÓN 2:** la clave del mapa es el `decision_id`; la inserción rechaza una clave ya presente y cada valor debe repetir/coincidir con su clave, por lo que la unicidad es estructural. Toda referencia se valida contra el mapa autoritativo y creación/cierre/eliminación ocurre en la misma mutación de `GameState`, evitando huérfanas. Persistencia, digest, replay, presentación y eventos recorren siempre claves ordenadas canónicamente, nunca el orden mutable de inserción, evitando orden no determinista.
- **ESTADO DEL GATE (W0.1): CERRADO.** Se adopta la opción 1, `pending_decision: PendingDecision | None`. Los primeros casos W1 sólo requieren una elección bloqueante a la vez; el slot es la mínima cardinalidad que impide por construcción colisiones, decisiones huérfanas y orden accidental. Una futura simultaneidad demostrada exigirá otra decisión arquitectónica y migración explícita, no un mapa anticipado.

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
- **PROPUESTA — forma:** introducir una dataclass inmutable `PendingDecision` o nombre equivalente dentro de `GameState`; su campo será exclusivamente una de las dos formas permitidas por C.2 tras aprobación explícita.
- **DECISIÓN W0 — cardinalidad de infraestructura:** `GameState` admite como máximo una decisión universal mediante un slot opcional. W1 no incorporará selección compuesta ni decisiones simultáneas.

## E. Integración con `GameState`

- **HECHO OBSERVADO — estado actual:** `GameState` persiste `pending_search`, `pending_move_replacement`, `pending_triggers`, `event_log`, `command_history` y `setup_mulligans`; no existe `pending_decision`.
- **DECISIÓN IMPLEMENTADA W0 — cambio aditivo:** añadir `pending_decision: PendingDecision | None = None` al final de los campos con default, preservando construcción posicional histórica y sin eliminar campos existentes.
- **CONTRATO APROBADO — invariantes:** `validate_invariants()` debe comprobar elector existente, tokens únicos/no vacíos conforme a la familia, coherencia `status/selected_option`, origen resoluble, identidad estable y vínculo de versión.
- **CONTRATO APROBADO — rollback:** creación y cierre se realizan dentro del snapshot transaccional existente de `GameEngine.execute`; cualquier error restaura estado, historial, eventos y contadores.
- **CONTRATO APROBADO — no duplicación:** ningún handler puede mantener la misma decisión viva simultáneamente en el campo universal y en un pending especializado.
- **PROPUESTA — eventos:** crear eventos tipados de creación y cierre con payload interno completo, más una proyección redactada; no emitir un evento de cierre antes de que la transacción y el CAS puedan confirmarse.
- **PREGUNTA ABIERTA — publicación del evento:** hay que fijar si el evento de dominio se acumula antes del `save` y sólo se publica fuera de proceso después del CAS, o si no existe bus externo; W0 debe impedir observables fantasma del perdedor CAS.

## F. Snapshot — W0.2

- **HECHO OBSERVADO — formato:** snapshot usa `SNAPSHOT_SCHEMA_VERSION = "2"`, sobre `{body, sha256}`, JSON canónico, `state_digest`, versión de motor, semántica, reglas, catálogo, estado y contadores.
- **PROPUESTA W0.2 — versión futura concreta:** después de aprobar e implementar en W0.1 la forma acordada de `GameState`, el primer writer de snapshot con ese campo fijará `SNAPSHOT_SCHEMA_VERSION = "3"`. Este cambio de snapshot no obliga a anticipar el cambio de replay: ambos formatos avanzan cuando su contenido runtime lo exige.
- **CONTRATO APROBADO W0.2 — lectura legacy explícita:** `src/card_duel_engine/persistence/migrations.py` incorporará la entrada `("snapshot", "2")` para la migración snapshot `2 → 3`. La función añadirá al `GameState` serializado la representación canónica de «sin decisiones» correspondiente al campo aprobado (slot `None` o mapa vacío), recalculará `state_digest` sobre el estado ya migrado, establecerá `schema_version = "3"` y conservará el sobre verificable: la frontera validará primero el `sha256` original y reconstruirá su checksum canónico alrededor del body migrado antes de persistirlo. No inferirá una decisión desde `pending_search`, `pending_move_replacement`, comandos o eventos.
- **CONTRATO APROBADO — fidelidad:** el round-trip debe conservar exactamente identidad, familia, elector, audiencia, opciones, versión, origen, estado y selección, además del digest canónico.
- **CONTRATO APROBADO — rechazo cerrado:** schema, enum, discriminador o semántica desconocidos se rechazan antes de instalar estado en el motor.
- **PROPUESTA — fixtures:** conservar fixtures golden de schema `1`, `2` y `3`, incluidos estados `pending` y `closed`, checksum corrupto y discriminadores desconocidos.
- **PROHIBICIÓN W0.2 — codec:** no añadir `GameState` a las excepciones ad hoc de `compatible_missing` en `persistence/codec.py`. La ausencia legacy se materializa únicamente mediante la migración explícita de schema; el codec seguirá rechazando campos requeridos ausentes tras migrar.

## G. Replay

- **HECHO OBSERVADO — formato:** replay usa `REPLAY_SCHEMA_VERSION = "2"`, conserva setup, mulligans, inicio, comandos, conteo y digest final; acepta el escape histórico de digest sólo para `0.20.0` y `0.20.1`.
- **CONTRATO APROBADO — calendario de versión:** replay permanece en schema `2` durante W0.1 mientras no exista ningún comando/evento runtime capaz de crear o cerrar una decisión. `REPLAY_SCHEMA_VERSION = "3"` se programa en la misma entrega que el primer comando/evento W1 que pueda crear o cerrar una decisión; sólo entonces se representará el lifecycle mediante comandos/eventos deterministas suficientes para reconstruirlo.
- **CONTRATO APROBADO — identidad:** `decision_id` no puede depender de UUID aleatorio, wall-clock, orden de diccionario no canónico ni secreto de proceso.
- **CONTRATO APROBADO — semántica histórica:** un replay schema `1/2` no gana decisiones retroactivas; se ejecuta con su semántica declarada y conserva sus bytes como artefacto histórico.
- **CONTRATO APROBADO — resultado:** replay nuevo debe reproducir estado, selección, orden observable de eventos y `final_digest`; una versión desconocida falla sin fallback.
- **PROPUESTA W1 — migración y goldens:** junto al primer comando/evento creador o cerrador, añadir en `src/card_duel_engine/persistence/migrations.py` la ruta `("replay", "2")` para replay `2 → 3`, fixtures golden v3 de creación y cierre, y validación obligatoria de `final_digest`. Se conservarán sin reescritura los replays golden `0.19.0`, y la excepción de digest seguirá limitada exclusivamente a artefactos `0.20.0`/`0.20.1`; no se ampliará a v3 ni a otras versiones.

## H. Migraciones

- **HECHO OBSERVADO — mecanismo:** `migrate_document()` copia el body y recorre una tabla explícita; hoy sólo hay rutas `snapshot/replay/manifest 1 → 2`.
- **PROPUESTA — rutas por wave:** en W0.2 añadir sólo `("snapshot", "2")` hacia `3`; conservar replay schema `2` durante W0.1. Añadir `("replay", "2")` hacia `3` en W1, junto al primer comando/evento capaz de crear o cerrar una decisión. No cambiar las funciones `1 → 2`, para mantener la composición histórica de cada formato cuando alcance v3.
- **CONTRATO APROBADO — propiedades:** la migración snapshot `2 → 3` será pura respecto de la entrada, determinista e idempotente a nivel de cadena (`migrate_document(..., "3")` aplicado al resultado no cambia bytes canónicos); recalculará el digest después de insertar la ausencia canónica y rechazará versiones desconocidas por ausencia de ruta. La persistencia será transaccional, no destructiva y con rollback operativo documentado; las mismas propiedades se exigirán a replay `2 → 3` cuando se incorpore en W1.
- **CONTRATO APROBADO — desconocidos:** ausencia de ruta, ciclo o versión no textual produce error; queda prohibido adivinar defaults salvo el `None` legacy aprobado.
- **PROPUESTA — despliegue:** desplegar reader `1/2/3` antes o junto al writer `3`; no permitir que un binario viejo reescriba snapshots `3`.
- **PREGUNTA ABIERTA — rollback de despliegue:** debe elegirse entre compatibilidad de writer dual temporal o rollback sólo hacia delante; no hay autoridad en los documentos auditados para writer dual.

## I. Storage/SQLite — W0.3

- **HECHO OBSERVADO — diseño:** `SQLiteMatchStore` mantiene una fila por partida con `match_id`, `version`, `snapshot` y `updated_at`; la autoridad de dominio está dentro del snapshot.
- **CONTRATO APROBADO — unidad:** W0 no crea tabla de decisiones ni columna JSON paralela; hacerlo produciría dos autoridades y violaría `CAP-ACTION-004-INV-01`.
- **CONTRATO APROBADO W0.3 — sin DDL:** no hace falta migración DDL ni tabla de decisiones. SQLite seguirá almacenando una única fila/documento snapshot autoritativo por partida; no se añadirá otra representación persistente.
- **CONTRATO APROBADO — atomicidad:** una actualización confirmada debe incluir conjuntamente snapshot con decisión cerrada, historial, eventos y nueva `version`.
- **PROPUESTA — operabilidad:** medir tamaño de snapshot y latencia de carga/guardado antes y después; documentar backup y restauración sobre una copia real de SQLite.
- **PROPUESTA W0.3 — estrategia de persistencia:** planificar únicamente una de estas dos variantes sobre el mismo documento: (a) actualización transaccional del payload completo bajo el CAS existente, o (b) migración perezosa al cargar en memoria y persistencia del schema `3` sólo en el siguiente guardado CAS exitoso. La recomendación es (b), sin job DDL ni escritura lateral. Las pruebas deberán forzar fallo antes del commit para demostrar rollback sin cambio de fila y, después, reaplicar la migración/guardado para demostrar un único resultado canónico, sin doble incremento ni divergencia.

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

La matriz siguiente sustituye la expectativa histórica de esta sección con el
estado comprobable posterior al PR #275: **snapshot reader/writer schema `3` y
replay reader/writer schema `2`**. No existe replay schema `3` en W0.

| Productor | Lector runtime W0 | Resultado | Escritura posterior | Estado |
|---|---|---|---|---|
| Snapshot schema `1` | Snapshot reader `3` | Migra `1 → 2 → 3`; `pending_decision = None`. | Snapshot writer `3` sólo al volver a persistir. | **IMPLEMENTADO / PROBADO** |
| Snapshot schema `2` | Snapshot reader `3` | Migra `2 → 3`; `pending_decision = None` y digest recalculado. | Snapshot writer `3` sólo al volver a persistir. | **IMPLEMENTADO / PROBADO** |
| Snapshot schema `3` | Snapshot reader `3` | Restaura `pending`/`closed` y valida checksum/digest. | Snapshot writer `3`. | **IMPLEMENTADO / PROBADO** |
| Snapshot schema `3` | Snapshot reader `2` histórico | Incompatible; debe fallar, nunca degradar. | Ninguna. | **COMPATIBILIDAD INTENCIONAL** |
| Replay schema `1` | Replay reader `2` | Migra a `2` y reproduce semántica histórica sin lifecycle universal. | Replay writer `2`; no reescribe el artefacto fuente. | **IMPLEMENTADO / PROBADO** |
| Replay schema `2` (`0.20.0/0.20.1`) | Replay reader `2` | Conserva la excepción histórica limitada de digest. | Replay writer `2`; no reescribe el artefacto fuente. | **IMPLEMENTADO / PROBADO** |
| Replay schema `3` | No existe en W0 | Fuera de alcance hasta comandos/eventos W1. | Ninguna. | **PENDIENTE W1** |
| Schema o discriminador desconocido | Cualquier reader | Rechazo sin mutación ni fallback. | Ninguna. | **CONTRATO APROBADO** |
| In-memory store | Runtime W0 | Conserva la semántica CAS existente. | Snapshot schema `3`. | **IMPLEMENTADO / PROBADO** |
| SQLite existente con payload `2` | Runtime W0 | Decode/migration; fila intacta hasta un `save`. | Actualización única bajo CAS. | **IMPLEMENTADO / PROBADO** |

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

0. **GATE OBLIGATORIO — cardinalidad:** obtener y registrar aprobación explícita de una de las dos formas de C.2; ninguna modificación W0.1 puede preceder este paso.
1. **PROPUESTA — `domain/enums.py` y `domain/models.py`:** definir discriminadores, registro y validación local conforme a la cardinalidad aprobada, sin integrar especializaciones.
2. **PROPUESTA — `persistence/codec.py`:** registrar tipos con dispatch cerrado; añadir tests negativos antes de writers.
3. **PROPUESTA W0.2 — `persistence/migrations.py`:** implementar `("snapshot", "2")`, ausencia canónica, recálculo de `state_digest`, idempotencia de cadena y rechazo de desconocidos; no introducir `GameState` en `compatible_missing` de `codec.py`.
4. **PROPUESTA W0.2 — `persistence/snapshot.py`:** fijar el futuro `SNAPSHOT_SCHEMA_VERSION = "3"`, escribir/restaurar el registro, conservar el sobre verificable y añadir goldens.
5. **PROPUESTA — `engine/commands.py`:** añadir comando de cierre al conjunto ejecutable y codec.
6. **PROPUESTA — `engine/game.py`:** creación, revalidación, cierre y rollback; cerrar sólo registra opción.
7. **PROPUESTA W1 — `persistence/replay.py`:** mantener v2 durante W0.1; elevar a v3 sólo con el primer comando/evento creador o cerrador, añadir migración `("replay", "2")`, goldens y validación de `final_digest` sin ampliar la excepción histórica.
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

## Q. Plan cerrado para el primer slice W1 (sin implementación en W0)

W1 introducirá el primer comando/evento capaz de crear y cerrar el slot único y,
en esa misma entrega, elevará replay a schema `3`. El orden de implementación y
sus pruebas de aceptación será:

1. creación determinista y persistible de una decisión `pending`, con origen y
   tokens opacos reproducibles;
2. comando de cierre que revalida en una sola transacción decisión, elector,
   opción, estado terminal y `expected_version`, y que sólo registra `closed` y
   `selected_option` exactamente una vez;
3. tests negativos de elector incorrecto, opción inválida, decisión ya cerrada y
   `expected_version` obsoleta, todos sin mutación;
4. carrera CAS de dos cierres, con un ganador, un `VersionConflict`, un incremento
   de versión y ningún evento fantasma del perdedor;
5. proyecciones separadas para elector, adversario y espectador, con pruebas de
   no interferencia que impidan revelar tokens o referencias fuera de audiencia;
6. replay schema `3`, migración `2 → 3` y goldens de creación/cierre que preserven
   digest y orden observable. Los replays schema `2` de 0.19.0 y 0.20.x seguirán
   ejecutándose sin decisiones ni eventos retroactivos.

No forman parte de W1 handlers mecánicos especializados, selección compuesta,
decisiones simultáneas, `expired`, `cancelled` ni una tabla de decisiones.

## Q. Gates

| Gate | Criterio de entrada/salida | Estado en este plan | Etiqueta |
|---|---|---|---|
| `W0-GATE-BASELINE` | SHA/tree/fecha/versión/rama y fixtures históricos fijados. | Listo. | **HECHO OBSERVADO** |
| `W0-GATE-CONTRACT` | Campos, exclusiones e invariantes `01`–`14` sin contradicción. | Listo con preguntas de forma no semántica. | **CONTRATO APROBADO** |
| `W0.1-GATE-CARDINALITY` | Slot opcional único; lista mutable prohibida; sin simultaneidad anticipada. | **Cerrado: `pending_decision: PendingDecision | None`.** | **DECISIÓN W0** |
| `W0-GATE-SCHEMA` | Numeración, readers, writers, migraciones y unknown-version tests. | **CERRADO** — snapshot reader/writer `3`, migraciones `1 → 2 → 3`, codec cerrado y pruebas de versión/discriminador desconocidos; replay permanece deliberadamente reader/writer `2`. | Evidencia local y CI de U.3/U.4. |
| `W0-GATE-PRIVACY` | Proyecciones y no interferencia para cuatro audiencias. | **PENDIENTE** — W0 aporta audiencia y opciones opacas al modelo, pero las proyecciones por elector/adversario/público y la no interferencia son recorrido W1. | Exclusión W0 confirmada en U.2. |
| `W0-GATE-CAS` | Persistencia del registro dentro del único snapshot sometido al CAS existente. | **PARCIAL** — el slot se persiste dentro del agregado y conserva el CAS de stores; la carrera de dos cierres y la ausencia de evento fantasma requieren comandos/eventos W1. | Tests de persistencia W0; cierre concurrente fuera de alcance. |
| `W0-GATE-HISTORY` | Lectura legacy, migración, replay/digest y rechazo de desconocidos. | **CERRADO** — snapshots `1/2` migran a `3`, snapshot `3` round-trip; replay continúa en `2` y los artefactos legacy conservan su semántica sin decisiones retroactivas. | Suite full del SHA común de U.3/U.4. |
| `W0-GATE-QUALITY` | Suite completa, perfil full y cuatro jobs remotos verdes para el mismo SHA. | **CERRADO** — `uv run pytest -q` (781 passed, 1 skipped, 816 subtests) y `verify_release --profile full` pasaron localmente; `runtime (3.11)`, `runtime (3.12)`, `runtime (3.13)` y `full` concluyeron `success` en CI, todo para `27e0c59eafd086f436f0c9aa4292ba46267d8359`. | Run `34450197883`; detalle en U.3/U.4. |
| `CAP-ACTION-004 CLOSED` | Recorrido completo público, persistente, replayable, privado y de servicio. | No alcanzado; sigue `MISSING / READY`. | **HECHO OBSERVADO** |
| `CAP-TIME-002 READY` | `CAP-ACTION-004` y `CAP-TIME-005` cerradas y autorización expresa posterior. | No alcanzado; sigue `PARTIAL / WAIT-PREREQ`. | **HECHO OBSERVADO** |

## R. Deudas

- **BASELINE DOCUMENTAL ANTERIOR — deuda originalmente registrada:** antes del
  PR #275 no existían modelo, comando, evento, codec, snapshot/replay versionado,
  migración ni recorrido `application`/`service` universal.
- **EVIDENCIA RUNTIME POST-#275 — deuda reducida:** ya existen el modelo
  `PendingDecision`, sus enums/validación, el registro en el codec, el slot
  opcional de `GameState`, snapshot reader/writer schema `3` y la migración
  snapshot `2 → 3`. Replay permanece correctamente en schema `2`.
- **DEUDA VIGENTE FUERA DE W0:** todavía no existen comandos ni eventos
  universales de creación/cierre, proyecciones por audiencia, ni el recorrido
  completo por `application.py` y `service.py`; esas superficies, sus pruebas de
  no interferencia y la carrera CAS de cierre pertenecen a W1. Por ello el
  primitive no constituye aún una capability cerrada.
- **HECHO OBSERVADO — setup:** `CAP-TIME-005` carece del lifecycle completo que crea participantes/mazos/manos, mantiene `SETUP`, registra decisiones y prepara la transición sin conceder prioridad.
- **HECHO OBSERVADO — mulligan:** `CAP-TIME-002` posee contador, restricción a setup, tamaños 5→1, reshuffle determinista, evento y persistencia/replay básicos, pero carece de KEEP/REPLACE público, pending universal, paridad legal, CAS específico, capas completas, privacidad y compatibilidad versionada.
- **PREGUNTA ABIERTA — orden:** `N-MULLIGAN-01.OPEN-ORDER` continúa abierta.
- **PREGUNTA ABIERTA — modo:** `N-MULLIGAN-01.OPEN-MODE` continúa abierta.
- **PREGUNTA ABIERTA — revelación:** `N-MULLIGAN-01.OPEN-REVEAL` continúa abierta.
- **PREGUNTA ABIERTA — jugador inicial:** `N-MULLIGAN-01.OPEN-STARTER` continúa abierta y la selección/concesión de prioridad permanece separada en `CAP-TIME-001`.
- **DECISIÓN W0 — forma del registro:** resuelta mediante el slot único
  `pending_decision: PendingDecision | None`; decisiones simultáneas y selección
  compuesta continúan fuera de alcance.
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

## T. Sincronización y contraste con GitHub — 2026-09-09

### T.1 Baseline remoto y compare solicitado

- **HECHO OBSERVADO — remoto:** `origin` tiene como fetch/push URL
  `https://github.com/Alphonsus411/card_duel.git`; `git fetch --prune origin`
  terminó correctamente y `git remote show origin` declaró `main` como HEAD.
- **HECHO OBSERVADO — avance:** el rango
  `7ae37497ed6aa5d69fb16ac42a715998e63141b4..59c07af59690aafec9f35faf6af1bb8435c41eee`
  contiene ocho commits (cuatro commits documentales y sus cuatro merges, PR
  `#270`–`#273`). Cambia únicamente dos documentos: modifica este informe de
  contrato (`44` inserciones, `8` borrados) y añade este plan W0 (`276`
  inserciones). No cambia ningún archivo de `src/card_duel_engine/` ni de
  `tests/`; por tanto no hay nueva implementación ni nueva evidencia funcional
  en el rango.
- **CONTRATO APROBADO — efecto:** las ampliaciones de `main` concretan el plan
  W0 (autoridad/cardinalidad y evolución compatible de schemas) y corrigen la
  atribución de resultados históricos. No alteran los catorce invariantes, no
  autorizan runtime y mantienen `CAP-ACTION-004` como `MISSING / READY`.

### T.2 Ramas remotas adicionales

El inventario de `refs/remotes/origin` encontró **275 ramas adicionales a
`main`**: 261 ya son ancestros de `origin/main` y 14 no están fusionadas. Las
ramas no fusionadas, que son las únicas candidatas a aportar contenido ausente
de `main`, quedan enumeradas exhaustivamente:

| Rama no fusionada | Tip SHA | Fecha Git | Relación con `main` |
|---|---|---|---|
| `Bella-2.0` | `851bc963692c` | `2026-07-23T09:56:29+02:00` | Sin historia común |
| `codex/actualiza-allowed_content-y-mejora-validaciones` | `faeaaaa8f1f0` | `2026-08-30T12:21:59+02:00` | Divergente |
| `codex/actualizar-documentacion-de-fases-y-definiciones` | `b103d0c8b6a9` | `2026-08-30T12:06:13+02:00` | Divergente |
| `codex/agregar-pruebas-para-targeting-local-cache` | `4aa6cccceeff` | `2026-08-23T08:45:27+02:00` | Divergente |
| `codex/anadir-anotacion-en-documento-de-deuda` | `402f88ca48da` | `2026-08-29T20:41:06+02:00` | Divergente |
| `codex/anadir-proyeccion-en-modulo-desacoplado` | `07b45d2e2e29` | `2026-08-30T11:43:02+02:00` | Divergente |
| `codex/capturar-perfil-de-acciones-legales-con-cprofile` | `6f1f5e9a3e67` | `2026-08-23T09:54:13+02:00` | Divergente |
| `codex/configurar-remoto-y-verificar-documentos` | `6ff85f5cf488` | `2026-08-30T12:21:27+02:00` | Divergente |
| `codex/corrige-errores-de-revision-de-codex` | `9c627ed6b94c` | `2026-08-22T16:37:34+02:00` | Divergente |
| `codex/corrige-errores-en-la-prueba-de-paridad` | `20248530cbea` | `2026-08-23T08:39:57+02:00` | Divergente |
| `codex/crear-modulo-cardpresentation-y-catalogo` | `a377dfb8c074` | `2026-08-30T11:36:29+02:00` | Divergente |
| `codex/crear-rama-para-card-duel-engine-0.18.0` | `532cf10560d8` | `2026-08-22T16:52:57+02:00` | Divergente |
| `codex/crear-tests-para-publiccard-y-cardpresentation` | `fe29a5df56ee` | `2026-08-30T11:52:27+02:00` | Divergente |
| `codex/fix-issues-from-codex-review-#146` | `e706d3baee4e` | `2026-08-23T09:44:20+02:00` | Divergente |

Ninguna rama no fusionada se acepta como autoridad de diseño: la autoridad es
el contrato aprobado en `origin/main`. En particular,
`codex/actualiza-allowed_content-y-mejora-validaciones` y
`codex/configurar-remoto-y-verificar-documentos` contienen lógica añadida que
selecciona destinos por IDs concretos de definición de carta; ese dispatch por
identidad contradice `CAP-ACTION-004-INV-13` y queda expresamente descartado.
El barrido de los diffs de las otras ramas no fusionadas no encontró propuestas
de estados `expired`/`cancelled`, una segunda autoridad persistida ni DDL/DML
destructivo para decisiones. Esto no las promueve: cualquier contenido futuro
debe volver a contrastarse contra `main` y pasar los gates aprobados.

### T.3 Pull requests y Actions

- **HECHO OBSERVADO — PR:** se intentó literalmente
  `gh pr list --state merged --search "CAP-ACTION-004 OR Phase 2C"`, pero el
  cliente local no tenía sesión GitHub y rechazó la consulta. La API pública de
  GitHub se usó como fallback y sitúa como último relacionado el PR
  [#273 — docs: aclarar evidencia de verificación CAP-ACTION-004](https://github.com/Alphonsus411/card_duel/pull/273),
  fusionado el `2026-09-09T12:14:18Z` en el SHA exacto de `origin/main`.
- **HECHO OBSERVADO — CI de `origin/main`:** la ejecución
  [tests #34349869544](https://github.com/Alphonsus411/card_duel/actions/runs/34349869544)
  corresponde exactamente a `59c07af59690aafec9f35faf6af1bb8435c41eee`.
  La segunda consulta confirmó la ejecución `completed / success` a las
  `2026-09-09T12:18:03Z`: `runtime (3.11)`, `runtime (3.12)`, `runtime (3.13)` y
  `full` concluyeron individualmente con `success`. Sólo tras esa conclusión se
  registra **`CI GREEN` para el SHA exacto de `origin/main`**.
- **REGLA DE EVIDENCIA:** el SHA del commit que contiene esta actualización
  documental se registrará y consultará después de crearlo. No heredará el
  resultado de `origin/main` ni podrá recibir una declaración `CI GREEN` antes
  de que todos sus jobs relevantes concluyan con `success`.

CAP-ACTION-004 W0 LISTO CON PRERREQUISITOS

## U. Evidencia runtime posterior al PR #275 — 2026-09-10

Esta sección no sustituye ni borra el plan histórico A–T: registra hechos que
ocurrieron después y evita atribuir pruebas de un SHA a otro.

### U.1 Identidades Git separadas

| Concepto | SHA exacto | Alcance probatorio |
|---|---|---|
| Baseline documental anterior | `7ae37497ed6aa5d69fb16ac42a715998e63141b4` | Corte original contra el que se contrastó la documentación; no contiene runtime W0. |
| Baseline previo al runtime W0 | `a8b3e26acf95bc50e6bda4aa1ccdb0bab05e6932` (primer padre de `2832b94ae61e7aa7c913cdd5207a212fed3de8b8`) | Estado de `main` inmediatamente anterior a incorporar la implementación del PR #275; no se confunde con el baseline documental original. |
| Commit de implementación | `73e769a8293e9dfbd0018ac3d01e358e254a3036` | Introduce modelo, codec, slot, migración y snapshot schema `3`; no es por sí mismo el merge de `main`. |
| Merge commit de `main` del PR #275 | `2832b94ae61e7aa7c913cdd5207a212fed3de8b8` | Incorpora `73e769a8293e9dfbd0018ac3d01e358e254a3036` a `main`. |
| SHA exacto probado localmente | `27e0c59eafd086f436f0c9aa4292ba46267d8359` | Checkout limpio antes de esta edición documental: suite completa y perfil `full`. |
| SHA exacto probado por CI | `27e0c59eafd086f436f0c9aa4292ba46267d8359` | Run `34450197883`; los cuatro jobs remotos finalizaron en verde. |

El baseline previo se obtiene como primer padre del merge y se registra completo
para que sea inequívoco. Ninguna prueba de la tabla se atribuye al commit
documental creado después de ejecutarla.

### U.2 Alcance implementado y alcance diferido

- **IMPLEMENTADO EN W0:** `PendingDecision`, enums cerrados, validación del
  registro, `GameState.pending_decision`, soporte cerrado del codec, snapshot
  reader/writer schema `3` y migración legacy a ausencia canónica.
- **CONSERVADO EN W0:** replay reader/writer schema `2`; no hay comando ni evento
  universal cuya reproducción justifique elevarlo.
- **PENDIENTE DE W1:** comandos, eventos, creación/cierre runtime, proyecciones
  por audiencia, no interferencia y recorrido `application`/`service`, incluida
  la carrera CAS de dos cierres y la publicación post-CAS.

### U.3 Prueba local del SHA exacto

Tras instalar el extra de desarrollo declarado por el proyecto, sobre
`27e0c59eafd086f436f0c9aa4292ba46267d8359`:

- `uv run pytest -q`: **781 passed, 1 skipped, 816 subtests passed**.
- `uv run python scripts/verify_release.py --profile full`: **exit 0**.

Un intento anterior a `uv sync --extra dev` no se usa como evidencia: falló en
collection por entorno incompleto (`card_duel_engine`/`mypy` ausentes), no por
una regresión del SHA. La repetición posterior es la evidencia válida.

### U.4 CI del mismo SHA exacto

La ejecución [tests #34450197883](https://github.com/Alphonsus411/card_duel/actions/runs/34450197883)
corresponde exactamente a
`27e0c59eafd086f436f0c9aa4292ba46267d8359`. Finalizaron con `success`:

| Job | Resultado | Finalización UTC |
|---|---|---|
| `runtime (3.11)` | `success` | `2026-09-10T07:31:22Z` |
| `runtime (3.12)` | `success` | `2026-09-10T07:31:17Z` |
| `runtime (3.13)` | `success` | `2026-09-10T07:30:48Z` |
| `full` | `success` | `2026-09-10T07:33:51Z` |

Por compartir el SHA con U.3, esta ejecución permite cerrar
`W0-GATE-QUALITY`. No prueba el commit documental posterior.

### U.5 Definiciones de estado no equivalentes

| Término | Definición |
|---|---|
| **IMPLEMENTADO** | El código o documento requerido existe en un commit identificable. No implica que se haya ejecutado ni que haya satisfecho un gate. |
| **PROBADO** | Una verificación concreta pasó sobre un SHA exacto y queda asociada a su comando o job. No implica por sí sola cobertura de todos los criterios del gate o de la capability. |
| **GATE CERRADO** | Toda la evidencia exigida por ese gate existe y su estado se registra como `CERRADO`; otros gates pueden seguir `PARCIAL`, `PENDIENTE` o `BLOQUEADO`. |
| **CAPABILITY CLOSED** | El recorrido completo público, persistente, replayable, privado y de servicio satisface contrato, tests y dependencias. Es un estado de capability y no se deduce de que una parte esté implementada/probada o de que uno o varios gates W0 estén cerrados. |

En consecuencia, W0 puede estar **IMPLEMENTADO** y **PROBADO**, y algunos gates
pueden estar **CERRADOS**, mientras `CAP-ACTION-004` continúa sin alcanzar
**CAPABILITY CLOSED** por el recorrido W1 pendiente.
