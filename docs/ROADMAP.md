# Hoja de ruta del backend

Esta hoja de ruta convierte únicamente trabajo ya documentado en tareas
separadas. No completa ambigüedades del reglamento ni añade cartas o mecánicas.
La fuente normativa continúa siendo `Fantasy Tokens.pdf`, interpretada mediante
`RULES_BASELINE.md` y su matriz `RULES_TRACEABILITY.md`.

## Entregas completadas

### R-07 — Separar la coordinación de disparos de pila

- **Entrega incremental:** inventariados pila, combate y movimiento, y extraído
  únicamente el grupo cohesivo de creación y encolado de disparos a
  `StackManager`, mediante un `StackContext` explícito.
- **Garantía:** `GameState` sigue siendo la única autoridad mutable; transacción,
  fases, comandos, invariantes y replay de sustituciones permanecen en
  `GameEngine`. Las pruebas de paridad confirman que no cambian reglas observables.

### R-07.1 — Extraer la validación y mutación de combate

- **Entrega incremental completada:** `CombatManager` contiene ya la declaración
  de Desafío, atacantes y bloqueadores y la resolución del combate. Los métodos
  homónimos de `GameEngine` son adaptadores de despacho, no lógica de combate
  residente en el coordinador.
- **Paridad cerrada:** la batería del límite compara el camino público con un
  `CombatContext` mínimo en éxito, comando ilegal y excepción. La huella compara
  explícitamente `GameState`, registro de eventos, historial de comandos y los
  contadores deterministas de instancias y pila; los rechazos y las excepciones
  transaccionales no dejan mutación parcial.
- **Coordinación cerrada:** `CombatManager` construye además los subconjuntos de
  atacantes, Desafíos, bloqueadores y `ResolveCombat`, con el mismo orden y límite
  deterministas. La enumeración limitada no restringe la validación autoritativa
  de comandos explícitos. Despacho, snapshot/rollback, avance de fases e
  invariantes permanecen en `GameEngine`.

### R-07.2 — Consolidar movimientos y sustituciones

- **Entrega incremental completada:** `ZoneManager` es la única implementación de
  robo, ordenación y aplicación de sustituciones y movimiento entre zonas. Los
  cuatro métodos homónimos de `GameEngine` son exclusivamente adaptadores.
- **Frontera verificada:** `ZoneContext` contiene solo estado y colaboradores de
  movimiento; transacción, despacho, historial, elecciones pendientes y
  contadores deterministas continúan perteneciendo al coordinador.
- **Paridad cerrada:** un contexto mínimo independiente compara estado, eventos,
  historial, semilla, replay, elección pendiente y contadores, incluidos rechazo
  y excepción sin mutación parcial. No se modifica ninguna regla.

### R-01 — Proteger las condiciones terminales multijugador

- **Evidencia:** el reglamento permite uno o más adversarios, pero no define la
  continuidad, la concesión ni los ganadores para tres o más participantes.
- **Entrega 0.18.3:** ante una concesión o el límite de Heridas, una partida con
  más de dos participantes pasa a `BLOCKED`, no declara ganadores y publica la
  causa y los participantes afectados.
- **Criterio de salida:** sustituir este bloqueo solo cuando exista una
  aclaración normativa trazable.

### R-04 — Política de confianza para colecciones

- **Entrega 0.19.0:** sobre de firma v1 separado del manifiesto v2, bytes
  canónicos únicos, resolución inyectada de claves y política estricta o
  permisiva elegida por la aplicación.
- **Garantía:** la autenticación de un lote completo se resuelve antes de
  modificar catálogo o procedencia, sin cargar módulos ni ejecutar contenido.

### R-06 — Frontera autenticada de aplicación

- **Entrega incremental:** creada una capa de aplicación agnóstica del
  transporte, con identidad externa estable, asociaciones por partida y
  capacidades independientes para crear, observar, enviar y administrar.
- **Garantía:** el jugador se deriva de la identidad autenticada; las respuestas
  usan DTO públicos, todas las escrituras de comandos conservan CAS y los errores
  públicos no exponen el motor, instantáneas ni información privada.
- **Comprobación:** la misma batería de contrato cubre memoria y SQLite,
  incluidas atribución falsa, cruces entre partidas, capacidades independientes,
  conflictos concurrentes y ausencia de mutación ante rechazos.

## Pendientes normativos bloqueados

### R-02 — Revisar el reparto de daño entre bloqueadores

- Contrastar el orden actualmente normalizado con una aclaración oficial.
- No cambiar el algoritmo hasta disponer de esa aclaración.

### R-03 — Formalizar contradicciones entre reglamento base y Mítica

- Registrar cada contradicción, las páginas fuente y la precedencia aplicada.
- Mantener mientras tanto la precedencia Mítica ya declarada para Divinos.

## Pendientes técnicos bloqueados

### R-05 — Evolución de formatos persistentes

- Añadir migraciones únicamente cuando exista un esquema 3 o posterior definido.
- Rechazar rutas desconocidas sin completar datos mediante suposiciones.

No hay incrementos técnicos habilitados por las fuentes vigentes. R-02, R-03 y
R-05 conservan los bloqueos indicados y no se promoverá una tarea nueva sin
respaldo explícito del reglamento, la línea base y la arquitectura.
