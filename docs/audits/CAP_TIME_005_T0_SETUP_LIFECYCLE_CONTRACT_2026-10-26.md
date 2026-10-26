# CAP-TIME-005 / T0 — Contrato de lifecycle autoritativo de setup

Fecha: 2026-10-26
Estado: planificación autorizada; sin cambio de runtime
Capability: `MISSING / WAIT-PREREQ`

## Mandato y frontera

Este es el segundo slice de planificación ordenado por
`PHASE_2C_ENGINE_EVOLUTION_ROADMAP.md` después de `CAP-ACTION-004`. Define la
evidencia que necesitaría el lifecycle de setup, pero no autoriza su ejecución.
En particular, `N-PHASE-02` sigue siendo **`IMPLEMENTATION BLOCKED`**: los
blockers normativos de mulligan y el recorrido público completo de decisión no
quedan cerrados por este documento.

T0 no modifica `src/`, esquemas, snapshot, replay, aplicación, servicio,
almacenamiento, comandos, tests de runtime ni la matriz de capabilities.

## Inventario del comportamiento actual

| Superficie | Hecho actual comprobado | Límite frente a CAP-TIME-005 |
| --- | --- | --- |
| `GameEngine.new_match` | Construye estado `SETUP`, reparte las manos iniciales y, por defecto, invoca `start_match`. | No registra decisiones obligatorias ni conserva setup hasta su cierre. |
| `GameEngine.mulligan` | Permite una operación imperativa durante `SETUP`, reduce la mano y anota `setup_mulligans`. | No expresa `KEEP`/`REPLACE` como decisión pendiente, no valida vigencia CAS ni determina cierre. |
| `GameEngine.start_match` | Cambia directamente a `RUNNING`, emite `MATCH_STARTED` y entra en `DRAW`. | Mezcla la salida de setup con prioridad inicial y transición de fase, ambas excluidas. |
| `GameState.setup_mulligans` | Conserva una lista de actores que repitieron mulligan. | Es un historial, no el estado autoritativo de decisiones, progreso, obligatoriedad o cierre. |
| Replay | Guarda `mulligans` y el booleano `started`; al reproducir llama a los métodos imperativos. | No puede reconstruir decisiones pendientes de setup ni su autorización/versionado. |
| Servicio y aplicación | Exponen `auto_start` al crear la partida, pero no una operación autenticada de decisión de setup. | No ofrecen proyección privada, capacidad específica ni CAS de una decisión obligatoria. |
| `pending_decision` | El slot universal interno puede persistir y cerrar una decisión autorizada. | No existe originador de setup ni se puede usar para inventar orden, modo o revelación de mulligan. |

Por tanto, ningún elemento existente se reclasifica como lifecycle autoritativo
de setup. El comportamiento histórico se conserva como baseline compatible,
no como una autorización implícita para ampliarlo.

## Invariantes que deberá demostrar una entrega futura autorizada

1. La creación prepara participantes, mazos y manos sin conceder prioridad
   inicial ni entrar en `DRAW`.
2. Cada decisión obligatoria de setup queda representada de forma autoritativa,
   persistible y proyectada exclusivamente a su audiencia.
3. Actor, vigencia, estado de setup y versión CAS se validan antes de barajar,
   mover cartas o escribir eventos; un rechazo conserva estado, RNG, zonas,
   versión e historial.
4. El cierre ocurre exactamente una vez sólo cuando concluyen las decisiones
   exigidas por una regla ya autorizada. No se infiere desde el reloj, la
   memoria del proceso, `auto_start` ni la mera longitud de una lista.
5. Snapshot, replay y reconexión conservan el mismo estado de setup sin volver
   a solicitar elecciones ya registradas.
6. Una transición posterior a `RUNNING`, prioridad inicial o `DRAW` requiere
   contratos propietarios separados; no forma parte de CAP-TIME-005.

## Exclusiones y blockers que se preservan

- No se decide orden, alternancia ni simultaneidad de elecciones:
  `N-MULLIGAN-01.OPEN-ORDER` y `OPEN-MODE` siguen abiertos.
- No se revela decisión, contenido u orden de manos/mazos:
  `N-MULLIGAN-01.OPEN-REVEAL` sigue abierto.
- No se conserva, elige o redetermina jugador inicial:
  `N-MULLIGAN-01.OPEN-STARTER` sigue abierto.
- No se implementa `KEEP`/`REPLACE`, mulligan público, comandos, nuevos DTO,
  persistencia, migraciones, 3+ jugadores, prioridad, pases, cartas ni fases.
- `CAP-TIME-002` sigue `PARTIAL / WAIT-PREREQ`; este T0 no cambia su
  autorización ni reabre `N-PHASE-02`.

## Gate de salida de T0 y siguiente trabajo condicionado

T0 queda completo como inventario y contrato de límites. Antes de cualquier
runtime se requiere una autorización documental posterior que cambie de forma
explícita el alcance, el esquema emitido/leído, la migración, los golden files
por audiencia y la matriz de pruebas de rollback/reconexión/replay. Esa
autorización deberá registrar por separado el estado de los dos prerequisites
técnicos y de los cuatro blockers normativos; no puede derivarse de este
inventario.

Hasta entonces `CAP-TIME-005` conserva `MISSING / WAIT-PREREQ` y el próximo
trabajo permitido sigue siendo de planificación o de otra capability `READY`;
no existe autorización para implementar el mulligan.
