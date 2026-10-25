# CAP-TAXONOMY-001 T0 — contrato de dimensiones canónicas

**Fecha:** 2026-10-25
**Estado:** T0 completada; habilita únicamente T1 (inventario de representación)
**Capability:** `CAP-TAXONOMY-001` permanece `PARTIAL / READY`

## Propósito del incremento

La primera capability transversal desbloqueada después de
`CAP-DAMAGE-002` es separar de forma estable las dimensiones mecánicas que ya
acredita la fuente: tipo funcional, rango, dominio de Señor, subtipo e
identidad. El trabajo no convierte el inventario documental en catálogo de 431
cartas ni completa selectores, keywords o reglas de combate.

La fuente autoritativa de significado sigue siendo
`CANONICAL_TAXONOMY.md` junto con los PDF Base–Mítica. Este contrato no resuelve
los silencios de `Leyenda`, tipos impresos múltiples ni tokens cuyo tipo original
no aparece en la fuente.

## Decisiones cerradas

1. **Dimensiones independientes.** `CardKind`, `CardRank`, `LordDomain`,
   `subtypes` e identidad por `definition_id` representan ejes distintos. La
   coincidencia de una palabra no autoriza a moverla entre ejes. En el baseline,
   `lord_domain` identifica un Señor tanto con `CardKind.LORD` como con la forma
   ya acreditada `CardKind.CREATURE + lord_domain`; T0 no colapsa esas formas.
2. **Identidad no es taxonomía.** `definition_id` conserva catálogo,
   persistencia, límites de copias y presentación; no se amplía como dispatch
   de reglas ni como sustituto de un selector taxonómico.
3. **Literalidad conservadora.** Un subtipo conserva su grafía y procedencia.
   `Pixy` y `Pixie` siguen siendo distintos hasta contar con una autoridad que
   autorice un alias; nombre, arte, edición, bloque temático o `card_id` no
   permiten inferir ninguno.
4. **No inventar dimensiones.** No se introducen `Race`, `Class`, `Family`,
   `Category`, facción ni una taxonomía de keywords para acomodar lenguaje
   editorial o capacidades impresas.
5. **Ausencia de fuente es ausencia de dato.** `Leyenda` autónoma, tipos
   impresos múltiples y el tipo original de Token Legendario/Divino permanecen
   documentados como no representables o bloqueados; ninguna migración los
   completa por heurística.
6. **Separar filtro de contexto.** Tipo/rango/dominio/subtipo describen una
   definición. Controlador, propietario, zona, visibilidad, elector y
   cardinalidad pertenecen a futuras capabilities de targeting, zonas y
   elecciones; T0 no los incorpora a `CardFilter`.

## Secuencia autorizada

| Fase | Entregable | Puerta de salida |
| --- | --- | --- |
| T0 — Contrato | Este documento y casos de aceptación. | No queda una dimensión implícita ni una inferencia autorizada. |
| T1 — Inventario | Mapa de cada lectura/escritura/proyección de las cinco dimensiones actuales. | Todas las superficies persistentes y sus pruebas de caracterización quedan localizadas. |
| T2 — Modelo mínimo | Propuesta versionada para representar sólo las dimensiones con significado inequívoco. | No introduce valores libres, aliases ni tipo múltiple por defecto. |
| T3 — Persistencia | Versión, migración y rechazo cerrado si T2 cambia estado serializado. | Legado conserva exactamente las dimensiones que ya tenía. |
| T4 — Consumidores | Adaptación mínima de filtros/proyecciones autorizados. | Ningún selector infiere dimensión desde identidad o texto libre. |
| T5 — Verificación | Matriz de positivo, negativo, legado, snapshot y replay. | Determinismo y rechazo cerrado acreditados. |
| T6 — Cierre | Nota de compatibilidad y matrices. | Sigue `PARTIAL` mientras persistan brechas documentadas. |

T2–T6 no quedan autorizadas por T0: antes de cada una se revisará que no exija
resolver una ambigüedad normativa ni ampliar el corpus.

## Casos de aceptación de T0

| ID | Dado | Cuando | Entonces |
| --- | --- | --- | --- |
| T0-A1 | Una Criatura Legendaria. | Se clasifica. | Tipo `CREATURE` y rango `LEGENDARY`, sin crear un tipo compuesto. |
| T0-A2 | Un Señor de Reinos. | Se clasifica. | Conserva su `CardKind` acreditado y dominio `REALMS`, sin convertir el dominio en subtipo ni inferir un tipo único. |
| T0-A3 | Dos grafías `Pixy` y `Pixie`. | Se filtran o proyectan. | Siguen literales y distintas; no hay alias implícito. |
| T0-A4 | Una carta llamada expresamente. | Se selecciona por identidad. | Usa identidad, no una familia taxonómica deducida. |
| T0-A5 | Un Token Legendario sin tipo original. | Se migra o representa. | No se inventa `CardKind`, subtipo ni dominio. |
| T0-A6 | Una keyword impresa. | Se modela taxonomía. | No se degrada a subtipo ni se le asigna semántica nueva. |
| T0-A7 | Una selección por zona/controlador/visibilidad. | Se diseña el filtro. | Se detiene para `CAP-TARGET-002`/zonas/privacidad; T0 no fusiona esos ejes. |

## Exclusiones persistentes

- Leyenda autónoma y tipos impresos múltiples (`CAP-TAXONOMY-002` bloqueada).
- Registro de aliases y procedencia de subtipo (`CAP-TAXONOMY-003`, posterior a
  la base de dimensiones).
- Selectores multidimensionales, keywords, inmunidades, elecciones y búsqueda.
- Alta o reclasificación masiva del corpus; nuevas cartas o handlers por
  `card_id`.

## Trazabilidad

- Base documental: `CANONICAL_TAXONOMY.md` §§1–6.
- Censo: `TOKEN_TYPES_MATRIX.md` §§1–4.
- Dependencias: `ENGINE_CAPABILITY_MATRIX.csv` y
  `ENGINE_CAPABILITY_DEPENDENCIES.md`.
- Regresión ya existente: `tests/test_taxonomy_vocabulary_regressions.py`.
