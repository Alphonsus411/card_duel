# Corpus de replays v2 de 0.19.0

Este corpus fue generado con el motor público del commit
`3f21a1e2e9ba3c05b7bede3c5a7dc375d71ae39d`, cuyo `pyproject.toml` declara
`version = "0.19.0"`. No se editó ningún documento replay a mano.

## Reproducción

Desde un worktree de ese commit:

```console
uv run python scripts/generate_legacy_019_replays.py
```

La copia exacta del script está en `generate_legacy_019_replays.py`. Solo crea
estados mediante `GameEngine.new_match`, `GameEngine.execute` y comandos públicos,
y serializa mediante `dump_replay`.

## Observables finales

| fixture | digest | fase | turno | comandos / eventos | `_next_instance` / `_next_stack_item` |
|---|---|---|---:|---:|---:|
| `drainage-outside-effects` | `f216145cb50c9cd8648debce523581f6f537d801558ee6e8a05497a85fa06110` | `COMBAT` | 1 | 10 / 21 | 5 / 1 |
| `challenge-combat` | `044970d424cc449607164dc3df955df3f04d4e8ebdef28670f7348c09edddd31` | `COMBAT` | 3 | 57 / 91 | 5 / 4 |
| `attackers-declared` | `1f2f8124a44f4d599587be89b564fea84d8d53b8513dab3e01bbdcb679be117a` | `COMBAT` | 3 | 54 / 86 | 5 / 3 |
| `challenge-non-realms` | `ec7f638d0c8897d0549e639731bf13634513a78f3ed1345897fc8895e41f9b6e` | `COMBAT` | 3 | 57 / 91 | 5 / 4 |

En Drenaje, A termina con 6 Heridas, 8 Pasos y
`drainage_used_turn_serial == 1`; B queda con 0/0. Las cuatro cartas permanecen
en las manos y el evento final es `DRAINAGE_USED {steps_gained: 3,
wounds_paid: 6}`.

En los otros tres casos A/B terminan con Heridas 0/0 y Pasos 10/5. Sus cartas
principales están respectivamente en `BATTLEFIELD` (`card-000001` y
`card-000003`), los rellenos en `HAND`, y el resto de zonas está vacío. El
historial termina en `ATTACKERS_DECLARED {attackers: [card-000001], defender:
B}` o `CHALLENGE_DECLARED {challenged_id: card-000003, defender: B}`. Los
payloads históricos no contienen `turn_serial`. El Señor no Reinos usa
`LordDomain.ABYSS`: 0.19.0 sí lo admite legalmente tras transformarlo en criatura.

## Inventario de diferencias relevantes frente al código actual

La comparación directa de los emisores de 0.19.0 con los actuales encontró las
siguientes diferencias necesarias para este corpus:

* Drenaje validaba jugador activo/prioridad, pero no restringía la fase; ahora
  las partidas vivas exigen `Phase.EFFECTS`.
* Desafío se declaraba en `Phase.COMBAT`, aceptaba cualquier Señor convertido en
  criatura y no registraba `turn_serial`; actualmente se declara en `EFFECTS`,
  concede elegibilidad general a Reinos transformado y exige `CAN_CHALLENGE`
  para otros dominios, además de usar el serial para impedir
  repeticiones/conflictos.
* `ATTACKERS_DECLARED` tampoco incluía `turn_serial` en 0.19.0.

No hay otra diferencia de emisor o payload necesaria para reproducir exactamente
las rutas de comandos de estos cuatro fixtures. Las restantes diferencias del
diff histórico (transacciones, objetivos divinos y ventanas de habilidades de
Señor) no alteran estas rutas.
