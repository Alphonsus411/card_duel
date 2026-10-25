# CAP-TAXONOMY-001 T4 — consumidores autorizados

**Fecha:** 2026-10-25
**Estado:** T4 completada; no habilita selectores ni API nuevos
**Decisión:** los consumidores conservan las dimensiones que ya exponen.

## Filtro de dominio

`CardFilter` permanece limitado a `kinds`, `ranks`, `subtypes` e identidad por
`definition_ids`. No incorpora `lord_domain`: convertir dominio en selector
ampliaría el contrato de targeting y corresponde a `CAP-TARGET-002` después del
cierre de esta capability.

La caracterización T4 prueba que las dos formas acreditadas siguen distintas al
filtrar por tipo:

- `CardKind.LORD + LordDomain.REALMS` coincide sólo con `CardKind.LORD`;
- `CardKind.CREATURE + LordDomain.ABYSS` coincide sólo con
  `CardKind.CREATURE`.

Por tanto, un dominio no reescribe ni deduce `CardKind`.

## Proyección pública

`PublicCard` conserva el `kind` mecánico serializado como texto estable. Para
las dos formas, la proyección resulta respectivamente `"lord"` y `"creature"`.
`lord_domain` no se proyecta y tampoco se infiere desde el nombre, la identidad
o la presentación editorial.

Exponerlo requeriría contrato de audiencia, compatibilidad JSON y casos de uso
autorizados; T4 no los inventa.

## Límites mantenidos

- No se modifica código de producción ni la forma del JSON público.
- No se introducen filtros por dominio, aliases o tipos compuestos.
- No se mezclan selección por identidad con familia taxonómica.
- `CAP-TAXONOMY-001` permanece `PARTIAL / READY`.
