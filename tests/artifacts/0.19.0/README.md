# Corpus de replays v2 de 0.19.0

Este corpus fue generado con el motor público del commit
`3f21a1e2e9ba3c05b7bede3c5a7dc375d71ae39d`, cuyo `pyproject.toml` declara
`version = "0.19.0"`. No se editó ningún documento replay a mano.

## Reproducción

Desde la raíz del checkout actual (el script crea un directorio temporal único
`card-duel-019-<sufijo>/` y ubica dentro su worktree detached en la subruta
`worktree/`):

```console
python tests/artifacts/0.19.0/generate_legacy_019_replays.py --output tests/artifacts/0.19.0
```

La copia exacta del script está en `generate_legacy_019_replays.py`. Solo crea
estados mediante `GameEngine.new_match`, `GameEngine.execute` y comandos públicos,
y serializa mediante `dump_replay`. El proceso ejecuta Python con `-I` y antepone
solo el `src` del worktree histórico, por lo que no puede importar el motor del
checkout actual. Al terminar ejecuta `git worktree remove --force` y
`git worktree prune`. El bloque `finally` sólo intenta retirar el worktree si
esta ejecución llegó a registrarlo; después poda el registro y el directorio
temporal exclusivo se elimina incluso si falla el alta o el worker.

## Observables finales

| fixture | digest | fase | turno | historial / eventos | evento final | contadores | SHA-256 del archivo |
|---|---|---|---:|---:|---|---:|---|
| `drainage-outside-effects` | `f216145cb50c9cd8648debce523581f6f537d801558ee6e8a05497a85fa06110` | `COMBAT` | 1 | 10 / 21 | `DRAINAGE_USED` | 5 / 1 | `4a390588f66e0e747896f09f5ee580836417c318be477345f548f7dfe80573a9` |
| `challenge-combat` | `044970d424cc449607164dc3df955df3f04d4e8ebdef28670f7348c09edddd31` | `COMBAT` | 3 | 57 / 91 | `CHALLENGE_DECLARED` | 5 / 4 | `299c8ee6514d1a244351ec559cafb446cbebf709f4a08acc4232809bc0bb9efc` |
| `attackers-declared` | `1f2f8124a44f4d599587be89b564fea84d8d53b8513dab3e01bbdcb679be117a` | `COMBAT` | 3 | 54 / 86 | `ATTACKERS_DECLARED` | 5 / 3 | `37011f3ff75d493479793f6e4680c2e87d53c23638b86766e63abe01f88aa7be` |
| `challenge-non-realms` | `ec7f638d0c8897d0549e639731bf13634513a78f3ed1345897fc8895e41f9b6e` | `COMBAT` | 3 | 57 / 91 | `CHALLENGE_DECLARED` | 5 / 4 | `402bf3c96281ff9241da30783337e150ed623fba2c37c02e1852cabbc0bc4a14` |
| `lord-ability-outside-effects` | `b78a99c291fe95ecc44f5d5f16bbdda02e129088093ff65788ae19f3cc4f5490` | `COMBAT` | 3 | 54 / 87 | `STACK_ITEM_RESOLVED` | 5 / 4 | `91d90bc93c711ff0c1f966c26fb0f1f3bc5b523dbff24bb00100867b2d44a229` |

Los contadores son `_next_instance / _next_stack_item`. El SHA-256 es el del
archivo completo; cada sobre contiene además el checksum canónico de su `body`.

En Drenaje, A termina con 6 Heridas, 8 Pasos y
`drainage_used_turn_serial == 1`; B queda con 0/0. Las cuatro cartas permanecen
en las manos y el evento final es `DRAINAGE_USED {steps_gained: 3,
wounds_paid: 6}`.

En los tres casos de combate/desafío A/B terminan con Heridas 0/0 y Pasos 10/5. Sus cartas
principales están respectivamente en `BATTLEFIELD` (`card-000001` y
`card-000003`), los rellenos en `HAND`, y el resto de zonas está vacío. El
historial termina en `ATTACKERS_DECLARED {attackers: [card-000001], defender:
B}` o `CHALLENGE_DECLARED {challenged_id: card-000003, defender: B}`. Los
payloads históricos no contienen `turn_serial`. El Señor no Reinos usa
`LordDomain.ABYSS`: 0.19.0 sí lo admite legalmente tras transformarlo en criatura.

En `lord-ability-outside-effects`, el Señor sintético de Reinos tiene
`combat-march`, una habilidad activada con `allowed_phases == {Phase.COMBAT}`.
Se activa legalmente en `COMBAT`, la pila se resuelve por pases de prioridad y
`STEPS_GAINED {amount: 2}` deja a A con Heridas/Pasos 0/12 y a B con 0/5. El
último evento es `STACK_ITEM_RESOLVED {remaining: 0}`; las cartas principales
quedan en `BATTLEFIELD`, los rellenos en `HAND` y las demás zonas vacías.

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
las rutas de comandos de estos cinco fixtures. Las restantes diferencias del
diff histórico (transacciones, objetivos divinos y ventanas de habilidades de
Señor) no alteran estas rutas.
