# Fase 2-C: inventario y selección del corpus Mítico por raza

## Estado y límites de esta entrega

**Resultado:** inventario editorial completo; **ninguna definición ejecutable
creada**. Este documento es una transcripción de trabajo que debe revisarse
antes de incorporar contenido al motor o a un manifiesto.

La revisión parte del commit
`352269d8bb80d3b0f427c93c11882be5c56093e6`, destinado a `main`, y conserva
`version = "0.20.1"` en `pyproject.toml`. Se leyeron primero, por este orden,
`Fantasy Tokens.pdf`, `Fantasy Tokens Edicion Mitica.pdf`,
`MYTHIC_RULES_AUDIT.md`, `MYTHIC_CARD_CORPUS_SCOPE.md`,
`PHASE_2_MECHANICAL_GAPS.md` y `PHASE_2_DECK_POINTS_CONFORMANCE.md`.

El catálogo comienza en Mítica, **página física 4 / interna 3**, con la entrada
001, y termina en la física 18 / interna 17 con la 189. La identidad se obtuvo
del número y del texto de cada entrada, no de su vecindad. Hay dos anomalías
editoriales que se preservan sin corregir: no existen entradas 091–099 y tanto
`Nirvana` como `Tambor Chamánico` llevan el nº 176.

### Criterio conservador de raza

Una carta se asocia a una raza sólo cuando su propio nombre o su propio texto
la identifica inequívocamente como miembro de ella. Una carta que busca,
beneficia, daña o menciona una raza **no adquiere** esa raza. Tampoco se hereda
raza por cercanía en el PDF. Los oficios o estados (`Clérigo`, `Monje`,
`Nigromante`, `Cultista`), los dominios de Señor y los nombres propios no se
convierten en raza sin una declaración de la fuente. Cuando nombre y texto no
permiten decidir, el campo es `AMBIGUOUS`.

## Cobertura de todas las entradas del catálogo

Esta tabla demuestra el recorrido exhaustivo de las entradas impresas. Los
intervalos son sólo una compactación de cobertura, no una atribución racial.

| Física / interna | Números o tokens originales observados | Cantidad | Incidencias |
|---|---:|---:|---|
| 4 / 3 | 001–007 | 7 | Inicio del catálogo |
| 5 / 4 | 008–019 | 12 | — |
| 6 / 5 | 020–033 | 14 | — |
| 7 / 6 | 034–045 | 12 | — |
| 8 / 7 | 046–057 | 12 | — |
| 9 / 8 | 058–070 | 13 | — |
| 10 / 9 | 071–083 | 13 | — |
| 11 / 10 | 084–090, 100–106 | 14 | 091–099 no aparecen en la fuente |
| 12 / 11 | 107–115 | 9 | — |
| 13 / 12 | 116–127 | 12 | — |
| 14 / 13 | 128–139 | 12 | — |
| 15 / 14 | 140–152 | 13 | — |
| 16 / 15 | 153–165 | 13 | — |
| 17 / 16 | 166–176, 176, 177 | 13 | nº 176 duplicado en dos entradas distintas |
| 18 / 17 | 178–189 | 12 | Fin del catálogo |
| **Total** | **001–090, 100–189 y un segundo 176** | **181** | **181 entradas recorridas** |

## Inventario de razas detectadas

La columna «cartas inequívocas» es exhaustiva bajo el criterio anterior. Las
cartas que sólo mencionan una raza se excluyen deliberadamente. Por ejemplo,
`El Orbe Celeste` no es Ángel/Elfo/Pixie; `El Emperador Oscuro` beneficia a los
Elfos Oscuros pero no declara serlo; y `Ferrick Barba Roja` beneficia a los
Enanos pero su propia raza queda `AMBIGUOUS`.

