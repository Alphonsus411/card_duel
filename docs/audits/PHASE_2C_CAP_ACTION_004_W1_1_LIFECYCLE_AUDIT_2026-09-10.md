# Auditoría de lifecycle W1.1 de `CAP-ACTION-004` — 2026-09-10

## A. Estado inicial

La auditoría comenzó sobre el `HEAD` limpio
`3f22be93ac2907d9d4dc17f359aa30fd945e0afd`. Ese corte ya contenía W0 y la API
interna W1.1. El estado documental de entrada de `CAP-ACTION-004` era
`MISSING / READY`; `CAP-TIME-002` era `PARTIAL / WAIT-PREREQ`. La evidencia de
esta auditoría no declara `SUPPORTED`, no declara el gate `CLOSED` y no
desbloquea `CAP-TIME-002`.

## B. Alcance

W1.1 acredita únicamente el slot autoritativo individual
`GameState.pending_decision` y sus transiciones internas `None -> PENDING ->
CLOSED`. Quedan fuera el comando público, la capa application/service, la
privacidad efectiva, el CAS concurrente del cierre, la publicación posterior al
CAS y el replay del lifecycle. Tampoco se especializan mulligan, búsquedas,
elecciones compuestas ni cartas.

## C. Arquitectura

La única autoridad de dominio es el campo opcional de `GameState`; el motor no
mantiene un atributo paralelo. Abrir o cerrar construye una copia candidata,
valida las invariantes del agregado y sólo entonces sustituye el estado. El
contrato usa identidad opaca, familia semántica versionada, elector, audiencia,
opciones opacas, versión y origen; el cierre sólo añade estado terminal y opción
seleccionada.

## D. Lifecycle

El lifecycle permitido es exactamente:

```text
None -> PENDING -> CLOSED
```

No existen en W1.1 consumo, retirada, reapertura ni sustitución. La siguiente
tabla conserva los catorce IDs permanentes y limita cuidadosamente la evidencia
al slice auditado:

| Invariante | Estado en W1.1 | Evidencia o límite |
|---|---|---|
| `INV-01` | **acreditado por W1.1** | Un único slot autoritativo en `GameState`; snapshot conserva esa autoridad. |
| `INV-02` | **acreditado por W1.1** | La identidad permanece estable durante apertura, cierre y round-trip de snapshot; falta llevarla a superficies públicas. |
| `INV-03` | **acreditado por W1.1** | El cierre interno rechaza cualquier actor distinto del elector autorizado. |
| `INV-04` | **acreditado por W1.1** | Sólo acepta un token perteneciente a las opciones opacas autorizadas. |
| `INV-05` | **acreditado por W1.1** | `PENDING -> CLOSED` ocurre una vez en memoria; el segundo intento se rechaza sin mutación. |
| `INV-06` | **acreditado por W1.1** | Las aperturas y cierres rechazados conservan estado y snapshot byte a byte. |
| `INV-07` | **pendiente de un slice posterior** | Requiere CAS público y una carrera real de dos cierres. |
| `INV-08` | **pendiente de un slice posterior** | Requiere proyección por audiencia en API, eventos y observabilidad. |
| `INV-09` | **acreditado por W1.1** | Snapshot v3 restaura ausencia, `PENDING` y `CLOSED` con digest coincidente. |
| `INV-10` | **pendiente de un slice posterior** | Requiere comandos/eventos reproducibles; replay v2 detecta hoy la divergencia interna. |
| `INV-11` | **preservado pero no cerrado** | Los valores internos inválidos se rechazan; debe completarse al integrar el versionado público. |
| `INV-12` | **acreditado por W1.1** | Ninguna transición consulta wall-clock ni deriva de él autoridad o caducidad. |
| `INV-13` | **preservado pero no cerrado** | El lifecycle es agnóstico a cartas y exige familia versionada, pero aún no existe dispatch público por familia. |
| `INV-14` | **acreditado por W1.1** | El cierre sólo registra `status` y `selected_option`; no ejecuta otra mecánica. |

