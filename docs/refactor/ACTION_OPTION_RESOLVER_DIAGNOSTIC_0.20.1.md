# Diagnóstico de `ActionOptionResolver` — 0.20.1

## 1. Veredicto

**GO**, exclusivamente para una extracción mecánica y de solo lectura cuya frontera se
limite a `_card_cost_options`, `_target_selections`, `_zone_target_selections`,
`_allocation_selections` y `_positive_compositions`. La extracción no autoriza a
mover autoridad, alterar el orden de iteración ni cambiar los puntos actuales de
truncado. Si durante la implementación cualquiera de las funciones marcadas como
prohibidas tuviera que moverse, el veredicto cambia automáticamente a **NO-GO** y la
implementación debe detenerse.

## 2. Línea base reproducible

- SHA de partida: `3cdab054667fed5f3ff506d527591336f8eaceb0`.
- Rama de trabajo creada desde ese SHA: `refactor/action-option-resolver`.
- `git status --short` no produjo salida antes de crear la rama: el árbol estaba limpio.
- La versión confirmada en `pyproject.toml` es `0.20.1`; queda fuera del cambio.
- Este documento es diagnóstico: no implementa todavía la extracción.

## 3. Integridad de documentos binarios

Hashes SHA-256 registrados antes de cualquier cambio:

| Archivo | SHA-256 |
| --- | --- |
| `Fantasy Tokens.pdf` | `1c51dabe2023626ad532368e2567d2084c47ec137c7a738bd8c0e0b707f86b21` |
| `Fantasy Tokens Edicion Mitica.pdf` | `61243b30d219dd12d8897a206ed664d95a5e3c38b6670a818933f6d90904af36` |

Los PDF no forman parte de la frontera y no deben modificarse.

## 4. Archivos inspeccionados

Se inspeccionaron directamente:

- `src/card_duel_engine/engine/game.py`: orquestación, enumeración, validación,
  costes, inmunidad y ejecución.
- `src/card_duel_engine/engine/actions.py`: `LegalActionEnumerator`, su protocolo de
  contexto, truncados y orden final de comandos.
- `src/card_duel_engine/engine/effects.py`: consumo de `_effect_amount` y
  `_card_can_be_targeted` durante resolución.
- `src/card_duel_engine/engine/stack.py`: viabilidad de disparos mediante
  `_trigger_target_commands` y mutación de pila/prioridad.
- `src/card_duel_engine/engine/commands.py`: forma y orden de campos de `PlayCard`,
  `ActivateAbility` y `ChooseTriggeredTargets`.
- Pruebas de replay: `tests/test_replay_legacy_019.py`,
  `tests/test_replay_legacy_020_profile.py` y los artefactos históricos asociados.
- Pruebas de privacidad: los casos de privacidad de
  `tests/test_legal_action_enumerator_parity.py` y el DTO público de
  `tests/test_authenticated_application_r06.py`.
- Pruebas de acciones legales: `tests/test_legal_action_enumerator_parity.py`, con
  apoyo de `tests/test_variable_rules_v080.py`, `tests/test_dynamic_rules_v070.py`,
  `tests/test_stack_and_priority.py` y `tests/test_resolution_v050.py`.

## 5. Entradas y salidas observables

`LegalActionEnumerator.legal_actions` consulta el estado autoritativo y delega en
`_trigger_target_commands`, `_legal_plays` y `_legal_ability_activations`. El resultado
observable no es un conjunto: es una tupla ordenada de dataclasses inmutables. Por
tanto son contrato el tipo de comando, el orden de los comandos, el orden de cada
tupla elegida, los índices de coste, el valor de X y el lugar exacto donde actúa cada
límite.

Los ejecutores `PlayCard`, `ActivateAbility` y `ChooseTriggeredTargets` no confían en
la enumeración: vuelven a validar el comando antes de mutar. Esta separación debe
preservarse.

## 6. Grafo desde `LegalActionEnumerator`

