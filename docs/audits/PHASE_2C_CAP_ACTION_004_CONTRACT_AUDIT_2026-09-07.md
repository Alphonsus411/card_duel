# Auditoría de contrato de CAP-ACTION-004 — 2026-09-07

## Fase 1 — Baseline

### Evidencia Git previa a la edición

La inspección se realizó antes de crear este documento. El punto de partida
esperado y el observado coinciden:

| Comprobación | Evidencia observada |
| --- | --- |
| SHA esperado | `9543806234a1b5af47dc1e40514323b2c5fc4324` |
| `HEAD` real | `9543806234a1b5af47dc1e40514323b2c5fc4324` |
| Rama activa | `work` |
| Referencia local `main` | No existe `refs/heads/main` en este checkout. |
| Referencia remota `origin/main` | No existe `refs/remotes/origin/main`; el checkout tampoco tiene remotos configurados. |
| Árbol de trabajo inicial | Limpio (`git status --porcelain=v1` no produjo entradas). |

Se consultaron explícitamente tanto la referencia local como la remota antes de
editar. Al no existir ninguna referencia `main`, no hay un extremo adicional
contra el que enumerar `9543806...main`. Como comprobación local equivalente,
`git rev-list --count 9543806234a1b5af47dc1e40514323b2c5fc4324..HEAD`
devolvió `0`; por tanto, la lista de commits intermedios es **vacía** y no hay
ningún commit posterior que evaluar por impacto sobre CAP-ACTION-004.

### Versión y metadatos

La comprobación estática confirma la versión **`0.20.1`**:

- `pyproject.toml` declara `project.version = "0.20.1"`.
- La entrada `card-duel-engine` de `uv.lock` declara `version = "0.20.1"`.
- `card_duel_engine.__version__` se asigna mediante `resolve_version()`; en un
  checkout, ese resolvedor lee y devuelve de forma explícita
  `project.version` desde `pyproject.toml`. No existe un segundo literal de
  versión del paquete que contradiga el metadato canónico.
- `CHANGELOG.md` conserva la sección de release `0.20.1`.

### Estados de planificación

La lectura estática de las dos fuentes solicitadas confirma los mismos estados:

| Documento | Phase 2C | Phase 3 |
| --- | --- | --- |
| `docs/PHASE_2C_ENGINE_EVOLUTION_ROADMAP.md` | `IN PROGRESS` | `PENDING` |
| `docs/ROADMAP.md` | `IN PROGRESS` | `PENDING` |

### Estado de CAP-ACTION-004

La fila `CAP-ACTION-004` de `docs/ENGINE_CAPABILITY_MATRIX.csv` conserva:

- estado de soporte: **`MISSING`**;
- estado de readiness: **`READY`**.

La fila sigue describiendo el contrato universal de decisión pendiente y no
presenta la capability como implementada.

### Veredicto de baseline

**`BASELINE VALID`**

El SHA real coincide exactamente con el esperado, no hay commits intermedios,
la versión y los metadatos permanecen en `0.20.1`, las fases conservan sus
estados y CAP-ACTION-004 continúa `MISSING / READY`. La ausencia de referencias
`main` se registra como una limitación del checkout, no como drift sustantivo:
el propio `HEAD` es exactamente el punto de partida exigido y el árbol inicial
estaba limpio. En consecuencia, no corresponde emitir **`CAP-ACTION-004
CONTRACT BLOCKED`** por la Fase 1.

## Fase 2 — Recorrido estático de las decisiones existentes

### Alcance y criterio

Se inspeccionaron `domain/models.py`, `engine/commands.py`, `engine/actions.py`,
`engine/options.py`, `engine/game.py`, `engine/zones.py`, `engine/stack.py`, las
fronteras `application.py`, `service.py` y `presentation.py`, los codecs de
`persistence/`, los almacenes de `storage/` y las pruebas asociadas. No se
infieren garantías de los nombres: cada afirmación de la matriz procede del
camino creación → estado → enumeración → validación/resolución → persistencia →
proyección observado.

Por «persistido» se entiende parte del estado o del historial serializado, no
durabilidad independiente. Por «exactly-once» se entiende que una misma versión
aceptada no puede resolver dos veces la misma espera; no significa deduplicación
global de peticiones, pues no existe `decision_id` ni clave de idempotencia.

### 2.1 `PendingSearch`: pausa y continuación de una búsqueda

