# Refactor conservador de `ActionOptionResolver` — 0.20.1

> El diagnóstico previo y la frontera autorizada se conservan en
> `ACTION_OPTION_RESOLVER_DIAGNOSTIC_0.20.1.md`; este documento describe la
> arquitectura finalmente aceptada.

## 1. Decisión y alcance

**GO.** Se acepta la extracción mecánica de cinco algoritmos de enumeración de
opciones. No se introduce una regla nueva, no se cambia la autorización de comandos
y no se amplía la frontera a ejecución, timing, inmunidad, persistencia o legacy.

Las cinco funciones extraídas desde `GameEngine` son:

1. `_card_cost_options` → `ActionOptionResolver.card_cost_options`;
2. `_target_selections` → `ActionOptionResolver.target_selections`;
3. `_zone_target_selections` → `ActionOptionResolver.zone_target_selections`;
4. `_allocation_selections` → `ActionOptionResolver.allocation_selections`;
5. `_positive_compositions` → `ActionOptionResolver.positive_compositions`.

Las fachadas privadas del motor permanecen y delegan, para no romper pruebas ni
consumidores internos que usan los nombres históricos.

## 2. Funciones expresamente no movidas

Continúan en `GameEngine`: `_card_cost_for_option`, `_effect_amount`,
`_trigger_target_commands`, `_legal_plays`, `_legal_ability_activations`,
`_validate_effect_targets`, `_card_can_be_targeted`, `_resolve_dynamic_cost` y
`_resolve_x_cost`. Tampoco se movieron validación de pagos, timing, prioridad,
stack, ejecución de comandos, emisión de eventos ni mutación de zonas/estado.

Esta separación es esencial: el resolver enumera candidatos, pero el motor conserva
la decisión autoritativa de si un `PlayCard`, `ActivateAbility` o
`ChooseTriggeredTargets` recibido puede ejecutarse.

## 3. Arquitectura anterior y posterior

```text
ANTES
LegalActionEnumerator
  └─ GameEngine
       ├─ orquestación de acciones legales
       ├─ cinco algoritmos combinatorios
       └─ validación y ejecución autoritativas

DESPUÉS
LegalActionEnumerator
  └─ GameEngine (ActionOptionContext)
       ├─ orquestación, fachadas, validación y ejecución
       └─ ActionOptionResolver
            └─ cinco algoritmos combinatorios de consulta
```

`GameEngine` crea un único resolver. No hay ciclo de importación hacia el motor ni
dependencia del resolver respecto de managers, controladores o almacenamiento.

## 4. Contrato mínimo del contexto y estado compartido

`ActionOptionContext` expone únicamente:

- `_option_state`, el **mismo objeto `GameState`** autoritativo del motor;
- `_option_enumeration_limit`;
- callbacks de consulta para coste dinámico, coste X, elegibilidad por inmunidad y
  magnitud del efecto.

`ActionOptionResolver` conserva **sólo `_context`** en su `__dict__`. No posee,
clona, cachea ni sustituye `GameState`; consulta exactamente la instancia compartida
por el motor. La prueba diferencial comprueba ambas propiedades.

## 5. No mutación

Los cinco métodos son consultas. La caracterización serializa el estado completo con
el codec estable antes y después de cada llamada y exige igualdad exacta. El resolver
no paga costes, no mueve cartas, no reserva objetivos y no emite eventos. Los
callbacks inyectados son las consultas autoritativas preexistentes.

## 6. Orden observable y límites

El resultado de acciones legales es una secuencia, no un conjunto. Se preservan:

- el orden del iterable de candidatos;
- el recorrido ascendente de cardinalidades y valores X;
- el orden lexicográfico de `itertools.combinations`;
- el orden recursivo ascendente de composiciones positivas;
- el orden de dimensiones de cada `product` en los constructores del motor;
- los índices de costes alternativos y las tuplas de los comandos;
- el punto exacto de cada `islice`.

`legal_action_enumeration_limit` se aplica donde ya era observable: por rango X,
selección, allocation y producto externo. No se reemplaza por un límite global ni se
materializa/reordena un conjunto intermedio.

