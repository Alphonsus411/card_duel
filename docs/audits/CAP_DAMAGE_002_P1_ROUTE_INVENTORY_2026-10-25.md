# P1 — Inventario de rutas y caracterización actual de `CAP-DAMAGE-002`

**Fecha:** 2026-10-25

**Estado:** cerrado; no modifica el contrato ni el modelo de P0

## Objetivo y método

P1 localiza todas las entradas y salidas que afectan a las reservas escalares
actuales. La caracterización fija el comportamiento observado antes de
introducir `DamageCause` en P2. No concede semántica causal a ningún recorrido
existente.

La evidencia ejecutable nueva está en
`tests/test_damage_prevention_characterization.py`.

## Inventario de estado y productores

| Superficie | Símbolo actual | Observación P1 |
| --- | --- | --- |
| Reserva de permanente | `CardInstance.damage_prevention` en `domain/models.py` | Entero escalar, inicializado a cero; no guarda causa, fuente ni duración propia. |
| Reserva de jugador | `PlayerState.wound_prevention` en `domain/models.py` | Entero escalar, inicializado a cero; no guarda causa, fuente ni duración propia. |
| Productor de heridas | `EffectManager._prevent_wounds` | `PREVENT_WOUNDS` suma el importe y emite `WOUND_PREVENTION_ADDED`. |
| Productor de daño | `EffectManager._prevent_damage` | `PREVENT_DAMAGE` suma el importe y emite `DAMAGE_PREVENTION_ADDED`. |

Los productores no etiquetan la reserva y no se reclasifican en P1.

## Inventario de consumidores y rutas de entrada

| Familia | Ruta hasta el consumidor | Consumidor | Nota de alcance |
| --- | --- | --- | --- |
| Daño de efecto a permanente | `EffectManager._deal_damage` y `_deal_allocated_harm` → contexto | `GameEngine._deal_damage` | Puede provenir de efectos/abilities; no es combate por construcción. |
| Heridas de efecto a jugador | `EffectManager._deal_wounds` y `_deal_allocated_harm` → contexto | `GameEngine._deal_wounds` | Puede provenir de efectos/abilities; no es combate por construcción. |
| API interna de heridas | `GameEngine.add_wounds` | `GameEngine._deal_wounds` | Entrada administrativa/interna que tampoco expresa causa. |
| Combate sin bloqueadores o remanente | `CombatManager._resolve_combat` | `GameEngine._deal_wounds` | Daño de combate a jugador. |
| Combate con bloqueadores | `CombatManager._resolve_combat` | `GameEngine._deal_damage` y, si queda remanente, `_deal_wounds` | Daño de combate a permanentes y jugador. |
| Desafío | `CombatManager._resolve_combat` con `CombatState.is_challenge` | `GameEngine._deal_damage` | Combate entre desafiante y desafiada; hoy comparte consumidor escalar, sin marcador de causa. |

Los consumidores calculan `min(reserva, importe)`, reducen la reserva y aplican
el remanente. Emiten `WOUNDS_PREVENTED`/`DAMAGE_PREVENTED` sólo si previenen,
y `WOUNDS_ADDED`/`DAMAGE_DEALT` sólo si aplican remanente. Ninguno recibe hoy
un parámetro causal.

## Limpieza, persistencia y proyección

| Superficie | Ruta actual | Consecuencia P1 |
| --- | --- | --- |
| Fin de turno | `GameEngine._cleanup_end_of_turn` | Pone ambas reservas a cero. |
| Salida del campo | `ZoneManager._move_card` | Al abandonar `BATTLEFIELD`, pone `damage_prevention` a cero junto con el daño de la carta. |
| Snapshot/digest | `persistence.codec.encode_value` → `snapshot._canonical_encoded_state` → `state_digest` | Los campos de dataclass se codifican completos, por lo que una reserva escalar parcial participa en snapshot y digest. |
| Restore | `snapshot.load_snapshot` → `codec.decode_value` | v4 exige los campos actuales de `CardInstance` y `PlayerState`; no existe perfil causal. |
| Replay | `replay.dump_replay` / `replay_from_log` | El replay persiste catálogo, comandos e historial, y vuelve a ejecutar rutas; una mutación manual de reserva no es una entrada de replay. |
| Storage / servicio / proyección pública | Sin referencias directas adicionales | No se encontró otra serialización o DTO público de estas reservas fuera del estado persistido. |

## Caracterización añadida

| Prueba | Hecho congelado |
| --- | --- |
| `test_effects_add_the_current_scalar_reserves` | Los dos efectos de prevención cargan contadores escalares y emiten sus eventos actuales. |
| `test_scalar_reserves_partially_consume_and_roundtrip_snapshot` | Un consumo parcial conserva el saldo y el snapshot v4/restauración conserva el digest. |
| `test_normal_combat_and_challenge_share_current_scalar_damage_path` | Combate normal y Desafío consumen exactamente las mismas reservas escalares de daño, sin causa. |
| `test_cleanup_and_battlefield_exit_clear_current_scalar_reserves` | Limpieza de turno y salida de tablero borran las reservas actuales. |

## Resultado y gate hacia P2

P1 queda cerrado: no hay una ruta de combate o Desafío sin identificar, y las
rutas no-combate están separadas como pruebas negativas futuras. P2 podrá
introducir el tipo cerrado y la representación mínima aprobada en P0, pero
debe conservar como perfil heredado el comportamiento aquí caracterizado.

P1 no autoriza cambios de schema, migraciones, replay, efectos existentes,
cartas ni una clasificación distinta de `CAP-DAMAGE-002`.
