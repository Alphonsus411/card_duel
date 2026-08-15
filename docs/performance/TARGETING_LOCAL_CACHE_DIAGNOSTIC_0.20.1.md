# Diagnóstico de caché local de targeting 0.20.1

## Estado inicial

Salida literal de `git status --short`:

```text
```

Salida literal de `git rev-parse HEAD`:

```text
0083c833fac7a138b892f21c1934ba98b03358f6
```

La salida vacía del primer bloque es significativa: el árbol estaba limpio. La
rama `perf/local-targeting-context` se creó directamente desde el SHA anterior.

## Objetivo y protocolo

Este diagnóstico comprueba si, **sólo durante una invocación de**
`legal_actions("A")`, existe repetición suficiente para justificar un contexto
local de consultas. No mide todavía el beneficio temporal de una caché ni
autoriza una caché persistente.

Se construyó un motor nuevo y determinista con `build_scenario`, semántica
`CURRENT` y `legal_action_enumeration_limit=128` para cada uno de `MEDIUM` y
`STRESS_CONTROLLED`. Después de construir el fixture (fuera del conteo), se hizo
exactamente una llamada medida a `engine.legal_actions("A")` por escenario.

La instrumentación temporal sustituyó en tiempo de ejecución los cuatro métodos
definidos en `src/card_duel_engine/engine/game.py` —`_definition`,
`_effective_keywords`, `_continuous_effects_for` y `_card_can_be_targeted`— por
wrappers que conservaron argumentos, retorno y excepciones. Cada wrapper contó
por escenario, método, `card_id` y rama activa de la pila. El bloque `finally`
restauró los cuatro métodos originales; el script temporal se eliminó. Por tanto,
**no queda instrumentación ni modificación de producto** en el árbol final.

Para evitar doble atribución, la clasificación usa esta prioridad cuando hay
ramas anidadas: `_allocation_selections` > `_legal_ability_activations` >
`_legal_plays` > `other_enumeration`. Así, una allocation solicitada desde una
jugada figura como trabajo de allocation y no también como trabajo de la jugada.

## Resultados

La llamada produjo 823 comandos en `MEDIUM` y 831 en `STRESS_CONTROLLED`.

### Totales y separación por origen

| Escenario | Método | Total | `_legal_plays` | `_legal_ability_activations` | `_allocation_selections` | Otras ramas |
|---|---|---:|---:|---:|---:|---:|
| MEDIUM | `_definition` | 5,749 | 3,411 | 816 | 1,512 | 10 |
| MEDIUM | `_effective_keywords` | 270 | 162 | 36 | 72 | 0 |
| MEDIUM | `_continuous_effects_for` | 272 | 162 | 38 | 72 | 0 |
| MEDIUM | `_card_can_be_targeted` | 270 | 162 | 36 | 72 | 0 |
| STRESS_CONTROLLED | `_definition` | 19,005 | 11,331 | 2,624 | 5,032 | 18 |
| STRESS_CONTROLLED | `_effective_keywords` | 510 | 306 | 68 | 136 | 0 |
| STRESS_CONTROLLED | `_continuous_effects_for` | 512 | 306 | 70 | 136 | 0 |
| STRESS_CONTROLLED | `_card_can_be_targeted` | 510 | 306 | 68 | 136 | 0 |

La diferencia de dos llamadas entre `_continuous_effects_for` y las otras dos
consultas de targeting procede de consultas adicionales de fuerza al enumerar
habilidades para `card-000008` y `card-000009`; no pasa por
`_card_can_be_targeted`.

### Agrupación completa por `card_id`

Para mantener el registro auditable sin repetir cientos de filas idénticas, la
notación `N × {ids}` significa **N llamadas para cada id enumerado**. Las listas
son exhaustivas.

Definimos los conjuntos observados:

- `M18` = {`card-000008`, `card-000009`, `card-000010`, `card-000012`,
  `card-000014`, `card-000016`, `card-000018`, `card-000020`, `card-000022`,
  `card-000024`, `card-000027`, `card-000029`, `card-000031`, `card-000033`,
  `card-000035`, `card-000037`, `card-000039`, `card-000041`}.
- `M16` = `M18` sin {`card-000008`, `card-000009`}.
- `M10` = {`card-000008`, `card-000009`, `card-000010`, `card-000012`,
  `card-000014`, `card-000016`, `card-000018`, `card-000020`, `card-000022`,
  `card-000024`}.
- `M8a` = {`card-000010`, `card-000012`, `card-000014`, `card-000016`,
  `card-000018`, `card-000020`, `card-000022`, `card-000024`}; `M8b` =
  {`card-000027`, `card-000029`, `card-000031`, `card-000033`, `card-000035`,
  `card-000037`, `card-000039`, `card-000041`}.
- `MH9` = {`card-000001`, `card-000002`, `card-000003`, `card-000004`,
  `card-000005`, `card-000006`, `card-000007`, `card-000011`, `card-000017`}.
