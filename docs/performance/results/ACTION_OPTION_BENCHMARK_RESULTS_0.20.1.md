# Resultados del benchmark de opciones de acción 0.20.1

## Veredicto

**GO.** Todos los controles solicitados terminaron con código de salida 0, los
resultados fueron deterministas en contenido, el wheel fue reproducible y el
diff confirma explícitamente **0 cambios en `src/`**. Este benchmark es una
**línea base diagnóstica**, no un *performance gate*: no se han definido umbrales
de latencia o memoria cuyo incumplimiento bloquee una entrega.

## Identidad y alcance auditado

| Dato | Valor |
|---|---|
| SHA base de la entrega | `ace328dc796043eaa4bb7597dcf679632e91dcc2` |
| SHA benchmarkeado | `dd8a1fb99035a18f6cedbd048489ce8e158e0a13` |
| Rama de entrega | `benchmark/action-option-hotspots` |
| Perfil conservado | `full`: 5 repeticiones de calentamiento y 15 medidas por caso |
| JSON | `benchmarks/results/action_options_benchmark.json` |
| Archivo modificado | `benchmarks/results/action_options_benchmark.json` (regenerado por `full`) |
| Archivo añadido | `docs/performance/results/ACTION_OPTION_BENCHMARK_RESULTS_0.20.1.md` |
| Producción | **0 archivos y 0 cambios en `src/`** |

El perfil `quick` se ejecutó primero como control rápido y el `full` después;
por tanto, el JSON final corresponde inequívocamente a `full`. La metadata
registra motor 0.20.1, CPython 3.12.13, Linux x86_64, glibc 2.39 y 3 CPU lógicas.

## Registro exacto de comandos

| Control | Comando exacto | Salida | Resumen verificable |
|---|---|---:|---|
| Sincronización | `uv sync --locked --extra dev` | 0 | 16 paquetes resueltos; 14 dependencias dev instaladas. |
| Benchmark quick | `uv run python benchmarks/benchmark_action_options.py --profile quick` | 0 | `GO`; JSON escrito en la ruta esperada. |
| Benchmark full | `uv run python benchmarks/benchmark_action_options.py --profile full` | 0 | `GO`; JSON final de perfil `full`. |
| Paridad | `uv run pytest -q tests/test_action_option_resolver_parity.py tests/test_legal_action_enumerator_parity.py tests/test_benchmark_scenarios.py` | 0 | 133 pruebas superadas en 1.64 s. |
| Pytest completo | `uv run pytest -q` | 0 | 554 superadas, 1 omitida y 711 subtests superados en 98.30 s. |
| Unittest completo | `uv run python -m unittest discover -s tests -v` | 0 | 396 pruebas; `OK` en 92.328 s. |
| Mypy | `uv run python -m mypy src/card_duel_engine` | 0 | Sin incidencias en 40 archivos fuente. |
| Compileall | `uv run python -m compileall -q src tests scripts` | 0 | Sin salida de error. |
| Release runtime | `uv run python scripts/verify_release.py --profile runtime` | 0 | `OK: perfil runtime completado`. |
| Release full | `uv run python scripts/verify_release.py --profile full` | 0 | `OK: perfil full completado`; incluye calidad, fuentes, simulación, persistencia y paquete. |
| Wheel reproducible | `uv run python scripts/verify_reproducible_wheel.py` | 0 | 2 builds binariamente idénticos desde worktree *detached* del SHA benchmarkeado. |
| Hashes PDF declarados | `uv run python scripts/verify_rules_sources.py` | 0 | Ambos PDF informaron `OK`. |
| Hashes PDF directos | `sha256sum "Fantasy Tokens.pdf" "Fantasy Tokens Edicion Mitica.pdf"` | 0 | Digests reproducidos y registrados abajo. |
| Hash wheel | `sha256sum dist/card_duel_engine-0.20.1-py3-none-any.whl` | 0 | Coincide con auditoría y `SHA256SUMS`. |
| Contenido wheel | `unzip -Z1 dist/card_duel_engine-0.20.1-py3-none-any.whl` | 0 | 44 entradas; lista cerrada auditada abajo. |
| Diff bien formado | `git diff --check` | 0 | Sin espacios o conflictos de parche. |
| Diff de producción | `git diff --exit-code -- src/` | 0 | Sin salida: confirmación programática de **0 cambios en `src/`**. |
| Inventario del diff | `git diff --name-status` | 0 | Antes de crear este informe, solo `M benchmarks/results/action_options_benchmark.json`. |

