# Plan fundacional: `CAP-DAMAGE-002` — prevención por causa `COMBAT`

**Fecha:** 2026-10-24  
**Estado:** plan de implementación; no cambia la clasificación de la capability  
**Prioridad de roadmap:** P0 / W1, después de las integraciones ya cerradas

## Decisión de alcance

La reserva escalar actual (`CardInstance.damage_prevention` y
`PlayerState.wound_prevention`) sólo acredita prevención consumible sin causa.
El siguiente incremento autorizado es **únicamente** una prevención tipada cuya
causa es `DamageCause.COMBAT`.

`DeclareChallenge` y toda su resolución de daño se consideran combate a estos
efectos. Por tanto, tanto el combate ordinario como Desafío deben recorrer el
mismo contrato causal `COMBAT`.

El incremento deja `CAP-DAMAGE-002` en `PARTIAL`: no declara prevención
ilimitada ni el contrato completo de filtros, fuente, procedencia y expiración
que exige la matriz de capabilities.

## Límites no negociables

| Incluido | Excluido explícitamente |
| --- | --- |
| Único discriminador nuevo: `DamageCause.COMBAT`. | Causas adicionales, valores implícitos o un comodín equivalente a «cualquier daño». |
| Daño de combate normal y de Desafío. | Redirección, reemplazo de daño, elección de orden de reemplazos o daños prevenibles por fuente. |
| Reserva consumible y su consumo atómico junto al daño remanente. | Escudos permanentes, renovables, acumulables sin límite o con duración distinta de la reserva actual. |
| Persistencia, migración, replay y pruebas de compatibilidad necesarios. | Cartas nuevas, cambios de corpus, cambios de targeting o promoción automática de la capability. |

No se permite usar `None`, una cadena vacía, un default de decoder ni una
heurística para escoger una causa. Una lectura heredada debe conservar su perfil
heredado; no puede reinterpretar una reserva escalar ya persistida como
`COMBAT`.

## Estado que obliga a tratarlo como cambio fundacional

La ruta actual almacena enteros sin causa y los consume desde las rutas de daño.
La nueva semántica debe estar disponible en estado, codec, snapshot y replay.
Cambiar cualquiera de esas superficies deja de ser un *quick win* según el
roadmap, por lo que requiere versiones explícitas, migradores, golden replays y
una nota de compatibilidad.

Las versiones de partida al redactar este plan son snapshot **v4** y replay
**v3**. Las versiones de salida se decidirán en la fase P3, pero han de ser
posteriores a éstas y rechazar documentos futuros desconocidos.

## Fases y puertas de salida

| Fase | Entregable | Puerta de salida |
| --- | --- | --- |
| P0 — Contrato | ADR corta y casos de aceptación cerrados. | Un único significado para `COMBAT`, incluido Desafío, y una política documentada para reservas heredadas. |
| P1 — Inventario | Mapa verificable de todas las entradas a daño/herida y de los lugares que cargan/consumen reservas. | Ninguna ruta de combate o Desafío queda sin etiquetar; las rutas ajenas quedan identificadas para pruebas negativas. |
| P2 — Dominio | Modelo tipado mínimo y API interna de carga/consumo. | No hay causa opcional ni API pública que acepte una cadena arbitraria; consumo y daño remanente son atómicos. |
| P3 — Persistencia | Versiones nuevas, codecs, migradores y fixtures de legado. | Una carga v4/v3 conserva semántica heredada; escritura nueva es determinista y versión desconocida falla cerrada. |
| P4 — Motor | Etiquetado de las dos familias de combate y aplicación de la reserva en la puerta común. | Combate y Desafío aplican exactamente la misma causa; otros daños no consumen una reserva `COMBAT`. |
| P5 — Verificación | Suite unitaria, integración, regresión y golden replay. | Todos los casos positivos, negativos y de rollback pasan sin alterar contratos no incluidos. |
| P6 — Cierre documental | Nota de compatibilidad, auditoría de alcance y actualización de matriz sólo con evidencia. | La matriz sigue `PARTIAL` salvo decisión posterior y evidencia independiente del contrato completo. |

