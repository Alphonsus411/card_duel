# CAP-ACTION-004 / W1.4A — Autorización de alcance

Fecha: 2026-10-26
Estado: autorización documental acotada; sin cambio de runtime
Capability: `PARTIAL / READY`

## Decisión

Se autoriza iniciar W1.4 exclusivamente por esta subfase W1.4A de contrato,
trazabilidad y pruebas documentales. La autorización resuelve la prohibición
histórica de iniciar W1.4 que dejó W1.3, pero no promociona la capability a
`SUPPORTED`, no desbloquea dependientes y no autoriza aún cambios en `src/`,
persistencia, snapshot, replay, aplicación ni servicio.

La primera preocupación técnica de W1.4 será el bloqueo selectivo de acciones
por `semantic_family`, ya contemplado por el contrato como familia versionada.
La apertura pública arbitraria, decisiones simultáneas y audiencias distintas de
`ELECTOR` siguen fuera de alcance.

## Alcance autorizado de W1.4A

| Permitido | Prohibido |
| --- | --- |
| Precisar la política de bloqueo por familia, sus invariantes y sus rechazos. | Añadir comandos, handlers, campos de estado, eventos o DTOs. |
| Inventariar las rutas actuales de enumeración, ejecución, aplicación y servicio. | Definir una apertura remota universal de decisiones. |
| Añadir pruebas de caracterización o contractuales que no modifiquen la semántica. | Cambiar schema, snapshot, replay, migraciones, CAS o compatibilidad. |
| Proponer el siguiente slice de runtime con criterios de entrada/salida verificables. | Modelar candidatos, cardinalidad, orden, selección compuesta, búsquedas o revelación. |

## Restricciones vinculantes

1. `Concede` no queda bloqueado por defecto ni por una familia no especificada.
2. Una política futura se decide por `semantic_family` versionada, nunca por
   `card_id`, nombre de carta, identidad externa o heurística de transporte.
3. El único slot, el lifecycle `None → PENDING → CLOSED → None`, la historia
   total, el CAS y la audiencia `ELECTOR` se preservan sin reinterpretación.
4. Cualquier subfase de runtime posterior deberá demostrar enumeración y
   revalidación congruentes, rechazo sin mutación, replay/snapshot compatibles y
   no filtración de opciones privadas.
5. Esta autorización no modifica los blockers de `CAP-TIME-002`: continúa
   bloqueada también por `CAP-TIME-005` y por sus asuntos normativos abiertos.

## Criterio para abrir W1.4B

W1.4B sólo podrá comenzar tras un documento W1.4A posterior que identifique la
familia mínima, su política explícita de bloqueo, el efecto sobre las acciones
legales y la matriz de compatibilidad. Deberá ser una sola familia de prueba,
sin simultaneidad, sin audiencias nuevas y sin abrir decisiones desde transporte.

## Resultado

W1.4 queda iniciado únicamente en su carril documental. `CAP-ACTION-004`
permanece `PARTIAL / READY`; `CAP-SECRET-002` y `CAP-TIME-002` no se promueven.