1. **Creación.** Al resolver un `StackItem`, `StackManager` encuentra
   `SEARCH_ZONE`, exige exactamente un `ZoneTarget`, calcula `eligible` desde la
   zona viva y el filtro de la definición, acota `maximum` y crea
   `PendingSearch`. Conserva el `stack_item` completo y
   `next_effect_index`, por lo que la continuación no se reconstruye desde el
   texto de la carta. El elector es el controlador del objeto de pila.
2. **Estado y opciones.** `GameState.pending_search` almacena elector, zona,
   IDs elegibles, mínimo/máximo, destino y banderas de barajado/revelado. El
   enumerador produce combinaciones `ResolveSearchChoice` dentro del límite de
   enumeración; los demás jugadores sólo obtienen `Concede`.
3. **Resolución e invalidación.** Se revalidan elector, unicidad, cardinalidad,
   pertenencia al conjunto persistido y presencia actual en la zona. Esa última
   comprobación es la invalidación semántica local. Después se mueven cartas,
   se baraja si procede, se borra la espera **antes** de continuar desde el
   índice guardado y se restaura prioridad si no apareció otra espera.
   `_execute_transaction` aporta rollback atómico ante cualquier fallo.
4. **Snapshot y codec.** `PendingSearch` entra automáticamente en el registro
   cerrado de dataclasses del codec porque vive en `domain.models`; el snapshot
   codifica todo `GameState`, lo protege con digest/checksum y al cargar restaura
   también el perfil seguro del `StackItem` anidado. Por tanto, una búsqueda
   pausada sí sobrevive a snapshot.
5. **Replay.** El replay no guarda `pending_search` como bloque separado: guarda
   `command_history`. El comando que originó la búsqueda ya fue añadido al
   historial y `ResolveSearchChoice` se añade al resolverse; reproducirlos vuelve
   a crear y consumir la espera determinísticamente, con verificación de digest
   final. Un replay capturado mientras la búsqueda sigue pendiente reproduce
   sólo el comando originador y termina de nuevo pendiente.
6. **Audiencia.** La observación publica el `pending_search_item_id` a todos,
   pero `searchable_card_ids` sólo al elector. Las acciones legales contienen
   los IDs reales sólo dentro del `MatchView` interno. La aplicación remota
   proyecta únicamente `{option_id, action}` y no los campos privados del
   comando. El evento final revela IDs sólo si `reveal_selection`; de lo
   contrario revela únicamente el conteo.

Este contrato especializado debe conservar en la capability de búsqueda:
`ZoneTarget`, filtro materializado, IDs de cartas candidatas, cardinalidad,
destino, barajado, revelación y cursor de continuación de efectos.

### 2.2 `PendingMoveReplacement`: rollback y reejecución del comando original

1. **Creación especializada.** `ZoneManager._move_card` reúne reemplazos
   aplicables con sus índices de definición. Si la carta declara elección
   diferida y hay más de uno, consume primero una elección privada de replay o
   lanza `MoveReplacementChoiceRequired` con elector (controlador de la carta),
   carta, razón, índices y destinos.
2. **Materialización.** `GameEngine._execute_transaction` captura un `deepcopy`
   previo. Al recibir la excepción restaura todo el comando, contadores incluidos,
   y publica `PendingMoveReplacement` con el **comando original**, el jugador que
   tenía prioridad y las elecciones ya consumidas. Esto evita dejar aplicada una
   mitad del comando compuesto.
3. **Elección y reanudación.** El enumerador ofrece un
   `ResolveMoveReplacement(index)` por índice al elector y sólo `Concede` al
   resto. La resolución revalida elector e índice, conserva otro respaldo, borra
   la espera, restaura prioridad, agrega el índice a `replay_choices` y reejecuta
   íntegramente `original_command`. El cursor hace que `_move_card` consuma las
   decisiones previas en el mismo orden; si surge otra elección, se publica una
   nueva espera con el prefijo acumulado. Si la reejecución falla, reaparece
   exactamente el pending anterior.
4. **Exactly-once y replay.** El efecto original no se confirma hasta que toda
   la reejecución termina; una espera consumida deja de ser resoluble. No hay
   idempotency key, pero CAS impide que dos clientes confirmen la misma versión.
   `execute` añade cada `ResolveMoveReplacement` al historial. Durante replay,
   el comando original crea de nuevo el pending y cada comando de resolución
   reinyecta el índice; la huella final detecta divergencia. `original_command`
   también es serializable porque el codec usa el vocabulario cerrado de
   comandos.
