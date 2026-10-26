# CAP-ZONE-003 — Z2: modelo causal mínimo de transición

**Fecha:** 2026-10-26
**Estado de la fase:** completada; diseño sin cambio de motor
**Capability:** `CAP-ZONE-003` sigue `PARTIAL / READY`

## Decisión de integración

El registro de transición será una evidencia **interna** del estado autoritativo.
Su audiencia inicial es `DecisionAudience.INTERNAL`: no se reutiliza `event_log`
como canal de proyección, ni se infiere visibilidad a partir de la zona. La
proyección por jugador, la redacción de identidades y cualquier audiencia distinta
de `INTERNAL` quedan explícitamente en `CAP-PRIVACY-001` y no forman parte de Z2–Z4.

Esta decisión permite persistir causalidad sin revelar cartas en mazo o mano y sin
crear una segunda autoridad de visibilidad. No afirma que toda transición sea
secreta: sólo impide que este nuevo registro cambie lo que hoy se publica.

## Modelo propuesto

Z4 introducirá una única entrada inmutable por movimiento efectivo:

| Campo | Tipo propuesto | Invariante |
| --- | --- | --- |
| `sequence` | entero positivo | monótono y asignado por la autoridad de transición; no se recicla dentro de una partida |
| `card_id` | identificador de instancia | debe identificar la carta desplazada |
| `origin_zone` / `origin_player_id` | zona y contenedor previo opcional | se captura antes de retirar la carta; `origin_player_id` es `None` para `RESOLUTION` y `VOID` |
| `requested_destination` / `requested_player_id` | zona y contenedor solicitados | conserva la intención del llamador incluso si hay reemplazo |
| `effective_destination` / `effective_player_id` | zona y contenedor final | coincide con el resultado de la mutación y con el retorno de `_move_card` |
| `reason` | `MoveReason` | causa tipada ya autorizada; no se convierte texto ni evento heredado |
| `batch_id` | token opaco no vacío | identifica una operación compuesta; una transición aislada recibe un lote propio |
| `audience` | `DecisionAudience` | en este incremento sólo admite `INTERNAL` |
| `prior_state` | `TransitionPriorState` acotado | contiene únicamente ubicación, controlador y estado de anexo inmediatamente previos; no es LKI general |

`TransitionPriorState` queda limitado a los datos que la puerta debe preservar
antes de su limpieza: `zone`, `container_player_id`, `controller_id` y
`attached_to`. No incluye fuerza, daño, modificadores, definición efectiva,
targets, habilidades ni texto. Añadirlos requerirá el contrato independiente de
last-known information (`CAP-ZONE-006`).

Una entrada cuyo reemplazo mantenga la carta en `BATTLEFIELD` sigue siendo una
transición causal: el destino solicitado y el efectivo difieren, y el registro
no se omite. Esto evita que el reemplazo actual oculte una intención de salida.

## Autoridad y atomicidad

1. Sólo la futura puerta de `ZoneManager` podrá asignar `sequence`, construir la
   entrada y anexarla a `GameState`; `GameEngine` conserva una fachada delegada.
2. `batch_id` lo abre el recorrido que conoce la operación compuesta y lo pasa a
   sus movimientos hijos. Si no existe tal contexto, la puerta genera un lote de
   una sola entrada. Ningún consumidor inventa, fusiona ni divide lotes.
3. La entrada se incorpora después de que se determine el destino efectivo y
   dentro del mismo snapshot/rollback de la operación pública. Ante excepción,
   ni estado de carta, ni zonas, ni secuencia, ni lote sobreviven parcialmente.
4. `MOVE_REPLACED`, `CARD_DRAWN`, `CARD_PLAYED` y eventos equivalentes se
   conservan con su semántica actual. No son fuente del registro ni se derivan
   obligatoriamente de él en esta fase.
5. El modelo no llama triggers, no ordena efectos y no expone LKI. Consumidores
   futuros deberán declarar su capability y no leer campos ausentes.

## Límites de compatibilidad para Z3 y Z4

Z3 añadirá versionado, codec, migración fail-closed y golden de legado. Los
snapshots previos no reciben transiciones inventadas: su historial causal será
vacío o explícitamente no disponible según el contrato de migración que se
apruebe allí. Z4 adaptará las rutas inventariadas en Z1 a la puerta, sin modificar
la forma de eventos públicos ni promover la capability.

Quedan fuera: políticas de visibilidad por zona o jugador, proyección pública,
reemplazos generalizados, LKI extendida, triggers de salida, decisiones pendientes
y cambios de corpus.

## Criterios de salida de Z2

- Cada campo tiene una autoridad única y una semántica no inferida.
- El destino solicitado y el efectivo permanecen distinguibles.
- El estado previo está acotado para no adelantar `CAP-ZONE-006`.
- La audiencia `INTERNAL` impide una nueva fuga hasta que exista una proyección
  autorizada.
- Z3 puede versionar el modelo sin revisar el diseño de datos causal.
