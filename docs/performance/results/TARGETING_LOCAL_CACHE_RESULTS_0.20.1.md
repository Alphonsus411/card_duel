# Resultados de la caché local de targeting 0.20.1

## Decisión

**GO** para conservar la optimización. La ruta pública
`STRESS_CONTROLLED legal_actions("A")` reduce su mediana un **69,44 %**, muy por
encima del objetivo del 10 %, y las 30 muestras alternadas mantienen una
separación clara. `MEDIUM` también mejora un 42,75 %. El pico adicional de
`tracemalloc` es 11.024 bytes (3,89 %) en STRESS y 6.080 bytes (2,11 %) en
MEDIUM: es pequeño en términos absolutos y coherente con el contexto efímero.

La llamada privada aislada `_legal_plays("A")` no crea el contexto local y, por
diseño, sus contadores son idénticos. Su diferencia de mediana (+2,82 %) se
considera ruido/deriva de una ruta cuyo código ejecutado es el mismo en ambos
SHAs; no contradice la mejora de la API optimizada, que crea y comparte el
contexto desde `legal_actions`.

## Versiones y aislamiento

- Baseline limpio: `baee1911d4963ce79cc72573bdbd075be9a79cdf`.
- Optimizado limpio: `8d71d44ba61f3858e5fb4545707d370822f9d4be` (incluye el cambio productivo
  `185962d2c135d0e1ac24d30aed8221f93263437c` y sus pruebas de paridad).
- Python: `3.12.13`, ejecutable compartido
  `/workspace/card_duel/.venv/bin/python`, GCC 13.3.0.
- uv: `uv 0.7.22`.
- Plataforma: `Linux-6.18.35-x86_64-with-glibc2.39`, afinidad CPU 0.
- Semilla: `benchmarks.fixtures.SCENARIO_SEED = 20260814`; límite: 128.
- Ambos worktrees quedaron en `detached HEAD`, sin salida de
  `git status --short`. Se usaron la misma máquina, intérprete, entorno y
  fixtures versionados.

## Protocolo

Para cada combinación caso/SHA se descartaron 5 warmups y se recogieron 30
mediciones. En cada ronda se invirtió el orden baseline/optimizado; la primera
versión también se contrabalanceó entre warmups y mediciones. Cada worker fijó
afinidad a CPU 0 y `PYTHONHASHSEED=20260814`.

El cronómetro (`perf_counter_ns`) rodeó **exclusivamente** una llamada al método
indicado. Construcción del fixture, serialización, SHA-256, comparaciones,
instrumentación, GC y `tracemalloc` quedaron fuera. Memoria y contadores se
midieron en procesos separados de los temporales. Antes de medir memoria se
ejecutó GC explícito, se inició `tracemalloc`, se hizo una llamada y se detuvo
antes de serializar.

En **cada repetición temporal** se comprobó entre SHAs: conteo, serialización
canónica completa (que implica tipo, contenido y orden), fingerprint SHA-256 y
estado canónico antes/después. Todas las comprobaciones pasaron. Los wrappers
temporales de los cuatro métodos aceptaron y reenviaron exactamente `*args` y
`**kwargs`, preservaron retornos/excepciones y se retiraron en `finally`.

## Tiempo

Valores en milisegundos. El porcentaje es `(optimizado / baseline - 1) × 100`;
un valor negativo es mejora.

| Caso | Métrica | Baseline | Optimizado | Cambio |
|---|---|---:|---:|---:|
| MEDIUM `legal_actions("A")` | mediana | 13,547 | 7,755 | **-42,75 %** |
| | media | 14,400 | 8,131 | -43,54 % |
| | p95 (nearest-rank) | 19,460 | 10,337 | -46,88 % |
| | desviación estándar muestral | 1,901 | 1,193 | -37,27 % |
| STRESS `legal_actions("A")` | mediana | 26,848 | 8,205 | **-69,44 %** |
| | media | 27,544 | 8,341 | -69,72 % |
| | p95 (nearest-rank) | 32,392 | 8,799 | -72,84 % |
| | desviación estándar muestral | 1,954 | 0,420 | -78,52 % |
| STRESS `_legal_plays("A")` | mediana | 18,700 | 19,227 | +2,82 % |
| | media | 19,249 | 19,967 | +3,73 % |
| | p95 (nearest-rank) | 22,779 | 25,586 | +12,32 % |
| | desviación estándar muestral | 1,423 | 2,024 | +42,25 % |