## Auditoría final de alcance (2026-08-14)

La revisión final se realizó sobre la rama de entrega antes de crear el único
commit. No se consigna el SHA de ese commit para evitar una referencia circular
o inventada. Todos los comandos terminaron con código **0**. Los dos diffs de
áreas protegidas no produjeron salida, por lo que no fue necesario restaurar
código productivo ni repetir mediciones: la evidencia sigue correspondiendo al
benchmark `full` documentado arriba.

| Comando exacto | Código | Resultado final |
|---|---:|---|
| `git diff --check` | 0 | Parche bien formado. |
| `git diff --stat` | 0 | Sólo mostró la actualización de este informe de evidencia. |
| `git status --short` | 0 | Sólo mostró este informe como modificado. |
| `git diff -- src/card_duel_engine` | 0 | Sin salida; cero cambios productivos. |
| `git diff -- pyproject.toml uv.lock scripts tests .github/workflows` | 0 | Sin salida; cero cambios en configuración, lockfile, scripts, pruebas o workflows. |

El inventario final queda limitado a los cinco artefactos de benchmark ya
presentes en la entrega y a la actualización auditora de este mismo informe:
`benchmarks/benchmark_action_options.py`, `benchmarks/fixtures.py`,
`benchmarks/results/action_options_benchmark.json`,
`docs/performance/ACTION_OPTION_BENCHMARK_0.20.1.md` y
`docs/performance/results/ACTION_OPTION_BENCHMARK_RESULTS_0.20.1.md`. La
decisión final permanece **GO**, con la candidata futura descrita al final y
sin implementar optimización alguna.

## Resultados principales

En `legal_actions`, CURRENT y límite 128, las medias fueron 10.955 ms
(SMALL, 1,469 comandos), 12.910 ms (MEDIUM, 823) y 25.959 ms
(STRESS_CONTROLLED, 831). El pico global de memoria fue **1,021,024 bytes
(997.1 KiB)** en `legal_actions/current/small/limit-512`; el gran número de
jugadas materializadas de SMALL explica que supere incluso a STRESS.

### Efecto del límite en CURRENT/STRESS_CONTROLLED

| Límite | Media (ms) | p95 (ms) | Conteo | Pico (bytes) |
|---:|---:|---:|---:|---:|
| 8 | 21.117 | 21.923 | 139 | 54,440 |
| 32 | 22.322 | 22.814 | 361 | 108,480 |
| 128 | 25.959 | 26.975 | 831 | 262,408 |
| 512 | 40.896 | 55.135 | 2,367 | 826,360 |

De 8 a 512, el conteo creció 17.0×, la media 1.94× y el pico de memoria
15.18×. El límite acota enumeraciones internas y no el total agregado, por lo
que el conteo final puede excederlo.

### Coste de `deepcopy`

| Escenario | Media (ms) | p95 (ms) | Pico (bytes) |
|---|---:|---:|---:|
| SMALL | 1.480 | 1.888 | 78,016 |
| MEDIUM | 1.550 | 1.638 | 84,928 |
| STRESS_CONTROLLED | 2.568 | 3.193 | 148,424 |

El `deepcopy` de STRESS costó 1.74× la media y 1.90× el pico de SMALL. Es
un coste observable, pero no domina `legal_actions` en estos escenarios.

### Top 5 hotspots de STRESS_CONTROLLED

La captura `cProfile` es una llamada instrumentada, ordenada por tiempo
acumulado; caller y callee se solapan y no deben sumarse.

