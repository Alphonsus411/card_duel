# ADR P0 — `CAP-DAMAGE-002`: causa cerrada de prevención de combate

**Fecha:** 2026-10-25

**Estado:** aceptada para P0; habilita sólo P1

**Alcance:** contrato del incremento fundacional `DamageCause.COMBAT`

## Contexto

El motor conserva hoy reservas cuantitativas en
`CardInstance.damage_prevention` y `PlayerState.wound_prevention`. Esas
reservas no codifican causa, fuente, duración, procedencia ni orden de
reemplazo. El roadmap permite una única primera extensión inequívoca:
prevención tipada para daño de combate, incluido Desafío.

La extensión modifica semántica persistible; no es un *quick win*. Su diseño
debe preservar partidas históricas y no puede usar una omisión o un valor por
defecto para elegir reglas.

## Decisiones

### D1 — Conjunto causal cerrado

El incremento introducirá un tipo cerrado `DamageCause` con **un único
miembro**, `COMBAT`. No se aceptan strings libres, `None`, comodines ni una
causa «sin clasificar» como sustituto de semántica.

Una ampliación posterior (por ejemplo, daño de habilidad, de efecto o de una
fuente concreta) requerirá una nueva decisión arquitectónica, versión y casos
de compatibilidad propios.

### D2 — Desafío pertenece a combate

Toda aplicación de daño u herida originada por la resolución de
`DeclareChallenge` se clasifica explícitamente como `DamageCause.COMBAT`.
Desafío no introduce otra causa, ni una excepción, ni un fallback. La
resolución de combate ordinario y la de Desafío tendrán que cruzar la misma
puerta causal antes de que P4 pueda cerrarse.

### D3 — Perfil heredado separado de `COMBAT`

Un snapshot v4 o replay v3 que contenga una reserva escalar conserva el perfil
histórico con el que fue grabado. Durante su decodificación y migración:

- no se le asigna `DamageCause.COMBAT`;
- no se pierde ni se agota anticipadamente;
- conserva el comportamiento histórico que el documento podía reproducir;
- queda representado de manera explícita como perfil heredado en el nuevo
  contrato persistido, no como ausencia de causa ambigua.

Por tanto, una reserva heredada y una reserva nueva `COMBAT` son estados
distintos aunque su cantidad coincida. Esta decisión evita cambiar
retroactivamente el resultado de un replay antiguo.

### D4 — No reclasificar productores existentes

`PREVENT_DAMAGE`, `PREVENT_WOUNDS`, las cartas existentes y sus efectos no se
reclasifican como `COMBAT` en P0. Sólo P2 podrá introducir la interfaz interna
que escriba una reserva tipada, y sólo con una causa explícita. Mantener la
conducta anterior no acredita nuevas causas ni amplía la superficie de cartas.

### D5 — Atomicidad normativa

Para una reserva tipada que coincide con `COMBAT`, el motor debe calcular la
cantidad prevenible, consumir únicamente esa cantidad y aplicar el daño o la
herida restante en una única operación reversible. Si la resolución falla,
ambos cambios vuelven al estado previo. Esta fase define el invariante; su
implementación y prueba pertenecen a P2, P4 y P5.

### D6 — Compatibilidad y rechazo cerrado

P3 emitirá versiones de snapshot y replay posteriores a v4 y v3,
respectivamente. Sus decodificadores deberán:

- leer de forma encadenada los documentos heredados soportados;
- conservar su perfil heredado sin inventar `COMBAT`;
- rechazar versión futura, causa desconocida, payload incompleto o discriminador
  inconsistente antes de mutar estado;
- escribir de forma canónica el perfil de prevención correspondiente.

## Alternativas descartadas

| Alternativa | Motivo del descarte |
| --- | --- |
| Migrar toda reserva escalar a `COMBAT`. | Cambiaría replays y snapshots históricos sin evidencia de que toda prevención antigua fuera de combate. |
| Usar `cause: null` para legado. | Desplaza la decisión semántica a cada consumidor y permite defaults divergentes. |
| Crear desde ahora causas genéricas o un comodín. | Amplía `CAP-DAMAGE-002` más allá del incremento autorizado y anticipa reglas no demostradas. |
| Convertir P0 en un cambio de cartas o efectos. | La fase es contractual; el corpus y la semántica general permanecen fuera de alcance. |

## Casos de aceptación cerrados

| ID | Dado | Cuando | Entonces |
| --- | --- | --- | --- |
| A1 | Una reserva tipada nueva con causa `COMBAT`. | Recibe daño de combate ordinario. | Sólo esa reserva puede aplicarse y se consume como máximo por la cantidad prevenida. |
| A2 | Una reserva tipada nueva con causa `COMBAT`. | Se resuelve un Desafío que causa daño o herida. | Se trata como `COMBAT`; no aparece una segunda causa ni una ruta excepcional. |
| A3 | Una reserva tipada nueva con causa `COMBAT`. | Se procesa una ruta que no es combate. | La reserva no coincide ni se consume. |
| A4 | Una reserva escalar en snapshot v4 o replay v3. | Se migra o reproduce el documento. | Conserva el perfil histórico; no se etiqueta como `COMBAT`. |
| A5 | Una reserva heredada y una reserva `COMBAT` de igual cantidad. | Se serializa el estado nuevo. | La representación distingue ambos perfiles de forma determinista. |
| A6 | Un documento nuevo con una causa desconocida, vacía o ausente. | El decoder intenta cargarlo. | Rechaza el documento sin mutación parcial ni fallback. |
| A7 | Una reserva `COMBAT` insuficiente. | Se resuelve daño de combate mayor que su saldo. | Sólo se consume el saldo disponible y el remanente se aplica una vez. |
| A8 | Una resolución de combate que falla tras calcular prevención. | Se ejecuta el rollback. | Reserva y daño/herida vuelven ambos a su estado anterior. |
| A9 | Un efecto o carta existente de prevención. | Se implementa este incremento. | No se le asigna `COMBAT` implícitamente ni se modifica su alcance en P0. |
| A10 | El trabajo de P0 finalizado. | Se evalúa el estado de capability. | `CAP-DAMAGE-002` permanece `PARTIAL`; no se declara prevención general. |

## Gate de P0

P0 queda cerrado porque el conjunto causal, el tratamiento de Desafío, la
política de legado, el rechazo cerrado y la atomicidad esperada tienen una
única interpretación. Este ADR **no autoriza cambios de runtime**; habilita
exclusivamente P1, el inventario verificable de rutas y pruebas de
caracterización.

## Consecuencias y límites persistentes

- Permanecen fuera: filtros por fuente/controlador, duraciones, expiraciones,
  prevención total, redirección, orden de reemplazos, nuevas cartas y cambios
  de corpus.
- `CAP-DAMAGE-002` no asciende a `SUPPORTED`.
- Si P1 descubre una ruta cuyo resultado histórico no pueda conservarse con el
  perfil heredado, se detiene el avance y se abre un ADR adicional; no se
  resuelve con un default local.

## Trazabilidad

- Plan rector: `docs/audits/CAP_DAMAGE_002_COMBAT_CAUSE_IMPLEMENTATION_PLAN.md`.
- Gap de capability: `docs/ENGINE_CAPABILITY_DEPENDENCIES.md`, fila
  `CAP-DAMAGE-002`.
- Reglas de versionado: `docs/PHASE_2C_ENGINE_EVOLUTION_ROADMAP.md`, secciones
  «Quick wins sin ruptura de contratos» y «Foundational changes que exigen
  versionado».
