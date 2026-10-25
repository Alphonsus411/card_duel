# P2 — Núcleo tipado mínimo para `CAP-DAMAGE-002`

**Fecha:** 2026-10-25

**Estado:** cerrado; habilita P3, pero no activa la semántica en partidas

## Entrega

P2 incorpora sólo tres piezas de dominio interno:

| Pieza | Ubicación | Contrato |
| --- | --- | --- |
| `DamageCause` | `domain/enums.py` | Enum cerrado con el único valor `COMBAT`. |
| `DamagePreventionReservation` | `domain/models.py` | Valor inmutable de causa explícita y cantidad positiva. |
| `resolve_damage_prevention` | `engine/damage_prevention.py` | Operación pura que devuelve importe prevenido, daño restante y saldo de reserva. |

`reserve_damage_prevention` es la única fábrica del módulo para crear una
reserva por su interfaz interna. Ninguna API acepta strings, `None` o una causa
por defecto.

## Atomicidad por construcción

`resolve_damage_prevention` no recibe ni muta `GameState`. A partir de una
reserva inmutable produce un `DamagePreventionResolution` completo:

- cantidad prevenida;
- daño restante;
- saldo restante de la reserva.

P4 deberá confirmar esos tres resultados junto con los cambios de partida en
una única transacción. Separarlos antes de ese punto rompería el invariante
fijado por P0.

## Restricciones respetadas

- No se añadieron causas distintas de `COMBAT`.
- No se modificaron `CardInstance.damage_prevention` ni
  `PlayerState.wound_prevention`.
- No se conectó la nueva reserva a efectos, combate, Desafío o API pública.
- No se alteraron snapshots, replay, codecs, migraciones, versiones ni digest.
- No se añadieron cartas, redirecciones, filtros de fuente, duraciones o
  escudos permanentes.

La separación es deliberada: incorporar la nueva reserva a `GameState` antes
de P3 cambiaría la forma serializada v4 sin migrador explícito y violaría el
contrato fundacional.

## Evidencia

`tests/test_damage_prevention_domain.py` verifica que:

1. el conjunto de causas contiene sólo `COMBAT`;
2. una reserva exige tipo de causa y cantidad positiva;
3. el consumo es puro y reporta todos los resultados requeridos;
4. importe cero conserva saldo y entradas inválidas fallan cerradas.

La batería focalizada de P1 se ejecuta junto a esta evidencia para conservar la
línea base escalar hasta que P3/P4 hagan la migración e integración
correspondientes.

## Gate hacia P3

P3 debe definir la nueva versión escrita de snapshot/replay, migradores desde
v4/v3, un perfil heredado explícito y fixtures golden. No puede sustituir un
contador escalar histórico por `COMBAT` ni aceptar un documento futuro o una
causa desconocida.
