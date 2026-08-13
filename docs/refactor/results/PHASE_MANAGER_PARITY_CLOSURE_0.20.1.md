# Cierre de paridad de `PhaseManager` — 0.20.1

## Identificación y veredicto

- Fecha UTC: **2026-08-13**.
- Rama: **`work`**.
- SHA inicial: **`0e2572f942423be7d1d0045341c5352d91e3be36`**.
- SHA final: no se consigna dentro del propio commit para no afirmar una
  autorreferencia imposible; sólo existe después de confirmar este documento.
- Veredicto: **GO DEFINITIVO**. Toda la evidencia local exigida terminó verde.

## Motivo, alcance y cambios

El cierre verifica que la extracción conservadora de coordinación a
`PhaseManager` mantiene el comportamiento observable del cuerpo anterior,
incluidos estado persistible, eventos y acciones legales. También vuelve a
validar de forma explícita compatibilidad persistente, replay histórico,
almacenes CAS, calidad y artefacto de release.

No se añadió ni modificó código de producto o de pruebas durante este cierre.
Las **26 pruebas diferenciales ya añadidas antes del SHA inicial** están en
`tests/test_phase_manager_parity.py`. En esta tarea sólo se añadió este archivo:

```text
docs/refactor/results/PHASE_MANAGER_PARITY_CLOSURE_0.20.1.md
```

`src/card_duel_engine` **no cambió**. Su resumen SHA-256 determinista antes de
las validaciones fue
`0b779e387bb332119351b4663b47970ae9f7a4c661af5ae0454d164bbe7b97c9`;
la revisión final vuelve a compararlo con ese valor.

## Escenarios diferenciales exactos

La suite específica ejecutó los siguientes escenarios, sin extrapolar casos:

1. Transición normal desde `DRAW`, `EFFECTS` y `DISCARD`, en `CURRENT` y
   `LEGACY_019`.
2. Supresión simple `NEXT_OCCURRENCE`.
3. Rechazo de jugador no activo.
4. Rechazo con prioridad incompleta.
5. Ausencia de estado independiente en `PhaseManager`.
6. Dos supresiones `NEXT_OCCURRENCE` compatibles apiladas.
7. Supresión continua coexistiendo con una almacenada.
8. `END_OF_TURN`: cleanup, rotación y robo.
9. Rotación de tres jugadores `A → B → C → A`.
10. Entrada a robo con mazo y descarte vacíos.
11. Reciclaje determinista del descarte.
12. Cleanup de un modificador realmente expirable.
13. `BLOCKED` al suprimir todas las fases y guarda estricta `>`.
14. Rechazo `FINISHED` en `advance`, `finish` y `enter`.
15. Rechazo de combate pendiente sin mutación.
16. Rechazo de stack no vacío sin mutación.
17. Fronteras de prioridad abierta y cerrada.
18. Igualdad de acciones legales ordenadas antes y después.
19. Supresión legacy de `DRAW` al cambiar el turno.

En todos los casos diferenciales aplicables se compararon el estado persistible
completo (incluido el log ordenado de eventos) y las vistas legales ordenadas.

## Identificación de pruebas persistentes y legacy

Los nombres y rutas actuales se identificaron y ejecutaron así:

| Área solicitada | Ruta y nombre actual |
|---|---|
| Replay 0.19 | `tests/test_replay_legacy_019.py::Legacy019ReplayTests` |
| Replay histórico 0.20 | `tests/test_replay_legacy_020_profile.py::Legacy020AbilitySourceProfileReplayTests` |
| Snapshot y replay actuales | `tests/test_persistence_v090.py::PersistenceV090Tests` |
| Migraciones snapshot/replay v1→v2 | `tests/test_hardening_v0100.py::HardeningV0100Tests::test_snapshot_and_replay_schema_one_migrate_to_schema_two` |
| Migración de manifest v1 | `tests/test_hardening_v0100.py::HardeningV0100Tests::test_manifest_schema_one_migrates_with_safe_defaults` |
| `InMemoryMatchStore` | contratos en `tests/test_service_v0110.py`, `tests/test_authenticated_application_r06.py`, `tests/test_expected_version_contract.py` y `tests/test_hardening_v0100.py` |
| `SQLiteMatchStore` | contratos en `tests/test_service_v0110.py`, `tests/test_authenticated_application_r06.py`, `tests/test_expected_version_contract.py` y `tests/test_hardening_v0100.py` |
| CAS concurrente | `tests/test_hardening_v0100.py::HardeningV0100Tests::test_sqlite_store_allows_only_one_concurrent_compare_and_swap` y las baterías comunes de `tests/test_authenticated_application_r06.py` |

## Comandos ejecutados, orden, cantidades y códigos

No hubo intentos fallidos. Los comandos de validación se ejecutaron en el orden
solicitado; todos devolvieron código **0**.

