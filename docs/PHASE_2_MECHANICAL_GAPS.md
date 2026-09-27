# Gaps mecánicos de la microcolección de fase 2

**Resultado:** **un gap requerido para las dos cartas con `CAN_CHALLENGE`**.

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
permiso declarativo `CAN_CHALLENGE`. Ninguna de las ocho cartas requiere una
resolución particular adicional.

## CURRENT ENGINE LIMITATION

El permiso declarado no basta para expresar esos comportamientos.
`CombatManager._can_initiate_challenge()` comprueba primero que la carta sea una
criatura lista **y** un Señor criatura. `_is_lord_creature()` requiere a su vez
una definición con `lord_domain` y una instancia transformada. Como `base-c003`
y `base-c007` son definiciones `CREATURE`, sin dominio ni transformación, el
método devuelve `False` antes de consultar `CAN_CHALLENGE`. En consecuencia, el
motor no enumera `DeclareChallenge` para ninguna de ellas y también rechaza el
comando si se construye directamente.

Se evitaron deliberadamente capacidades que las ocho cartas no piden: efectos
al entrar o activados, costes alternativos o variables, objetivos y reparto,
búsqueda o movimiento entre zonas, reemplazos, cambios de control, modificación
de texto o definición, efectos continuos, inmunidades, regeneración,
transformación, rangos Legendario/Divino y dominios de Señor. Su existencia en
el motor no justifica agregarlas a esta microcolección y su ausencia en una
carta no constituye un gap.

## IS GENERAL CAPABILITY?

Sí. El gap debe resolverse mediante un contrato declarativo general: por
ejemplo, definiendo si `CAN_CHALLENGE` autoriza a toda criatura lista o si el
Desafío debe continuar reservado a Señores y, en ese caso, modelando estas
cartas de acuerdo con ese requisito. Se descarta expresamente cualquier
solución o rama de resolución basada en `card_id`; la elegibilidad debe depender
de tipos, estado, dominios y keywords reutilizables.

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
transformación de definición y modificación de texto. Las seis criaturas sin
texto mecánico ya están cubiertas. Las otras dos exponen la discrepancia entre
la presencia serializable de `CAN_CHALLENGE` y el contrato de elegibilidad, que
limita su interpretación a Señores transformados.

## PROPOSED FOLLOW-UP

La Fase 2-A permanece abierta. Antes de cerrarla se debe decidir y documentar el
contrato general de `CAN_CHALLENGE`, implementar la alternativa elegida y añadir
pruebas que usen `base-c003` y `base-c007` para verificar tanto la enumeración
como la ejecución de `DeclareChallenge`. El cambio deberá cubrir, como mínimo:

- pruebas unitarias del contrato declarativo y del resolutor, casos inválidos,
  selección de objetivos y atomicidad;
- persistencia completa en snapshots, incluida validación y migración cuando
  cambie el esquema;
- replay de comandos y decisiones, compatibilidad con artefactos anteriores y
  equivalencia del estado y del historial reproducidos; y
- determinismo frente a orden de catálogos, objetivos y colecciones, con toda
  aleatoriedad registrada o derivada de una fuente reproducible.

Ese seguimiento deberá seguir excluyendo condicionales por `card_id`. Esta nota
no reserva una implementación ni convierte las capacidades deliberadamente
evitadas en trabajo pendiente.
