# CAP-EFFECT-001 — E2: modelo mínimo de extensión

**Fecha:** 2026-10-26
**Estado de la fase:** completada; decisión de diseño sin cambio de runtime
**Capability:** `CAP-EFFECT-001` permanece `PARTIAL / READY`.

## Decisión

No se añadirá un nuevo miembro a `EffectKind` en este incremento. El inventario
de E1 y el contraste del corpus no prueban una operación atómica nueva con
semántica independiente y prerrequisitos cerrados. Las 23 primitivas actuales
cubren el vocabulario atómico ya implementado; añadir una etiqueta para ocultar
elección, secuencia, orden de zona o estado continuo produciría una API falsa y
adelantaría capabilities que siguen abiertas.

El modelo de extensión mínimo conserva cuatro elementos ya presentes:

| Elemento | Autoridad | Regla de extensión |
| --- | --- | --- |
| Discriminador | `EffectKind` | cerrado, tipado y estable; nunca `card_id`, texto editorial ni cadena libre |
| Declaración | `EffectDefinition` | valida payload, target, duración y campos exclusivos del discriminador |
| Contexto congelado | `StackItem` | conserva fuente, objetivos, X y perfil de fuente al apilar; la resolución revalida estado actual |
| Resolución | `StackManager` y `EffectManager` | una primitiva delega sólo en autoridades existentes; los casos pausables conservan continuación explícita |

`PendingSearch(next_effect_index=...)` sigue siendo una continuación específica
de búsqueda. No se generaliza como máquina de estados de efectos: hacerlo
introduciría `CAP-EFFECT-003` y `CAP-SECRET-002` sin sus gates.

## Clasificación de huecos encontrada

| Hueco observado | Decisión | Capability propietaria |
| --- | --- | --- |
| Secuencias, condiciones, repetición, ramas y valores capturados | no es una primitiva atómica | `CAP-EFFECT-003` |
| Colocar en fondo/cima, reordenar o seleccionar cartas ocultas | exige posición, elección persistible y audiencia | `CAP-SEARCH-003`, `CAP-SECRET-002`, `CAP-ZONE-003` |
| Crear fichas o instancias en resolución | crea identidad y movimiento atómico | `CAP-EFFECT-004` |
| Descarte forzado con elector | requiere elección autorizada y visibilidad | `CAP-EFFECT-005`, `CAP-SECRET-002` |
| Prevención por causa, fuente o duración general | altera el dominio de prevención e inmunidad | `CAP-DAMAGE-002`, `CAP-IMMUNITY-001` |
| Conceder/retirar comportamiento o estado persistente general | exige layers, procedencia y limpieza | `CAP-EFFECT-002`, `CAP-KEYWORD-001/002` |

Ninguna fila se reetiqueta como soportada por esta decisión. El corpus sólo podrá
usar una primitiva cuando todos sus demás campos de coste, target, duración,
visibilidad, trigger y composición ya estén acreditados.

## Reglas para una futura primitiva

Una propuesta posterior deberá demostrar, antes de editar código, que:

1. su semántica es atómica y no se expresa como composición o especialización;
2. sus targets, duración, fuente y audiencia están completamente definidos por
   capabilities cerradas;
3. no necesita orden, elección o posición persistible aún no disponible;
4. tiene ruta completa declaración → pila → revalidación → resolución →
   snapshot/replay, con migración si modifica representación persistida;
5. añade tests negativos de fizzle/rollback y no usa dispatch por identidad de
   carta.

## Salida de E2

E3 caracterizará en pruebas el cierre del registro actual: cada `EffectKind`
deberá tener una categoría declarativa, validación de forma y handler asociado,
y los huecos anteriores deberán continuar rechazados o fuera de alcance. E3 no
añadirá schema, eventos públicos ni primitivas nuevas. Cualquier propuesta que
incumpla esta frontera vuelve a su capability propietaria.
