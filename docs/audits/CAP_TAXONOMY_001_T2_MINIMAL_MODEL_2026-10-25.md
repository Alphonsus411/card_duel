# CAP-TAXONOMY-001 T2 — modelo mínimo de dimensiones

**Fecha:** 2026-10-25
**Estado:** T2 completada; no habilita cambio de esquema
**Decisión:** no se modifica la forma persistida.

## Resultado de la revisión

El inventario T1 confirmó que `CardDefinition` ya conserva separadamente tipo,
rango, dominio, subtipos e identidad. Durante T2 se comprobó que el baseline
acreditado usa dos formas para un Señor:

- `CardKind.LORD + lord_domain`;
- `CardKind.CREATURE + lord_domain`.

La segunda forma participa en reglas Mítica de Fuerza, efectos continuos y
Desafío. Rechazarla, o migrarla sin fuente adicional, rompería comportamiento
existente y convertiría en decisión técnica la ambigüedad de tipos impresos
múltiples que pertenece a `CAP-TAXONOMY-002`.

Por decisión explícita, T2 preserva ambas formas. `lord_domain` es el marcador
actual de Señor; `CardKind` conserva el tipo funcional ya acreditado. Ninguna
forma implica ni reemplaza la otra.

## Consecuencias de modelo

No se añade enum, campo, alias, tipo compuesto, rol, selector ni API pública.
Tampoco se endurece una validación que excluya la forma `CREATURE +
lord_domain`. Un cambio así requeriría antes resolver normativamente los tipos
impresos múltiples y planificar una migración propia.

No hay modificación de snapshot/replay/codec, por lo que T3 debe limitarse a
verificar y documentar que esta decisión conserva las rutas de persistencia
existentes; no puede crear una versión nueva sin cambio de forma.

## Evidencia

`tests/test_taxonomy_t2_minimal_model.py` fija ambas formas válidas. Las suites
Mítica y de Señores siguen siendo la evidencia funcional de que la forma
`CREATURE + lord_domain` no es un dato muerto.

## Límites mantenidos

- No se representa Leyenda autónoma ni tipos impresos múltiples.
- No se infiere tipo desde dominio, nombre, texto, arte o `card_id`.
- No se añaden filtros por dominio ni se proyecta dominio en `PublicCard`.
- `CAP-TAXONOMY-001` continúa `PARTIAL / READY`.
