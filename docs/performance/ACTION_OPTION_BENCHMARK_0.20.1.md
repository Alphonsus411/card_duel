# Benchmark de opciones de acción 0.20.1

## Objetivo, alcance y exclusiones

El objetivo es establecer una **línea base reproducible** del coste temporal y de memoria de la enumeración de opciones/acciones legales del motor 0.20.1, identificar dónde se acumula el tiempo y observar cómo responde `legal_actions` a límites crecientes. Este trabajo es diagnóstico: **no implementa, propone como realizada ni valida ninguna optimización**, no cambia el motor ni sus reglas y no pretende demostrar capacidad de carga sin límite. Tampoco compara versiones de código: `CURRENT` y `LEGACY_019` son perfiles semánticos ejecutados sobre el mismo SHA.

Artefacto fuente: `benchmarks/results/action_options_benchmark.json`. SHA medido: **`421ae27c6afc81a72ca80a909fb62af6ca352568`**. Los resultados siguientes son una transcripción redondeada de ese artefacto; el JSON conserva los bytes y nanosegundos originales.

## Hardware y entorno

| Elemento | Valor medido |
|---|---|
| Motor | 0.20.1 |
| SO/plataforma | Linux 6.18.35 x86_64, glibc 2.39 |
| Arquitectura/procesador observable | x86_64 |
| CPU lógicas visibles | 3 |
| Python | 3.12.13 |
| Implementación | CPython |
| Perfil | `full` |

No se registraron modelo de CPU, frecuencia, RAM física, hipervisor, afinidad, gobernador ni carga concurrente; por ello no deben inferirse características ausentes ni extrapolarse los valores absolutos a otra máquina.

## Metodología y cronómetros

1. Cada caso construye un fixture sintético determinista (semilla `20260814`) y obtiene una observación inicial que fija conteo, serialización canónica y fingerprint SHA-256.
2. Se ejecutan **5 repeticiones de warm-up**, no incluidas en las estadísticas. Cada una verifica conteo, contenido, orden y ausencia de mutación. El warm-up reduce efectos de primera ejecución, pero también puede calentar cachés del intérprete/SO; no los elimina ni representa necesariamente una petición fría.
3. Se ejecutan **15 repeticiones medidas**. Se usa `time.perf_counter_ns()` alrededor de la llamada consultada.
4. El cronómetro **incluye** la ejecución completa de la consulta (`target_selections`, `legal_actions`, etc.) y la materialización de su resultado. Para `deepcopy`, incluye exclusivamente `copy.deepcopy(state)`.
5. El cronómetro **excluye** la construcción del fixture, el estado canónico anterior/posterior, la validación, la serialización, el hash, GC explícito y `tracemalloc`. Esas operaciones ocurren fuera del intervalo, aunque la actividad previa/posterior puede introducir ruido indirecto.
6. La memoria se mide en una ejecución adicional, separada del cronómetro: tras `gc.collect()`, se inicia y reinicia `tracemalloc`, se llama una vez a la consulta y se leen memoria actual y pico antes de detenerlo. **Actual** es memoria trazada aún viva al acabar la llamada; **pico** es el máximo durante ella. Se excluyen construcción del fixture y memoria no seguida por `tracemalloc` (por ejemplo, parte de asignaciones nativas/RSS).
7. Antes y después se comprueba que el estado original no muta; `deepcopy` debe conservar contenido y devolver otra identidad. Una divergencia convierte la ejecución en NO-GO.
8. El p95 usa **nearest rank sin interpolación**: se ordenan las 15 duraciones y se elige `sorted[ceil(0.95 × 15) - 1]`; con 15 muestras es la máxima observación. La desviación del JSON es muestral (`n-1`).
9. `cProfile` se ejecuta aparte una vez por escenario sobre `CURRENT`, límite 128; sus tiempos instrumentados no son los del cronómetro normal.

### Métricas y redondeo

Las columnas `media`, `p95`, `conteo`, `actual` y `pico` son mediciones directas (las memorias se muestran en KiB, redondeadas a 0.1). Las marcadas con asterisco son **métricas derivadas**, no mediciones independientes:

- **`ns/opción*`** = media en ns / conteo.
- **`μs/comando*`** = media en ns / 1 000 / conteo, sólo para casos clasificados como comandos legales.
- **`bytes pico/opción*`** = pico en bytes / conteo.

`deepcopy` tiene conteo técnico 1, por lo que `ns/opción` existe en el JSON pero no debe interpretarse como opción de juego; aquí se omiten las métricas derivadas que resultarían semánticamente engañosas.

## Escenarios y parámetros

| Escenario | candidatos objetivo | cantidad repartida | triggers ordenables | uso |
|---|---:|---:|---:|---|
| SMALL | 4 | 3 | 3 | base |
| MEDIUM | 16 | 10 | 5 | crecimiento intermedio |
| STRESS_CONTROLLED | 32 | 20 | 7 | estrés finito y limitado |

Todos usan dos jugadores (`A` consulta), fase `EFFECTS`, 40 pasos y 5 heridas para A, cartas sintéticas y combinaciones de objetivos de jugador, permanente y zona, reparto, descarte y sacrificio. Los microbenchmarks cubren candidatos 4/8/16/32; selecciones exactas o rango 1–4; zonas `(jugadores, zonas, min, max)` de `(2,2,1,1)`, `(2,8,1,3)`, `(3,4,2,2)`, `(4,8,0,3)`; ocho formas de reparto hasta 32 candidatos, cantidad 20, 2–6 objetivos y X hasta 10; seis familias de coste. Los límites son 8, 32, 128 y 512. Las consultas directas de alto nivel usan límite 128; `legal_actions` varía los cuatro límites; `deepcopy` usa 128.

## Microbenchmarks neutrales a la semántica

Estos helpers no dependen del perfil de compatibilidad y se midieron **una sola vez** (`semantics: not_applicable`); duplicarlos como CURRENT/LEGACY_019 habría medido el mismo código/fixture, no una diferencia semántica. Las tablas eligen la forma más combinatoria para comparar límites y, para costes, muestran todas las familias a límite 128; el JSON contiene la matriz completa.

### `target_selections`
| Caso | media (ms) | p95 (ms) | conteo | actual (KiB) | pico (KiB) | ns/opción* | μs/comando* | bytes pico/opción* |
|---|---|---|---|---|---|---|---|---|
| n=32, rango 1–4, límite 8 | 0.010 | 0.030 | 8 | 0.5 | 1.7 | 1303.2 | — | 221.0 |
| n=32, rango 1–4, límite 32 | 0.012 | 0.022 | 32 | 1.8 | 3.1 | 363.7 | — | 99.5 |
| n=32, rango 1–4, límite 128 | 0.019 | 0.033 | 128 | 4.8 | 6.0 | 148.2 | — | 47.8 |
| n=32, rango 1–4, límite 512 | 0.058 | 0.090 | 512 | 28.8 | 30.9 | 114.2 | — | 61.9 |

### `zone_target_selections`
| Caso | media (ms) | p95 (ms) | conteo | actual (KiB) | pico (KiB) | ns/opción* | μs/comando* | bytes pico/opción* |
|---|---|---|---|---|---|---|---|---|
| 4×8 zonas, objetivos 0–3, límite 8 | 0.024 | 0.026 | 8 | 1.1 | 3.8 | 3059.7 | — | 490.0 |
| 4×8 zonas, objetivos 0–3, límite 32 | 0.028 | 0.052 | 32 | 3.4 | 4.9 | 867.3 | — | 157.8 |
| 4×8 zonas, objetivos 0–3, límite 128 | 0.038 | 0.054 | 128 | 6.7 | 8.1 | 300.4 | — | 65.1 |
| 4×8 zonas, objetivos 0–3, límite 512 | 0.130 | 0.162 | 512 | 32.4 | 34.7 | 253.5 | — | 69.5 |