## Diseño previsto por fase

### P0 — Fijar el contrato antes de codificar

1. Crear un ADR que defina `DamageCause.COMBAT` como el único miembro expuesto
   en este incremento.
2. Establecer que Desafío no es una causa nueva: es una modalidad de combate y
   emite/usa `COMBAT`.
3. Definir una representación separada para la reserva tipada, sin cambiar el
   sentido histórico de los campos escalares. La decisión debe indicar si los
   contadores existentes se mantienen como perfil heredado de compatibilidad o
   se migran a una estructura explícita que preserve ese perfil.
4. Especificar el orden atómico: calcular protección aplicable, consumir sólo
   la cantidad usada y aplicar el remanente en la misma transacción. Un error
   posterior debe restaurar ambos cambios.

**No se inicia P1** hasta que la política de legado responda con precisión qué
ocurre con un snapshot v4 que contiene una reserva escalar no agotada.

### P1 — Inventario y pruebas de caracterización

Inventariar con referencias a función y test:

- productores de `PREVENT_DAMAGE` y `PREVENT_WOUNDS`;
- puertas de daño a carta y de herida a jugador;
- resolución de combate normal y la de `DeclareChallenge`;
- serialización de `CardInstance` y `PlayerState`, digest de estado, snapshot,
  replay, stores y proyecciones que reflejen esos campos.

Añadir pruebas de caracterización para el comportamiento actual, incluida una
reserva parcialmente consumida. Estas pruebas congelan el perfil heredado; no
son todavía evidencia de prevención por causa.

### P2 — Modelo de dominio y atomicidad

Introducir un tipo cerrado `DamageCause` con el solo valor `COMBAT` y una
estructura de reserva tipada que contenga, como mínimo, cantidad y causa.
Mantener la estructura mínima: no añadir fuente, controlador, duración,
prioridad, procedencia, selector ni capacidad de sustitución mientras no formen
parte de una capability posterior autorizada.

La interfaz interna debe requerir una causa para solicitar protección tipada.
Debe distinguir inequívocamente:

- reserva nueva `COMBAT`, que sólo coincide con daño etiquetado `COMBAT`;
- estado heredado, que conserva exactamente la semántica que tenía al ser
  grabado;
- ausencia de reserva, que no inventa protección.

La aplicación del daño no puede exponer un estado intermedio donde el contador
se consumió pero el daño no se aplicó, ni viceversa.

### P3 — Versionado, codec y replay

1. Incrementar explícitamente las versiones de snapshot y replay que cambien.
2. Añadir migradores encadenados desde snapshot v4 y replay v3; conservar los
   migradores existentes y sus fixtures.
3. Codificar de forma canónica el discriminador y las reservas tipadas, con
   orden estable cuando haya más de una reserva representable.
4. Preservar en lectura el perfil heredado, sin asignarle `COMBAT` por defecto.
5. Rechazar esquema desconocido, causa desconocida y payload incompleto; no
   corregirlos silenciosamente.
6. Actualizar `state_digest` y cualquier checksum sólo después de que el
   contrato de serialización esté fijado, regenerando los fixtures de forma
   revisable.

Los golden fixtures mínimos son: snapshot/replay heredado sin reserva, heredado
con reserva escalar, documento nuevo con reserva `COMBAT` intacta y documento
nuevo con reserva `COMBAT` parcialmente consumida. Cada fixture debe comprobar
el digest y el resultado de replay, no sólo que el JSON se decodifica.

### P4 — Integración en el motor

Canalizar toda aplicación de prevención por causa por una única puerta interna
de resolución de daño. La resolución de combate ordinario y la de Desafío deben
pasar `DamageCause.COMBAT` de manera explícita. No se permite inferir la causa
desde el nombre de una carta, el tipo de objetivo ni el estado de fase.

