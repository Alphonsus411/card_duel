# CAP-TAXONOMY-001 T1 — inventario de representación

**Fecha:** 2026-10-25
**Estado:** T1 completada; habilita únicamente T2 (modelo mínimo versionado)
**Límite:** inventario y caracterización; no cambia modelos, catálogos ni reglas.

## Autoridad actual por dimensión

| Dimensión | Escritura/autorización | Lecturas mecánicas | Persistencia y proyección |
| --- | --- | --- | --- |
| Tipo funcional | `CardDefinition.kind` en `domain/models.py`; sets de contenido. | `CardFilter.matches`; juego de cartas, Equipo, criatura efectiva, efectos continuos y pila. | Codec de dataclasses/enum; catálogo incluido en snapshot/replay; `PublicCard.kind`. |
| Rango | `CardDefinition.rank`; constructor de mazo. | `CardFilter.matches`; límite de copias, pila de efectos legendarios e inmunidad Divina. | Codec; catálogo de snapshot/replay; `PublicCard.rank`. |
| Dominio de Señor | `CardDefinition.lord_domain`, validado para `CardKind.LORD`. | Elegibilidad de Señor, Fuerza, acciones basadas en estado y Desafío de Reinos (`CombatManager`). | Codec; catálogo de snapshot/replay. **No se proyecta hoy en `PublicCard`.** |
| Subtipo | `CardDefinition.subtypes` como `frozenset[str]`; contenido, parches y efectos continuos. | `CardFilter.matches` por intersección; efectos continuos por intersección; búsquedas existentes. | Codec con orden canónico de `frozenset`; catálogo de snapshot/replay; `PublicCard.subtypes` ordenado. |
| Identidad | `CardDefinition.card_id`, `CardInstance.definition_id` y override de definición. | Catálogo, instancia, transformaciones/copias, límites de copias y el predicado histórico `CardFilter.definition_ids`. | Referencia estable en estado, catálogos, manifest, snapshot/replay y `PublicCard.card_id`. |

## Rutas localizadas

| Superficie | Referencias | Observación contractual |
| --- | --- | --- |
| Modelo y validación | `domain/models.py`: `CardDefinition`, `CardFilter`, `CardInstance`. | `kind`, `rank`, dominio y subtipo son campos separados; `CardFilter` combina sus cuatro predicados actuales mediante AND y subtipos mediante intersección no vacía. |
| Catálogo y contenido | `catalog.py`, `content/base_set.py`, `content/mythic_set.py`, `content/registry.py`. | El catálogo indexa identidad; los manifests conservan procedencia. No hay registro canónico de alias. |
| Motor | `engine/game.py`, `engine/combat.py`, `engine/stack.py`, `engine/actions.py`, `engine/effects.py`. | Tipo, rango, dominio y subtipo ya alimentan reglas distintas. Ninguna de estas lecturas autoriza inferir una dimensión desde otra. |
| Persistencia | `persistence/codec.py`, `snapshot.py`, `replay.py`, `migrations.py`. | Codec enum/dataclass; snapshot y replay incluyen el catálogo completo. Cualquier cambio de campo de `CardDefinition` será fundacional y versionado. |
| Proyección | `public_catalog.py`, `presentation.py`. | Proyecta identidad, tipo, rango y subtipos; no dominio de Señor. La ausencia es un hecho de T1, no permiso para calcularlo del nombre o texto. |
| Pruebas | `test_taxonomy_vocabulary_regressions.py`, `test_public_card_catalog.py`, `test_base_set_content.py`, `test_synthetic_lord_rules.py`. | Cubrían literalidad de aliases, orden público, contenido y conducta de Señores; T1 añade caracterización conjunta de filtro y round-trip. |

## Caracterización añadida

`tests/test_taxonomy_t1_characterization.py` fija que:

1. un filtro combina tipo, rango, subtipo e identidad sin convertir una
   coincidencia de subtipo en coincidencia exacta;
2. codec y catálogo de snapshot conservan separadamente tipo, rango, dominio,
   subtipos e identidad;
3. la proyección pública actual conserva identidad/tipo/rango/subtipos y no
   fabrica ni expone un dominio ausente del DTO.

## Brechas confirmadas, no resueltas

- `CardFilter` aún no filtra dominio, keyword, controlador, zona, visibilidad,
  cardinalidad ni coincidencia exacta de subtipo: pertenece a `CAP-TARGET-002`.
- `lord_domain` no está presente en `PublicCard`; T2 deberá decidir si una
  proyección versionada es imprescindible, sin tratar este inventario como
  autorización automática.
- Tipos impresos múltiples, Leyenda autónoma y tipos fuente ausentes continúan
  bloqueados en `CAP-TAXONOMY-002`.
- Alias, grafía canónica y procedencia de subtipo continúan para
  `CAP-TAXONOMY-003`; T1 no fusiona `Pixy`/`Pixie`.
- `definition_ids` sigue siendo deuda de selector histórico y no habilita
  handlers, legalidad o reglas especiales por carta.

## Puerta de T1

Las cinco dimensiones y sus superficies observables están localizadas. T2 debe
proponer un modelo mínimo únicamente para significado inequívoco y detenerse si
requiere una de las brechas anteriores.