### `allocation_selections`
| Caso | media (ms) | p95 (ms) | conteo | actual (KiB) | pico (KiB) | ns/opción* | μs/comando* | bytes pico/opción* |
|---|---|---|---|---|---|---|---|---|
| n=32, cantidad=20, objetivos 2–6, X=10, límite 8 | 0.803 | 1.092 | 8 | 1.8 | 4.3 | 100423.9 | — | 549.0 |
| n=32, cantidad=20, objetivos 2–6, X=10, límite 32 | 0.872 | 0.911 | 32 | 7.1 | 9.8 | 27257.2 | — | 314.5 |
| n=32, cantidad=20, objetivos 2–6, X=10, límite 128 | 1.207 | 1.446 | 128 | 28.1 | 31.6 | 9426.0 | — | 252.6 |
| n=32, cantidad=20, objetivos 2–6, X=10, límite 512 | 2.378 | 2.459 | 512 | 112.1 | 118.6 | 4644.7 | — | 237.3 |

### `card_cost_options`
| Caso | media (ms) | p95 (ms) | conteo | actual (KiB) | pico (KiB) | ns/opción* | μs/comando* | bytes pico/opción* |
|---|---|---|---|---|---|---|---|---|
| fixed | 0.014 | 0.052 | 1 | 0.3 | 1.1 | 13860.2 | — | 1112.0 |
| dynamic | 0.022 | 0.050 | 1 | 0.5 | 2.0 | 21564.3 | — | 2048.0 |
| x | 0.111 | 0.126 | 21 | 4.5 | 6.1 | 5285.3 | — | 296.8 |
| alt-fixed | 0.009 | 0.011 | 3 | 0.5 | 1.3 | 2885.4 | — | 434.7 |
| alt-dynamic | 0.032 | 0.073 | 2 | 0.7 | 2.7 | 16232.8 | — | 1388.0 |
| alt-x | 0.127 | 0.210 | 22 | 4.7 | 6.4 | 5761.2 | — | 299.6 |


## Benchmarks de alto nivel: CURRENT frente a LEGACY_019

Se separan explícitamente ambos perfiles. Son semánticas distintas sobre el mismo código: el fixture está en `EFFECTS`, donde la diferencia histórica de ventanas de activación no se manifiesta en conteos/fingerprints. Las diferencias pequeñas de tiempo sin cambio de resultado son ruido/variación de ejecución, no evidencia de superioridad semántica.

### `_legal_plays`
| Perfil | Escenario | media (ms) | p95 (ms) | conteo | actual (KiB) | pico (KiB) | ns/opción* | μs/comando* | bytes pico/opción* |
|---|---|---|---|---|---|---|---|---|---|
| CURRENT | SMALL | 6.067 | 7.294 | 1202 | 405.1 | 430.0 | 5047.7 | 5.05 | 366.4 |
| CURRENT | MEDIUM | 6.173 | 7.022 | 550 | 153.4 | 175.4 | 11223.8 | 11.22 | 326.6 |
| CURRENT | STRESS_CONTROLLED | 13.716 | 15.734 | 550 | 150.1 | 171.2 | 24937.5 | 24.94 | 318.7 |
| LEGACY_019 | SMALL | 6.701 | 21.356 | 1202 | 405.1 | 430.0 | 5575.1 | 5.58 | 366.4 |
| LEGACY_019 | MEDIUM | 6.025 | 6.227 | 550 | 153.4 | 175.4 | 10953.7 | 10.95 | 326.6 |
| LEGACY_019 | STRESS_CONTROLLED | 13.514 | 15.554 | 550 | 150.1 | 171.2 | 24570.8 | 24.57 | 318.7 |

### `_legal_ability_activations`
| Perfil | Escenario | media (ms) | p95 (ms) | conteo | actual (KiB) | pico (KiB) | ns/opción* | μs/comando* | bytes pico/opción* |
|---|---|---|---|---|---|---|---|---|---|
| CURRENT | SMALL | 1.041 | 1.139 | 128 | 52.7 | 55.2 | 8131.5 | 8.13 | 441.9 |
| CURRENT | MEDIUM | 1.447 | 1.786 | 128 | 52.6 | 56.1 | 11305.3 | 11.31 | 448.9 |
| CURRENT | STRESS_CONTROLLED | 2.684 | 3.086 | 128 | 51.2 | 55.0 | 20967.5 | 20.97 | 440.4 |
| LEGACY_019 | SMALL | 0.981 | 1.054 | 128 | 52.7 | 55.2 | 7666.2 | 7.67 | 441.9 |
| LEGACY_019 | MEDIUM | 1.395 | 1.435 | 128 | 52.6 | 56.1 | 10897.5 | 10.90 | 448.9 |
| LEGACY_019 | STRESS_CONTROLLED | 2.967 | 3.519 | 128 | 51.2 | 55.0 | 23177.9 | 23.18 | 440.4 |