- `S34` = {`card-000008`, `card-000009`, `card-000010`, `card-000012`,
  `card-000014`, `card-000016`, `card-000018`, `card-000020`, `card-000022`,
  `card-000024`, `card-000026`, `card-000028`, `card-000030`, `card-000032`,
  `card-000034`, `card-000036`, `card-000038`, `card-000040`, `card-000043`,
  `card-000045`, `card-000047`, `card-000049`, `card-000051`, `card-000053`,
  `card-000055`, `card-000057`, `card-000059`, `card-000061`, `card-000063`,
  `card-000065`, `card-000067`, `card-000069`, `card-000071`, `card-000073`}.
- `S32` = `S34` sin {`card-000008`, `card-000009`}; `S18` = los primeros 18
  ids de `S34` (de `card-000008` a `card-000040`); `S16a` = `S18` sin
  {`card-000008`, `card-000009`}; `S16b` = los últimos 16 ids de `S34`
  (de `card-000043` a `card-000073`).
- `SH9` = {`card-000001`, `card-000002`, `card-000003`, `card-000004`,
  `card-000005`, `card-000006`, `card-000007`, `card-000033`, `card-000039`}.

#### MEDIUM

| Método/origen | Llamadas por `card_id` (exhaustivo) |
|---|---|
| `_card_can_be_targeted`, total | 15 × `M18` |
| ↳ `_legal_plays` / habilidades / allocations | 9 × `M18` / 2 × `M18` / 4 × `M18` |
| `_effective_keywords`, total | 15 × `M18` |
| ↳ `_legal_plays` / habilidades / allocations | 9 × `M18` / 2 × `M18` / 4 × `M18` |
| `_continuous_effects_for`, total | 16 × {`card-000008`, `card-000009`}; 15 × `M16` |
| ↳ `_legal_plays` | 9 × `M18` |
| ↳ habilidades | 3 × {`card-000008`, `card-000009`}; 2 × `M16` |
| ↳ allocations | 4 × `M18` |
| `_definition`, total | 1 × `MH9`; 322 × {`card-000008`, `card-000009`}; 320 × `M8a`; 317 × `M8b` |
| ↳ `_legal_plays` | 1 × `MH9`; 189 × `M18` |
| ↳ habilidades | 48 × {`card-000008`, `card-000009`}; 46 × `M8a`; 44 × `M8b` |
| ↳ allocations | 84 × `M18` |
| ↳ otras ramas | 1 × `M10` |

#### STRESS_CONTROLLED

| Método/origen | Llamadas por `card_id` (exhaustivo) |
|---|---|
| `_card_can_be_targeted`, total | 15 × `S34` |
| ↳ `_legal_plays` / habilidades / allocations | 9 × `S34` / 2 × `S34` / 4 × `S34` |
| `_effective_keywords`, total | 15 × `S34` |
| ↳ `_legal_plays` / habilidades / allocations | 9 × `S34` / 2 × `S34` / 4 × `S34` |
| `_continuous_effects_for`, total | 16 × {`card-000008`, `card-000009`}; 15 × `S32` |
| ↳ `_legal_plays` | 9 × `S34` |
| ↳ habilidades | 3 × {`card-000008`, `card-000009`}; 2 × `S32` |
| ↳ allocations | 4 × `S34` |
| `_definition`, total | 1 × `SH9`; 562 × {`card-000008`, `card-000009`}; 560 × `S16a`; 557 × `S16b` |
| ↳ `_legal_plays` | 1 × `SH9`; 333 × `S34` |
| ↳ habilidades | 80 × {`card-000008`, `card-000009`}; 78 × `S16a`; 76 × `S16b` |
| ↳ allocations | 148 × `S34` |
| ↳ otras ramas | 1 × `S18` |

## Pureza de la consulta

Antes y después de cada única llamada se calculó
`canonical_json(encode_value(engine.state))` mediante el helper
`benchmarks.fixtures.canonical_state`. La igualdad se comprobó sobre el texto
canónico completo, no sólo sobre el hash; los SHA-256 se incluyen como evidencia
compacta:

| Escenario | Bytes/caracteres canónicos | SHA-256 antes | SHA-256 después | Igualdad |
|---|---:|---|---|---|
| MEDIUM | 29,434 | `33468e0e7c517cb28932e3f9d38f0ffbc4d6d2660494c9be78cc7fa327599cd0` | `33468e0e7c517cb28932e3f9d38f0ffbc4d6d2660494c9be78cc7fa327599cd0` | sí |
| STRESS_CONTROLLED | 49,450 | `f04b31eb1b7a13020dfc3327236360e663a0c60ac38ec6610406625c0bcfed` | `f04b31eb1b7a13020dfc3327236360e663a0c60ac38ec6610406625c0bcfed` | sí |

La instrumentación y la enumeración no mutaron el `GameState` observable.

## Recorrido observado

1. `GameEngine.legal_actions` delega en `LegalActionEnumerator.legal_actions`.
2. La enumeración general consulta definiciones para clasificar permanentes y
   después entra en `_legal_plays` y `_legal_ability_activations`.