Para cualquier ruta que no pertenezca a combate, la reserva `COMBAT` no debe
coincidir ni consumirse. Esta es una garantía negativa, no una invitación a
crear más causas en el mismo cambio.

Si la ruta de Desafío no comparte el punto de aplicación de daño con el combate
normal, P4 debe extraer sólo la puerta causal necesaria. No debe aprovecharse
el cambio para rediseñar combate, añadir triggers ni modificar prioridades.

### P5 — Matriz mínima de pruebas

| Caso | Resultado exigido |
| --- | --- |
| Reserva `COMBAT` frente a daño de combate de carta | Previene hasta el saldo, consume exactamente lo usado y aplica el remanente. |
| Reserva `COMBAT` frente a herida de combate de jugador | Misma semántica y consumo atómico. |
| Reserva `COMBAT` en Desafío | Mismo resultado que combate ordinario, sin una causa alternativa. |
| Daño ajeno a combate | No consume ni aplica la reserva `COMBAT`. |
| Reserva insuficiente | Saldo llega a cero; el excedente se aplica una sola vez. |
| Fallo/rollback durante la resolución | Daño y reserva vuelven al estado previo conjuntamente. |
| Snapshot/replay heredado | Reproduce su comportamiento histórico; no aparece `COMBAT` inventado. |
| Snapshot/replay nuevo | Conserva tipo, saldo, digest y resolución tras restaurar/reproducir. |
| Esquema o causa desconocidos | Rechazo cerrado y sin mutación parcial. |

La suite debe incluir paridad entre ejecución directa, snapshot restaurado y
replay para cada familia positiva. Las pruebas de propiedades existentes pueden
ampliarse sólo si generan causas desde el conjunto cerrado actual; no deben
simular futuras causas con strings libres.

### P6 — Evidencia y comunicación

Publicar una nota de compatibilidad que detalle:

- versión emitida y versiones leídas;
- tratamiento exacto de reservas heredadas;
- incompatibilidades intencionadas (versiones/categorías desconocidas);
- que `COMBAT` cubre también Desafío;
- exclusiones que siguen pendientes.

Actualizar la matriz y la auditoría de dependencias únicamente para enlazar la
evidencia nueva. No elevar `CAP-DAMAGE-002` a `SUPPORTED`: siguen pendientes
prevención ilimitada y los filtros tipados por fuente, causa, procedencia y
duración.

## Superficies esperadas y control de cambios

| Superficie | Cambio permitido | Control |
| --- | --- | --- |
| `domain/` | Tipo cerrado y reserva mínima. | Revisión de exhaustividad; ningún string libre. |
| Resolución de daño/combate | Parámetro causal interno explícito y puerta común. | Pruebas de combate normal, Desafío y no-combate. |
| Efectos de prevención | Carga de la reserva mínima aprobada. | No ampliar semántica de efectos ni añadir cartas. |
| Codec/snapshot/replay | Nueva versión, migración y rechazo cerrado. | Golden fixtures y equivalencia de digest. |
| Servicio/proyección | Sólo cambios indispensables para representar estado ya autorizado. | No exponer detalles de estado interno innecesarios. |
| Documentación/matriz | ADR, nota de compatibilidad y trazabilidad. | Mantener clasificación `PARTIAL`. |

## Criterio de parada

Se detiene el trabajo y se abre una decisión de roadmap si aparece cualquiera
de estas necesidades: una causa adicional; selección por fuente/controlador;
duración o expiración nueva; redirección o reemplazo; elección del jugador;
cambio de carta/corpus; o una semántica para legado que no conserve el replay
histórico. Ninguna de ellas se resuelve con un default local.

## Resultado esperado

Al completar todas las fases, el motor podrá demostrar una única extensión
pequeña y persistible: reservas consumibles que previenen daño o heridas de
**combate**, incluyendo **Desafío**, sin reinterpretar partidas antiguas ni
abrir las capacidades de prevención general que el roadmap mantiene fuera de
alcance.