### `_trigger_target_commands`
| Perfil | Escenario | media (ms) | p95 (ms) | conteo | actual (KiB) | pico (KiB) | ns/opción* | μs/comando* | bytes pico/opción* |
|---|---|---|---|---|---|---|---|---|---|
| CURRENT | SMALL | 0.885 | 0.985 | 128 | 47.4 | 49.7 | 6911.0 | 6.91 | 397.4 |
| CURRENT | MEDIUM | 1.340 | 1.788 | 128 | 46.4 | 49.7 | 10467.6 | 10.47 | 397.3 |
| CURRENT | STRESS_CONTROLLED | 2.511 | 2.702 | 128 | 44.5 | 48.1 | 19614.8 | 19.61 | 384.8 |
| LEGACY_019 | SMALL | 0.847 | 0.881 | 128 | 47.4 | 49.7 | 6614.9 | 6.61 | 397.4 |
| LEGACY_019 | MEDIUM | 1.271 | 1.398 | 128 | 46.4 | 49.7 | 9932.5 | 9.93 | 397.3 |
| LEGACY_019 | STRESS_CONTROLLED | 2.976 | 7.456 | 128 | 44.5 | 48.1 | 23247.4 | 23.25 | 384.8 |

### `legal_actions` a límite 128
| Perfil | Escenario | media (ms) | p95 (ms) | conteo | actual (KiB) | pico (KiB) | ns/opción* | μs/comando* | bytes pico/opción* |
|---|---|---|---|---|---|---|---|---|---|
| CURRENT | SMALL | 8.001 | 9.907 | 1469 | 506.4 | 531.8 | 5446.9 | 5.45 | 370.7 |
| CURRENT | MEDIUM | 9.153 | 10.989 | 823 | 246.7 | 261.3 | 11121.4 | 11.12 | 325.1 |
| CURRENT | STRESS_CONTROLLED | 21.264 | 41.299 | 831 | 241.6 | 256.3 | 25587.9 | 25.59 | 315.8 |
| LEGACY_019 | SMALL | 8.890 | 12.242 | 1469 | 506.4 | 531.8 | 6052.0 | 6.05 | 370.7 |
| LEGACY_019 | MEDIUM | 8.823 | 9.339 | 823 | 246.7 | 261.3 | 10720.4 | 10.72 | 325.1 |
| LEGACY_019 | STRESS_CONTROLLED | 19.331 | 22.238 | 831 | 241.6 | 256.3 | 23262.2 | 23.26 | 315.8 |

### `deepcopy` (neutral; no se duplicó)
| Escenario | media (ms) | p95 (ms) | actual (KiB) | pico (KiB) |
|---|---|---|---|---|
| SMALL | 1.004 | 1.089 | 40.5 | 76.2 |
| MEDIUM | 1.089 | 1.235 | 44.6 | 82.9 |
| STRESS_CONTROLLED | 2.079 | 4.213 | 76.1 | 144.9 |


## Efecto del límite de enumeración

La siguiente tabla cumple la comparación 8/32/128/512 usando `legal_actions`, CURRENT y STRESS_CONTROLLED; el fixture se reconstruye idéntico y sólo cambia `RuleSet.legal_action_enumeration_limit`. El conteo no coincide exactamente con el límite porque la respuesta agrega familias de acciones y el límite acota enumeraciones internas, no el total final.
| Límite | media (ms) | p95 (ms) | conteo | actual (KiB) | pico (KiB) |
|---|---|---|---|---|---|
| 8 | 15.274 | 16.376 | 139 | 50.0 | 53.2 |
| 32 | 16.595 | 17.342 | 361 | 99.1 | 105.9 |
| 128 | 21.264 | 41.299 | 831 | 241.6 | 256.3 |
| 512 | 32.980 | 53.333 | 2367 | 766.8 | 807.0 |


