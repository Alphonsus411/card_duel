# Auditoría normativa de Edición Mítica

## Alcance, fuentes y jerarquía

Esta auditoría separa reglas, formatos, organización y cartas; no intenta
convertir el contenido de una carta en una regla del juego.

1. `Fantasy Tokens.pdf` es la **fuente base**.
2. `Fantasy Tokens Edicion Mitica.pdf`, fechado **2018-06-13**, prevalece
   únicamente cuando modifica expresamente una regla base.
3. Una adición Mítica no constituye, por sí sola, una contradicción con la base.
4. Toda contradicción o ambigüedad permanece bloqueada: no se elige una
   interpretación normativa sin aclaración oficial.
5. El Markdown, el código y las pruebas de este repositorio son materiales
   derivados. Sirven para trazabilidad y protección técnica, pero no son prueba
   normativa.

No se reproduce aquí el texto completo de ninguno de los PDF. Las paráfrasis
son deliberadamente breves y el texto particular de cartas solo se inventaría
como categoría D, nunca como fundamento de una regla universal.

## Convención de paginación Mítica

Toda referencia al PDF Mítico usa primero la página física del archivo y luego
la página interna impresa. La portada es **física 1, sin numeración interna**;
introducción y mazos ocupan **físicas 2–3 / internas 1–2**; Drenaje,
Legendarios, Divinos y los primeros Señores están en **física 3 / interna 2**;
y Señores de los Reinos, Desafío y el comienzo del inventario están en
**física 4 / interna 3**. No se usa «p. 3» aisladamente para esa última página.

## Taxonomía obligatoria

Cada hallazgo de la tabla tiene exactamente una categoría:

- **A:** regla universal o actualización mecánica.
- **B:** formato o construcción de mazo.
- **C:** organización o torneo físico.
- **D:** texto particular de carta.
- **E:** ambigüedad o contradicción; queda bloqueada.

## Comienzo y límites del corpus

La sección de reglas generales comienza bajo `INTROITOS` en **física 2 /
interna 1** y continúa hasta el párrafo de Desafío en **física 4 / interna 3**.
El encabezado `EDICION MITICA` aparece en **física 4 / interna 3**,
inmediatamente después de Desafío. El párrafo siguiente anuncia el inventario y
la primera entrada concreta es la carta de colección nº 001. **Desde ese
encabezado comienza el corpus de cartas concretas (categoría D)** y termina el
bloque de reglas generales de esta auditoría. Nada situado desde allí se usa
para generalizar una mecánica.

## Inventario clasificado

