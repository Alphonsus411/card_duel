# CAP-EFFECT-001 / E7 — Revisión de cierre incremental

Fecha: 2026-10-26
Estado: cierre del incremento E0–E7
Capability: `PARTIAL / READY`

## Dictamen

El incremento acredita la frontera del vocabulario atómico cerrado ya existente,
pero no una semántica completa de efectos de carta. Por ello no se añade ninguna
primitiva, no se promociona `CAP-EFFECT-001` a `SUPPORTED` y no se desbloquea
`CAP-EFFECT-002` ni `CAP-EFFECT-003`.

## Evidencia consolidada

| Tramo | Evidencia | Garantía acreditada |
| --- | --- | --- |
| E0 | contrato de primitivas | frontera explícita: discriminador tipado, declaración, pila, fizzle y compatibilidad |
| E1 | inventario de rutas | declaración, stack, pausa de búsqueda y persistencia tienen autoridades identificadas |
| E2 | modelo de extensión | las 23 primitivas actuales permanecen cerradas; los huecos se asignan a su capability propietaria |
| E3 | `test_effect_contract_e3.py` | categorías exhaustivas, forma mínima válida y registro completo |
| E4 | `test_effect_persistence_e4.py` | codec, snapshot y replay preservan el contrato sin cambio de esquema |
| E5 | `test_effect_validation_e5.py` | definiciones incompatibles fallan antes de llegar a la pila |
| E6 | `test_effect_fizzle_e6.py` | un target inválido emite fizzle y no deja mutación parcial para los 23 discriminadores |

La regresión de las superficies de efectos, resolución, revelación, persistencia
y E3–E6 supera 75 pruebas y 7 subpruebas en el cierre.

## Brechas que permanecen fuera del incremento

| Brecha | Capability propietaria | Motivo para no integrarla aquí |
| --- | --- | --- |
| Secuencias, ramas, valores capturados y atomicidad compuesta | `CAP-EFFECT-003` | requieren intérprete/continuaciones y gates adicionales |
| Elección secreta, audiencias y descartes con elector | `CAP-SECRET-002`, `CAP-EFFECT-005` | exigen lifecycle público autorizado y privacidad |
| Fichas/instancias en resolución | `CAP-EFFECT-004` | necesita identidad, definición y transición atómica |
| Continuos, layers, keywords y procedencia | `CAP-EFFECT-002`, `CAP-KEYWORD-001/002` | dependen de taxonomía, selectores, precedencia y limpieza |
| Triggers generales, LKI y cambios de zona compuestos | `CAP-TRIGGER-001`, `CAP-ZONE-005/006` | requieren orden, causalidad y audiencias fuera de la primitiva atómica |
| Cobertura de las 431 entradas del corpus | `CAP-CATALOG-001` | un discriminador representable no acredita texto completo ni sus prerrequisitos |

## Decisión de dependencia

`CAP-EFFECT-002` conserva `WAIT-PREREQ`, entre otros motivos por
`CAP-TARGET-002` y `CAP-KEYWORD-001`. `CAP-EFFECT-003` conserva
`WAIT-PREREQ`: además de esta capability, requiere secreto compuesto, zonas
causales completas, triggers y otras fronteras aún parciales. Ninguna de esas
restricciones se suaviza en E7.

## Próximo trabajo válido

No hay un subtramo adicional seguro dentro de `CAP-EFFECT-001` sin invadir una
capability propietaria. El siguiente avance debe seleccionarse entre las
capabilities `READY` del roadmap mediante su prioridad y dependencias, no por
añadir efectos ad hoc.
