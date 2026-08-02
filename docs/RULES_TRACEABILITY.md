# Trazabilidad de reglas

Esta matriz enlaza grupos de `RULES_BASELINE.md` con implementación y pruebas.
No convierte normalizaciones ni pendientes en reglas nuevas.

| Grupo | Módulos autoritativos | Pruebas principales |
|---|---|---|
| Preparación, mano, robo, Reserva, fases y descarte | `engine/game.py`, `engine/zones.py`, `rules/config.py` | `test_setup_and_phases.py`, `test_resources_and_zones.py` |
| Pago atómico, habilidades, costes alternativos, dinámicos y X | `engine/game.py`, `rules/resolvers.py`, `domain/models.py` | `test_stack_and_priority.py`, `test_advanced_mechanics.py`, `test_dynamic_rules_v070.py`, `test_variable_rules_v080.py` |
| Prioridad, pila, objetivos, búsquedas y disparos | `engine/stack.py`, `engine/effects.py`, `engine/game.py` | `test_stack_and_priority.py`, `test_resolution_v050.py`, `test_extensibility_v060.py`, `test_manager_contracts_v0130.py` (paridad arquitectónica, sin cambio normativo) |
| Efectos, prevención, daño, regeneración y estado | `engine/effects.py`, `engine/game.py`, `engine/zones.py` | `test_effect_manager_v0170.py`, `test_advanced_mechanics.py`, `test_resolution_v050.py` |
| Combate, Desafío, Divinos, Señores y Legendaria | `engine/combat.py`, `engine/game.py` | `test_combat_and_legendary.py`, `test_mythic_v040.py` |
| Zonas, barajado, sustituciones y control | `engine/zones.py`, `engine/stack.py`, `engine/effects.py` | `test_resolution_v050.py`, `test_extensibility_v060.py`, `test_variable_rules_v080.py` |
| Texto efectivo, copia y transformación | `rules/resolvers.py`, `engine/effects.py`, `engine/game.py` | `test_dynamic_rules_v070.py`, `test_extensibility_v060.py` |
| Documentos v2 y migraciones v1 | `persistence/`, `content/manifest.py` | `test_persistence_v090.py`, `test_hardening_v0100.py` |
| Persistencia CAS | `storage/`, `service.py` | `test_service_v0110.py`, `test_hardening_v0100.py` |

## Matriz de decisiones base–Mítica (R-03B)

Las páginas de esta matriz son páginas físicas del PDF base y, para Mítica, el
par **física / interna**. «Backend actual» describe el estado observado, no le
otorga autoridad normativa. La decisión usa un vocabulario cerrado: **ya
cumple**, **requiere prueba**, **requiere corrección**, **bloqueada** o **sólo
documentación**. Una fila sólo puede pasar a «ya cumple» cuando fuente, código,
documentación y pruebas coincidan.