## E. Política `CLOSED`

`CLOSED` es terminal y continúa ocupando el slot. W1.1 no permite reciclar una
decisión `CLOSED`: una nueva apertura recibe `DecisionSlotOccupied`. En
particular, no existen `CLOSED -> None`, `CLOSED -> PENDING` ni reemplazo
silencioso. Un slice posterior deberá definir consumo, historia, persistencia y
replay antes de liberar el slot.

## F. `state_version`

`PendingDecision.state_version` es un vínculo determinista declarado al abrir y
revalidado al cerrar. W1.1 no lo incrementa, no lo deriva de
`StoredMatch.version` y no lo equipara con `expected_version`. La eventual
integración pública debe definir esa relación sin crear dos autoridades; allí se
completará `INV-11` y una versión desconocida deberá fallar de forma cerrada.

## G. Zero mutation

Las validaciones preceden a la instalación de la copia candidata. Slot ocupado o
vacío, identidad incorrecta, actor no autorizado, opción ajena, versión obsoleta
y datos de apertura inválidos dejan iguales el objeto de estado y su snapshot
canónico. Esto acredita zero mutation dentro de la frontera interna W1.1, no en
application/service ni ante conflictos del store.

## H. Exactly-once

El primer cierre válido transforma `PENDING` en `CLOSED`; el segundo recibe
`DecisionAlreadyClosed` sin modificar el agregado. Es exactly-once local. No se
extrapola a dos clientes: el exactly-once distribuido sigue pendiente hasta que
un comando público atraviese application/service y CAS, y el perdedor no
publique evento ni proyección.

## I. Eventos

W1.1 no añade eventos. No son necesarios para conservar las invariantes internas
del slice porque la decisión vive en el estado autoritativo, las transiciones son
atómicas sobre una copia, el snapshot persiste el resultado y el digest detecta
la divergencia. Añadir un evento sin comando, codec, replay, CAS y política de
publicación habría creado una segunda representación incompleta y una falsa
promesa de reproducibilidad. Los eventos se aplazan, no se consideran
innecesarios para el recorrido público futuro.

## J. Snapshot/digest

Snapshot schema v3 conserva todos los campos de la decisión tanto `PENDING` como
`CLOSED`. El digest autoritativo distingue ausencia, opciones, todos los campos
contractuales, estado y opción seleccionada. El round-trip produce el mismo
estado, digest y documento canónico.

## K. Replay/legacy

Replay permanece deliberadamente en schema v2. Como las llamadas internas no se
añaden a `command_history`, el verificador de digest rechaza un replay que
pretenda reconstruirlas; desactivar esa verificación recupera correctamente un
estado sin decisión y hace visible el límite. No se modifican fixtures ni
fallbacks legacy 0.19/0.20. `INV-10` sólo podrá cerrarse con comandos/eventos
reproducibles y migración/goldens explícitos.

## L. Privacidad

El modelo valida y persiste `audience`, pero no proyecta vistas. Por tanto no se
acredita confidencialidad ni ausencia de fugas: `INV-08` exige una proyección por
audiencia probada para elector, oponente y observadores. La privacidad permanece
explícitamente pendiente y `CAP-PRIVACY-001` no se considera consumida por esta
infraestructura.

## M. Ausencia de dispatch por carta

Las operaciones internas no aceptan ni inspeccionan `card_id`, `definition_id`,
nombre, set o expansión. `semantic_family` debe ser opaca y versionada, pero
W1.1 no implementa todavía handlers públicos por familia. Así se preserva la
regla arquitectónica de no despachar cartas concretas sin simular el cierre de
`INV-13`.

## N. Tests

En el SHA inicial se ejecutó primero el comando focal sin sincronizar el entorno;
falló en collection por ausencia del paquete editable y no por defecto del
runtime. Tras `uv sync --locked --extra dev`, la selección conjunta W1.1, W0 y
roadmap obtuvo **116 passed**. Cubre transiciones, rechazos atómicos,
exactly-once local, snapshot/digest, límite de replay, `INV-14` y agnosticismo de
carta. La suite completa posterior obtuvo **850 passed, 1 skipped y 816
subtests passed**.

