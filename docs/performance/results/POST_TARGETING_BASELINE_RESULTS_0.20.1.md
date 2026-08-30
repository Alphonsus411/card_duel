# Resultados del baseline posterior a targeting 0.20.1

## Veredicto

**GO** para registrar el baseline. No se hizo ningún cambio productivo; el estado
canónico no mutó, los fingerprints fueron estables, se conservaron `CURRENT` y
`LEGACY_019` y los gates ejecutados quedaron verdes. La candidata indicada al
final queda sólo documentada y **no está implementada**.

## Tiempo, memoria y estado (CURRENT, límite 128)

| Escenario | Mediana | Media | p95 | σ muestral | Pico `tracemalloc` | Acciones |
|---|---:|---:|---:|---:|---:|---:|
| MEDIUM | 6,510 ms | 6,671 ms | 7,290 ms | 0,290 ms | 273.128 B | 823 |
| STRESS_CONTROLLED | 7,234 ms | 7,515 ms | 10,457 ms | 0,831 ms | 272.896 B | 831 |

| Escenario | Fingerprint resultado | Estado antes/después | Igualdad canónica |
|---|---|---|---|
| MEDIUM | `0e94cbf2783b9025832147d94d55cceff9da2b3815d05209517e08daaad3efc0` | `33468e0e7c517cb28932e3f9d38f0ffbc4d6d2660494c9be78cc7fa327599cd0` | sí |
| STRESS_CONTROLLED | `819f98ef64451c8177367e0be2ecab97dd33494b0e5417781c2f06011212e4ee` | `f04b31eb1b7b1a13020dfc3327236360e663a0c60ac38ec6610406625c0bcfed` | sí |

En las 15 muestras de cada caso el hash anterior coincidió con el posterior. Los
casos equivalentes de `LEGACY_019` conservaron estos mismos conteos y hashes en
el fixture controlado, sin mezclar ambos perfiles como si fueran uno solo.

## Comparación histórica solicitada

Porcentajes sobre medianas sin profiler; negativo significa menor duración.

| Escenario | Antes de caché | Baseline optimizado registrado | Post-targeting actual | vs. antes | vs. optimizado registrado |
|---|---:|---:|---:|---:|---:|
| MEDIUM | 13,547 ms | 7,755 ms | 6,510 ms | **-51,95 %** | -16,06 % |
| STRESS_CONTROLLED | 26,848 ms | 8,205 ms | 7,234 ms | **-73,05 %** | -11,83 % |

La conclusión sólida frente al valor anterior a la caché es que la mejora se
mantiene y los fingerprints coinciden con los registrados. La diferencia frente
al baseline optimizado anterior **no debe presentarse como una aceleración nueva**:
aquél alternó dos worktrees, fijó CPU 0 y tomó 30 muestras; éste usa un solo SHA,
no fija afinidad y toma 15. También hay ruido KVM y outliers (en STRESS el p95
10,457 ms frente a mediana 7,234 ms). Es contexto histórico, no A/B directo.

En memoria, el pico actual es 273.128 B frente a 293.792 B históricos en MEDIUM
(-7,03 %) y 272.896 B frente a 294.464 B en STRESS (-7,32 %). La misma diferencia
de protocolo impide atribuir ese descenso a producto.

## Top 20 de `cProfile`

Una captura por escenario, `CURRENT`, límite 128, orden acumulado. `propio` y
`acum.` están en milisegundos; los acumulados se solapan y no se suman.

### MEDIUM

| # | Función | Llamadas | Propio | Acum. |
|---:|---|---:|---:|---:|
| 1 | `game.py:654(legal_actions)` | 1 | 0,015 | 15,431 |
| 2 | `actions.py:97(legal_actions)` | 1 | 0,181 | 15,416 |
| 3 | `game.py:777(_legal_plays)` | 1 | 1,462 | 9,922 |
| 4 | `game.py:868(_allocation_selections)` | 56 | 0,067 | 6,342 |
| 5 | `options.py:130(allocation_selections)` | 56 | 2,179 | 6,275 |
| 6 | `game.py:1204(_legal_ability_activations)` | 10 | 0,457 | 4,919 |
| 7 | `options.py:166(<genexpr>)` | 1.456 | 0,959 | 2,530 |
| 8 | `<string>:2(__init__)` | 944 | 1,444 | 1,571 |
| 9 | `list.extend` | 37 | 0,070 | 1,141 |
| 10 | `game.py:731(_card_cost_options)` | 9 | 0,016 | 1,073 |
| 11 | `options.py:57(card_cost_options)` | 9 | 0,069 | 1,057 |
| 12 | `game.py:1134(_card_can_be_targeted)` | 270 | 0,373 | 1,005 |
| 13 | `game.py:792(<genexpr>)` | 171 | 0,098 | 0,860 |
| 14 | `game.py:179(_option_resolve_x_cost)` | 42 | 0,027 | 0,736 |
| 15 | `options.py:175(positive_compositions)` | 1.504/640 | 0,721 | 0,721 |
| 16 | `game.py:724(_resolve_x_cost)` | 42 | 0,021 | 0,709 |
| 17 | `resolvers.py:49(resolve_x_cost)` | 42 | 0,085 | 0,688 |
| 18 | `dataclasses.py:1540(replace)` | 44 | 0,206 | 0,606 |
| 19 | `game.py:2041(_effective_keywords)` | 270 | 0,173 | 0,523 |
| 20 | `game.py:1994(_continuous_effects_for)` | 20 | 0,276 | 0,448 |