| ID | Materia | Reglamento base | Edición Mítica | Clasificación | Backend actual | Decisión |
|---|---|---|---|---|---|---|
| R-03B.3-DECK | Construcción de mazos | Reglas básicas 1–2, p. 5: igualdad y mínimo de 50 puntos; no fija cantidad de cartas. | Física 2 / interna 1: 40–60 cartas; el presupuesto de puntos es contradictorio (`N-POINTS-01`). | B — formato de mazo, con extremo E en puntos. | Acepta mazos sin validar 40–60 cartas ni presupuesto. | **requiere corrección**: aplicar 40–60 sólo mediante un formato explícito; los puntos siguen bloqueados. |
| R-03B.3-COPIES | Copias máximas | P. 5: no establece un máximo de copias verificable. | Física 2 / interna 1: hasta cinco no Legendarias y cuatro Legendarias. | B — formato de mazo. | No cuenta copias por identidad y rango al crear la partida. | **requiere corrección**: la validación de formato aún no existe. |
| R-03B.3-ZERO | Cartas de coste cero | Reglas básicas 1 y 3, p. 5: el coste interviene en el ajuste de mazo y las cartas se pagan para jugarse. | Física 2 / interna 1: Clásico limita las de coste cero; Mística fija costes 5–50 para sus cartas. | B — restricción de formato. | El modelo admite coste cero, pero no conoce formatos ni aplica su límite. | **requiere corrección**: no debe prohibirse universalmente; debe validarse por formato. |
| R-03B.3-FORMATS | Formatos Clásico y Mística | Sin esos formatos en las reglas básicas verificadas, pp. 5–8. | Física 2 / interna 1 y física 3 / interna 2: ediciones admitidas y circuito de cada formato. | B — formato de mazo. | `RuleSet` es universal y no representa Clásico/Mística. | **requiere corrección**: introducir perfiles sólo antes de validar mazos del formato. |
| R-03B.2-DRAIN | Drenaje | Sin Drenaje en las reglas básicas verificadas, pp. 5–8. | Física 3 / interna 2: una vez en turno activo, 1–5 Pasos y Heridas escalonadas. | A — regla universal Mítica. | `DrainSteps` aplica ventana, frecuencia, rango y coste; `test_mythic_v040.py` cubre el camino principal. | **ya cumple**. |
| R-03B.2-LEGENDARY | Legendarios | Regla básica 19, p. 8: protección antigua dentro del tratamiento conjunto de especiales. | Física 3 / interna 2: subtipo y afectación normal salvo inmunidad expresa. | A — actualización universal. | Representa rango, subtipos y efectos de Fase Legendaria, pero no hay una prueba documental/mecánica dedicada a toda la actualización de afectación. | **requiere prueba**. |
| R-03B.2-DIVINE | Divinos | Regla básica 19, p. 8: inmunidad antigua, incluso frente al descarte. | **Página física 3 / página interna 2**: inmunidad limitada y Transmutación permitida. | A — modificación posterior expresa. | Permite Transmutación, pero bloquea toda habilidad como fuente, no sólo habilidades de criaturas permanentes. | **requiere corrección**: alinear el alcance exacto y su prueba antes de cerrar. |
| R-03B.2-ABYSS | Señores del Abismo | Sin este tipo en las reglas básicas verificadas, pp. 5–8. | Física 3 / interna 2: Fuerza derivada del coste, pago de Fuerza, descarte a cero y límites de combate. | A — regla universal Mítica. | Modela dominio, Fuerza y descarte a cero; comparte caminos genéricos con otros Señores. | **requiere prueba**: falta una prueba de contrato completa por dominio. |
| R-03B.2-ELYSIUM | Señores del Elíseo | Sin este tipo en las reglas básicas verificadas, pp. 5–8. | Física 3 / interna 2: mismas propiedades mecánicas generales del bloque de Señores. | A — regla universal Mítica. | Existe el dominio, sin cobertura específica del Elíseo. | **requiere prueba**. |
| R-03B.2-MAGIC | Señores de la Magia | Sin este tipo en las reglas básicas verificadas, pp. 5–8. | Física 3 / interna 2: análogo general y neutral respecto de facción. | A — regla universal Mítica. | Existe el dominio y una prueba de conversión a criatura, pero esa conversión procede de una habilidad de prueba, no de una regla universal del dominio. | **requiere prueba**. |
| R-03B.2-REALMS | Señores de los Reinos | Sin este tipo en las reglas básicas verificadas, pp. 5–8. | Física 4 / interna 3: puede transformarse en criatura para combatir y usar capacidades. | A — regla universal Mítica. | El motor sólo lo transforma mediante efectos declarados por contenido; no garantiza la capacidad por ser de Reinos. | **requiere corrección**. |
| R-03B.2-CHALLENGE | Desafío | Combate ordinario, reglas básicas 13–18, pp. 7–8; no define Desafío. | Física 4 / interna 3: una vez por turno en Fase Activa y sustitución del combate. | A — regla universal Mítica. | Resuelve el duelo sin daño sobrante, pero lo sitúa en Combate y no registra un límite independiente de una vez por turno. | **requiere corrección**. |
| R-03B.2-LEGENDARY-PHASE | Fase Legendaria | Secuencia de turno y Fase Legendaria, pp. 3–4. | Física 3 / interna 2: mantiene el tratamiento de Legendarios dentro de la actualización. | A — regla universal. | `RuleSet` exige Robo, Mantenimiento, Efectos, Combate, Legendaria y Descarte; existen pruebas de fase y disparos. | **ya cumple**. |
| R-03B.2-MULTIPLAYER-END | Condiciones terminales multijugador | Objetivo, p. 3; Heridas, p. 4; regla básica 2, p. 5; empate de dos, pp. 7–8. Admite uno o más adversarios, pero no define continuidad ni ganadores para 3+. | Sin aclaración en la sección normativa, físicas 2–4 / internas 1–3. | E — silencio normativo. | Para 3+ detiene en `BLOCKED` sin inventar ganadores; conserva los finales de dos jugadores. | **bloqueada**: requiere aclaración oficial, no una inferencia de código. |
| R-03B.1-TOURNAMENT | Administración de torneos | Organización general y modalidades, pp. 9–10. | Física 2 / interna 1 y física 3 / interna 2: circuito, legibilidad, sustitución y sanciones. | C — organización física. | El motor headless no administra torneos ni inspecciona soportes físicos. | **sólo documentación**. |
| R-03B.4-CORPUS | Comienzo del catálogo de cartas | El catálogo sucede a las reglas y organización; no es regla universal. | Física 4 / interna 3: `EDICION MITICA`, anuncio del descriptivo y primera carta nº 001. | D — texto particular de carta. | El paquete de producción no instancia ni incorpora cartas; sólo ofrece contratos para colecciones externas. | **sólo documentación**: esta entrega no importa el corpus. |