| Posición | Función | Llamadas | Tiempo acumulado |
|---:|---|---:|---:|
| 1 | `_card_can_be_targeted` | 510 | 0.043 s |
| 2 | `_effective_keywords` | 510 | 0.041 s |
| 3 | `_legal_plays` | 1 | 0.040 s |
| 4 | `_continuous_effects_for` | 512 | 0.035 s |
| 5 | `_definition` | 19,005 | 0.026 s |

Se excluyen de este ranking los dos wrappers `legal_actions` (0.057 s cada
uno), porque representan la misma operación completa y no un foco interno.

### CURRENT frente a LEGACY_019

En STRESS/límite 128, `legal_actions` midió 25.959 ms CURRENT y 25.882 ms
LEGACY_019 (LEGACY 0.30 % menor). En consultas directas, LEGACY fue mayor en
`_legal_plays` (19.225 frente a 18.002 ms), `_legal_ability_activations`
(3.786 frente a 3.627 ms) y `_trigger_target_commands` (3.608 frente a
3.466 ms). Estas diferencias pequeñas son variación temporal, no una diferencia
de resultado ni evidencia de superioridad. El fixture está en fase `EFFECTS`,
donde la distinta ventana histórica de activación no se manifiesta.

## Fingerprints y estabilidad

| Escenario principal (`legal_actions`, límite 128) | CURRENT | LEGACY_019 | Conteo |
|---|---|---|---:|
| SMALL | `64390a1066b8f86f4074637e633b544764527802d959e9f4b32ade53f0a90d88` | igual | 1,469 |
| MEDIUM | `0e94cbf2783b9025832147d94d55cceff9da2b3815d05209517e08daaad3efc0` | igual | 823 |
| STRESS_CONTROLLED | `819f98ef64451c8177367e0be2ecab97dd33494b0e5417781c2f06011212e4ee` | igual | 831 |

**Estabilidad confirmada:** cada caso comparó su observación inicial con 5
repeticiones de calentamiento, 15 repeticiones medidas y la ejecución de
memoria; conteo, orden, serialización y SHA-256 permanecieron estables. El
script también comprobó que el estado original no mutó. Los fingerprints
CURRENT/LEGACY resultaron iguales para estos fixtures, sin convertir esa
igualdad en requisito general entre perfiles semánticos.

## Wheel y fuentes normativas

Wheel: `card_duel_engine-0.20.1-py3-none-any.whl`  
SHA-256: `74d56d311412da138830b8c5ba75e27c3f00e55049558160391997e9b7a7d14e`.

La auditoría verificó **44 entradas**, `RECORD` íntegro, orden ZIP canónico,
licencia Apache-2.0, etiqueta `py3-none-any`, `Root-Is-Purelib: true`, cero
dependencias runtime, ausencia de fixtures, cartas de producción y PDF, y dos
builds byte a byte idénticos. El contenido auditado fue:

- 40 módulos `.py` bajo `card_duel_engine/`: raíz, `content`, `controllers`,
  `domain`, `engine`, `persistence`, `rules`, `simulation` y `storage`;
- `card_duel_engine-0.20.1.dist-info/METADATA`;
- `card_duel_engine-0.20.1.dist-info/WHEEL`;
- `card_duel_engine-0.20.1.dist-info/top_level.txt`;
- `card_duel_engine-0.20.1.dist-info/RECORD`.

Hashes normativos confirmados:

- `Fantasy Tokens.pdf`: `1c51dabe2023626ad532368e2567d2084c47ec137c7a738bd8c0e0b707f86b21`;
- `Fantasy Tokens Edicion Mitica.pdf`: `61243b30d219dd12d8897a206ed664d95a5e3c38b6670a818933f6d90904af36`.

## Única candidata futura

**Candidata única, no implementada:** evaluar la eliminación segura de cálculos
repetidos de `_effective_keywords`/`_continuous_effects_for` durante
`_card_can_be_targeted` dentro de `_legal_plays`. Deriva del top 5 (0.043,
0.041 y 0.035 s acumulados) y deberá demostrar beneficio aislado sin cambiar
orden, conteos, fingerprints, semántica ni invalidación. **No se implementó
ninguna optimización en esta entrega.**

