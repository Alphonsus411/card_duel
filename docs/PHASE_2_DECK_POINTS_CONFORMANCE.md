# Conformidad de puntos de mazo de Fase 2-B

Este documento consolida la conclusión normativa y técnica sobre los puntos de
construcción sin reproducir el texto de las fuentes. Mantiene la paginación
empleada por las auditorías: `Fantasy Tokens.pdf`, físicas 3 y 5, y
`Fantasy Tokens Edicion Mitica.pdf`, física 2 / interna 1. El inventario y la
clasificación completos siguen en `MYTHIC_RULES_AUDIT.md`.

## Normativa confirmada

La fuente base distingue el uso de una carta y la construcción del mazo, pero
emplea el mismo valor en ambos casos: el coste impreso/declarado de una carta se
expresa en Pasos y los puntos del mazo se calculan sumando esos valores. Según
la evidencia disponible, por tanto, `CardDefinition.cost` es la fuente
autoritativa tanto para el coste en Pasos como para el total de construcción;
no existe evidencia para mantener una segunda puntuación por carta.

La misma fuente confirma un mínimo base de **50 puntos**. Ese mínimo no pertenece
a toda instancia neutra de `DeckConstructionPolicy`: se activa exactamente en
las fábricas de política `classic_deck_policy()` y `mythic_deck_policy()`, que
declaran `min_points=50`. Una política genérica conserva `min_points=None` salvo
configuración explícita del llamador.

## Implementación existente

La validación individual ya sumaba de forma embebida `card.cost` para aplicar
los límites de puntos. Fase 2-B hizo explícito ese conocimiento mediante la API
reutilizable `deck_points(cards)`, que materializa el iterable una vez y devuelve
la suma entera. `DeckConstructionPolicy.validate()` reutiliza esa misma
semántica para el mínimo y para el techo opcional `point_budget`.

Los perfiles Clásico y Mítico comparten el mínimo base de 50 y dejan
`point_budget=None` por defecto. Así, la implementación modela lo confirmado sin
convertir una cifra Mítica dudosa en regla del motor.

## Cambios introducidos

Fase 2-B separó tres responsabilidades que antes podían confundirse:

1. `deck_points()` ofrece el cálculo reusable basado exclusivamente en
   `CardDefinition.cost`;
2. `min_points` modela declarativamente el mínimo individual y las fábricas de
   formato activan el valor confirmado de 50; y
3. `validate_deck_group(..., require_equal_points=True)` modela la comparación
   opcional entre varios mazos fuera de `DeckConstructionPolicy`.

No se añadió un campo de puntos a `CardDefinition`, ni una tabla paralela, ni un
presupuesto implícito.

## N-POINTS-01

**`N-POINTS-01` sigue abierto y bloqueado.** La fuente Mítica, en física 2 /
interna 1, reúne referencias incompatibles a 200, 300 y al intervalo 300–400.
El código no elige **200, 300, 400 ni ninguna otra cifra Mítica**. En particular,
ninguna de ellas es el valor predeterminado de `point_budget` en las políticas
Clásica o Mítica.

Un consumidor puede configurar expresamente un techo para un formato propio,
pero hacerlo es configuración de aplicación y no resuelve ni reinterpreta
`N-POINTS-01`. El bloqueo requiere aclaración normativa oficial.

## Cost vs deck points

`CardDefinition.cost` representa el coste base declarativo en Pasos. Para
construcción, cada copia aporta exactamente ese mismo entero al total del mazo;
renombrar la carta, cambiar su presentación editorial o su identificador no
cambia sus puntos. Costes alternativos, dinámicos o efectivos durante una
partida tampoco crean otra puntuación de construcción según la evidencia
auditada.

Esta identidad evita duplicación y divergencias: el total se deriva con
`sum(card.cost for card in cards)` a través de `deck_points()`.

## Reglas relacionales

La igualdad de puntos no es una propiedad de un mazo aislado, sino una relación
entre los mazos participantes. Por eso se valida fuera de
`DeckConstructionPolicy`, mediante `validate_deck_group`, y **sólo cuando el
formato la solicita** con `require_equal_points=True`. Con el valor predeterminado
`False`, mazos con totales diferentes no producen una incidencia relacional.

Esta separación permite validar primero cada mazo contra su política individual
y después comparar el grupo sin atribuir a la política individual información
que no recibe.

## Límites

- Este documento resume las fuentes; no sustituye la auditoría ni transcribe
  extensamente los PDF.
- Las referencias normativas conservadas son Base, físicas 3 y 5, y Mítica,
  física 2 / interna 1.
- El mínimo de 50 y la fórmula de suma están confirmados; un máximo Mítico no.
- `point_budget` sólo expresa un techo aportado explícitamente por el llamador.
- La API no decide balance, legalidad de colecciones ni equivalencia salvo que
  las políticas y el formato correspondientes los soliciten.