| Orden | Comando literal | Código | Resultado observado |
|---:|---|---:|---|
| 1 | `uv sync --locked --extra dev` | 0 | 16 paquetes resueltos; entorno dev sincronizado desde lock. |
| 2 | `uv run pytest -q tests/test_phase_manager_parity.py` | 0 | **26 passed** en 0.37 s. |
| 3 | `uv run python -m unittest discover -s tests -v` | 0 | **396 tests**, `OK`, 1 omitida, en 74.734 s. |
| 4 | `uv run pytest -q` | 0 | **458 passed**, 711 subtests, en 70.79 s. |
| 5 | `uv run pytest -q tests/test_persistence_v090.py tests/test_hardening_v0100.py tests/test_service_v0110.py tests/test_authenticated_application_r06.py tests/test_expected_version_contract.py` | 0 | **82 passed**, 241 subtests, en 11.46 s. |
| 6 | `uv run pytest -q tests/test_replay_legacy_019.py tests/test_replay_legacy_020_profile.py` | 0 | **16 passed**, 99 subtests, en 6.03 s. |
| 7 | `uv run python -m mypy` | 0 | Sin incidencias en **39 archivos fuente**. |
| 8 | `uv run python -m compileall -q src tests scripts` | 0 | Sin salida; compilación correcta. |
| 9 | `uv run python scripts/verify_release.py --profile runtime` | 0 | `OK: perfil runtime completado`. |
| 10 | `uv run python scripts/verify_release.py --profile full --json dist/release-verification.json` | 0 | `status=ok`; evidencia efímera creada. |
| 11 | `uv run python scripts/verify_reproducible_wheel.py` | 0 | Dos builds idénticos y auditoría correcta. |
| 12 | `sha256sum 'Fantasy Tokens.pdf' 'Fantasy Tokens Edicion Mitica.pdf'` | 0 | Ambos hashes calculados correctamente. |
| 13 | `uv run pytest -q tests/test_release_metadata.py tests/test_release_compliance.py tests/test_release_scripts.py` | 0 | **61 passed**, 47 subtests, en 53.23 s, después de añadir este documento. |

Las cantidades pedidas quedan, por tanto: específicas **26**; legacy **16**
(más 99 subtests); persistencia/almacenes/CAS **82** (más 241 subtests);
`unittest` **396**; `pytest` integral **458** (más 711 subtests). Las suites
específicas se vuelven a incluir en las integrales; estas cifras no deben
sumarse como si fueran casos únicos.

## Release, cobertura y matriz de Python

El perfil **runtime** completó sus etapas no empaquetadoras. El perfil **full**
terminó con `status=ok` y ejecutó exactamente ocho etapas:
`metadata`, `lockfile`, `security`, `quality`, `rules-sources`, `simulations`,
`persistence` y `package`.

La etapa de calidad confirmó mypy, compileall y **89.0 % de cobertura**, por
encima del umbral de 88 %. Simulaciones registró 300 simulaciones, 54.000
comandos y 84.000 eventos; persistencia registró 30 roundtrips. La instalación
del wheel fue verde en la matriz **Python 3.11, 3.12 y 3.13**.

`dist/release-verification.json`, `.coverage`, wheels, caches y `.pyc` son
evidencia efímera ignorada y **no se versionan**.

## Wheel reproducible y fuentes normativas

El wheel `card_duel_engine-0.20.1-py3-none-any.whl` se construyó dos veces desde
un worktree separado del SHA inicial; ambos archivos fueron binariamente
idénticos. La auditoría confirmó 43 archivos, `RECORD` íntegro, etiqueta
`py3-none-any`, ausencia de dependencias runtime y árbol fuente limpio.

- SHA-256 del wheel reproducible:
  **`786751ea9642fc74c663188f32371f99a0bd97522fdc28d4c61822ae1ffa8134`**.
- `Fantasy Tokens.pdf`:
  **`1c51dabe2023626ad532368e2567d2084c47ec137c7a738bd8c0e0b707f86b21`**.
- `Fantasy Tokens Edicion Mitica.pdf`:
  **`61243b30d219dd12d8897a206ed664d95a5e3c38b6670a818933f6d90904af36`**.

## Fallos, omisiones y límites

- Intentos fallidos: **ninguno**.
- Comprobaciones exigidas no ejecutadas: **ninguna** dentro del alcance local.
- `git diff --check` terminó con código 0 y sin salida; el resumen SHA-256 final
  de `src/card_duel_engine` volvió a ser exactamente
  `0b779e387bb332119351b4663b47970ae9f7a4c661af5ae0454d164bbe7b97c9`.
- No se publicaron paquetes, no se creó tag, no se fusionó la rama y no se
  esperaron trabajos remotos de CI; son acciones externas fuera del alcance de
  esta verificación local y no se presentan como evidencia.
- El wheel acredita el código del SHA inicial. Este documento no entra en el
  paquete y su commit posterior no cambia los bytes del código de producto.

## Veredicto final

**GO DEFINITIVO.** Las pruebas específicas, integrales, persistentes y legacy,
el tipado, la compilación, ambos perfiles de release, la matriz Python, los
hashes normativos y la reproducibilidad del wheel son verdes. No existe un
punto de fallo que obligue a emitir `NO-GO`.