### STRESS_CONTROLLED

| # | Función | Llamadas | Propio | Acum. |
|---:|---|---:|---:|---:|
| 1 | `game.py:654(legal_actions)` | 1 | 0,007 | 19,424 |
| 2 | `actions.py:97(legal_actions)` | 1 | 0,248 | 19,417 |
| 3 | `game.py:777(_legal_plays)` | 1 | 1,791 | 13,019 |
| 4 | `game.py:868(_allocation_selections)` | 56 | 0,087 | 7,044 |
| 5 | `options.py:130(allocation_selections)` | 56 | 2,394 | 6,957 |
| 6 | `game.py:1204(_legal_ability_activations)` | 18 | 0,477 | 5,709 |
| 7 | `game.py:1134(_card_can_be_targeted)` | 510 | 0,756 | 2,742 |
| 8 | `options.py:166(<genexpr>)` | 1.392 | 0,769 | 2,684 |
| 9 | `game.py:792(<genexpr>)` | 315 | 0,172 | 2,380 |
| 10 | `<string>:2(__init__)` | 880 | 1,783 | 1,916 |
| 11 | `game.py:2041(_effective_keywords)` | 510 | 0,502 | 1,760 |
| 12 | `list.extend` | 45 | 0,080 | 1,543 |
| 13 | `game.py:1994(_continuous_effects_for)` | 36 | 1,000 | 1,476 |
| 14 | `game.py:731(_card_cost_options)` | 9 | 0,015 | 1,314 |
| 15 | `options.py:57(card_cost_options)` | 9 | 0,099 | 1,299 |
| 16 | `game.py:179(_option_resolve_x_cost)` | 42 | 0,035 | 0,881 |
| 17 | `game.py:724(_resolve_x_cost)` | 42 | 0,028 | 0,845 |
| 18 | `resolvers.py:49(resolve_x_cost)` | 42 | 0,111 | 0,817 |
| 19 | `dataclasses.py:1540(replace)` | 44 | 0,260 | 0,727 |
| 20 | `game.py:2167(_definition)` | 1.869 | 0,520 | 0,688 |

## Top 5 hotspots resumidos

Las primeras cinco filas acumuladas en ambos escenarios son: los dos wrappers
de `legal_actions`, `_legal_plays`, `_allocation_selections` y
`allocation_selections`. Los wrappers representan el total inclusivo, no trabajo
duplicado. El hotspot accionable dominante es `allocation_selections`: 6,275 ms
acumulados en MEDIUM y 6,957 ms en STRESS, con construcción de resultados,
generadores y composiciones bajo esa ruta.

La atribución exclusiva confirma el diagnóstico:

| Categoría | MEDIUM tiempo propio | STRESS tiempo propio |
|---|---:|---:|
| Combinatoria/materialización | **50,85 %** (6,153 ms) | **42,60 %** (6,661 ms) |
| Orquestación/costes | 32,31 % (3,910 ms) | 38,57 % (6,031 ms) |
| Targeting | 15,15 % (1,833 ms) | 15,50 % (2,423 ms) |
| Resolución `_definition` | **1,69 %** (0,204 ms) | **3,33 %** (0,520 ms) |

## Respuestas explícitas al diagnóstico

- **Hotspot dominante:** combinatoria/materialización, concretada en la ruta
  `allocation_selections`; es 50,85 % del tiempo propio perfilado en MEDIUM y
  42,60 % en STRESS.
- **Peso relativo de `_definition`:** ya no domina. Retiene 709 de 5.749 llamadas
  históricas (12,33 %) en MEDIUM y 1.869 de 19.005 (9,83 %) en STRESS, pero sólo
  pesa 1,69 % y 3,33 % del tiempo propio total respectivamente.
- **Combinatoria/materialización:** sí domina con atribución exclusiva; no es una
  inferencia obtenida sumando tiempos inclusivos.
- **`deepcopy`:** es secundario en MEDIUM (mediana 1,520 ms; 23,35 % de
  `legal_actions`) y material en STRESS (2,642 ms; 36,51 %), pero se midió fuera
  de `legal_actions` y no aparece en su top 20. Es relevante para operaciones que
  realmente copien estado, no explica este hotspot de enumeración.
- **Porcentaje del hotspot principal:** 50,85 % MEDIUM y 42,60 % STRESS; para el
  escenario de control más exigente se toma **42,60 %** como porcentaje principal.
