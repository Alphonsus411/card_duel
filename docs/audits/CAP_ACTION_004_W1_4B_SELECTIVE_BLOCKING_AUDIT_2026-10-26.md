# CAP-ACTION-004 / W1.4B — Bloqueo selectivo de familia de prueba

Fecha: 2026-10-26
Estado: incremento de runtime acotado
Capability: `PARTIAL / READY`

## Implementación

`LegalActionEnumerator` consulta el único registro autoritativo
`GameState.pending_decision`. Cuando, y sólo cuando, su familia es exactamente
`test-choice/v1` y su estado es `PENDING`, devuelve `Concede(player_id)` como
única acción legal para cualquier jugador.

La comparación no usa prefijos, `origin`, carta, identidad de transporte ni
otro estado derivado. No se añadió campo, comando, evento, DTO, token,
persistencia, migración ni versión de schema. La resolución permanece en la
frontera autenticada W1.2 y no se convierte en una acción del motor.

## Evidencia

| Caso | Resultado acreditado |
| --- | --- |
| Familia `test-choice/v1` pendiente | A y B reciben exclusivamente `Concede`. |
| Familia `test-choice/v1` cerrada | se conserva la enumeración anterior. |
| Familia no registrada `second-choice/v2` | se conserva la enumeración anterior. |
| Snapshot y replay de la familia de prueba pendiente | restauran la misma lista sin campos nuevos. |
| Resolución por elector | la ruta autenticada existente cierra la decisión. |
| `Concede` | permanece disponible siempre. |

La prueba histórica de que un slot pendiente no bloquea globalmente las acciones
se conserva para una familia no registrada; evita confundir este incremento con
un bloqueo universal.

## Límites

W1.4B no registra una familia de producción, no abre decisiones públicamente y
no asocia mecánicas a la opción seleccionada. Tampoco define múltiples
electores, simultaneidad, nuevas audiencias, candidatos, cardinalidad, orden,
búsquedas o revelación.

`CAP-ACTION-004` permanece `PARTIAL / READY`: este incremento no promociona
`CAP-SECRET-002` ni `CAP-TIME-002` y no altera sus blockers independientes.
