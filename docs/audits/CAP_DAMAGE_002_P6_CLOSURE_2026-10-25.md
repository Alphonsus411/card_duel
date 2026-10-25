# CAP-DAMAGE-002 P6 — cierre documental y compatibilidad

**Fecha:** 2026-10-25
**Estado:** incremento `COMBAT` cerrado; capability global `PARTIAL`

## Compatibilidad emitida y leída

| Artefacto | Versión emitida | Compatibilidad relevante |
| --- | --- | --- |
| Snapshot | v5 | Migra snapshots v4 al perfil `LEGACY_UNTYPED` y a una tupla vacía de reservas tipadas. Las rutas históricas anteriores conservan sus migraciones encadenadas y sus huellas compatibles. |
| Replay | v4 | Migra replay v3 y verifica la huella heredada sin los campos v5 cuando corresponde. Las rutas históricas anteriores conservan sus comprobaciones de digest. |

Los esquemas futuros, causas desconocidas, payloads incompletos y mezclas ambiguas
entre v4/v5 fallan cerrados. Una reserva escalar histórica nunca se convierte
automáticamente en `COMBAT`.

## Comportamiento acreditado

- `DamageCause` está cerrado y expone únicamente `COMBAT`.
- Combate ordinario y Desafío cruzan las mismas puertas causales para daño y
  Heridas.
- Las rutas no pertenecientes a combate no consumen reservas `COMBAT`.
- El saldo se consume sólo por la cantidad prevenida; el remanente se aplica
  una vez y el rollback público restaura saldo, daño/heridas y eventos.
- Snapshot restaurado y ejecución directa tienen paridad para combate ordinario
  y Desafío. Los replays históricos mantienen su cobertura de compatibilidad.

## Límite intencional de replay positivo

No hay aún un comando ni efecto autorizado que cree una reserva tipada. Por
ello, un replay no puede reconstruir una reserva `COMBAT` positiva sin añadir
un productor nuevo o una mutación no registrada. Esta entrega no añade ninguno:
la paridad positiva de replay queda para la fase que autorice ese productor.

## Exclusiones que permanecen abiertas

- prevención ilimitada o renovable;
- fuente, controlador, procedencia, objetivo o selector tipados;
- duraciones y expiraciones nuevas;
- causas distintas de `COMBAT`;
- redirección, sustitución, prioridad u orden de reemplazos;
- cartas, corpus y APIs públicas nuevos.

Por esas exclusiones, `CAP-DAMAGE-002` permanece en `PARTIAL` y su gate sigue
`READY`: el incremento fundacional se ha cerrado, pero la capability amplia no
se promueve a `SUPPORTED`.

## Trazabilidad

- Contrato: `CAP_DAMAGE_002_P0_COMBAT_CAUSE_ADR_2026-10-25.md`.
- Inventario y dominio: P1 y P2.
- Persistencia: `CAP_DAMAGE_002_P3_VERSIONED_PERSISTENCE_2026-10-25.md`.
- Motor: `CAP_DAMAGE_002_P4_COMBAT_ENGINE_2026-10-25.md`.
- Verificación: `CAP_DAMAGE_002_P5_VERIFICATION_2026-10-25.md`.
- Matrices actualizadas: `ENGINE_CAPABILITY_MATRIX.csv`,
  `ENGINE_CAPABILITY_DEPENDENCIES.md` y `UNIVERSAL_MECHANICS_MATRIX.md`.