5. **Snapshot y exposición.** El snapshot incluye el pending íntegro, incluidos
   comando original y prefijo de elecciones. La observación expone a todos el
   ID de la carta pendiente, pero sólo al elector los pares índice/destino; esto
   es una exposición pública deliberada de que existe la espera y puede revelar
   una carta que de otro modo fuese privada. La aplicación vuelve opacos esos
   comandos mediante option IDs, aunque conserva el nombre de acción.

Deben permanecer en la capability de reemplazos: razón de movimiento, carta,
índices ligados al orden de definiciones, destinos candidatos, prefijo de
elecciones para reejecutar, prioridad de reanudación y estrategia concreta de
rollback/reejecución del comando original.

### 2.3 Mecanismos separados que no deben colapsarse por parecido superficial

#### Selección de targets

Los targets ordinarios se eligen al construir `PlayCard` o `ActivateAbility` y
quedan congelados en `StackItem`; `engine/options.py` genera combinaciones de
jugadores, permanentes, zonas y asignaciones según `TargetMode`, cardinalidades,
protecciones y costes. Para triggers, `pending_triggers` conserva `StackItem`
con `targets_locked=False`; `ChooseTriggeredTargets(item_id, ...)` identifica un
objeto concreto, revalida contra los comandos actualmente generados y lo
reemplaza por una copia con targets bloqueados. Su dato especializado es la
estructura heterogénea del target (`player/card/zone/allocation`) y sus reglas de
legalidad; no es una opción opaca persistida genérica.

#### Ordenación de triggers

`pending_triggers` es un lote de objetos de pila simultáneos bajo control del
jugador que recibe prioridad. Sólo después de que todos tengan targets cerrados,
el enumerador genera permutaciones de `item_id`. `OrderTriggeredAbilities`
valida una permutación exacta, vacía el lote y extiende la pila en el orden
elegido. Actor, objetos y orden viven en estado/historial y snapshot, pero la
semántica especializada es ordenar objetos de pila simultáneos, no escoger una
alternativa de búsqueda ni un reemplazo.

#### Orden de replacements

`SetReplacementOrder` no es `PendingMoveReplacement`: es una acción ordinaria
de prioridad sobre un permanente propio cuya definición declara
`player_orders_replacements`. Persiste `ordered_indices` en
`CardInstance.replacement_order`, y los movimientos futuros consultan ese orden
para escoger el primer reemplazo aplicable. Puede cambiarse varias veces, por lo
que no tiene estado pendiente/resuelto ni exactly-once. Sus índices, pertenencia
a una carta y efecto sobre movimientos futuros son datos de reemplazo.

#### Action option IDs

Los option IDs sólo existen en `AuthenticatedMatchApplication`. Son HMAC de
`match_id`, actor, versión e índice de la enumeración con un secreto efímero del
proceso. No se almacenan en `GameState`, snapshot, replay ni storage, y tras
reiniciar la aplicación dejan de ser reproducibles. `submit_option` vuelve a
leer y enumerar, exige igualdad de versión, compara en tiempo constante y envía
el comando recuperado al CAS del servicio. Son referencias opacas y acotadas a
audiencia/versión, no decisiones persistidas.

## Fase 3 — Matriz contractual observada