```text
LegalActionEnumerator.legal_actions
├─ _trigger_target_commands
│  ├─ _target_selections (jugadores)
│  ├─ _card_can_be_targeted [PROHIBIDA]
│  ├─ _target_selections (permanentes)
│  ├─ _zone_target_selections
│  ├─ _allocation_selections
│  │  ├─ _card_can_be_targeted [PROHIBIDA]
│  │  ├─ _effect_amount [PROHIBIDA]
│  │  └─ _positive_compositions
│  └─ islice(product(...), limit) → ChooseTriggeredTargets
├─ _legal_plays
│  ├─ _timing_allows_play [PROHIBIDA]
│  ├─ _target_selections (jugadores)
│  ├─ _card_can_be_targeted [PROHIBIDA]
│  ├─ _target_selections (permanentes)
│  ├─ _zone_target_selections
│  ├─ _card_cost_options
│  │  ├─ _resolve_dynamic_cost [PROHIBIDA]
│  │  └─ _resolve_x_cost [PROHIBIDA]
│  ├─ _allocation_selections → _effect_amount / inmunidad / composiciones
│  ├─ combinations (descartes y sacrificios)
│  └─ islice(product(...), limit) → PlayCard
└─ _legal_ability_activations
   ├─ timing/estado/once-per-turn [PROHIBIDOS]
   ├─ _resolve_dynamic_cost / _resolve_x_cost [PROHIBIDAS]
   ├─ combinations (descartes y sacrificios)
   ├─ _target_selections (jugadores)
   ├─ _card_can_be_targeted [PROHIBIDA]
   ├─ _target_selections (permanentes)
   ├─ _zone_target_selections
   ├─ _allocation_selections → _effect_amount / inmunidad / composiciones
   └─ islice(product(...), limit) → ActivateAbility
```

## 7. Grafo desde `PlayCard`

```text
execute(PlayCard) → _play_card
├─ prioridad, pertenencia a mano y _timing_allows_play [VALIDACIÓN/TIMING]
├─ _validate_effect_targets [PROHIBIDA]
│  ├─ consulta de estado autoritativo
│  ├─ _card_can_be_targeted [PROHIBIDA]
│  └─ _effect_amount [PROHIBIDA]
├─ _card_cost_for_option [PROHIBIDA]
│  ├─ _resolve_dynamic_cost [PROHIBIDA]
│  └─ _resolve_x_cost [PROHIBIDA]
├─ validación de pago [PROHIBIDA]
└─ pago, pila, eventos y prioridad [MUTACIÓN; PROHIBIDOS]
```

La futura extracción sólo ayuda a **ofrecer** opciones; nunca decide que un comando
recibido es válido ni calcula el coste autoritativo que finalmente se paga.

## 8. Grafo desde `ActivateAbility`

```text
execute(ActivateAbility) → _activate_ability
├─ prioridad y validez de fuente [VALIDACIÓN/TIMING]
├─ fase, trigger y once-per-turn [VALIDACIÓN/TIMING/LEGACY]
├─ _validate_effect_targets [PROHIBIDA]
│  ├─ _card_can_be_targeted [PROHIBIDA]
│  └─ _effect_amount [PROHIBIDA]
├─ _resolve_x_cost o _resolve_dynamic_cost [PROHIBIDAS]
├─ validación de pago [PROHIBIDA]
└─ pago, marcado, pila, eventos y prioridad [MUTACIÓN; PROHIBIDOS]
```

No se debe reutilizar `_card_cost_options` para habilidades: hoy la enumeración de
habilidades conserva su propio orden de rangos X y su propia forma de costes.

## 9. Grafo desde `ChooseTriggeredTargets`

```text
execute(ChooseTriggeredTargets) → _choose_triggered_targets
├─ prioridad, existencia y bloqueo del disparo [VALIDACIÓN]
├─ _validate_effect_targets [PROHIBIDA]
│  ├─ _card_can_be_targeted [PROHIBIDA]
│  └─ _effect_amount [PROHIBIDA]
└─ replace(StackItem), bloqueo y evento [MUTACIÓN; PROHIBIDOS]
```

En la dirección de enumeración, `StackManager._queue_trigger_batch` usa
`_trigger_target_commands` como consulta de viabilidad: una lista vacía hace que el
disparo se descarte. Cambiar truncado, candidatos o inmunidad podría por ello cambiar
el estado, aunque los helpers candidatos sean conceptualmente de solo lectura.

## 10. Clasificación de helpers trazados