De 8 a 512, el conteo crece **17.0×** (139→2367), la media **2.16×** (15.274→32.980 ms) y el pico **15.2×** (53.2→807.0 KiB). La memoria sigue mucho más de cerca el volumen materializado que el tiempo: hay un coste fijo apreciable en STRESS, visible en que `μs/comando` baja de 109.89 a 13.93 mientras aumenta el límite.

## `cProfile`: 20 mayores tiempos acumulados

Son capturas instrumentadas de una sola llamada `legal_actions`, CURRENT, límite 128, ordenadas por tiempo acumulado. Las rutas se abreviaron al archivo/función sin alterar cifras; el tiempo acumulado puede solaparse entre caller y callee y no debe sumarse por filas.

### MEDIUM (823 comandos)

| ncalls | tottime (s) | por llamada | cumtime (s) | por llamada acum. | función |
|---|---|---|---|---|---|
| 1 | 0.000 | 0.000 | 0.023 | 0.023 | `src/card_duel_engine/engine/game.py:645(legal_actions)` |
| 1 | 0.000 | 0.000 | 0.023 | 0.023 | `src/card_duel_engine/engine/actions.py:73(legal_actions)` |
| 1 | 0.001 | 0.001 | 0.015 | 0.015 | `src/card_duel_engine/engine/game.py:768(_legal_plays)` |
| 270 | 0.000 | 0.000 | 0.011 | 0.000 | `src/card_duel_engine/engine/game.py:1114(_card_can_be_targeted)` |
| 270 | 0.002 | 0.000 | 0.011 | 0.000 | `src/card_duel_engine/engine/game.py:2002(_effective_keywords)` |
| 272 | 0.002 | 0.000 | 0.009 | 0.000 | `src/card_duel_engine/engine/game.py:1965(_continuous_effects_for)` |
| 56 | 0.000 | 0.000 | 0.008 | 0.000 | `src/card_duel_engine/engine/game.py:850(_allocation_selections)` |
| 56 | 0.002 | 0.000 | 0.008 | 0.000 | `src/card_duel_engine/engine/options.py:127(allocation_selections)` |
| 10 | 0.000 | 0.000 | 0.007 | 0.001 | `src/card_duel_engine/engine/game.py:1183(_legal_ability_activations)` |
| 171 | 0.000 | 0.000 | 0.007 | 0.000 | `src/card_duel_engine/engine/game.py:779(<genexpr>)` |
| 5749 | 0.003 | 0.000 | 0.007 | 0.000 | `src/card_duel_engine/engine/game.py:2117(_definition)` |
| 37 | 0.000 | 0.000 | 0.004 | 0.000 | `{method 'extend' of 'list' objects}` |
| 5749 | 0.002 | 0.000 | 0.003 | 0.000 | `src/card_duel_engine/engine/game.py:2121(_definition_for)` |
| 76 | 0.000 | 0.000 | 0.003 | 0.000 | `src/card_duel_engine/engine/options.py:141(<genexpr>)` |
| 72 | 0.000 | 0.000 | 0.003 | 0.000 | `src/card_duel_engine/engine/game.py:180(_option_card_can_be_targeted)` |
| 1456 | 0.001 | 0.000 | 0.002 | 0.000 | `src/card_duel_engine/engine/options.py:158(<genexpr>)` |
| 38 | 0.000 | 0.000 | 0.001 | 0.000 | `src/card_duel_engine/engine/game.py:1246(<genexpr>)` |
| 944 | 0.001 | 0.000 | 0.001 | 0.000 | `<string>:2(__init__)` |
| 9 | 0.000 | 0.000 | 0.001 | 0.000 | `src/card_duel_engine/engine/game.py:722(_card_cost_options)` |
| 5749 | 0.001 | 0.000 | 0.001 | 0.000 | `src/card_duel_engine/catalog.py:58(get)` |