Los cuatro frentes de R-03B son: `R-03B.1`, **fuente verificable** y decisiones
documentales; `R-03B.2`, **reglas universales**; `R-03B.3`, **formatos de mazo**;
y `R-03B.4`, **futuro corpus**. Esta matriz no declara R-03B completada: las
filas bloqueadas, con corrección o sin prueba impiden cerrarla hasta alinear
código, documentación y pruebas.

## Auditoría base–Mítica (R-03A)

El inventario completo, su jerarquía, las categorías A–E y la frontera exacta
entre reglas generales y cartas están en `MYTHIC_RULES_AUDIT.md`. El PDF Mítico
sí está versionado y paginado: Divinos se documenta en física 3 / interna 2.
La actualización limita su inmunidad y conserva Transmutación, frente a la regla
básica 19 (`Fantasy Tokens.pdf`, p. 8), por lo que prevalece como modificación
posterior expresa. Las adiciones no se cuentan automáticamente como conflictos.

Permanecen bloqueados `N-POINTS-01` (200, 300, intervalo 300–400 y recomendación
aproximada de 300) y `M-LORD-EVENT-01`: «a modo de Eventos» respalda la ventana
de Fase Activa, no una reclasificación universal de habilidades de Señor.
Cualquier cambio del motor o de pruebas que resolviese esos extremos requiere
aclaración oficial.

## Ambigüedades y deuda normativa conservadas

- El reglamento sí contempla más de dos participantes: presenta el objetivo
  como enfrentarse a «uno o más adversarios» (PDF, p. 3) y su regla básica 2
  se refiere expresamente a «ambos jugadores o todos los participantes» al
  acordar el mismo límite de Heridas (PDF, p. 5).
- El mismo texto no define cómo termina una partida de tres o más participantes.
  La concesión abandona el juego y otorga la victoria a «su oponente» (PDF,
  p. 3), alcanzar el límite de Heridas hace perder «al que» llega a él (PDF,
  p. 4), y la única regla de derrota simultánea describe un empate entre «el
  jugador pasivo» y «el otro jugador» (regla básica 18, PDF, pp. 7–8).
  No se especifica si una concesión o derrota individual termina toda la
  partida, si continúan los supervivientes, ni cómo seleccionar u ordenar
  ganadores. Hasta que exista aclaración normativa, no se eleva a regla ninguna
  de esas posibles mecánicas multijugador.
- Reparto entre bloqueadores en orden declarado, pendiente de aclaración.
- Regeneración como escudo consumible, sin inferir un procedimiento ausente.
- La precedencia Mítica para Divinos se conserva con referencia física 3 /
  interna 2; los bloqueos de puntos y habilidades de Señor están inventariados en
  `MYTHIC_RULES_AUDIT.md` y cualquier decisión normativa pertenece a R-03B.
- Los esquemas 3+ siguen siendo pendientes,
  no reglas. Un adaptador HTTP u otro transporte está excluido del alcance y no
  es un pendiente implementable. La firma y política de
  confianza de colecciones (R-04), así como la frontera autenticada de
  aplicación agnóstica del transporte (R-06), ya están completadas; esa frontera
  no equivale a una autorización para implementar un adaptador de red.

