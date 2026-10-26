# CAP-SECRET-001 / S1 — Inventario de rutas de observación

Fecha: 2026-10-26
Estado: inventario estático; sin cambio de runtime
Capability: `MISSING / READY`

## Rutas observadas

| Etapa | Superficie | Hecho observado | Límite frente a S0 |
| --- | --- | --- | --- |
| Motor | `GameEngine.observe(player_id)` | incluye mano propia, campos públicos y datos restringidos de decisiones pendientes para su elector | acepta `player_id` interno; no ofrece un alcance de mirada efímero tipado |
| Observación interna | `PlayerObservation` | puede transportar `searchable_card_ids` y destinos de reemplazo únicamente cuando el observador es el chooser | es una vista interna de especializaciones existentes, no una lectura general de zona |
| Servicio | `MatchService._view_for` | carga el motor y construye `MatchView` con la observación y acciones legales del jugador solicitado | presupone que su llamador ya determinó el jugador autorizado |
| Aplicación | `AuthenticatedMatchApplication.view` | resuelve `ExternalIdentity` mediante `Capability.OBSERVE` antes de llamar al servicio | es la frontera que impide al transporte escoger arbitrariamente el jugador |
| DTO remoto | `PublicPlayerObservation` y `PublicMatchView` | proyectan sólo campos explícitos; no contienen `searchable_card_ids`, destinos de reemplazo, stack interno ni opciones opacas | no transportan una futura mirada privada general |

## Especializaciones que no se deben promover

### Búsqueda pendiente

`PendingSearch` conserva `eligible_card_ids` en el estado porque debe pausar y
reanudar una resolución. `GameEngine.observe` los entrega sólo si
`chooser_id == player_id`; `legal_actions` restringe igualmente
`ResolveSearchChoice` al elector. Las pruebas de paridad comprueban que el rival
recibe una tupla vacía.

Esta ruta es necesaria para `CAP-SEARCH-001` y su elección especializada. No
implementa una mirada S0 porque persiste candidatos, participa en resolución y
termina en una elección.

### Reemplazo de movimiento pendiente

`PendingMoveReplacement` expone índices y destinos sólo al chooser en
`replacement_destinations`; el rival recibe una tupla vacía. Igual que la
búsqueda, es estado de una continuación y no una lectura privada general.

### Mano propia

La mano propia está en `PlayerObservation.own_hand`, mientras que de los demás
jugadores sólo se publica el tamaño. Esta política ya satisface parte de la
audiencia de `CAP-PRIVACY-001`, pero no aporta selección de zona/subconjunto ni
un contrato de no interferencia para una mirada temporal.

## Seguridad observada

1. La aplicación autentica y liga la identidad a un único jugador antes de
   solicitar una vista.
2. El DTO público se construye desde `MatchView` y no vuelve a inspeccionar el
   motor; así evita ampliar accidentalmente la audiencia de campos internos.
3. Las especializaciones actuales restringen tanto la observación como las
   acciones legales del elector; ninguna de ellas autoriza reutilizar sus IDs o
   tokens como API de lectura genérica.
4. El servicio documenta `get_match` como operación interna: devolver el motor
   restaurado a un adaptador remoto rompería la frontera de privacidad.

## Brechas contra S0

- No existe un valor de dominio que exprese alcance de zona/subconjunto y
  audiencia para una mirada efímera.
- No existe una ruta autorizada de aplicación/servicio que produzca tal valor
  sin persistirlo ni emitirlo.
- `observe` aún mezcla estado público, mano propia y especializaciones
  pendientes; no puede reutilizarse sin separar el contrato solicitado.
- Falta una prueba de no interferencia entre dos estados que sólo difieran en
  contenido oculto para la futura salida privada.

## Salida de S1

S2 podrá diseñar el modelo mínimo de una mirada temporal si mantiene la frontera
de S0 y no reutiliza `PendingSearch`, `PendingMoveReplacement`, decisión
pendiente, token opaco ni DTO público. S1 no modifica persistencia, replay,
esquema, decisiones o visibilidad publicada; tampoco desbloquea
`CAP-SECRET-002`.
