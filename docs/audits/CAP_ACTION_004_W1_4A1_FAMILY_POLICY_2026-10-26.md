# CAP-ACTION-004 / W1.4A.1 — Política mínima por familia

Fecha: 2026-10-26
Estado: contrato documental; sin cambio de runtime
Capability: `PARTIAL / READY`

## Inventario y elección mínima

El runtime valida que `semantic_family` sea una cadena versionada, pero no
posee todavía un registro de familias ni una política de bloqueo. Las únicas
familias concretas presentes son valores de fixtures (`test-choice/v1`,
`second-choice/v2` y variantes de compatibilidad); ninguna procede de una carta,
comando público o regla de juego cerrada.

W1.4A.1 elige únicamente `test-choice/v1` como familia de prueba. La elección
no promociona ese nombre a vocabulario de dominio: sirve para probar el
enrutamiento por una familia versionada sin usar `card_id`, nombres de carta o
datos del transporte.

## Política autorizada para W1.4B

| Condición | Acciones legales de cualquier jugador | Resolución de decisión |
| --- | --- | --- |
| No hay decisión o la familia no es `test-choice/v1` | comportamiento actual sin cambios | comportamiento actual sin cambios |
| `test-choice/v1` está `PENDING` | sólo `Concede(player_id)` | sólo el `authorized_elector` conserva la ruta autenticada existente de resolución opaca |
| `test-choice/v1` está `CLOSED` | comportamiento actual sin cambios | no vuelve a cerrar; el consumo sigue siendo interno y fuera de W1.4B |

El bloqueo se aplica a todos los jugadores mientras la decisión esté pendiente;
de ese modo no existe una ventana en la que otro actor pueda avanzar fase,
jugar, pasar prioridad o resolver otra acción mientras el elector decide. No
crea un segundo slot ni convierte la resolución remota en un `GameCommand`.

## Reglas de compatibilidad

1. `Concede` queda siempre disponible y no se filtra por ninguna familia.
2. Familias no registradas, incluidas las fixtures de legado, conservan de
   momento el comportamiento actual. W1.4B no debe reinterpretarlas ni
   rechazarlas: hacerlo sería un cambio de compatibilidad no autorizado.
3. La comparación es por igualdad exacta con `semantic_family`; no se admiten
   prefijos, sufijos, regex, nombres de carta, `origin` ni heurísticas.
4. El bloqueo sólo mira el registro autoritativo `pending_decision` y su
   `status`; no persiste una bandera derivada, no modifica snapshot/replay y no
   emite eventos.
5. Un rechazo de ejecución debe continuar siendo validado por el motor y dejar
   estado, historia, digest y versión CAS sin mutación.

## Superficie prevista y evidencia requerida

W1.4B podrá modificar exclusivamente la enumeración de acciones para consultar
esta política. Deberá comprobar que, para `test-choice/v1` pendiente, ambos
jugadores reciben sólo `Concede`; que el elector aún puede resolver por la
frontera autenticada; que `CLOSED` y familias no registradas preservan la lista
actual; y que snapshot/replay reproducen la misma lista sin nuevos campos.

Quedan excluidos la apertura pública, dispatch de mecánicas, familias de cartas,
audiencias nuevas, decisiones simultáneas, candidatos, cardinalidad, orden y
revelación. `CAP-ACTION-004` permanece `PARTIAL / READY` y esta política no
desbloquea `CAP-SECRET-002` ni `CAP-TIME-002`.