## Trazabilidad 0.18.0

El registro de colecciones es infraestructura de contenido y no modifica reglas observables. Los manifiestos, snapshots y replays continúan en esquema v2 y las migraciones v1 a v2 permanecen vigentes. La igualdad exacta entre una definición del mazo y la registrada se comprueba antes de crear la partida.

## Trazabilidad 0.18.1

La secuencia de fases y el mínimo de dos participantes ya documentados se
rechazan ahora durante la construcción de un `RuleSet` inválido. La validación
previa de mazos y el arreglo del SQLite en memoria son garantías de atomicidad e
infraestructura; no incorporan texto de cartas ni resuelven las ambigüedades
normativas pendientes.

## Trazabilidad 0.18.2

La revisión directa de `Fantasy Tokens.pdf` confirma que el formato admite uno
o más adversarios y que todos los participantes comparten el límite de Heridas.
No resuelve la concesión, la continuidad tras una derrota, las derrotas
simultáneas ni la selección y el orden de ganadores cuando participan más de dos;
esas cuestiones quedan registradas como deuda normativa, sin convertir el
comportamiento actual del motor en una regla fuente.

## Trazabilidad 0.18.3

`engine/game.py` deja de aplicar a tres o más participantes la inferencia de que
todos los jugadores no derrotados son ganadores. Ante concesión o límite de
Heridas conserva los afectados, no asigna ganadores y usa `BLOCKED` como parada
técnica pendiente de aclaración. `test_end_conditions.py` verifica ambos caminos
y conserva las condiciones terminales existentes para exactamente dos jugadores.
Esta protección se registra como entrega completada en la hoja de ruta. R-04 es
la única tarea siguiente; R-02 y R-03 permanecen bloqueadas por aclaraciones
normativas, R-05 por la falta de un esquema 3 definido, y R-06 y R-07 continúan
como pendientes técnicos sin promover.

## Trazabilidad 0.19.0

El sobre de firma v1 y la política de claves son infraestructura de distribución,
no reglas del juego: no cambian fases, acciones, cartas ni resultados. El
manifiesto permanece en esquema v2 y conserva sus bytes canónicos y su SHA-256;
el sobre separado añade autenticidad cuando una aplicación exige una firma de
una clave confiable. Los formatos persistentes de partidas continúan en v2 y no
se añade ninguna migración. R-04 queda completada sin resolver deuda normativa.

## Trazabilidad de R-06

La frontera autenticada es infraestructura y no modifica reglas observables.
`AuthenticatedMatchApplication` deriva el jugador de (`iss`, `sub`), partida y
capacidad; entrega DTO públicos y conserva la escritura CAS de `MatchService`.
La batería compartida de memoria y SQLite verifica además que crear, observar,
enviar y administrar son permisos independientes. R-06 queda completada.
El transporte queda fuera de alcance. Solo otra decisión documental expresa podría
habilitarlo y deberá mantener
esta aplicación como frontera autoritativa y no podrá aceptar `player_id`, exponer
`GameEngine` o `GameState`, omitir `expected_version`/CAS ni reinterpretar los
comandos recibidos.

## Trazabilidad de R-07.1

La extracción de combate no modifica reglas: `CombatManager` reproduce la
enumeración determinista de atacantes, Desafíos y bloqueadores y la oferta de
resolución, incluido su límite configurable. La validación de `execute` sigue
siendo autoritativa aunque una acción no aparezca en el prefijo enumerado. La
paridad cubre dos y más jugadores y huellas de estado, eventos, historial y
contadores. R-07.1 quedó completada con un límite explícito: el alcance de
movimientos y sustituciones se abordó después en R-07.2, sin formar parte de
aquella entrega de combate.

## Trazabilidad de R-07.2

La consolidación de movimientos es exclusivamente arquitectónica. Robo,
reciclaje, movimiento, separación de Equipo, limpieza de instancia y
sustituciones conservan los resultados anteriores y tienen una sola autoridad
en `ZoneManager`; `GameEngine` conserva coordinación, transacción y replay. La
paridad de `test_zone_parity_r072.py` compara todas las observaciones
deterministas mediante un `ZoneContext` mínimo independiente. R-07.2 queda
cerrada sin resolver ambigüedades ni cambiar reglas del juego.
