# CAP-TAXONOMY-001 T6 — cierre documental y compatibilidad

**Fecha:** 2026-10-25
**Estado:** incremento T0–T6 cerrado; capability global `PARTIAL / CLOSED`

## Resultado de la entrega

El incremento cierra el gate de las dimensiones ya representadas por
`CardDefinition`: `CardKind`, `CardRank`, `LordDomain`, `subtypes` e identidad
por `definition_id`. El cierre permite a los dependientes asumir estas
dimensiones como contrato técnico existente; no autoriza a completar su
semántica normativa ni a ingerir el corpus pendiente.

| Superficie | Contrato cerrado | Compatibilidad |
| --- | --- | --- |
| Modelo | `CardKind` y `LordDomain` permanecen ejes independientes; se preservan `LORD + dominio` y `CREATURE + dominio`. | No se añade campo, enum ni tipo compuesto. |
| Codec | Enums y campos tipados se codifican por separado. | Valores futuros o forma incompatible se rechazan; no hay fallback. |
| Snapshot y replay | La forma actual conserva ambas representaciones. | Se mantienen snapshot v5 y replay v4; artefactos v1/v2 siguen legibles sin completar dominios ausentes. |
| Filtros | `CardFilter` conserva tipo, rango, subtipo e identidad. | No se incorpora selector por dominio. |
| JSON público | `PublicCard` proyecta el tipo acreditado. | No añade ni infiere `lord_domain`. |

## Evidencia de fases

| Fase | Evidencia | Estado |
| --- | --- | --- |
| T0 | Contrato de ejes independientes y exclusiones. | Cerrada |
| T1 | Inventario y caracterización de modelo, codec, filtros y proyección. | Cerrada |
| T2 | Conservación de las dos formas acreditadas de Señor. | Cerrada |
| T3 | Snapshot/replay sin cambio de schema. | Cerrada |
| T4 | Consumidores sin inferencia ni expansión de API. | Cerrada |
| T5 | Matriz positiva, negativa, de legado y determinismo. | Cerrada |

## Estado y límites

`CLOSED` corresponde al gate de este incremento: sus dependientes ya no deben
duplicar ni reinventar sus dimensiones básicas. `PARTIAL` sigue describiendo la
capability global y prohíbe presentarla como taxonomía completa.

Permanecen fuera de alcance y requieren trabajo independiente:

- Leyenda autónoma y tipos impresos múltiples (`CAP-TAXONOMY-002`,
  `NORM-BLOCKED`);
- aliases, vocabulario y procedencia de subtipos (`CAP-TAXONOMY-003`);
- selectores multidimensionales y filtros por dominio (`CAP-TARGET-002`);
- exposición pública de dominio, creación/reclasificación del corpus y reglas
  específicas por `card_id`.

Por tanto, este cierre no promueve cartas ni habilita defaults, inferencias
desde texto/nombre/identidad, ni migraciones taxonómicas silenciosas.
