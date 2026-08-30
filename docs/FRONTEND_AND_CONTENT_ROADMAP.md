# Roadmap de frontend y contenido

## Estado general

**Fase 1: IN PROGRESS**

La fase global permanece abierta aunque sus dos primeros incrementos estén
completos. Los estados registrados son:

| Incremento | Estado | Resultado |
| --- | --- | --- |
| Fase 1-A | **COMPLETE** | Metadatos editoriales separados de la definición mecánica. |
| Fase 1-B | **COMPLETE** | Proyección pública, segura e inmutable para UI. |

## Principio de arquitectura

`CardDefinition = mechanical truth`, `CardPresentation = editorial/display metadata` y `PublicCard = safe UI projection`.

Esta separación evita que una interfaz o una revisión editorial modifiquen el
comportamiento autoritativo del motor:

1. `CardDefinition` determina la validación y resolución mecánicas.
2. `CardPresentation` mantiene nombre, token, arte y texto destinados a las
   personas usuarias.
3. `PublicCard` proyecta de forma segura los datos necesarios para mostrarlos,
   sin exponer objetos internos como contrato de UI.

En particular, `rules_text` es exclusivamente humano/editorial y nunca
interviene en la resolución de reglas. No es una entrada del motor y no se
interpreta como lógica ejecutable.

## Fase 1-A: COMPLETE

Se completó el límite de contenido editorial:

- modelo `CardPresentation` independiente;
- asociación explícita y única mediante `card_id`;
- validación de los metadatos de presentación;
- snapshots defensivos y recorrido determinista.

## Fase 1-B: COMPLETE

Se completó el límite público para UI:

- modelo `PublicCard` inmutable;
- construcción determinista desde mecánica y presentación;
- rechazo de asociaciones incompletas, duplicadas o huérfanas;
- serialización de una proyección segura;
- comprobación de que las variantes editoriales no cambian la mecánica.

## Criterio de seguimiento

Los hitos 1-A y 1-B se consideran cerrados por separado. Este registro no
amplía su alcance ni declara terminada la fase superior: **Fase 1: IN
PROGRESS**.