| Raza detectada | Cartas inequívocamente asociadas (nº: nombre exacto) | Tamaño | Legibilidad |
|---|---|---:|---|
| Pixie | 005 `Pixie Cantante.`; 006 `Pixie Bailarina.`; 007 `Pixie de la Luz.`; 008 `Pixie Melancólica.`; 009 `Pixie Encantadora.`; 010 `Pixie Abjuradora Aprendiz.`; 011 `Pixie Ladrona.`; 012 `Pixie Mentirosa.` | 8 | Completa |
| Hada | 013 `Selena, el Hada de los Deseos.`; 014 `Alisa, el Hada del Sueño.`; 015 `Alondra, el Hada de los Juegos.`; 016 `Melara, el Hada Naturista.`; 017 `La Reina de las Hadas, Elora.` | 5 | Completa |
| Elfo | 023 `Elfo de los Bosques.`; 024 `Elfo Explorador.`; 025 `Elfo Montaraz.`; 026 `Elfo Adivinador.`; 027 `Elfo Duelista.`; 028 `Elfo Cabalista.`; 029 `Alberich, el Rey de los Elfos.` | 7 | Completa |
| Goblin | 036 `Goblin Traicionero.`; 037 `Goblin Espía.`; 038 `Goblin Kamikaze.`; 039 `Goblin Negociador.`; 040 `Goblin Chapucero.`; 041 `Goblin Volador.`; 042 `Graz, el General Goblin.`; 043 `Zurullo, Vidente Goblin.`; 044 `Kril, Consejero Goblin.`; 045 `Ojo Podrido, Rey de los Goblin.` | 10 | Completa |
| Orco | 052 `Orco Berseker.`; 053 `Orco Batidor.`; 054 `Orco Mercenario.`; 055 `Orco Cavernario.`; 056 `Orco Sargento.`; 057 `Orco Chamán.`; 058 `Orco Anciano.`; 059 `Furia Sangrienta, Rey de los Orcos.` | 8 | Completa |
| Zombi | 065 `Zombi de la Ciénaga.`; 066 `Zombi de la Horda.`; 067 `Zombi Guerrero.`; 068 `Zombi Arcanista.`; 069 `Zombi Sargento.`; 070 `Zombi Táctico.` | 6 | Completa |
| Aberración | 072 `Aberración Necrótica.`; 073 `Aberración del Abismo.`; 178 `Aberración Visionaria.` | 3 | Completa; 072 tiene coste compuesto legible |
| Elfo Oscuro | 118 `Elfo Oscuro.`; 119 `Elfo Oscuro Duelista.`; 120 `Elfo Oscuro Batidor.`; 121 `Elfo Oscuro Arcano.`; 122 `Elfo Oscuro Adivino.`; 123 `Elfo Oscuro Pretoriano.`; 124 `Sabine, la Princesa Oscura.` | 7 | Completa; 124 declara «Sabine es un Elfo Oscuro» |
| Espíritu | 134 `Espíritu Encadenado.`; 136 `Espíritu Atormentado.` | 2 | Completa |
| Ángel | 140 `Ángel de la Guarda.`; 141 `Ángel de Piedad.`; 142 `Ángel de la Justicia.`; 143 `Ángel de la Verdad.`; 144 `Ángel de la Muerte.`; 145 `Arcángel.` | 6 | Completa |
| Ninfa | 151 `Ninfa de los Bosques.`; 152 `Ninfa Seductora.`; 153 `Ninfa Naturista.`; 154 `Ninfa Abjuradora.`; 155 `Selena, Ninfa Principal.`; 156 `Argéntea, Reina de las Ninfas.` | 6 | Completa |
| Primigenio | 181 `Bailarín Primigenio.` | 1 | Completa |

`Alma en Pena.`, `Poltergeist.`, `Esfinge Ancestral.`, `Cronos, el
Devorador.`, `Portador de Plagas.`, `Flautista del Abismo.`, `Cultista
Cósmico.` y `Profeta del Abismo.` pueden sugerir una naturaleza fantástica,
pero la entrada no imprime un subtipo racial inequívoco: **raza `AMBIGUOUS`**.
Lo mismo se aplica a cualquier otra criatura no enumerada en la tabla.

## Comparación y selección de dos razas completas

