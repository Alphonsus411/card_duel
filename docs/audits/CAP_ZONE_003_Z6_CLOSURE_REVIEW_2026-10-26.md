# CAP-ZONE-003 — Z6: revisión de cierre

**Fecha:** 2026-10-26
**Estado del incremento Z0–Z6:** cerrado
**Estado de la capability:** `CAP-ZONE-003` permanece `PARTIAL / READY`.

## Evidencia consolidada

| Tramo | Evidencia | Resultado acreditado |
| --- | --- | --- |
| Z0–Z2 | `CAP_ZONE_003_Z0_UNIFORM_TRANSITION_CONTRACT_2026-10-25.md`, `CAP_ZONE_003_Z1_TRANSITION_INVENTORY_2026-10-25.md`, `CAP_ZONE_003_Z2_CAUSAL_TRANSITION_MODEL_2026-10-26.md` | contrato causal interno, inventario y límites explícitos antes de cambiar el motor |
| Z3 | schema 6, `ZoneTransition`, `TransitionPriorState`, codec y migración `snapshot_5_to_6` | la traza es persistible; los documentos previos a schema 6 se restauran sin inventar causalidad y quedan marcados con prefijo incompleto |
| Z4 | `ZoneManager._move_card`, invariantes de `GameEngine` y bloqueo de replay | cada movimiento efectivo de la puerta anexa un registro ordenado, atómico e interno; un prefijo histórico incompleto no se exporta a replay |
| Z5 | `test_zone_transition_verification_z5.py` y `CAP_ZONE_003_Z5_VERIFICATION_MATRIX_2026-10-26.md` | rollback, snapshot/replay para partidas trazables y ausencia de fuga en observaciones públicas |

## Decisión de gate

Se cierra el incremento, no la capability global. La implementación satisface el
contrato mínimo de registro causal y preserva la compatibilidad de forma cerrada,
pero todavía no acredita las condiciones necesarias para declarar
`CAP-ZONE-003` como `SUPPORTED`:

1. `batch_id` es determinista por transición (`zone-batch-<sequence>`), pero no
   hay una autoridad que abra y propague un lote semántico a varios movimientos
   de una misma operación compuesta.
2. La única audiencia admitida es `DecisionAudience.INTERNAL`. No existe una
   proyección causal por jugador ni una política de visibilidad para ese registro.
3. Los snapshots anteriores a schema 6 no poseen prefijo causal. La migración no
   fabrica historia y `dump_replay` rechaza esos estados de forma fail-closed.

Por tanto no se modifican las puertas de `CAP-ZONE-004`, `CAP-ZONE-005` ni
`CAP-ATTACH-001`, ni se adelantan LKI (`CAP-ZONE-006`), triggers generales,
reemplazos generalizados o cambios de API pública.

## Compatibilidad y salida

El schema actual es 6. Las partidas nuevas producen un prefijo causal completo;
las anteriores mantienen restauración compatible, pero no se presentan como
replays causalmente completos. No se añadieron eventos públicos, DTOs ni campos
de observación. El siguiente incremento deberá seleccionar otra capability lista
del roadmap o especificar de forma independiente los huecos de lote y audiencia
anteriores.