### STRESS_CONTROLLED (831 comandos)

| ncalls | tottime (s) | por llamada | cumtime (s) | por llamada acum. | función |
|---|---|---|---|---|---|
| 1 | 0.000 | 0.000 | 0.044 | 0.044 | `src/card_duel_engine/engine/game.py:645(legal_actions)` |
| 1 | 0.000 | 0.000 | 0.044 | 0.044 | `src/card_duel_engine/engine/actions.py:73(legal_actions)` |
| 510 | 0.001 | 0.000 | 0.033 | 0.000 | `src/card_duel_engine/engine/game.py:1114(_card_can_be_targeted)` |
| 510 | 0.004 | 0.000 | 0.032 | 0.000 | `src/card_duel_engine/engine/game.py:2002(_effective_keywords)` |
| 1 | 0.001 | 0.001 | 0.031 | 0.031 | `src/card_duel_engine/engine/game.py:768(_legal_plays)` |
| 512 | 0.008 | 0.000 | 0.027 | 0.000 | `src/card_duel_engine/engine/game.py:1965(_continuous_effects_for)` |
| 315 | 0.000 | 0.000 | 0.020 | 0.000 | `src/card_duel_engine/engine/game.py:779(<genexpr>)` |
| 19005 | 0.009 | 0.000 | 0.020 | 0.000 | `src/card_duel_engine/engine/game.py:2117(_definition)` |
| 56 | 0.000 | 0.000 | 0.013 | 0.000 | `src/card_duel_engine/engine/game.py:850(_allocation_selections)` |
| 56 | 0.002 | 0.000 | 0.013 | 0.000 | `src/card_duel_engine/engine/options.py:127(allocation_selections)` |
| 18 | 0.000 | 0.000 | 0.012 | 0.001 | `src/card_duel_engine/engine/game.py:1183(_legal_ability_activations)` |
| 45 | 0.000 | 0.000 | 0.010 | 0.000 | `{method 'extend' of 'list' objects}` |
| 19005 | 0.007 | 0.000 | 0.009 | 0.000 | `src/card_duel_engine/engine/game.py:2121(_definition_for)` |
| 140 | 0.000 | 0.000 | 0.009 | 0.000 | `src/card_duel_engine/engine/options.py:141(<genexpr>)` |
| 136 | 0.000 | 0.000 | 0.009 | 0.000 | `src/card_duel_engine/engine/game.py:180(_option_card_can_be_targeted)` |
| 70 | 0.000 | 0.000 | 0.004 | 0.000 | `src/card_duel_engine/engine/game.py:1246(<genexpr>)` |
| 19005 | 0.002 | 0.000 | 0.002 | 0.000 | `src/card_duel_engine/catalog.py:58(get)` |
| 20656 | 0.002 | 0.000 | 0.002 | 0.000 | `src/card_duel_engine/engine/game.py:2342(_require_state)` |
| 1392 | 0.001 | 0.000 | 0.001 | 0.000 | `src/card_duel_engine/engine/options.py:158(<genexpr>)` |
| 880 | 0.001 | 0.000 | 0.001 | 0.000 | `<string>:2(__init__)` |


En MEDIUM, `_legal_plays` acumula 0.015/0.023 s (≈65% del total perfilado) y la cadena `_card_can_be_targeted`→`_effective_keywords` acumula 0.011 s. En STRESS, esa cadena llega a 0.033/0.044 s (≈75%) y `_legal_plays` a 0.031/0.044 s (≈70%); son tiempos inclusivos y solapados. `allocation_selections` suma 0.008 s MEDIUM y 0.013 s STRESS. La tendencia demostrada señala el cálculo repetido de elegibilidad/keywords dentro de jugadas como el mayor impacto acumulado, no una suma independiente de esos porcentajes.

## Limitaciones

