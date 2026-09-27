# Gaps mecánicos de la microcolección de fase 2

**Resultado:** **un gap general de elegibilidad para Desafío**.

Esta evaluación se limita a las ocho candidatas reales publicadas por la
microcolección `base`: Ember Initiate, Grove Sentinel, Skyline Duelist,
Stoneback Warden, Ashen Vanguard, Verdant Colossus, First Arena Champion y
Ancient Grove Keeper. No usa cartas hipotéticas ni convierte posibilidades del
motor en necesidades de contenido.

## CARD

`base-c001` a `base-c008`, es decir, las ocho definiciones de
`BASE_CARD_DEFINITIONS`. Las ocho son criaturas permanentes con coste y Fuerza
base; `base-c003` y `base-c007` añaden únicamente `CAN_CHALLENGE`. El resto no
tiene efectos, habilidades ni keywords.

## DESIRED BEHAVIOR

Al jugarse, cada carta debe seguir el flujo ordinario de una criatura, conservar
su coste y Fuerza base y participar en combate conforme a las reglas existentes.
Skyline Duelist y First Arena Champion deben poder declarar Desafío mediante el
permiso declarativo `CAN_CHALLENGE`. Las otras seis no requieren una
resolución particular adicional.

## CURRENT ENGINE LIMITATION

El motor no permite que una criatura ordinaria inicie un Desafío, aunque tenga
`CAN_CHALLENGE`. `CombatManager._can_initiate_challenge()` exige primero que la
carta lista sea una criatura Señor; sólo después consulta el dominio de Señor o
la keyword. Como `base-c003` y `base-c007` son `CardKind.CREATURE`, no tienen
`LordDomain` y no se transforman en Señor, sus acciones de Desafío no aparecen
en la enumeración de acciones legales y una declaración directa es rechazada.

Se evitaron deliberadamente capacidades que las ocho cartas no piden: efectos
al entrar o activados, costes alternativos o variables, objetivos y reparto,
búsqueda o movimiento entre zonas, reemplazos, cambios de control, modificación
de texto o definición, efectos continuos, inmunidades, regeneración,
transformación, rangos Legendario/Divino y dominios de Señor. Su existencia en
el motor no justifica agregarlas a esta microcolección y su ausencia en una
carta no constituye un gap.

## IS GENERAL CAPABILITY?

Sí. La capacidad general ausente es que una criatura lista con
`CAN_CHALLENGE` pueda iniciar un Desafío sin tener que ser una criatura Señor.
La elegibilidad debe derivarse del tipo y las keywords efectivos, no de las
identidades de `base-c003` y `base-c007`. Se descarta expresamente cualquier
solución o rama de resolución basada en `card_id`: debe modelarse mediante el
contrato declarativo reutilizable de `CAN_CHALLENGE`.

## EVIDENCE

Se cotejaron las ocho `CardDefinition` y sus presentaciones. En el vocabulario
de tipos se inspeccionaron `CardKind` (incluido `CREATURE`), `CardRank`, `Zone`,
`Phase`, `TargetMode`, `EffectDuration`, `TriggerKind`, `LordDomain` y
`MoveReason`. En las definiciones declarativas se revisaron
`EffectDefinition`, `AbilityDefinition`, `ContinuousEffectDefinition`, costes,
filtros, reemplazos de movimiento y parches de texto. También se inspeccionó la
única keyword cerrada, `CAN_CHALLENGE`.

En resolución se revisaron el mapa de resolutores de `EffectManager`, el flujo
de juego de permanentes, combate y Desafío. Los resolutores existentes cubren
heridas, curación, Pasos, robo, daño, Fuerza, agotar/enderezar, destruir,
prevención, transformación en criatura, daño repartido, movimiento, búsqueda y
barajado de zonas, regeneración, supresión de fases, control, copia,
transformación de definición y modificación de texto. Los resolutores no
necesitan expresar algo adicional para las seis criaturas
sin texto mecánico. Sin embargo, el flujo de Desafío sólo interpreta
`CAN_CHALLENGE` después de exigir que el iniciador sea Señor. Esa precondición
hace inoperante la keyword de las dos criaturas ordinarias y demuestra el gap
de elegibilidad descrito arriba.

## PROPOSED FOLLOW-UP

Se propone ampliar la regla general de elegibilidad de Desafío para que una
criatura lista pueda iniciarlo cuando tenga efectivamente `CAN_CHALLENGE`, sin
exigir rango Señor. Debe conservarse la elegibilidad vigente de los Señores de
Reinos y cualquier comportamiento legado compatible, sin condicionales para
las dos cartas concretas. El seguimiento debe cubrir, como mínimo:

- pruebas unitarias del contrato declarativo y del resolutor, casos inválidos,
  selección de objetivos y atomicidad;
- persistencia completa en snapshots, incluida validación y migración cuando
  cambie el esquema;
- replay de comandos y decisiones, compatibilidad con artefactos anteriores y
  equivalencia del estado y del historial reproducidos; y
- determinismo frente a orden de catálogos, objetivos y colecciones, con toda
  aleatoriedad registrada o derivada de una fuente reproducible.

Ese seguimiento deberá incluir casos de enumeración y declaración directa para
criaturas ordinarias con y sin `CAN_CHALLENGE`, además de seguir excluyendo
condicionales por `card_id`. Esta nota documenta el gap; no implementa todavía
el cambio del motor ni convierte las demás capacidades deliberadamente evitadas
en trabajo pendiente.