## O. Cobertura

La auditoría no inventa un porcentaje: la ejecución focal no se instrumentó con
`coverage`, por lo que la cobertura porcentual de este cambio queda **no
medida**. La evidencia válida es funcional (116/116 pruebas seleccionadas); los
porcentajes históricos de otros SHA no se reutilizan.

## P. Cambios por archivo

- `docs/audits/PHASE_2C_CAP_ACTION_004_W1_1_LIFECYCLE_AUDIT_2026-09-10.md`:
  incorpora la presente auditoría A–T y la clasificación `INV-01`–`INV-14`.
- `docs/ENGINE_CAPABILITY_MATRIX.csv`: reclasifica sólo `CAP-ACTION-004` de
  `MISSING` a `PARTIAL`, conserva `gate=READY` y registra las fronteras W1.1.
- `docs/PHASE_2C_ENGINE_EVOLUTION_ROADMAP.md`: sincroniza el estado técnico y el
  prerequisite del primer slice sin cambiar su bloqueo.
- `docs/audits/PHASE_2C_FIRST_SLICE_READINESS_AUDIT_2026-09-07.md` y
  `docs/audits/PHASE_2C_FIRST_SLICE_TRACEABILITY_2026-09-07.md`: sincronizan el
  mismo prerequisite técnico, manteniendo el veredicto bloqueado.
- No se modifica runtime, tests, corpus, dependientes ni el estado/gate de
  `CAP-TIME-002`.

## Q. Riesgos

Persisten seis riesgos principales: no hay comando público; no hay recorrido
application/service; `audience` aún no protege una proyección; dos clientes no
compiten mediante CAS de cierre; aún no se garantiza publicar sólo después del
CAS ganador; y replay no reconstruye el lifecycle. También falta definir el
consumo de `CLOSED` y el contrato de compatibilidad/versionado público.

## R. Gates

| Gate evaluado | Estado | Motivo |
|---|---|---|
| Lifecycle interno W1.1 | **ACREDITADO** | `None -> PENDING -> CLOSED`, terminal y atómico. |
| Snapshot/digest W1.1 | **ACREDITADO** | Round-trip y discriminación de campos. |
| Comando + application/service | **PENDIENTE** | No existe recorrido público. |
| Privacidad/proyección | **PENDIENTE** | No existe proyección por audiencia. |
| CAS + publicación | **PENDIENTE** | Falta carrera pública y ausencia de observable fantasma. |
| Replay lifecycle | **PENDIENTE** | No hay comando/evento reproducible. |
| Capability global | **ABIERTO** | Se prohíbe declarar `CLOSED`. |

## S. Estado de capability

Antes de editar la matriz se evaluó su taxonomía canónica: `MISSING` significa
que no hay ningún subconjunto ejecutable demostrable; `PARTIAL`, que existe un
subconjunto real sin contrato completo; `SUPPORTED` exige recorrido público,
persistente, replayable y de servicio. W1.1 sí aporta un subconjunto runtime
ejecutable y probado, por lo que corresponde promover **únicamente a
`PARTIAL / READY`**. No corresponde `SUPPORTED` ni `CLOSED`. Esta promoción
técnica no promueve cartas, no completa ningún dependiente y no desbloquea
`CAP-TIME-002`, que conserva `PARTIAL / WAIT-PREREQ`.

## T. Próximo slice

El próximo slice debe diseñar e implementar el comando público versionado de
apertura/cierre, enumeración y revalidación, application/service, proyección por
audiencia, CAS real de dos cierres y publicación únicamente después del CAS
ganador. Después debe incorporar comandos/eventos reproducibles, replay y
compatibilidad/goldens del lifecycle, incluida la política explícita de consumo
de `CLOSED`. Hasta completar y probar ese recorrido permanecen pendientes
`INV-07`, `INV-08`, `INV-10`, la parte pública de `INV-11` y el cierre de la
capability.
