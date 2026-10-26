# CAP-EFFECT-001 / E4 — Compatibilidad de persistencia y replay

Fecha: 2026-10-26
Estado: completada

## Objetivo

Verificar que el vocabulario cerrado de primitivas de efecto se conserva por los
canales persistidos actuales, sin ampliar `EffectKind`, sin introducir valores por
defecto semánticos y sin cambiar los esquemas de snapshot o replay.

## Cobertura ejecutable

`tests/test_effect_persistence_e4.py` comprueba que:

1. Las 23 variantes de `EffectKind` admitidas por el contrato E3 hacen
   `encode_value`/`decode_value` sin perder su definición.
2. Un snapshot conserva el lote completo de efectos tanto en una definición del
   catálogo como en un `StackItem`, y mantiene su `state_digest`.
3. Un replay generado desde una partida normal vuelve a ejecutar una carta con
   `DEAL_WOUNDS` y termina con el mismo digest, sin mutaciones fuera del
   historial.
4. La compatibilidad histórica de `EffectDefinition` no inventa destinos ni
   política de agotamiento para `REVEAL_UNTIL`: un documento antiguo sin esos
   campos es rechazado al reconstruir una revelación.

## Decisiones y límites

- No se incrementa `SNAPSHOT_SCHEMA_VERSION` ni `REPLAY_SCHEMA_VERSION`.
- Se conserva la compatibilidad existente para los dos campos añadidos a
  `EffectDefinition`, pero la validación del modelo sigue siendo la autoridad
  semántica: sólo los efectos que no los requieren pueden usar sus valores por
  defecto.
- Esta fase verifica transporte y restauración. No cambia la resolución de
  primitivas, las políticas de secreto ni las continuaciones de búsqueda; esos
  trabajos permanecen delimitados por E0–E2 para fases posteriores.