| Raza | Tamaño | Contratos generales aprovechables | Gaps o riesgos dominantes |
|---|---:|---|---|
| Pixie | 8 | giro/enderezado, robo, daño, inmunidad, movimiento | bloqueo de permanentes, prohibición por tipo, azar y mitad de mazo |
| Hada | 5 | vuelo, inmunidad, modificación de Fuerza, giro | mitad de mazo y descarte/destrucción masivos |
| **Elfo** | **7** | búsqueda, barajado, prevención, Desafío, inmunidad, modificación de Fuerza, transformación de Señor | búsqueda repetida hasta coincidencia y coste de Fuerza del Señor |
| Goblin | 10 | daño, movimiento, búsqueda, vuelo, Fuerza | moneda, anexión, robo entre Reservas y búsquedas variables |
| Orco | 8 | combate, daño, Desafío, inmunidad, búsqueda, transformación | Dureza variable y no-enderezado persistente |
| Zombi | 6 | giro, búsqueda, prevención, Fuerza | Infectar y cambio persistente de Fuerza sin cambiar coste |
| Aberración | 3 | giro, inmunidad, Fuerza, descarte | coste compuesto y barrido selectivo |
| Elfo Oscuro | 7 | combate, inmunidad, búsqueda, giro, destrucción, Fuerza | ataque doble y gasto/recuperación de Fuerza |
| Espíritu | 2 | vuelo, giro, transferencia de Pasos | Intangible y bloqueo de enderezado ligado a fuente |
| **Ángel** | **6** | vuelo, inmunidad, prevención, curación, destrucción, búsqueda, Fuerza | ataque doble y disparo al salir hacia la Pila |
| Ninfa | 6 | giro, inmunidad, prevención, Fuerza, devolución a mano | supresión global de fase/tipos y enlace de enderezado |
| Primigenio | 1 | inmunidad, giro, robo, transmutación | coste de girar cinco permanentes |

Se seleccionan **Elfo (023–029)** y **Ángel (140–145)**. Son conjuntos
completos, totalmente legibles y de tamaño útil (13 cartas en total); concentran
su comportamiento en contratos generales ya auditados —búsqueda y movimiento,
barajado, prevención, curación/daño, Fuerza, inmunidad, transformación y
`CAN_CHALLENGE`— y evitan costes compuestos, monedas, control ajeno, anexiones,
supresiones globales y destrucción/reconstrucción masiva de zonas. No se elimina
ninguna carta difícil: 026, 029, 142 y 145 permanecen en el corpus y sus riesgos
se señalan expresamente.

### Cobertura probatoria de las razas seleccionadas

| Raza | Números que la constituyen | Entradas detalladas abajo | Omitidas |
|---|---|---:|---:|
| Elfo | 023, 024, 025, 026, 027, 028, 029 | 7/7 | 0 |
| Ángel | 140, 141, 142, 143, 144, 145 | 6/6 | 0 |

## Fichas fuente completas: Elfo

En estas fichas, `Fuerza` sólo copia un valor cuando la fuente dice
`Coste/Fuerza`; `rango` y `subtipo` no se reconstruyen. «Texto de reglas»
conserva ortografía, cifras, mayúsculas y terminología de la fuente.

### 023 — Elfo de los Bosques.

- **Página:** física 6 / interna 5
- **Número o token original:** nº023
- **Nombre exacto:** `Elfo de los Bosques.`
- **Raza:** Elfo
- **Coste:** 10
- **Fuerza:** 10
- **Tipo:** `Token de Criatura`
- **Rango:** `AMBIGUOUS`
- **Subtipo:** `AMBIGUOUS`
- **Texto completo de reglas:** “Cuando el Elfo de los Bosques entre en juego, busca una carta de Recurso Rápido de tu mazo de Recursos y ponla en tu mano, baraja tu mazo.”

### 024 — Elfo Explorador.

- **Página:** física 6 / interna 5
- **Número o token original:** nº024
- **Nombre exacto:** `Elfo Explorador.`
- **Raza:** Elfo
- **Coste:** 10
- **Fuerza:** 10
- **Tipo:** `Token de Criatura`
- **Rango:** `AMBIGUOUS`
- **Subtipo:** `AMBIGUOUS`
- **Texto completo de reglas:** “Cuando esta carta entre en juego, busca una carta de Elfo de tu mazo de Recursos, ponla en tu mano, baraja tu mazo.”

### 025 — Elfo Montaraz.

