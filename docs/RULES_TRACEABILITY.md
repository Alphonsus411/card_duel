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
- Precedencia Mítica para la inmunidad de Divinos.
- Firma de colecciones, esquemas 3+, red/autenticación y registro formal de
  contradicciones siguen siendo pendientes, no reglas.

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
enviar y administrar son permisos independientes. R-06 queda completada; el
siguiente incremento permitido es R-07.1, limitado a la extracción de combate.
