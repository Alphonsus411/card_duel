# CAP-DAMAGE-002 P4 — puerta causal de combate

**Fecha:** 2026-10-25
**Estado:** completada
**Alcance:** sólo `DamageCause.COMBAT`; la capability continúa en `PARTIAL`.

## Cambio implementado

`CombatManager` ya no usa las puertas genéricas de daño/herida al resolver
combate. Usa exclusivamente `_deal_combat_damage` y
`_deal_combat_wounds`. Ambas puertas proporcionan de forma explícita
`DamageCause.COMBAT` a la resolución de reservas tipadas.

La bifurcación de Desafío se mantiene dentro de la misma resolución de combate;
sus dos impactos pasan por las mismas puertas, sin una causa alternativa ni
inferencias desde carta, objetivo o fase.

## Compatibilidad y consumo

Las puertas genéricas `_deal_damage` y `_deal_wounds` no consultan reservas
tipadas. Por tanto, un efecto, limpieza u otra ruta ajena a combate no consume
ni aprovecha una reserva `COMBAT`.

Para no alterar el comportamiento de partidas heredadas, la reserva escalar
histórica se descuenta primero, igual que antes. Sólo el importe que sobrevive a
esa protección se enfrenta a las reservas `COMBAT`. Las reservas se recorren en
el orden persistido, se consume sólo el importe usado y se eliminan al llegar a
cero; las reservas no coincidentes se conservan sin modificación.

La mutación del saldo de reserva y la aplicación del remanente ocurren dentro
de la transacción de comando existente. Un fallo de resolución restaura el
estado completo, incluido saldo y daño/heridas.

## Evidencia

`tests/test_damage_prevention_characterization.py` cubre:

- combate ordinario y Desafío con las mismas reservas `COMBAT`;
- herida de combate sin bloqueadores;
- prioridad de la reserva escalar heredada frente a una reserva tipada;
- rutas no pertenecientes a combate, que dejan la reserva `COMBAT` intacta.

No se añadieron causas, cartas, corpus, redirección, reemplazos, prioridades ni
triggers. P5 queda reservado para ampliar la matriz de verificación (incluido
rollback y paridad completa de snapshot/replay).