- **Página:** física 6 / interna 5
- **Número o token original:** nº025
- **Nombre exacto:** `Elfo Montaraz.`
- **Raza:** Elfo
- **Coste:** 10
- **Fuerza:** 10
- **Tipo:** `Token de Criatura`
- **Rango:** `AMBIGUOUS`
- **Subtipo:** `AMBIGUOUS`
- **Texto completo de reglas:** “Cuando este naipe entre en juego, busca una carta de Evento y ponla en tu mano. Baraja tu mazo de Recursos.”

### 026 — Elfo Adivinador.

- **Página:** física 6 / interna 5
- **Número o token original:** nº026
- **Nombre exacto:** `Elfo Adivinador.`
- **Raza:** Elfo
- **Coste:** 10
- **Fuerza:** 10
- **Tipo:** `Token de Criatura`
- **Rango:** `AMBIGUOUS`
- **Subtipo:** `AMBIGUOUS`
- **Texto completo de reglas:** “Cuando esta carta entre en juego, mira la primera carta de tu mazo, si es de Elfo, ponla en tu mano, sino, ponla en la Pila de Descartes. Continua este proceso hasta sacar un naipe de este tipo.”

### 027 — Elfo Duelista.

- **Página:** física 6 / interna 5
- **Número o token original:** nº027
- **Nombre exacto:** `Elfo Duelista.`
- **Raza:** Elfo
- **Coste:** 10
- **Fuerza:** 10
- **Tipo:** `Token de Criatura`
- **Rango:** `AMBIGUOUS`
- **Subtipo:** `AMBIGUOUS`
- **Texto completo de reglas:** “Cuando el Elfo Duelista entra en el tablero, puedes designar a cualquier criatura del jugador objetivo para usar la regla de Desafío con ella.”

### 028 — Elfo Cabalista.

- **Página:** física 6 / interna 5
- **Número o token original:** nº028
- **Nombre exacto:** `Elfo Cabalista.`
- **Raza:** Elfo
- **Coste:** 10
- **Fuerza:** 10
- **Tipo:** `Token de Criatura`
- **Rango:** `AMBIGUOUS`
- **Subtipo:** `AMBIGUOUS`
- **Texto completo de reglas:** “Girar el Elfo Cabalista, pagar 5 Pasos: la criatura objetivo previene todo el daño de combate hasta el final del turno.”

### 029 — Alberich, el Rey de los Elfos.

- **Página:** física 6 / interna 5
- **Número o token original:** nº029
- **Nombre exacto:** `Alberich, el Rey de los Elfos.`
- **Raza:** Elfo
- **Coste:** 20
- **Fuerza:** 20
- **Tipo:** `Token de Criatura/Señor de los Reinos`
- **Rango:** `AMBIGUOUS`
- **Subtipo:** `Señor de los Reinos`
- **Texto completo de reglas:** “Inmunidad a Recursos Rápidos, Eventos y habilidades. Pagar 5 de Fuerza: esta carta se transforma en una criatura. Pagar 10 de Fuerza: los Elfos, Duendes y Pixies reciben +5 a su Fuerza hasta el final del turno. Pagar 5 Heridas: recuperas 5 de Fuerza a este Señor. Usa estas habilidades como un Evento.”

## Fichas fuente completas: Ángel

### 140 — Ángel de la Guarda.

- **Página:** física 15 / interna 14
- **Número o token original:** nº140
- **Nombre exacto:** `Ángel de la Guarda.`
- **Raza:** Ángel
- **Coste:** 15
- **Fuerza:** 15
- **Tipo:** `Token de Criatura`
- **Rango:** `AMBIGUOUS`
- **Subtipo:** `AMBIGUOUS`
- **Texto completo de reglas:** “Vuelo, inmunidad a Eventos, no se gira al atacar. Pagar cinco Pasos: la criatura objetivo no puede ser destruida por daño de combate.”

### 141 — Ángel de Piedad.

- **Página:** física 15 / interna 14
- **Número o token original:** nº141
- **Nombre exacto:** `Ángel de Piedad.`
- **Raza:** Ángel
- **Coste:** 15
- **Fuerza:** 15
- **Tipo:** `Token de Criatura`
- **Rango:** `AMBIGUOUS`
- **Subtipo:** `AMBIGUOUS`
- **Texto completo de reglas:** “Vuelo, inmunidad a Recursos Rápidos, Dureza. Pagar cinco Pasos: recupera cinco Heridas a la criatura o jugador objetivo.”

