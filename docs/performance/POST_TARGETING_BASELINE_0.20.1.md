# Baseline posterior a la optimización de targeting 0.20.1

## Identidad y propósito

Este documento fija el baseline **posterior** a la caché local de targeting. No
autoriza ni implementa otra optimización: describe el punto de partida para una
decisión futura y remite los números completos a
`results/POST_TARGETING_BASELINE_RESULTS_0.20.1.md`.

- SHA medido: `f66fd8008837baf76f2fc2877332b6417d28a2a5`.
- SHA de cierre documental: `0b1355e12f3da6d6e5e80a38970dd2b575d84621`.
- Versión del motor: `0.20.1`.
- Artefacto primario: `benchmarks/results/post_targeting_benchmark.json`, esquema 1.
- Perfil ejecutado: `full`.

El SHA medido y el de cierre difieren porque las mediciones se capturaron antes
de los merges que incorporaron el perfil estructurado y el caso de `deepcopy`.
Esos commits sólo modificaron benchmark, README y el JSON de resultados; no se
modificó código productivo entre la medición y este cierre.

## Entorno y hardware observable

| Elemento | Valor observado |
|---|---|
| Python | CPython 3.12.13 |
| Plataforma | Linux 6.18.35, x86_64, glibc 2.39 |
| CPU visible | 3 CPU lógicas, Intel Xeon Platinum 8370C @ 2.80 GHz |
| Virtualización | KVM completa |
| Cachés visibles | L1d 96 KiB, L1i 64 KiB, L2 2,5 MiB, L3 48 MiB |
| Afinidad disponible al documentar | CPU 0–2 |
| Afinidad durante el benchmark | no fijada por el controlador |
| Semilla de fixture | `SCENARIO_SEED = 20260814` |

La marca/modelo y cachés proceden de `lscpu` ejecutado en el mismo contenedor,
pero no forman parte de la metadata persistida por el JSON. La falta de pinning
es una limitación explícita: el planificador pudo mover el proceso entre las tres
CPU visibles.

## Metodología paso a paso

1. Se construyó un motor determinista nuevo por caso mediante
   `benchmarks.fixtures.build_scenario`.
2. Se evaluaron por separado `CURRENT` y `LEGACY_019`, los tamaños `SMALL`,
   `MEDIUM` y `STRESS_CONTROLLED`, y límites productivos 8, 32, 128 y 512.
3. Para el foco comparable se usó `legal_actions("A")`, límite 128, en MEDIUM y
   STRESS_CONTROLLED.
4. Se descartaron 5 calentamientos y se conservaron 15 repeticiones. El
   cronómetro `perf_counter_ns` rodeó únicamente la consulta.
5. El pico de memoria se midió aparte con `tracemalloc`; por tanto no debe
   sumarse ni compararse como RSS del proceso.
6. Cada repetición comprobó igualdad byte a byte del estado canónico antes y
   después, conteo y SHA-256 del resultado ordenado.
7. `cProfile` se ejecutó una vez aparte para cada escenario CURRENT/límite 128,
   ordenando por tiempo acumulado y conservando las primeras 20 filas.
8. Para diagnosticar dominancia sin doble conteo, cada función se asignó a una
   sola categoría por tiempo propio. Los tiempos acumulados sólo describen la
   relación llamador–llamado.
9. `deepcopy(GameState)` se midió como caso aislado, con equivalencia canónica,
   identidad distinta de objeto y estado original inalterado.

Comando de reproducción del artefacto:

```bash
.venv/bin/python benchmarks/benchmark_action_options.py --profile full \
  --output benchmarks/results/post_targeting_benchmark.json
```

## Aislamiento, límites y restricciones

- No hubo comparación alternada entre dos worktrees en esta corrida. Los valores
  históricos sí proceden de un protocolo alternado de 30 muestras; cualquier
  comparación cruzada es contextual, no una prueba A/B directa.
- Construcción del fixture, canonicalización, hashes y comprobaciones quedaron
  fuera del cronómetro. `cProfile` y `tracemalloc` se ejecutaron fuera de las
  muestras temporales normales.
- El límite 128 es parte del caso comparable; los resultados no extrapolan a una
  enumeración ilimitada ni a cargas reales concurrentes.
- No se controla frecuencia, turbo, vecinos KVM, temperatura, carga del host ni
  política del scheduler. Un outlier visible afecta media, p95 y desviación.
- `tracemalloc` observa asignaciones Python, no RSS, memoria nativa ni consumo
  total del contenedor.
- Una única captura de `cProfile` es diagnóstico, no estimación estadística; su
  instrumentación altera el tiempo de pared y los tiempos inclusivos se solapan.
- Los escenarios son sintéticos y deterministas. No sustituyen telemetría de
  partidas reales ni prueban distribuciones de mazos no representadas.
- No se cambian reglas, API, persistencia, replay, snapshots, `GameState`,
  `PhaseManager`, combinatoria, materialización ni `deepcopy` en este trabajo.

## Perfiles semánticos y gates

`CURRENT` y `LEGACY_019` se registran como casos independientes. En estos
fixtures ambos producen el mismo conteo y fingerprint porque la fase ejercitada
no alcanza su diferencia normativa de ventanas de activación; no se presupone
por ello equivalencia general entre perfiles.

Los gates de este baseline son: árbol sin cambios productivos; versión 0.20.1;
consulta sin mutación; conteo, orden y fingerprint estables dentro de cada caso;
perfiles semánticos registrados separadamente; benchmark y suite verdes. Una
divergencia en cualquiera obliga a **NO-GO**.

## Regla de decisión

Este cierre es **GO** exclusivamente para aceptar la evidencia como baseline:
no hay cambios productivos, todas las consultas medidas preservan el estado,
los fingerprints son estables y los perfiles semánticos están separados. El GO
no autoriza por sí solo la candidata futura descrita en resultados.