| ID | Categoría | Ubicación | Hallazgo y decisión de auditoría |
|---|---|---|---|
| M-SCOPE-01 | B | Mítica, física 2 / interna 1 | La introducción declara obligatorias las actualizaciones para juego competitivo y recomienda su uso en partidas amistosas. Es alcance de formato, no sustitución indiscriminada de toda regla base. |
| N-POINTS-01 | E | Mítica, física 2 / interna 1 | **Contradicción abierta:** el mismo bloque menciona 200 puntos por baraja y jugador, un máximo situado en el intervalo 300–400, y aproximadamente 300 como recomendación; después vuelve a indicar 300 al resumir los ajustes. La base, por su parte, exige equivalencia y un mínimo de 50 (`Fantasy Tokens.pdf`, reglas básicas 1–2, p. 5). No se eligen 200, 300, 400 ni otro valor normativo. |
| M-DECK-02 | B | Mítica, física 2 / interna 1 | Construcción: mínimo de 40 y máximo de 60 cartas; hasta cinco copias de una no Legendaria y cuatro de una Legendaria, sujeto a las restricciones de formato. Estos límites se registran aparte de `N-POINTS-01`. |
| M-FORMAT-03 | B | Mítica, física 2 / interna 1 | Clásico admite todas las ediciones con restricciones propias para coste cero; Mística admite desde Edición Mítica, prohíbe Alfa/Beta y fija para sus cartas costes entre 5 y 50 Pasos. Son reglas de formato, no texto universal de cartas. |
| M-DECK-04 | B | Mítica, física 2 / interna 1 | Los ajustes base por coste en Pasos se declaran vigentes y se añaden límites de cartas, puntos y edición. La cifra de puntos permanece bloqueada por `N-POINTS-01`. |
| M-TOURNAMENT-01 | C | Mítica, física 2 / interna 1; física 3 / interna 2 | Mística/Edición Mítica entra en el circuito competitivo y Clásico queda fuera del circuito oficial o clasificatorio descrito. |
| M-TOURNAMENT-02 | C | Mítica, física 3 / interna 2 | Administración física: texto y coste deben ser claros, legibles e identificables; una carta manuscrita o infiel se sustituye según el documento, y dos o más irregularidades provocan pérdida. Se registra la política, sin extenderla a reglas mecánicas. |
| M-DRAIN-01 | A | Mítica, física 3 / interna 2 | Drenaje se introduce como habilidad universal: una vez por turno activo, recupera hasta cinco Pasos; el primer Paso no añade Heridas y cada Paso adicional añade tres. No está disponible en Fase Pasiva. |
| M-LEGENDARY-01 | A | Mítica, física 3 / interna 2 | Los Legendarios reciben un subtipo procedente de los tipos existentes y son afectados normalmente por Recursos Rápidos, Eventos o habilidades salvo inmunidad indicada. Es una actualización general expresa. |
| M-DIVINE-01 | A | Mítica, física 3 / interna 2 | Los Divinos reciben subtipo, son inmunes a Eventos, Recursos Rápidos y habilidades de criaturas permanentes, pueden transmutarse y usar habilidades bajo sus condiciones. Esta modificación expresa prevalece sobre la inmunidad completa, incluso al descarte, de la regla básica 19 (`Fantasy Tokens.pdf`, p. 8). |
| M-LORD-ABYSS-01 | A | Mítica, física 3 / interna 2 | Señor del Abismo: nuevo tipo de criatura permanente; su Fuerza parte del coste, puede variar al usar habilidades y a cero va a la Pila de Descartes. No ataca ni bloquea, pero puede ser atacado y recibir daño salvo protección aplicable. |
| M-LORD-ELYSIUM-01 | A | Mítica, física 3 / interna 2 | Señor del Elíseo comparte las propiedades mecánicas indicadas para Abismo y se diferencia por su dominio temático. |
| M-LORD-MAGIC-01 | A | Mítica, física 3 / interna 2 | Señor de la Magia se presenta como análogo mecánico de los anteriores y neutral respecto de facción. |
| M-LORD-KINGDOMS-01 | A | Mítica, física 4 / interna 3 | Señor de los Reinos puede transformarse en criatura para atacar, bloquear y usar sus capacidades. |
| M-LORD-EVENT-01 | E | Mítica, física 3 / interna 2 | **Ambigüedad abierta:** que las propiedades de Señor se usen «a modo de Eventos» respalda su temporización en Fase Activa, pero no basta para reclasificar universalmente las habilidades como cartas o efectos de tipo Evento. Solo queda respaldada la ventana de Fase Activa; inmunidades, objetivos, pila y demás consecuencias de una reclasificación permanecen bloqueados. |
| M-CHALLENGE-01 | A | Mítica, física 4 / interna 3 | Desafío es una regla universal utilizable una vez por turno en Fase Activa y sustituye el combate normal por el duelo descrito. Los Señores de los Reinos transformados pueden usarla; Abismo, Elíseo y Magia no pueden sin capacidad apropiada. Los detalles no expresados no se completan con textos de cartas. |
| M-CARDS-START-01 | D | Mítica, física 4 / interna 3 | `EDICION MITICA` y el anuncio del descriptivo de colección marcan el comienzo del inventario de cartas concretas; la nº 001 es su primera entrada. Todo hallazgo posterior sobre una carta pertenece a D y no prueba reglas A. |

## Bloqueos y efectos derivados

- `N-POINTS-01` impide afirmar un total normativo de puntos para barajas Míticas.
- `M-LORD-EVENT-01` impide tratar todas las habilidades de Señor como Eventos;
  solo permite documentar la Fase Activa indicada.
- Las demás dudas que requieran completar silencios del texto siguen bloqueadas.
- Una implementación o una prueba que elija una conducta puede proteger el
  estado técnico existente, pero no resolver ninguno de esos bloqueos.
