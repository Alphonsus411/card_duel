# CAP-ACTION-004 / W1.4C — Revalidación del bloqueo en ejecución

Fecha: 2026-10-26
Estado: incremento de runtime acotado
Capability: `PARTIAL / READY`

## Motivo y alcance

W1.4B redujo la enumeración de `test-choice/v1` pendiente a `Concede`, pero
la enumeración no es una frontera autoritativa: un cliente puede construir y
enviar un comando sin haberlo obtenido de `legal_actions`.

W1.4C reutiliza el mismo predicado estricto en `GameEngine.execute`. Mientras
exista una decisión de familia exactamente `test-choice/v1` en estado
`PENDING`, todo comando distinto de `Concede` se rechaza antes de iniciar una
transacción o modificar el estado. La excepción de concesión permanece igual.

## No se amplía el contrato

No se añadieron familias, campos, comandos, eventos, DTOs, tokens, persistencia,
migraciones ni cambios de schema. La resolución sigue en la frontera autenticada
existente y las familias cerradas o no registradas conservan su comportamiento.

## Evidencia

| Caso | Resultado acreditado |
| --- | --- |
| `GameEngine.execute(PassPriority(...))` directo | rechaza y conserva el digest del estado. |
| `MatchService.submit(...)` directo | rechaza, no incrementa versión ni persiste mutación. |
| `Concede` | continúa como única excepción permitida. |
| Familias no registradas | permanecen cubiertas por la regresión W1.3. |

`CAP-ACTION-004` permanece `PARTIAL / READY`. Este guard no promociona
capacidades bloqueadas ni convierte la familia de prueba en una mecánica de
producción.
