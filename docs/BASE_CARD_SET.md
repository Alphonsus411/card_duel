# Microcolección base de cartas

## Propósito y alcance

La microcolección **base** es un corpus inicial, pequeño y trazable para validar
el recorrido de contenido de la Fase 2-A sobre capacidades que el motor ya
ofrece. Permite cotejar definiciones mecánicas, presentaciones editoriales,
manifiesto de colección y catálogo público sin inventar mecánicas ni ampliar el
alcance del producto.

| Propiedad | Valor |
| --- | --- |
| Identificador de colección (`set_id`) | `base` |
| Revisión | `1` |
| Tamaño | `8` cartas |
| Esquema de tokens | `BASE-001`…`BASE-008`, correlativo, explícito y estable |

Los tokens están declarados individualmente y no se derivan de la posición de
una carta. Reordenar el corpus, por tanto, no debe cambiar su identidad
editorial.

## Inventario canónico

`—` representa un conjunto vacío. Los nombres de enums y los identificadores de
keywords y subtipos se reproducen como datos mecánicos canónicos.

| `card_id` | Token | Nombre mecánico histórico | Nombre público español | Kind | Coste | Rank | Fuerza | Keywords | Subtipos |
| --- | --- | --- | --- | --- | ---: | --- | ---: | --- | --- |
| `base-c001` | `BASE-001` | Ember Initiate | Iniciado de la Brasa | `CREATURE` | 1 | `STANDARD` | 1 | — | `warrior` |
| `base-c002` | `BASE-002` | Grove Sentinel | Centinela de la Arboleda | `CREATURE` | 2 | `STANDARD` | 3 | — | `guardian` |
| `base-c003` | `BASE-003` | Skyline Duelist | Duelista del Horizonte | `CREATURE` | 3 | `STANDARD` | 2 | `CAN_CHALLENGE` | `warrior` |
| `base-c004` | `BASE-004` | Stoneback Warden | Guardián de Espalda Pétrea | `CREATURE` | 4 | `STANDARD` | 5 | — | `guardian` |
| `base-c005` | `BASE-005` | Ashen Vanguard | Vanguardia de Ceniza | `CREATURE` | 5 | `STANDARD` | 4 | — | `warrior` |
| `base-c006` | `BASE-006` | Verdant Colossus | Coloso Frondoso | `CREATURE` | 6 | `STANDARD` | 7 | — | `beast` |
| `base-c007` | `BASE-007` | First Arena Champion | Primer Campeón de la Arena | `CREATURE` | 7 | `STANDARD` | 6 | `CAN_CHALLENGE` | `warrior` |
| `base-c008` | `BASE-008` | Ancient Grove Keeper | Guardián de la Arboleda Ancestral | `CREATURE` | 8 | `STANDARD` | 9 | — | `guardian` |

## Correspondencia de nombres

La traducción afecta sólo al nombre visible de `CardPresentation`; el nombre
mecánico histórico de `CardDefinition` permanece estable.

| Inglés (mecánico histórico) | Español (público) |
| --- | --- |
| Ember Initiate | Iniciado de la Brasa |
| Grove Sentinel | Centinela de la Arboleda |
| Skyline Duelist | Duelista del Horizonte |
| Stoneback Warden | Guardián de Espalda Pétrea |
| Ashen Vanguard | Vanguardia de Ceniza |
| Verdant Colossus | Coloso Frondoso |
| First Arena Champion | Primer Campeón de la Arena |
| Ancient Grove Keeper | Guardián de la Arboleda Ancestral |

## Autoridad mecánica y separación editorial

`CardDefinition` es la **autoridad mecánica**. Sus valores declaran identidad,
tipo, coste, rank, Fuerza, keywords y subtipos consumidos por el motor; ninguna
fuente editorial puede sustituirlos ni modificarlos.

`CardPresentation` contiene **exclusivamente información editorial** y se enlaza
con su `CardDefinition` por `card_id`. El token, el nombre visible, el texto de
reglas y la referencia de arte sirven para publicación y presentación: no son
ejecutables y no determinan legalidad ni resolución. La validación exige
cobertura exacta entre ambos catálogos y mantiene separadas las dos fuentes.

## Revisión de gaps mecánicos

La evaluación completa se registra en
[`PHASE_2_MECHANICAL_GAPS.md`](PHASE_2_MECHANICAL_GAPS.md). No se encontraron
gaps mecánicos obligatorios para estas ocho cartas: las seis criaturas sin
keywords usan estadísticas ordinarias y `BASE-003` y `BASE-007` sólo requieren
`CAN_CHALLENGE`, una capacidad declarativa general que ya existe. En
consecuencia, la microcolección no solicita efectos, resolutores, persistencia ni
ramas de comportamiento nuevas, y prohíbe cualquier solución específica por
`card_id`.

## Limitaciones deliberadas

Este corpus de Fase 2-A se cierra deliberadamente:

- **sin arte final:** todas las presentaciones conservan literalmente `art=""`;
- **sin balance competitivo:** los costes y Fuerzas sirven para validar el
  recorrido de contenido, no constituyen una declaración de equilibrio;
- **sin colección completa:** ocho cartas forman una microcolección, no el
  catálogo final del producto;
- **sin deck builder:** la construcción y experiencia de mazos quedan fuera de
  este entregable;
- **sin UI:** no se crea ni anticipa ninguna interfaz;
- **sin lógica específica por carta:** no existen ni se permiten condicionales
  de comportamiento basados en `card_id`.