## 7. Multiplicadores combinatorios principales

Los multiplicadores que gobiernan coste y truncado son, explícitamente:

1. **Combinaciones de targets por cardinalidad:** para un pool de `n` y cardinalidad
   `k`, cada dimensión aporta `C(n, k)`; si se admiten varias cardinalidades se suman
   sus coeficientes.
2. **Composiciones positivas por selección distribuida:** repartir `t` unidades
   positivas entre `k` targets aporta `C(t - 1, k - 1)` cuando `t >= k >= 1`, y se
   multiplica por las selecciones de targets.
3. **Producto de targets, zonas, allocations y pagos:** los tamaños de targets de
   jugador, permanente, zona, allocations, descartes y sacrificios se multiplican en
   el `product` correspondiente; la dimensión derecha avanza más rápido.
4. **Rango de cada coste X:** cada coste X aporta `maximum - minimum + 1` opciones
   antes del límite, con extremos inclusivos y recorrido ascendente.
5. **Alternativas de coste:** se agregan coste normal/X principal, alternativas
   fijas, dinámicas y cada alternativa X, conservando sus índices.
6. **Combinaciones de descarte y sacrificio:** un pago multiplica
   `C(cartas_elegibles, descartes)` por
   `C(permanentes_elegibles, sacrificios)`.

Estos límites son protección de recursos **y** contrato funcional: sólo el mismo
prefijo ordenado puede sobrevivir al truncado.

## 8. Compatibilidad de acciones legales

La prueba diferencial congela los cuerpos anteriores y compara igualdad estructural
y de orden con el resolver. Además compara, mediante el oráculo previo del enumerador,
las acciones públicas `PlayCard`, `ActivateAbility` y
`ChooseTriggeredTargets`. Cubre objetivos de jugador, permanente y zona,
allocations, inmunidad, costes fijos/dinámicos/X/alternativos, pagos por descarte y
sacrificio y límites pequeños.

Las fachadas garantizan compatibilidad interna; no cambian dataclasses de comandos,
campos, exportaciones públicas ni mensajes de validación.

## 9. Replay, legacy y persistencia

`ActionOptionResolver` **no participa en snapshots, codec, replay ni persistencia**.
No añade campos a `GameState` ni tipos al esquema. La suite integral valida 30
roundtrips y los perfiles de replay existentes.

La matriz diferencial se ejecuta con `EngineSemantics.CURRENT` y
`EngineSemantics.LEGACY_019`. El resolver no almacena ni consulta la semántica: las
ramas legacy continúan en sus autoridades anteriores. Por ello tampoco altera
digests ni migra artefactos históricos.

## 10. Privacidad

La extracción no crea un canal de observación ni una API pública. Los candidatos se
consumen dentro de la enumeración autorizada existente y los DTO públicos siguen
filtrándose en las capas actuales. El resolver no persiste ni expone IDs de mano o
mazo rival, y la verificación integral mantiene las pruebas de privacidad existentes.

## 11. Resultado

La extracción satisface el diagnóstico: cinco helpers aislados, un contexto mínimo,
el mismo estado autoritativo, consultas sin mutación y paridad ordenada en ambos
perfiles semánticos. La validación full obtiene 89 % de cobertura, ejecuta mypy y
compileall, 300 simulaciones/54 000 comandos, 30 roundtrips y la instalación del
wheel en Python 3.11, 3.12 y 3.13.

## 12. Deuda restante y criterio NO-GO futuro

Permanecen intencionadamente la combinatoria externa y las nueve funciones excluidas
en `GameEngine`. También permanece la posibilidad de explosión combinatoria antes de
ciertos productos; optimizarla requerirá demostrar el mismo prefijo y granularidad
de límites. No se propone trasladar validación, inmunidad, pagos, timing, legacy o
mutación. Cualquier cambio que necesitase hacerlo debe volver a diagnóstico y se
considera **NO-GO** dentro de este alcance.

La lista ideal de la iniciativa completa queda limitada a `options.py`, `game.py`,
la prueba diferencial y los tres informes (diagnóstico, refactor y resultados). No
se modifican PDF, snapshots, fixtures, codec, replay ni configuración de release.
