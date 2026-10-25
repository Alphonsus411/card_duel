# CAP-ZONE-003 — Z1: inventario de transiciones y caracterización

**Fecha:** 2026-10-25  
**Estado de la fase:** completada  
**Capability:** `CAP-ZONE-003` sigue `PARTIAL / READY`

## Alcance de Z1

Z1 inventaría el comportamiento existente que deberá atravesar la puerta uniforme
definida en Z0. No crea un registro causal, no cambia la secuencia de eventos, no
añade LKI y no promueve la capability. Su resultado es una línea base para Z2 y
Z3: cualquier diseño nuevo debe conservar estas rutas, sus garantías transaccionales
y los límites de audiencia aún ausentes.

## Fronteras actuales

| Frontera | Recorridos que la usan | Garantía actual | Vacío respecto a CAP-ZONE-003 |
| --- | --- | --- | --- |
| `ZoneManager._move_card` | movimientos directos y delegados | retira de la zona anterior, actualiza `CardInstance.zone`, inserta en destino y limpia estado al salir del campo | no materializa origen, lote, audiencia ni estado anterior en un registro común |
| `GameEngine._move_card` | juego de carta, costes, descarte, transmutación, SBA/destrucción y adaptadores de managers | delegación transparente a `ZoneManager` y retorno del destino efectivo | la fachada no añade identidad causal ni observabilidad uniforme |
| `ZoneManager._draw` / `GameEngine._draw` | mano inicial, fase de robo, mulligan y reciclaje | compone movimientos `DECK→HAND` y, si procede, `DISCARD→DECK` con barajado determinista | emite eventos de robo/reciclaje, no un evento de transición general |
| `EffectResolver` | `MOVE_CARD` y retorno controlado de cartas | delega por el protocolo de contexto | la causa usa `MoveReason.RULE`; no porta audiencia ni lote |
| `StackManager` | resolución de carta/efecto y limpieza de fuente | delega por el protocolo de contexto | la resolución no conserva una traza causal de zona autónoma |

No se han encontrado escrituras productivas alternativas de `CardInstance.zone` ni
mutaciones de listas de zonas fuera de `ZoneManager` para desplazar una carta. El
estado de zona también se serializa genéricamente como parte de `GameState` y
`CardInstance`; actualmente no existe una colección de transiciones que pueda
versionarse o reproducirse de forma independiente.

## Inventario por entrada funcional

| Entrada | Destino / causa actual | Señales de evento existentes | Observación para la futura puerta |
| --- | --- | --- | --- |
| creación y mano inicial | `DECK→HAND`, `RULE` | `CARD_DRAWN` | el evento expresa robo, no origen ni destino |
| mulligan | `HAND→DECK`, `RULE`, seguido de robo | `MULLIGAN`, `CARD_DRAWN` | el lote del mulligan no está identificado |
| jugar carta y pagar costes | descarte/sacrificio/mill a `DISCARD`; carta a `RESOLUTION` | `CARD_PLAYED` | causas específicas para descarte/sacrificio, pero el paso a resolución no las normaliza |
| resolver pila | fuente a `BATTLEFIELD` o `DISCARD`; efectos pueden mover cartas | eventos propios de resolución/efecto | la procedencia de cada cambio queda repartida entre llamadas |
| robo con reciclaje | `DISCARD→DECK`, barajado, `DECK→HAND` | `DISCARD_RECYCLED`, `CARD_DRAWN`, o `DRAW_FAILED` | hay dos familias de evento para una sola operación compuesta |
| ajuste de mano | `HAND→DISCARD`, `DISCARD` | `HAND_ADJUSTED` | el evento es agregado y no identifica cada transición |
| transmutación | `BATTLEFIELD→DISCARD`, `TRANSMUTE` | `CARD_TRANSMUTED` | el controlador se conserva temporalmente para triggers; no debe ser inferido a posteriori |
| destrucción y SBA | `BATTLEFIELD→DISCARD`, `DESTROY` o `STATE_BASED` | `PERMANENT_DESTROYED`, `DESTRUCTION_REPLACED`, `LORD_DEPLETED` | la sustitución puede cambiar el destino efectivo |
| reemplazo de movimiento | destino alternativo o permanencia en campo | `MOVE_REPLACED` | sólo cubre el caso de reemplazo actual y no equivale al hecho de transición |

## Caracterización congelada

1. `_move_card` devuelve el **destino efectivo**. Un reemplazo permitido puede
   devolver `BATTLEFIELD` o cambiar el destino solicitado; la petición original
   no basta para reconstruir el resultado.
2. El movimiento normal no emite por sí mismo un evento universal. Los eventos
   se producen en las operaciones que lo componen o en ramas particulares
   (robo, reciclaje, destrucción, transmutación o reemplazo).
3. La ejecución de comandos protege la mutación mediante snapshot/rollback del
   motor. La futura puerta debe integrarse dentro de esa misma unidad atómica;
   no puede publicar un registro antes de que falle la operación.
4. Snapshot, codec y replay preservan el estado final y el historial de comandos,
   pero no una historia causal de transiciones. Z3 decidirá la versión y la
   migración, sin reinterpretar snapshots heredados.
5. `MoveReason` ya representa parte de la causa (`DISCARD`, `SACRIFICE`,
   `TRANSMUTE`, `DESTROY`, `STATE_BASED`, `RULE`), pero no identifica lote,
   audiencia, originador ni estado previo.

## Restricciones para Z2

Z2 deberá proponer el modelo causal mínimo y su audiencia antes de tocar las
fachadas. Debe registrar tanto destino solicitado como efectivo cuando haya
reemplazo, no deducir historia anterior de eventos heterogéneos y mantener fuera
de alcance: LKI (`CAP-ZONE-006`), generalización de reemplazos
(`CAP-ZONE-004`), triggers generales (`CAP-ZONE-005`) y política de privacidad
(`CAP-PRIVACY-001`).

La decisión concreta de audiencia para zonas privadas queda abierta: el inventario
demuestra que no existe aún una proyección común desde la que inferirla sin
ampliar el contrato de privacidad. Por ello Z2 debe definirla explícitamente o
elevarla como integración pendiente, nunca asumir que el `event_log` es público.