- **Ruido del sistema:** no hubo aislamiento de CPU, afinidad, control de frecuencia ni registro de carga; los p95 con 15 muestras equivalen al máximo y son sensibles a outliers (por ejemplo, LEGACY_019 SMALL `_legal_plays`).
- **Una sola máquina:** los números absolutos sólo caracterizan el entorno descrito y no establecen rendimiento multiplataforma.
- **`tracemalloc`:** añade sobrecoste y sólo observa asignaciones trazadas de Python; se ejecutó fuera del cronómetro, pero sus picos no equivalen a RSS ni a producción sin instrumentación.
- **Warm-up:** cinco pasadas reducen primeras ejecuciones, pero favorecen cachés calientes; no se midió explícitamente cold start ni se aleatorizó el orden de casos.
- **Repeticiones:** 15 permiten una referencia, no intervalos robustos ni causalidad entre diferencias pequeñas.
- **Fixtures sintéticos y límites:** cubren ejes controlados, no toda combinación de estados/cartas ni carga ilimitada.
- **`cProfile`:** instrumenta y perturba una única ejecución; los tiempos inclusivos se solapan.
- **Sin umbrales de CI:** no se define pass/fail, presupuesto ni regresión automática. Estos datos son baseline diagnóstico, no gate de CI.

## Recomendaciones condicionales y candidata futura

1. **Si** el producto necesita elevar el límite por encima de 128 en estados STRESS, **entonces** conviene presupuestar primero memoria: 128→512 multiplica conteo 2.85×, media 1.55× y pico 3.15× (256.3→807.0 KiB). La recomendación deriva de esa pendiente observada, no de una intuición sobre estructuras concretas.
2. **Si** el objetivo es reducir latencia STRESS a límite 128, **entonces** el perfil justifica investigar la cadena de elegibilidad/keywords en `_legal_plays`: acumula 0.033 s de 0.044 s perfilados (≈75%) y crece 3× frente a MEDIUM (0.011→0.033 s), mientras el benchmark CURRENT de `_legal_plays` crece 2.22× (6.173→13.716 ms).
3. **Si** se contempla una optimización, debe conservar conteos, orden, fingerprints, paridad CURRENT/LEGACY_019 y volver a medir en proceso/máquina comparables; diferencias aisladas entre perfiles con el mismo resultado no bastan como conclusión.

**Única candidata para una iteración futura (no implementada):** investigar y, sólo si una medición aislada lo confirma, reducir el cálculo repetido de `_effective_keywords`/`_continuous_effects_for` durante `_card_can_be_targeted` dentro de `_legal_plays`. Se elige por el mayor impacto demostrado (≈75% acumulado inclusivo en STRESS y crecimiento de 0.011 a 0.033 s), por encima de `allocation_selections` (0.013 s STRESS). No se prescribe memoización ni otra técnica antes de probar corrección, invalidación y beneficio neto.

## Priorización final

| Hotspot | Impacto temporal | Impacto memoria | Escalabilidad | Riesgo de optimización | Prioridad propuesta |
|---|---|---|---|---|---|
| Elegibilidad → keywords/efectos continuos en `_legal_plays` | 0.033/0.044 s acumulados en STRESS (≈75%, inclusivo) | No aislado por `cProfile`; `_legal_plays` pico 171.2 KiB | 0.011→0.033 s de MEDIUM a STRESS (3×) | Alto: reglas, efectos continuos e invalidación | 1 — única candidata futura |
| Materialización por límite en `legal_actions` | 15.274→32.980 ms, límite 8→512 (2.16×) | 53.2→807.0 KiB pico (15.2×) | conteo 139→2367 (17.0×) | Medio: orden, truncamiento y API | 2 — observar/presupuestar |
| `allocation_selections` dentro de `legal_actions` | 0.008→0.013 s acumulados MEDIUM→STRESS | No aislado en perfil; microbench documentado | 1.63× en tiempo perfilado | Alto: combinatoria y orden estable | 3 — medir tras prioridad 1 |
| `deepcopy(GameState)` | 1.004→2.079 ms SMALL→STRESS (2.07×) | 76.2→144.9 KiB pico (1.90×) | crece con estado | Alto: identidad y aislamiento transaccional | 4 — sin acción con esta evidencia |