Las 180 observaciones crudas en nanosegundos, sin redondeo, están en
`benchmarks/results/targeting_local_cache.json`, agrupadas por caso y SHA bajo
`raw_ns`. El mismo artefacto contiene los estadísticos calculados, revisiones,
entorno y evidencia de validación; esta separación evita una tabla de 180 celdas
en este documento sin perder auditabilidad.

## Memoria

| Caso | Baseline peak | Optimizado peak | Cambio |
|---|---:|---:|---:|
| MEDIUM `legal_actions("A")` | 287.712 B | 293.792 B | +2,11 % (+6.080 B) |
| STRESS `legal_actions("A")` | 283.440 B | 294.464 B | +3,89 % (+11.024 B) |
| STRESS `_legal_plays("A")` | 190.208 B | 190.248 B | +0,02 % (+40 B) |

## Contadores separados

| Caso / SHA | `_definition` | `_effective_keywords` | `_continuous_effects_for` | `_card_can_be_targeted` |
|---|---:|---:|---:|---:|
| MEDIUM baseline | 5.749 | 270 | 272 | 270 |
| MEDIUM optimizado | 709 | 270 | 20 | 270 |
| STRESS legal actions baseline | 19.005 | 510 | 512 | 510 |
| STRESS legal actions optimizado | 1.869 | 510 | 36 | 510 |
| STRESS legal plays baseline | 13.847 | 374 | 374 | 374 |
| STRESS legal plays optimizado | 13.847 | 374 | 374 | 374 |

Los wrappers cuentan entradas al método. Por eso las entradas a
`_effective_keywords` y `_card_can_be_targeted` no bajan, mientras que el
trabajo interno caro (`_continuous_effects_for` y `_definition`) sí queda
amortizado por el contexto.

## Paridad observada

| Caso | Acciones/jugadas | Fingerprint de resultado | Fingerprint de estado |
|---|---:|---|---|
| MEDIUM `legal_actions` | 823 | `0e94cbf2783b9025832147d94d55cceff9da2b3815d05209517e08daaad3efc0` | `33468e0e7c517cb28932e3f9d38f0ffbc4d6d2660494c9be78cc7fa327599cd0` |
| STRESS `legal_actions` | 831 | `819f98ef64451c8177367e0be2ecab97dd33494b0e5417781c2f06011212e4ee` | `f04b31eb1b7b1a13020dfc3327236360e663a0c60ac38ec6610406625c0bcfed` |
| STRESS `_legal_plays` | 550 | `7091291e73bb72ba2d7265abf3cf222be51d9b41236db8d572339305bf4054fa` | `f04b31eb1b7b1a13020dfc3327236360e663a0c60ac38ec6610406625c0bcfed` |

## Comandos exactos

```bash
rm -rf /workspace/card_duel_baseline /workspace/card_duel_optimized
git worktree add --detach /workspace/card_duel_baseline baee1911d4963ce79cc72573bdbd075be9a79cdf
git worktree add --detach /workspace/card_duel_optimized 8d71d44ba61f3858e5fb4545707d370822f9d4be
git -C /workspace/card_duel_baseline status --short
git -C /workspace/card_duel_optimized status --short
.venv/bin/python benchmarks/benchmark_targeting_local_cache.py \
  --baseline /workspace/card_duel_baseline \
  --optimized /workspace/card_duel_optimized \
  --output benchmarks/results/targeting_local_cache.json
uv --version
uname -a
```

El controlador documentado es infraestructura conservable: reproduce las tres
consultas exactas, impide mezclar imports entre SHAs y falla inmediatamente ante
cualquier diferencia de paridad.
