# Hoja de ruta del backend

Esta hoja de ruta convierte únicamente trabajo ya documentado en tareas
separadas. No completa ambigüedades del reglamento ni añade cartas o mecánicas.
La fuente base es `Fantasy Tokens.pdf`; la actualización de 2018-06-13
`Fantasy Tokens Edicion Mitica.pdf` prevalece ante modificaciones expresas.
`MYTHIC_RULES_AUDIT.md`, `RULES_BASELINE.md` y `RULES_TRACEABILITY.md` son
materiales derivados, no prueba normativa.

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

### R-03A — Inventariar contradicciones entre reglamento base y Mítica

- **Resultado documental completado:** `MYTHIC_RULES_AUDIT.md` registra la
  jerarquía, paginación física/interna, categorías A–E, reglas, formatos,
  torneos y el comienzo exacto del corpus de cartas. El PDF Mítico está
  disponible en el repositorio.
- **Bloqueos:** `N-POINTS-01` conserva sin elección las cifras 200, 300, el
  intervalo 300–400 y la recomendación aproximada de 300. La expresión «a modo
  de Eventos» solo respalda Fase Activa y no reclasifica universalmente las
  habilidades de Señor.
- **Límite:** no usa cartas particulares para justificar reglas universales ni
  convierte adiciones en contradicciones.

### R-COMPAT-019-REPLAY — Puente semántico temporal

- **Entrega:** los documentos v2 se deserializan normalmente, pero los replays
  cuyo `RuleSet` es 0.19 activan sólo durante su reproducción la semántica
  histórica de Drenaje, fase de Desafío y elegibilidad de Señores.
- **Evidencia:** los fixtures fueron generados con el commit histórico fijado en
  `tests/artifacts/0.19.0/README.md`; las pruebas verifican sus hashes y
  observables, restauración del modo ante éxito o error y aislamiento frente a
  replays 0.20 y partidas actuales.
- **Vida limitada:** no habilita comandos legacy en juego nuevo y no promete
  soporte indefinido. Su retirada exige una decisión de compatibilidad
  versionada; no debe confundirse deserialización estructural con reproducción
  semántica.

## Decisión sobre transportes

Un adaptador HTTP, HTTPS u otro servicio de red **permanece fuera de alcance** de
esta hoja de ruta. No es una entrega técnica futura habilitada, no recibe un
identificador `R-*` y no debe tratarse como pendiente implementable. Su eventual
incorporación exige una nueva decisión documental explícita que defina su propio
alcance, dependencias, criterios de aceptación y modelo de amenazas; hasta
entonces no se implementará.

Esta exclusión no rebaja la frontera ya entregada: `AuthenticatedMatchApplication`
es la única entrada autoritativa para cualquier transporte futuro. Un adaptador
no podrá aceptar `player_id` del cliente, exponer ni serializar `GameEngine` o
`GameState`, omitir `expected_version` ni el CAS en una escritura, reinterpretar
comandos o aplicar reglas del juego. Solo podrá autenticar, decodificar y validar
el formato, invocar la aplicación y serializar sus DTO públicos seguros.

## Pendientes normativos bloqueados

### R-02 — Revisar el reparto de daño entre bloqueadores

- Contrastar el orden actualmente normalizado con una aclaración oficial.
- No cambiar el algoritmo hasta disponer de esa aclaración.

### R-03B — Alinear fuentes, reglas, formatos y futuro corpus

R-03A permanece completada **únicamente como inventario histórico**. R-03B no
está completada y se divide en entregas independientes, trazadas fila por fila
en `RULES_TRACEABILITY.md`:

- **R-03B.1 — Fuente verificable:** conservar los PDF, hashes, paginación
  física/interna y decisiones documentales comprobables.
- **R-03B.2 — Reglas universales:** la conducta verificable de Drenaje,
  Legendarios, Divinos, los cuatro dominios y Desafío ya está alineada con sus
  identificadores y pruebas; permanecen bloqueados los silencios normativos.
- **R-03B.3 — Formatos de mazo:** conservar los perfiles Clásico/Mística ya
  probados sin elegir un presupuesto de puntos
  mientras `N-POINTS-01` siga bloqueado. La aplicación de 40–60 y 5/4 a Clásico
  se vincula a la conclusión textual de físicas 2–3 / internas 1–2 y no se
  presenta como una regla independiente inferida.
- **R-03B.4 — Futuro corpus:** mantener las cartas fuera del paquete y preparar
  una carga futura por manifiestos, según `MYTHIC_CARD_CORPUS_SCOPE.md`.

Estas cuatro líneas son seguimiento separado, no una orden de incorporar el
catálogo completo. En particular, `N-POINTS-01` permanece bloqueado y R-03B.4
solo define la frontera externa para un trabajo futuro expresamente autorizado.

**Criterio de cierre:** R-03B sólo podrá declararse completada cuando código,
documentación y pruebas estén alineados en todas las filas. Una aclaración
oficial sigue siendo obligatoria para puntos (`N-POINTS-01`), reclasificación de
habilidades de Señor (`M-LORD-EVENT-01`) y condiciones terminales multijugador;
ninguna implementación resuelve
por sí misma esos bloqueos.

## Pendientes técnicos bloqueados

### R-05 — Evolución de formatos persistentes

- Añadir migraciones únicamente cuando exista un esquema 3 o posterior definido.
- Rechazar rutas desconocidas sin completar datos mediante suposiciones.

No hay incrementos técnicos habilitados por las fuentes vigentes. R-02, R-03B y
R-05 conservan los bloqueos indicados; R-03A está completada documentalmente. No
se promoverá una tarea nueva sin respaldo explícito del reglamento, la línea base y la arquitectura. El transporte
queda excluido, no bloqueado ni pendiente.