| Helper | Clasificación primaria | Clasificaciones adicionales | ¿Movible? |
| --- | --- | --- | --- |
| `_card_cost_options` | enumeración | consulta de estado vía coste dinámico | Sí |
| `_card_cost_for_option` | validación | consulta autoritativa de coste | **No** |
| `_target_selections` | enumeración | — | Sí |
| `_zone_target_selections` | enumeración | consulta de estado autoritativo | Sí |
| `_allocation_selections` | enumeración | inmunidad y consulta autoritativa por colaboración | Sí |
| `_positive_compositions` | enumeración | combinatoria pura | Sí |
| `_effect_amount` | validación | cálculo autoritativo de reglas | **No** |
| `_trigger_target_commands` | enumeración | consulta usada por mutación de pila | **No** |
| `_legal_plays` | enumeración | timing, inmunidad y consulta autoritativa | **No** |
| `_legal_ability_activations` | enumeración | timing, legacy, inmunidad y estado autoritativo | **No** |
| `_validate_effect_targets` | validación | inmunidad y consulta autoritativa | **No** |
| `_card_can_be_targeted` | inmunidad | validación y consulta autoritativa | **No** |
| `_resolve_dynamic_cost` | consulta de estado autoritativo | reglas de pago | **No** |
| `_resolve_x_cost` | validación | reglas de pago | **No** |

La **mutación** reside en los ejecutores `_play_card`, `_activate_ability` y
`_choose_triggered_targets`, y en gestores de pila; no en los cinco candidatos. El
**legacy** aparece en ventanas de habilidades y en `LegalActionEnumerator`, no debe
entrar al resolver extraído.

## 11. Frontera propuesta

Crear posteriormente un colaborador interno `ActionOptionResolver` que posea sólo
los cinco algoritmos aprobados. Debe recibir entradas explícitas y colaboradores de
consulta, sin poseer `GameState`, sin exponerlo y sin mutarlo:

- límite de enumeración;
- consulta de estado requerida para construir candidatos de zona/asignación;
- callback autoritativo para coste dinámico y coste X;
- callback autoritativo de `_card_can_be_targeted`;
- callback autoritativo de `_effect_amount`.

`GameEngine` seguirá siendo dueño de `_legal_plays`, `_legal_ability_activations` y
`_trigger_target_commands`; éstos construirán `PlayCard`, `ActivateAbility` y
`ChooseTriggeredTargets` exactamente en el orden actual. Se pueden conservar métodos
delegadores privados en `GameEngine` para minimizar el parche y mantener tests que
ejerciten esos nombres.

## 12. Dependencias permitidas y prohibidas

Permitidas: modelos inmutables (`EffectDefinition`, `TargetAllocation`, `ZoneTarget`,
`CompositeCost`), enums (`TargetMode`, `Zone`), tipos de colección, `combinations`,
`islice` y consultas inyectadas. El resolver no debe importar `GameEngine`, gestores,
servicio, persistencia ni controladores.

Prohibido mover o reimplementar: `_card_cost_for_option`, `_effect_amount`,
`_trigger_target_commands`, `_legal_plays`, `_legal_ability_activations`,
`_validate_effect_targets`, `_card_can_be_targeted`, `_resolve_dynamic_cost`,
`_resolve_x_cost`, lógica de timing, ramas legacy y cualquier mutación. Delegar hacia
esas autoridades actuales sí está permitido; duplicarlas no.

## 13. Hotspot: `combinations`

`combinations` determina tanto cardinalidad como orden lexicográfico según el orden
del iterable de entrada. Aparece en objetivos de jugador/permanente/zona, candidatos
de reparto y selecciones de pago (descarte y sacrificio). No se deben convertir pools
a `set`, ordenar nuevamente, materializar en otro momento ni compartir un iterador
consumible entre opciones: cualquiera de esas acciones cambia los comandos visibles.

El coste puede crecer como `C(n, k)` por cada dimensión. En pagos, las dimensiones
de descarte y sacrificio se multiplican posteriormente mediante `product`.

## 14. Hotspot: `product` y construcción de comandos

`product` combina las dimensiones en el orden declarado y hace avanzar más rápido la
dimensión situada más a la derecha. Ese orden fija qué comandos sobreviven al límite:

- disparos: jugadores, permanentes, zonas, repartos;
- jugadas: jugadores, permanentes, zonas, repartos, descartes, sacrificios;
- habilidades: descartes, sacrificios, jugadores, permanentes, zonas, repartos.

`product` debe permanecer en los tres constructores externos y **no** trasladarse al
resolver. Así se conserva tanto la frontera aprobada como el orden de los campos de
los comandos.

