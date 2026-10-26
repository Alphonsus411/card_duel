# CAP-SECRET-001 / S0 — Contrato de observación privada

Fecha: 2026-10-26
Estado: contrato de alcance; sin cambio de runtime
Capability: `MISSING / READY`

## Objetivo

Fijar la unidad mínima de `CAP-SECRET-001`: permitir a un observador autorizado
mirar una zona o subconjunto oculto sin convertir esa información en revelación
pública, selección, ordenación ni cambio de estado.

## Hechos de partida

| Superficie existente | Hecho observado | Límite |
| --- | --- | --- |
| `GameEngine.observe(player_id)` | la observación del jugador contiene su mano propia y no las identidades de la mano rival | no expone una lectura temporal de mazo ni subconjunto oculto |
| `PublicPlayerObservation` | copia exclusivamente la observación ya autorizada a un DTO de transporte | no debe inspeccionar el motor ni añadir identificadores ocultos |
| `CAP-PRIVACY-001` | la audiencia evita publicar mano rival, orden de mazo y detalles de pila | proyectar estado actual no autoriza mirar contenido adicional |
| `CAP-ZONE-002` | modela mazo, mano y las zonas técnicas de resolución/revelado | no define por sí sola audiencia ni vida de una mirada privada |

## Contrato mínimo propuesto

Una futura operación de mirada privada deberá cumplir simultáneamente:

1. Recibir una identidad de observador autorizada y un alcance de zona o
   subconjunto definido por una capability cerrada; nunca un `player_id` elegido
   libremente por el transporte.
2. Devolver contenido sólo a su audiencia explícita. Ninguna observación del
   rival, espectador o DTO público puede inferir identidad, posición, filtro o
   cardinalidad más allá de lo que ya autorice `CAP-PRIVACY-001`.
3. Ser de sólo lectura: no mueve, revela, baraja, marca, bloquea prioridad ni
   consume una decisión; tampoco crea eventos públicos.
4. Ser efímera: el resultado observado no entra en `GameState`, snapshot,
   replay, digest, historial de comandos ni eventos. El replay reproduce la
   decisión posterior autorizada, no una lectura privada como si fuera una
   transición de juego.
5. Revalidar autorización y estado de zona en la frontera de lectura y usar un
   rechazo público estable que no distinga contenido, elegibilidad o existencia
   de una carta oculta.

## Exclusiones deliberadas

| Necesidad | Capability propietaria |
| --- | --- |
| Elegir cartas, límites, modo, orden o revelación posterior | `CAP-SECRET-002` |
| Buscar filtrando, pausar y reanudar una resolución | `CAP-SEARCH-001` / `CAP-SEARCH-002` |
| Mirar/reordenar top-N o colocar al fondo | `CAP-SEARCH-003` |
| Revelar públicamente, mover o registrar causalidad de zona | `CAP-ZONE-003` y capabilities de efecto/zona correspondientes |
| Last-known information o audiencia de transiciones históricas | `CAP-ZONE-006` |

## Compatibilidad y seguridad

S0 no introduce un tipo persistido ni requiere una versión de snapshot o replay.
Una implementación futura que convierta la mirada en decisión, evento, estado
pendiente o token durable deberá detenerse y definir primero su contrato de
autorización, audiencia, invalidación, proyección y versionado. No se permiten
tokens reutilizables ni errores que funcionen como oráculo de información oculta.

## Salida de S0

S1 deberá inventariar las rutas actuales de observación, aplicación y servicio
contra este contrato, incluida la no interferencia entre dos estados que sólo
difieran en datos ocultos. S0 no acredita todavía una operación de mirada y no
promueve la capability ni desbloquea `CAP-SECRET-002`.