| Mecanismo | Actor persistido | Opciones persistidas | Audiencia | Invalidación | Exactly-once | Replay | Snapshot | CAS | Generalización posible |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `PendingSearch` | Sí: `chooser_id`. | Sí: IDs elegibles + min/max; además datos de búsqueda. | Existencia/item a todos; candidatos y comandos sólo al elector; transporte opaco. | Actor, duplicados, cardinalidad, elegibilidad congelada y presencia en zona; versión en frontera. | Parcial: se borra antes de continuar y rollback; sin `decision_id`/idempotencia. | Por comando originador + `ResolveSearchChoice`; digest final. | Sí, pending y continuación completos. | Sí, sólo a nivel de submit/store. | Extraer lifecycle/actor/audiencia/opciones opacas; no extraer semántica de cartas/búsqueda. |
| `PendingMoveReplacement` | Sí: `chooser_id`; también prioridad a restaurar. | Sí: índices/destinos y prefijo elegido. | Carta pendiente a todos; opciones sólo al elector; transporte opaco. | Actor e índice aplicable; rollback y versión. | Parcial fuerte por clear + reejecución transaccional; sin clave universal. | Comando original seguido de resoluciones; cursor determinista + digest. | Sí, incluso comando original. | Sí, submit/store. | Extraer lifecycle; conservar reejecución, razón, carta e índices en replacements. |
| Targets de play/ability | Sí, dentro del comando/`StackItem`. | Las selecciones elegidas sí; el universo legal no. | Observación de pila parcial; comando remoto opaco; eventos según efecto. | Revalidadores de target al anunciar/lock y posible fizzle al resolver. | El comando se ejecuta una vez por CAS; el objeto resuelve una vez al salir de pila. | Sí, comandos; stack pendiente se recrea. | Sí. | Sí. | Sólo el sobre de decisión; tipos, cardinalidad, inmunidad y asignaciones quedan en targeting. |
| Targets de triggers | Sí: controlador + item desbloqueado. | No como conjunto; se regeneran comandos legales. | Lote visible en observación; campos de opciones ocultos remotamente. | Debe coincidir con una opción regenerada para ese `item_id`; fizzle sin target. | Lock una vez; después pasa a fase de orden. | Sí, `ChooseTriggeredTargets`. | Sí, `pending_triggers`. | Sí. | Lifecycle de pending; identidad y legalidad del target quedan especializadas. |
| Orden de triggers | Sí: controlador/priority y lote. | Implícitas: permutaciones regeneradas, no almacenadas. | Lote visible; alternativas completas sólo internas y opacas fuera. | Permutación exacta de todos los `item_id`. | Vacía lote una vez; no hay `decision_id`. | Sí, `OrderTriggeredAbilities`. | Sí. | Sí. | Actor + opciones + resolución; lote simultáneo y semántica LIFO quedan en stack. |
| Orden persistente de replacements | Actor sólo en comando/historial; el estado conserva la carta y orden. | El orden elegido sí; alternativas se regeneran. | Orden del propio battlefield; acción remota opaca. | Propiedad/control, flag de definición y permutación completa. | No: es configuración mutable repetible. | Sí, `SetReplacementOrder`. | Sí, en `CardInstance`. | Sí. | No modelarlo como pending; reutilizar autorización/opacidad si procede. |
| Action option ID | Actor ligado criptográficamente, pero no persistido. | No; sólo índice en enumeración regenerada. | Token distinto por actor; payload del comando nunca público. | MAC, match, actor, versión, índice y nueva enumeración; reinicio invalida secreto. | CAS evita doble escritura de versión; token no registra consumo. | No aparece. | No aparece. | Sí, dos comprobaciones (app y store). | Es la representación pública opaca que un contrato universal puede adoptar, no su almacenamiento. |

## Fase 4 — Infraestructura transversal frente a especializaciones

### Duplicación transversal que sí debe converger

Los recorridos repiten un núcleo verificable: (a) identidad del elector; (b)
bloqueo de acciones incompatibles mientras hay una espera; (c) enumeración de
alternativas sólo para ese elector; (d) proyección por audiencia y alternativa
remota opaca; (e) revalidación al resolver; (f) transición pendiente→consumida
con rollback; (g) inclusión indirecta en snapshot y replay; y (h) CAS en
servicio/storage. Hoy ese núcleo está repartido entre campos concretos de
`GameState`, ramas prioritarias del enumerador, dispatch del motor, observación y
frontera HMAC. Esa es duplicación contractual, aunque las implementaciones no
sean idénticas.

El mínimo común futuro puede expresar `decision_id`, elector, audiencia,
referencias opacas a opciones, versión/estado de creación, estado
pendiente/resuelto y política de expiración; debe registrar la resolución una
sola vez y atravesar snapshot/replay/CAS. El ID no debe ser el índice de una lista
ni depender de un secreto efímero. La enumeración puede materializar opciones o
referenciarlas mediante un proveedor especializado, siempre que la resolución
revalide autoridad y versión.

### Datos especializados que deben permanecer en sus capabilities

No pertenecen al primitive universal: IDs de cartas candidatas, filtros y
cardinalidades; zonas, destinos, barajado o revelación; estructuras de target y
asignación; `StackItem`, `item_id`, simultaneidad y orden LIFO; razones y
definiciones de reemplazo; reejecución de un comando y cursor de elecciones;
orden persistente de replacements; ni reglas de secreto compuesto o revelación
simultánea. El primitive coordina **quién puede elegir cuál alternativa opaca y
cuándo queda consumida**; cada capability interpreta el payload y valida su
semántica.

## Veredicto

Hay suficiente conducta común observada para justificar la abstracción mínima
de `CAP-ACTION-004`; crear otra primitive universal paralela duplicaría actor,
audiencia, invalidación, exactly-once, persistencia, replay y CAS. A la vez, el
recorrido rechaza convertir `PendingSearch`, `PendingMoveReplacement`, targeting
u ordenación en una única superestructura cargada con todos sus datos.

COMMON CONTRACT FOUND
