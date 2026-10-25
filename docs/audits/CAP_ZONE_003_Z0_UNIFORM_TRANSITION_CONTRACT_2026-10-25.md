# CAP-ZONE-003 Z0 — contrato de puerta uniforme de zona

**Fecha:** 2026-10-25
**Estado:** Z0 completada; habilita únicamente Z1 (inventario y caracterización)
**Capability:** `CAP-ZONE-003` permanece `PARTIAL / READY`.

## Propósito

Cerrar una única frontera interna para toda transición de carta entre zonas. La
frontera futura debe conservar, de manera determinista, origen, destino final,
causa, lote, audiencia y el estado anterior necesario para consumidores
autorizados. Z0 no implementa ese registro: sólo congela qué debe acreditarse
antes de cambiar modelos, eventos, snapshot o replay.

## Baseline acreditado

`ZoneManager._move_card` ya centraliza numerosos movimientos: aplica el
reemplazo local existente, retira la carta de su contenedor, actualiza zona e
instancia, limpia estado al salir del campo de batalla y devuelve el destino
efectivo. `GameEngine._move_card` delega en ese gestor. `MoveReason` conserva
parte de la causa.

Esto no equivale todavía a una puerta uniforme: hay llamadas internas y eventos
heterogéneos (`MOVE_REPLACED`, `CARD_DRAWN`, etc.), sin registro causal común,
lote ni last-known information. Ningún evento existente se reinterpretará como
LKI ni como trigger general.

## Decisiones y límites

1. **Una transición tiene destino efectivo.** Si un reemplazo altera el destino,
   la futura evidencia registra el destino final, sin borrar la causa solicitada.
2. **No hay inferencias retroactivas.** Origen, audiencia o estado anterior que
   no estén conservados explícitamente no se reconstruyen desde eventos,
   `card_id`, texto ni el estado final.
3. **Atomicidad existente se conserva.** La futura puerta sólo podrá mutar junto
   a la transacción pública ya existente; una excepción no puede dejar tarjeta,
   zonas y registro causal divergentes.
4. **Separación de capabilities.** Reemplazos generales pertenecen a
   `CAP-ZONE-004`; triggers de salida a `CAP-ZONE-005`; LKI a `CAP-ZONE-006`;
   visibilidad y redacción a `CAP-PRIVACY-001`.

## Secuencia autorizada

| Fase | Entregable | Puerta de salida |
| --- | --- | --- |
| Z0 — Contrato | Este documento y exclusiones. | No se trata un evento actual como registro causal completo. |
| Z1 — Inventario | Censo de cada llamada y mutación de zona. | Se localizan todas las rutas que deben cruzar la puerta. |
| Z2 — Modelo | Registro causal mínimo y contrato de audiencia. | No hay campos libres ni segunda autoridad. |
| Z3 — Persistencia | Versionado, migración y golden legado. | Snapshot/replay conservan orden e identidad. |
| Z4 — Motor | Una puerta efectiva y adaptación mínima de rutas. | Ninguna transición autorizada evita la frontera. |
| Z5 — Verificación | Matriz de atomicidad, replay y privacidad. | Paridad y rechazo cerrado acreditados. |
| Z6 — Cierre | Compatibilidad, límites y gate. | Sólo se promueve con evidencia completa. |

## Exclusiones persistentes

- No se añade LKI, trigger general, selector, prioridad ni decisión pendiente.
- No se amplían reemplazos, orden de múltiples reemplazos ni elecciones.
- No se modifican schemas, eventos públicos, snapshots, replay, API o corpus.
- No se promueve `CAP-ZONE-003` ni ninguna carta por esta fase documental.