3. Ambas ramas recorren repetidamente los mismos permanentes. La elegibilidad
   llama `_card_can_be_targeted` → `_effective_keywords` →
   `_continuous_effects_for`.
4. `_continuous_effects_for` vuelve a resolver la definición del objetivo y
   recorre todas las cartas para localizar fuentes en battlefield, resolviendo
   sus definiciones. Esto explica que `_definition` crezca de 5,749 a 19,005
   aunque las consultas de targeting sólo crezcan de 270 a 510.
5. Los efectos distribuidos entran en `_allocation_selections`, que vuelve a
   filtrar los mismos permanentes. Con la atribución exclusiva elegida representa
   1,512/5,749 definiciones en MEDIUM y 5,032/19,005 en STRESS.

El patrón uniforme (15 consultas de targeting por permanente: 9 jugadas, 2
habilidades y 4 allocations) muestra reutilización real dentro de una sola
enumeración y un límite natural de vida para el contexto.

## Riesgos de invalidación

- `_definition` depende del `definition_id`/override de la instancia, del
  catálogo y de todos los `text_patches` dirigidos a esa carta.
- `_effective_keywords` depende además de zona, controlador, attachments y de
  todas las fuentes y definiciones de efectos continuos en battlefield.
- `_continuous_effects_for` depende de zona/controlador del objetivo y fuentes,
  `affected_kinds`, subtipos, conversión efectiva a criatura y exclusión de la
  propia fuente. Esa conversión puede encadenar más consultas.
- `_card_can_be_targeted` incorpora el tipo de la fuente, `from_ability` y
  `source_card_id`; almacenar sólo por objetivo sería incorrecto para su
  resultado booleano.
- Comandos, resolución de stack, cambios de zona/control, text patches, equipo y
  efectos basados en estado invalidan datos. Una caché que sobreviva a
  `legal_actions` necesitaría versionado/invalidation exhaustivo y queda fuera
  de alcance.
- Los iteradores de `_continuous_effects_for` no deben cachearse como generadores
  consumibles; si se materializa, debe preservarse exactamente el orden estable.
- El contexto no puede alterar truncamiento, orden de comandos, semántica
  `LEGACY_019`, identidad relevante de definiciones ni propagación de errores.

## Alcance permitido para el cambio productivo posterior

Se permite investigar un contexto **privado, efímero y por invocación** creado al
entrar en `legal_actions` y descartado al salir, incluso ante una excepción. Sólo
podrá reutilizar resultados de consultas puras con claves completas; deberá
preservar API, comandos y orden, y demostrar paridad en CURRENT y LEGACY_019.
No se permite cachear entre invocaciones, añadir estado serializable a
`GameState`, introducir invalidación global, cambiar reglas, fixtures o límites,
ni conservar contadores/logging de diagnóstico.

## Decisión preliminar

**GO, condicionado, para un prototipo de caché local por llamada; NO-GO para una
caché persistente o para integrar sin medición de paridad y rendimiento.**

La repetición por id es alta y determinista, especialmente las 19,005 consultas
de definición en STRESS. El siguiente cambio debe demostrar: (1) estado canónico
idéntico; (2) tuple de acciones idéntica y en el mismo orden para ambos perfiles
y semánticas; (3) ausencia de fuga del contexto tras retorno/excepción; y (4)
mejora neta reproducible frente al coste de claves/materialización. Este
documento por sí solo no afirma todavía un porcentaje de aceleración.

## Trazabilidad de cierre del cambio autorizado

La comparación cerrada usada para aceptar la única optimización es:

- SHA baseline: `baee1911d4963ce79cc72573bdbd075be9a79cdf`.
- SHA optimizado: `8d71d44ba61f3858e5fb4545707d370822f9d4be`.
- Versión antes y después: `0.20.1`; `pyproject.toml` y `uv.lock` no aparecen
  en la comparación y no se modificó la versión.

Salida exacta de `git diff --stat baee1911d4963ce79cc72573bdbd075be9a79cdf..8d71d44ba61f3858e5fb4545707d370822f9d4be`:

```text
 src/card_duel_engine/engine/actions.py     |  46 ++++-
 src/card_duel_engine/engine/game.py        | 107 ++++++++---
 src/card_duel_engine/engine/options.py     |  10 +-
 tests/test_targeting_local_cache_parity.py | 286 +++++++++++++++++++++++++++++
 4 files changed, 416 insertions(+), 33 deletions(-)
```

Lista exacta de archivos modificados entre esos SHAs:

```text
src/card_duel_engine/engine/actions.py
src/card_duel_engine/engine/game.py
src/card_duel_engine/engine/options.py
tests/test_targeting_local_cache_parity.py
```

Por inspección de esa lista y del diff, se confirma explícitamente que snapshots,
replay, persistencia, `GameState`, `PhaseManager`, algoritmos combinatorios,
`deepcopy`, los dos PDF y la versión **no aparecen en el diff**. El diseño y la
razón del GO final se detallan en
`TARGETING_LOCAL_CACHE_OPTIMIZATION_0.20.1.md`; no se abrió otra candidata.
