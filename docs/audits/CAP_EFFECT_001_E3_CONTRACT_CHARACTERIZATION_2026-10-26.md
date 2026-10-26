# CAP-EFFECT-001 — E3: caracterización del contrato cerrado

**Fecha:** 2026-10-26
**Estado de la fase:** completada
**Capability:** `CAP-EFFECT-001` permanece `PARTIAL / READY`.

## Evidencia añadida

`tests/test_effect_contract_e3.py` convierte el resultado de E2 en un contrato
ejecutable:

| Comprobación | Garantía |
| --- | --- |
| Categorías exhaustivas y disjuntas | los 23 miembros de `EffectKind` pertenecen a exactamente una familia: jugador, permanente, zona o reparto |
| Forma declarativa válida | cada discriminador conserva una construcción mínima válida de `EffectDefinition`, incluidos los campos obligatorios de transformación, texto, fase, búsqueda y revelación |
| Registro del gestor | `EffectManager` expone exactamente el vocabulario cerrado de `EffectKind` |

La caracterización no ejecuta una carta ni afirma semántica completa de una
familia. Complementa las pruebas de resolución, targeting, búsqueda y snapshot
ya existentes, y falla si se introduce un discriminador sin clasificar, sin
forma declarativa válida o sin handler.

## Límites preservados

No se modificaron `EffectKind`, `EffectDefinition`, codec, snapshot, replay,
eventos ni rutas públicas. La prueba no habilita composición, elecciones
ocultas, orden de zona, continuos, prevención tipada, fichas o descarte forzado.
Esas necesidades continúan en las capabilities indicadas por E2.

## Salida de E3

El contrato mínimo queda protegido antes de revisar persistencia y replay en E4.
La capability no se promueve: un registro completo de handlers sigue sin ser un
intérprete general ni una prueba de combinaciones completas.