## 15. Hotspot: `islice`, límites y orden observable

`islice(..., legal_action_enumeration_limit)` no es sólo protección de rendimiento:
es truncado observable. Se aplica en distintos niveles: opciones X, selecciones de
targets, selecciones de zona, asignaciones y cada producto de comandos. No existe un
límite global equivalente; por ejemplo, el límite de jugadas se aplica por carta y
opción de coste. Mover un `islice` hacia fuera o dentro cambia contenido y longitud.

También debe preservarse el orden final estable impuesto por
`LegalActionEnumerator`: `PlayCard` antes de `ActivateAbility`, seguido de las demás
categorías según su tabla. Ningún cambio debe depender de hash iteration order.

## 16. Hotspot: rangos X y composiciones positivas

Los rangos X son inclusivos (`minimum` a `maximum`, ambos incluidos) y se recorren en
orden ascendente antes de truncarse. Las alternativas X conservan índice derivado de
la posición de alternativas fijas/dinámicas; no deben compactarse tras un truncado.

Para un total `total` distribuido entre `parts` objetivos con cantidades estrictamente
positivas, `_positive_compositions` produce las tuplas en orden recursivo ascendente.
Su cardinalidad es:

```text
C(total - 1, parts - 1)
```

cuando `total >= parts >= 1`; en otro caso no hay composiciones. Este crecimiento se
multiplica por `C(candidatos, parts)`, de modo que materializar todo antes del corte
puede disparar memoria y tiempo. Aun así, una optimización sólo es aceptable si
preserva exactamente el prefijo observable actual.

## 17. Riesgos, invariantes y criterio de parada

Riesgos principales: cambiar orden de candidatos basado en `turn_order`, orden de
jugadores/zonas/campo, granularidad del límite, excepciones de magnitud/coste,
tratamiento de una fuente de habilidad que ya no esté en campo, índices de costes
alternativos, privacidad de IDs, y viabilidad de disparos. También existe riesgo de
confundir enumeración con autorización: un comando no enumerado aún debe pasar por
las validaciones autoritativas normales y uno enumerado puede requerir revalidación
si cambia el estado.

Invariantes obligatorios: cero mutaciones durante enumeración; mismos tipos, tuplas,
orden, excepciones y truncados; mismos callbacks autoritativos; ninguna dependencia de
capas externas; replay/digest sin cambios; ningún ID privado nuevo en observaciones.

**Criterio de parada:** si para compilar, tipar o preservar conducta fuera necesario
mover cualquiera de las nueve funciones prohibidas, timing, inmunidad, legacy,
validación o mutación, declarar **NO-GO**, revertir la implementación parcial y no
ampliar la frontera sin un diagnóstico nuevo.

## 18. Pruebas requeridas para la implementación

Antes de aceptar una extracción futura se requiere:

1. Ejecutar toda la suite (`pytest`).
2. Ejecutar de forma aislada paridad de acciones legales, incluidos límites pequeños,
   tuplas exactas, opciones por coste y no mutación.
3. Añadir pruebas unitarias del resolver para cero targets, mínimos/máximos, orden de
   combinaciones, zonas, reparto y fórmula/cardinalidad de composiciones positivas.
4. Añadir casos con límites `1`, pequeños e inferiores al espacio combinatorio para
   fijar el prefijo exacto de cada `islice`.
5. Cubrir costes normales, dinámicos, alternativos y rangos X inclusivos, incluidos
   índices y errores al ejecutar opciones inválidas.
6. Verificar paridad exacta de `PlayCard`, `ActivateAbility` y
   `ChooseTriggeredTargets`, no sólo igualdad como conjuntos.
7. Ejecutar replay 0.19 y perfiles replay 0.20, conservando digests, esquema y
   semántica legacy.
8. Ejecutar privacidad de acciones/observaciones y confirmar que IDs de mano/mazo del
   rival y candidatos ocultos sólo llegan al jugador autorizado.
9. Ejecutar resolución, pila/prioridad, inmunidad divina y fuentes de habilidad
   presentes/sacrificadas.
10. Confirmar nuevamente versión `0.20.1`, hashes de ambos PDF y árbol Git esperado.

El criterio de aceptación es paridad byte-a-byte de artefactos persistidos y paridad
estructural/ordenada de comandos observables; “mismas posibilidades” no es suficiente.
