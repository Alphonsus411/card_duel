# CAP-ZONE-003 — Z5: matriz de verificación

**Fecha:** 2026-10-26
**Estado de la fase:** completada
**Capability:** `CAP-ZONE-003` permanece `PARTIAL / READY`.

## Matriz acreditada

| Riesgo | Evidencia de Z5 | Resultado exigido |
| --- | --- | --- |
| Registro parcial tras fallo público | `test_public_command_rollback_restores_causal_history_atomically` | el rollback repone carta, zonas y `zone_transition_history` exactamente al snapshot previo |
| Orden e identidad en snapshot | `test_snapshot_and_replay_preserve_causal_order_and_identity` | snapshot conserva cada entrada causal y su secuencia |
| Determinismo de replay | `test_snapshot_and_replay_preserve_causal_order_and_identity` | replay desde un match nuevo reconstruye la misma secuencia, lotes e identidades |
| Fuga por observación o DTO público | `test_internal_transition_history_is_absent_from_player_projection` | `PlayerObservation` y `PublicPlayerObservation` no contienen historial, lote ni estado previo |
| Artefacto histórico incompleto | pruebas de `test_pending_decision_w13.py` y `test_hardening_v0100.py` | migración marca prefijo causal desconocido y `dump_replay` rechaza el documento de forma cerrada |

## Límites verificados

Los registros siguen siendo internos y no generan eventos. El lote unitario es
determinista (`zone-batch-<sequence>`) y únicamente acredita la transición
individual; no presenta una agrupación semántica de efectos compuestos. No se
han añadido LKI, triggers generales, proyección por audiencia ni inferencia de
historial para snapshots antiguos.

## Salida de Z5

La puerta uniforme acredita atomicidad, persistencia y no exposición para el
contrato mínimo de Z2–Z4. La revisión de cierre Z6 deberá evaluar compatibilidad,
documentación de límites y el gate de la capability, sin promover dependientes
por anticipado.
