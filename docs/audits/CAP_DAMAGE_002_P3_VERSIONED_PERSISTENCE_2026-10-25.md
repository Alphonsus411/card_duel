# P3 — Persistencia versionada de `CAP-DAMAGE-002`

**Fecha:** 2026-10-25

**Estado:** cerrado; habilita P4, sin conectar aún la resolución de combate

## Versiones emitidas

| Artefacto | Anterior | Nueva | Cambio |
| --- | --- | --- | --- |
| Snapshot | v4 | **v5** | Perfil explícito de reserva escalar heredada y tuplas de reservas causales. |
| Replay | v3 | **v4** | Huella final calculada sobre el estado que ya contiene el perfil persistible. |

Documentos con una versión futura o sin una ruta de migración continúan fallando
cerrados.

## Modelo persistido

`CardInstance` y `PlayerState` persisten por separado:

- el contador escalar existente (`damage_prevention` o `wound_prevention`);
- su perfil explícito `DamagePreventionProfile.LEGACY_UNTYPED`;
- una tupla de `DamagePreventionReservation` causales, inicialmente vacía.

El perfil no convierte el contador escalar en `DamageCause.COMBAT`. La reserva
causal es un campo distinto, aunque ambas cantidades sean iguales. Así se
preserva el significado de una partida anterior y se permite a P4 consumir
solamente reservas tipadas.

## Migraciones y compatibilidad

### Snapshot v4 → v5

El migrador valida la forma de `GameState`, `CardInstance` y `PlayerState`.
Para cada estado histórico añade de manera explícita:

- perfil `LEGACY_UNTYPED`;
- tupla vacía de reservas causales.

Después recalcula el digest interno. Un documento v4 que mezcle campos v5 de
forma ambigua se rechaza; no se corrige silenciosamente.

### Replay v3 → v4

El migrador conserva el historial autoritativo y actualiza su versión. Al
verificar un replay v3 original, el lector calcula además la huella compatible
sin campos de prevención v5. Los replays v4 nuevos sólo aceptan la huella nueva.

Las huellas de v1/v2 siguen usando la compatibilidad histórica existente y
también excluyen los campos v5, de modo que la evolución no rompe dichos
artefactos.

## Rechazo cerrado

- esquema desconocido o futuro: sin migración, error;
- enum o causa desconocidos: `ValueError`, sin mutación parcial;
- campo faltante en v5: error del codec;
- mezcla de forma v4/v5: error del migrador.

El decoder ahora traduce tanto `KeyError` como `AttributeError` de miembros de
enum inexistentes a un único `ValueError` de validación.

## Golden checks y evidencia

`tests/test_damage_prevention_persistence.py` ejerce envelopes canónicos para:

1. snapshot v5 con contador heredado y reserva `COMBAT` separados;
2. snapshot v4 con saldo parcial, migrado a perfil heredado sin causa nueva;
3. replay v3 con digest heredado, reproducido por la ruta compatible;
4. schema y causa desconocidos, rechazados cerradamente.

La batería de persistencia, decisión pendiente, replay histórico, daño y
Desafío se ejecuta junto a esta prueba. El tipo estático de `src/` también se
valida en P3.

## Límites mantenidos

P3 no enruta efectos existentes a reservas tipadas, no consume la reserva
`COMBAT`, no clasifica todavía los ataques ni Desafío, y no modifica cartas,
duraciones, redirecciones ni APIs públicas. Esos cambios son exclusivamente
P4 y P5.