- **Riesgo de intervenirlo:** alto. Los repartos combinan cantidad, mínimo/máximo,
  valor X, orden determinista y truncamiento; cambiar cuándo se materializan
  comandos puede cambiar contenido u orden observable.
- **Conveniencia:** sí conviene una investigación acotada, porque el perfil
  posterior trasladó claramente la dominancia a esa ruta. No conviene integrar
  nada sin benchmark A/B y paridad completa.

## Única candidata futura sustentada por el perfil

**Candidata única: reducir materializaciones intermedias dentro de
`allocation_selections`, conservando exactamente el algoritmo y el orden público
de los comandos.** El alcance se limita a `engine/options.py` y a pruebas y
benchmarks específicos de repartos; no incluye `deepcopy`, targeting, costes ni
otra ruta.

- **Beneficio esperado:** reducir el 42,60 % de tiempo propio atribuido a
  combinatoria/materialización en STRESS y sus asignaciones temporales, buscando
  una mejora observable de la consulta pública sin alterar sus opciones.
- **Riesgo semántico:** alto por orden, límites, mínimos/máximos, valor X,
  truncamiento temprano y representación exacta de cada allocation.
- **Criterio de aceptación:** mediana de STRESS `legal_actions`, límite 128,
  al menos 10 % menor en 30 rondas alternadas y CPU fijada; MEDIUM no puede
  empeorar más de 5 %; pico de memoria no puede crecer más de 5 %; conteo,
  serialización ordenada, fingerprints y estado deben coincidir exactamente en
  `CURRENT` y `LEGACY_019` para límites 8/32/128/512; toda la suite y gates de
  release deben quedar verdes. Cualquier incumplimiento implica retirar el
  prototipo y registrar **NO-GO**.

No se implementa esta candidata en el presente cambio y no se abren candidatas
alternativas equivalentes.

## Limitaciones y ruido

Además de no existir A/B simultáneo, no hubo afinidad fija ni control del host
KVM. Las muestras contienen outliers y `cProfile` sólo tiene una repetición por
escenario. El coste de `deepcopy` es aislado y no debe agregarse al de
`legal_actions`; `tracemalloc` no equivale a RSS. Por estas diferencias, sólo la
estabilidad funcional y la persistencia de la mejora histórica son conclusiones
directas; los descensos adicionales de tiempo y memoria son orientativos.

## Registro final de comandos y artefactos (2026-08-15 UTC)

Se repitió el cierre sobre `4b95c73e9258cdfc67a34cfd77920cfd744eb9c6` sin
modificar producto ni ejecutar la candidata. Resultados resumidos y códigos de
terminación:

| Comando exacto | Resultado | Código |
|---|---|---:|
| `uv sync --locked --extra dev` | sincronización bloqueada correcta | 0 |
| `uv run pytest -q` | 576 passed, 1 skipped, 711 subtests passed (94,32 s) | 0 |
| `uv run python -m unittest discover -s tests -v` | 396 tests, `OK` (90,845 s) | 0 |
| `uv run python -m mypy` | 40 archivos sin incidencias | 0 |
| `uv run python -m compileall -q src tests scripts benchmarks` | correcto, sin salida | 0 |
| `uv run python scripts/verify_release.py --profile runtime` | perfil runtime `OK` | 0 |
| `uv run python scripts/verify_release.py --profile full --json dist/release-verification.json` | perfil full correcto; JSON generado | 0 |
| `uv run python scripts/verify_reproducible_wheel.py` | 2 builds idénticos, 44 entradas, integridad RECORD correcta | 0 |
| `uv run python scripts/verify_rules_sources.py` | 2 fuentes PDF `OK` | 0 |

El wheel reproducible fue
`card_duel_engine-0.20.1-py3-none-any.whl`, SHA-256
`350addc4694d9bb1e03cc4c5d037290eb2bf90971889580cbb560e9748f7f024`.
La lista obtenida mediante `unzip -Z1` no contiene `benchmarks/` ni archivos PDF.

La comparación de `sha256sum` frente a `docs/RULES_SOURCES.json` fue exacta:

| Fuente | SHA-256 calculado y registrado |
|---|---|
| `Fantasy Tokens.pdf` | `1c51dabe2023626ad532368e2567d2084c47ec137c7a738bd8c0e0b707f86b21` |
| `Fantasy Tokens Edicion Mitica.pdf` | `61243b30d219dd12d8897a206ed664d95a5e3c38b6670a818933f6d90904af36` |

`git diff -- src/card_duel_engine` quedó vacío. La auditoría final del diff no
encontró cambios en reglas, comandos, `GameState`, snapshots/replay,
persistencia, `PhaseManager`, `ActionOptionResolver`, caché local, `deepcopy`,
PDF, `pyproject.toml`, `uv.lock` o workflows. Por tanto se conserva el veredicto
**GO para el baseline**, el hotspot sigue siendo combinatoria/materialización y
la única candidata sigue documentada, no implementada.
