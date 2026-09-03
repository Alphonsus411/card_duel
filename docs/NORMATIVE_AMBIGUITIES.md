# Ambigüedades normativas abiertas

Fecha de revisión: 2026-09-03. Este registro depende del documento maestro
[`FANTASY_TOKENS_BACKEND_GAP_AUDIT.md`](FANTASY_TOKENS_BACKEND_GAP_AUDIT.md)
y no concede permisos ni impone prohibiciones por silencio.

## Criterio

`AMBIGUOUS` cubre tanto una redacción insuficiente como el silencio material de
Mítica al enlazar una regla Base. La regla Base sigue vigente por precedencia,
pero el silencio no puede usarse para inventar una extensión Mítica. `CONFLICT`
requiere enunciados expresos incompatibles. `OPEN/BLOCKED` significa que no debe
cerrarse la cuestión mediante código, pruebas o documentación derivada.

## Registro activo

| ID estable | Estado | Evidencia y duda conservada | Conducta documental/técnica actual | Condición de desbloqueo |
|---|---|---|---|---|
| `N-POINTS-01` | `OPEN/BLOCKED` (`CONFLICT`) | Base pp. 3 y 5: mínimo 50 y equivalencia entre mazos. Mítica física 2 / interna 1 menciona separadamente 200, máximo 300–400, aproximadamente 300 y 300. | No elegir presupuesto. `CardDefinition.cost` sigue aportando los puntos de cada copia, con `point_budget=None` por defecto. | Aclaración normativa oficial que identifique cifra, carácter mínimo/máximo/recomendado y formato aplicable. |
| `N-LEGENDARY-06` / `M-LORD-EVENT-01` | `OPEN/BLOCKED` (`AMBIGUOUS`) | Mítica física 3 / interna 2: propiedades de Señor «a modo de Eventos (en la Fase Activa […] se entiende)». No define reclasificación. | Conservar Fase Activa; no derivar inmunidades, tipo de fuente, objetivos, pila ni interacción con Divinos como si fueran Eventos. | Definición oficial de «a modo de Eventos» y lista de consecuencias mecánicas. |
| `N-COMBAT-03` | `OPEN/BLOCKED` (`AMBIGUOUS`) | Base p. 6 permite múltiples bloqueadores y daño restante al jugador, pero no ordena ni distribuye el daño entre bloqueadores. Mítica guarda silencio. | El orden declarado existente es sólo normalización de compatibilidad; no se presenta como norma. | Regla oficial de asignación, orden, simultaneidad y daño sobrante. |
| `N-COMBAT-06` | `OPEN/BLOCKED` (`AMBIGUOUS`) | Base admite uno o más adversarios, pero concesión y empate hablan de un oponente/dos jugadores; Mítica no aclara partidas de 3+. | Ante terminación con 3+, el backend puede detenerse en `BLOCKED`, sin inventar ganadores. | Regla oficial sobre eliminación/fin global, supervivientes, empates y orden de ganadores. |
| `N-PHASE-01`–`02`, `N-PHASE-04`–`05`, `N-PHASE-07`, `N-PHASE-09`–`10` | `BASE VIGENTE / MITICA SILENTE` (`AMBIGUOUS`) | Preparación, mulligan, robo, mantenimiento, descarte, pila y enderezado están en Base; Mítica no los modifica expresamente. | Aplicar Base. No afirmar que el silencio Mítico añade excepciones. | Sólo es necesaria aclaración si se pretende una conducta Mítica distinta. |
| `N-ZONE-01`–`03`, `N-COST-03`, `N-COMBAT-04` | `BASE VIGENTE / MITICA SILENTE` (`AMBIGUOUS`) | Reciclaje, zonas ocultas, Equipo, coste de equipar y aptitud tras giro constan en Base; no hay modificación expresa Mítica. | Aplicar Base sin ampliar ni restringir. | Texto Mítico u oficial expreso que modifique el extremo. |
| `N-PHASE-03`, `N-COMBAT-05` | `OPEN` (`AMBIGUOUS`) | Mítica se apoya en Fase Activa y «jugador», pero no reenumera fases ni precisa el alcance multijugador. | Mantener la secuencia Base y admitir preparación 2+; no derivar condiciones terminales. | Aclaración expresa si Mítica pretende alterar secuencia o alcance. |

## Hallazgos negativos controlados

- No se detectó un conflicto expreso nuevo fuera de `N-POINTS-01`.
- La ausencia de una regla Mítica de reparto no valida ni invalida el orden de
  bloqueadores del backend.
- La ausencia de finales 3+ no convierte automáticamente a los no derrotados en
  ganadores ni obliga a que termine toda la partida.
- La adición de Drenaje, Señores y Desafío no sustituye Transmutación, combate o
  fases salvo en el alcance que su texto declara expresamente.