### 142 — Ángel de la Justicia.

- **Página:** física 15 / interna 14
- **Número o token original:** nº142
- **Nombre exacto:** `Ángel de la Justicia.`
- **Raza:** Ángel
- **Coste:** 15
- **Fuerza:** 15
- **Tipo:** `Token de Criatura`
- **Rango:** `AMBIGUOUS`
- **Subtipo:** `AMBIGUOUS`
- **Texto completo de reglas:** “Vuelo, Dureza, ataca dos veces, inmunidad a Recursos Rápidos. Si fuera a ir a la Pila de Descartes, destruye la criatura objetivo. No puede ser transmutado.”

### 143 — Ángel de la Verdad.

- **Página:** física 15 / interna 14
- **Número o token original:** nº143
- **Nombre exacto:** `Ángel de la Verdad.`
- **Raza:** Ángel
- **Coste:** 15
- **Fuerza:** 15
- **Tipo:** `Token de Criatura`
- **Rango:** `AMBIGUOUS`
- **Subtipo:** `AMBIGUOUS`
- **Texto completo de reglas:** “Vuelo, Dureza, inmunidad a Eventos. Pagar cinco Pasos: busca una carta de Elfo, Duende, Pixie o Ángel y ponla en tu mano, mezcla tu baraja.”

### 144 — Ángel de la Muerte.

- **Página:** física 15 / interna 14
- **Número o token original:** nº144
- **Nombre exacto:** `Ángel de la Muerte.`
- **Raza:** Ángel
- **Coste:** 20
- **Fuerza:** 20
- **Tipo:** `Token de Criatura`
- **Rango:** `AMBIGUOUS`
- **Subtipo:** `AMBIGUOUS`
- **Texto completo de reglas:** “Vuelo, Dureza, inmunidad a Eventos, Recursos Rápidos y Habilidades. Pagar diez Pasos: destruye la criatura objetivo, no puede ser transmutada, el jugador objetivo descarta una carta.”

### 145 — Arcángel.

- **Página:** física 15 / interna 14
- **Número o token original:** nº145
- **Nombre exacto:** `Arcángel.`
- **Raza:** Ángel
- **Coste:** 30
- **Fuerza:** 30
- **Tipo:** `Token de Criatura`
- **Rango:** `AMBIGUOUS`
- **Subtipo:** `AMBIGUOUS`
- **Texto completo de reglas:** “Vuelo, Dureza, inmunidad a Eventos y Recursos Rápidos o Habilidades. Girar el Arcángel: busca una carta con el tipo de criatura Ángel y ponlo en tu mano. Todos los Ángeles tienen +5 a su Fuerza.”

## Gaps mecánicos que condicionan la revisión

Esta selección **no afirma implementabilidad inmediata**. Antes de publicar
cartas deben verificarse como contratos generales, entre otros: búsqueda que
descarta repetidamente (026), gasto y recuperación de Fuerza y transformación
de Señor (029), Vuelo/Dureza/no girarse al atacar, ataque doble y disparo antes
de ir a la Pila (142), inmunidades según procedencia, tutor racial y aumento
continuo de Fuerza (143/145). Los resolutores existentes de búsqueda,
movimiento, barajado, prevención, curación, daño, Fuerza, destrucción,
transformación y permisos de Desafío son puntos de reutilización, no licencia
para completar silencios editoriales.

## Bloqueos normativos

- **`N-POINTS-01`: `OPEN/BLOCKED`.** Coste y Fuerza se transcriben por carta,
  pero 200, 300, 400 y cualquier otra cifra quedan expresamente excluidos como
  presupuesto Mítico predeterminado.
- El rango no se infiere de nombres como «Rey», «Reina» o «Arcángel»; donde el
  tipo no dice `Legendario` o `Divino`, figura `AMBIGUOUS`.
- La raza no se usa como subtipo impreso. Salvo `Señor de los Reinos`, que sí
  aparece en el tipo compuesto de 029, el subtipo queda `AMBIGUOUS`.
- No se crean IDs, manifiestos, efectos, keywords ni definiciones de catálogo
  ejecutables en esta fase.
