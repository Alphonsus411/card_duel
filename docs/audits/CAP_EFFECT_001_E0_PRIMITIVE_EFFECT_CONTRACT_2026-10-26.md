# CAP-EFFECT-001 — E0: contrato de primitivas declarativas

**Fecha:** 2026-10-26
**Estado de la fase:** completada; sólo contrato e inventario de frontera
**Capability:** `CAP-EFFECT-001` permanece `PARTIAL / READY`.

## Decisión de alcance

Este incremento fija qué acredita una primitiva declarativa antes de ampliar el
motor. No incorpora cartas, efectos nuevos, composición general, selección
secreta, triggers, LKI, audiencias, reglas de fase ni cambios de schema. La
unidad de trabajo sigue siendo `EffectDefinition` con `EffectKind` cerrado;
`EffectManager` despacha una entrada ya declarada y `StackManager` conserva la
secuencia de resolución.

Una entrada en `EffectKind` o un handler registrado no equivale a soporte de una
carta ni de una oración completa. Sólo acredita la operación atómica que su
contrato y sus precondiciones actuales puedan ejecutar.

## Contrato mínimo de una primitiva

Toda primitiva que se declare soportada en esta capability deberá cumplir estas
condiciones dentro de su alcance concreto:

1. Su discriminador será un miembro estable de `EffectKind`, no un `card_id`,
   una cadena libre ni un handler registrado por carta.
2. `EffectDefinition` validará localmente la forma de objetivo, cantidad,
   duración y campos específicos antes de que la pila la acepte.
3. La resolución entrará por `StackManager` y `EffectManager`; el gestor no
   poseerá un segundo `GameState` ni inventará una fuente, target o audiencia.
4. Un objetivo malformado o no válido producirá el fizzle ya previsto sin mutar
   parcialmente el estado. Una inmunidad se revalida mediante el perfil de
   fuente congelado del `StackItem`.
5. El efecto sólo delegará en una autoridad existente para daño, zonas,
   controlador, barajado o estado derivado. Esa delegación no promociona la
   capability ajena ni permite saltar sus guardas.
6. La definición deberá seguir siendo serializable por snapshot y replay. Añadir
   o reinterpretar campos/discriminadores persistidos requerirá versionado,
   decoder de legado, migración y golden replay; no se aceptan defaults
   semánticos implícitos.

## Inventario de frontera actual

| Familia | Primitivas presentes | Autoridad efectiva | Límite que no se debe inferir |
| --- | --- | --- | --- |
| Jugador | `DEAL_WOUNDS`, `HEAL_WOUNDS`, `GAIN_STEPS`, `DRAW_CARDS`, `PREVENT_WOUNDS`, `SKIP_PHASE` | `EffectManager` y métodos autoritativos de `GameEngine` | no define timing canónico ni prioridad de fase |
| Permanente | `DEAL_DAMAGE`, `MODIFY_STRENGTH`, `TAP`, `UNTAP`, `DESTROY`, `PREVENT_DAMAGE`, `BECOME_CREATURE`, `ADD_REGENERATION` | objetivo congelado, chequeo de inmunidad y estado derivado | no completa prevención por procedencia, layers ni keywords nominales |
| Zona | `MOVE_CARDS`, `SHUFFLE_ZONE`, `SEARCH_ZONE`, `REVEAL_UNTIL` | `ZoneManager` para movimientos; `StackManager` pausa búsquedas | no completa elección secreta, top-N, reordenación ni audiencia de revelación |
| Definición/control | `CHANGE_CONTROL`, `COPY_DEFINITION`, `TRANSFORM_DEFINITION`, `MODIFY_TEXT` | control y definición efectiva ya existentes | no resuelve composición de copias, layers o procedencia general |
| Reparto | `DEAL_HARM` | `TargetAllocation` validado en resolución | no autoriza cardinalidad arbitraria ni elección compuesta |

`SEARCH_ZONE` es una excepción deliberada de frontera: su handler no ejecuta la
elección; `StackManager` crea `PendingSearch`, pausa la resolución y continúa
después del comando correspondiente. E1 deberá registrar esta cooperación, no
convertirla en un handler vacío ni afirmar que implementa `CAP-SECRET-002`.

## Compatibilidad y restricciones

`EffectDefinition` se persiste dentro de definiciones, pila, snapshot y replay.
Los nombres actuales de `EffectKind` y la semántica de cada campo persistido son
por tanto compatibilidad observada. El codec sólo admite los campos históricos
documentados como ausentes; no puede usar esa tolerancia para dar significado a
una nueva primitiva. La prueba de registro completo demuestra que existe un
handler por discriminador, pero no sustituye pruebas de legalidad, rollback,
round-trip, replay o privacidad.

Quedan expresamente fuera de E0: `CAP-EFFECT-002`, `CAP-EFFECT-003`,
`CAP-SECRET-002`, `CAP-TRIGGER-001`, `CAP-ZONE-006` y toda promoción de corpus.
El siguiente tramo E1 inventariará rutas de declaración, apilado, persistencia y
resolución por cada familia, sin modificar runtime.
