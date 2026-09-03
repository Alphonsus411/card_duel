# Registro normativo base–Mítica de Fantasy Tokens

Fecha de la auditoría: 2026-09-03. Estado: **registro documental; no cambia el
motor ni incorpora cartas**.

## 1. Alcance, fuentes y método

Este documento es el registro maestro de reglas normalizadas. Su denominador de
fuente es el inventario de las **49/49 páginas** y **431/431 cartas/tokens** de
[`FANTASY_TOKENS_SOURCE_INVENTORY.csv`](FANTASY_TOKENS_SOURCE_INVENTORY.csv).
Las fuentes primarias son `Fantasy Tokens.pdf` (**Base**) y `Fantasy Tokens
Edicion Mitica.pdf` (**Mítica**); sus hashes y paginación están fijados en
[`RULES_SOURCES.json`](RULES_SOURCES.json). Los extractos siguientes son breves:
la ubicación indicada, no esta transcripción, es la autoridad.

Se aplicó este procedimiento:

1. separar cada enunciado normativo del material editorial y de las cartas;
2. asignarle un ID estable `N-<DOMINIO>-<NN>` (el ID no expresa prioridad);
3. registrar fuente, página física, sección/carta y texto relevante;
4. normalizar sólo lo que afirma el texto;
5. enlazar evidencia Mítica y clasificarla con el vocabulario cerrado de §2;
6. enviar contradicciones, silencios materiales y extremos incompletos al
   registro enlazado de [ambigüedades normativas](NORMATIVE_AMBIGUITIES.md).

Las páginas de Base coinciden con su número impreso. Para Mítica siempre se usa
el par **página física / página interna**. Ningún texto posterior al encabezado
`EDICION MITICA` (física 4 / interna 3) se generaliza desde una carta concreta.

## 2. Precedencia y significado de la relación

Se aplica literalmente la precedencia de [`RULES_BASELINE.md`](RULES_BASELINE.md):
Mítica prevalece **sólo** cuando modifica expresamente la Base. Una adición no
sustituye por sí sola una regla previa. Código, pruebas y Markdown son derivados,
no evidencia normativa.

| Relación | Uso en este registro |
|---|---|
| `SAME` | Mítica confirma expresamente la misma regla. |
| `EXTENDS` | Añade un caso o requisito compatible sin sustituir la Base. |
| `CLARIFIES` | Precisa expresamente un extremo sin cambiar su resultado. |
| `OVERRIDES` | Modifica expresamente la regla base y prevalece en su alcance. |
| `CONFLICT` | Dos mandatos expresos no pueden cumplirse conjuntamente. Queda bloqueado. |
| `AMBIGUOUS` | Hay silencio material, redacción insuficiente o varias lecturas; no equivale a permiso ni prohibición. |

`Evidencia Mítica: silencio` significa únicamente que no se localizó una
modificación expresa en su bloque normativo (físicas 2–4 / internas 1–3). Por la
precedencia anterior, la regla Base continúa; **no** se infiere del silencio una
regla Mítica nueva.

## 3. Registro numerado

### 3.1 Fases, preparación y prioridad

| ID | Fuente, página y sección | Texto fuente relevante | Interpretación normalizada | Evidencia Mítica vinculada | Relación |
|---|---|---|---|---|---|
| `N-PHASE-01` | Base p. 3, «Preparación y turnos»; regla 3, pp. 5–6 | «cada jugador baraja su mazo y roba […] seis cartas» | Cada participante baraja, roba seis y se decide aleatoriamente quién comienza. | Silencio en Mítica, físicas 2–4. | `AMBIGUOUS` |
| `N-PHASE-02` | Base p. 6, regla 4 | «robar de nuevo hasta cinco cartas […] una carta menos […] hasta […] una sola» | Mulligan repetible: 5, 4, 3, 2 y 1 cartas; tras una carta no se repite. | Silencio en Mítica, físicas 2–4. | `AMBIGUOUS` |
| `N-PHASE-03` | Base pp. 4–5, listado de fases; p. 7, regla 15 | Robo, Mantenimiento, Efectos, Combate; Legendaria «antes de […] Descarte» | Orden: Robo → Mantenimiento → Efectos → Combate → Legendaria → Descarte. | Mítica física 3 / interna 2, «Legendarios», conserva su tratamiento pero no reenumera la secuencia. | `AMBIGUOUS` |
| `N-PHASE-04` | Base p. 4, «Fase de Robo»; regla 5, p. 6 | «Al comienzo del turno, el jugador roba una carta» | El jugador activo roba una carta; efectos pueden añadir o impedir robos. | Silencio en Mítica, físicas 2–4. | `AMBIGUOUS` |
| `N-PHASE-05` | Base p. 4, «Mantenimiento»; regla 6, p. 6 | «endereza […] recibiendo cinco pasos […] acumulándolos» | En Mantenimiento se enderezan permanentes y se añaden cinco Pasos a la Reserva. | Silencio en Mítica, físicas 2–4. | `AMBIGUOUS` |
| `N-PHASE-06` | Base p. 4, «Efectos»; regla 7, p. 6 | «gastarse “pasos” para bajar Criaturas […] Equipos y Eventos» | Efectos es la fase activa ordinaria para jugar permanentes/eventos y transmutar, con respuestas rápidas. | Mítica física 3 / interna 2, «Drenaje» y «Señores», sitúa esas acciones nuevas en Fase Activa. | `EXTENDS` |
| `N-PHASE-07` | Base p. 4, «Descarte»; regla 9, pp. 6–7 | «más de seis cartas […] quitarse tantas […] como supere» | Al acabar, el activo elige descartes hasta una mano máxima de seis. | Silencio en Mítica, físicas 2–4. | `AMBIGUOUS` |
| `N-PHASE-08` | Base p. 7, regla 10 | En Fase Pasiva no roba, juega Criaturas/Eventos/Equipo ni endereza; sí responde, transmuta y bloquea. | El no activo carece de fases activas y conserva sólo las respuestas y acciones expresamente listadas. | Mítica física 3 / interna 2, «Drenaje»: «no durante la Fase Pasiva». | `CLARIFIES` |
| `N-PHASE-09` | Base p. 7, regla 11 | «primera carta, es decir, […] última jugada […] orden de retroceso» | Las respuestas apiladas se resuelven en orden LIFO. | Silencio en Mítica, físicas 2–4. | `AMBIGUOUS` |
| `N-PHASE-10` | Base p. 7, regla 12 | Un girado «tan solo se endereza […] mediante […] Mantenimiento», salvo habilidades/cartas. | Enderezado normal sólo en Mantenimiento; texto específico puede hacerlo fuera de fase. | Silencio en Mítica, físicas 2–4. | `AMBIGUOUS` |

### 3.2 Zonas, información y movimientos

| ID | Fuente, página y sección | Texto fuente relevante | Interpretación normalizada | Evidencia Mítica vinculada | Relación |
|---|---|---|---|---|---|
| `N-ZONE-01` | Base p. 4, reglas generales | Si no queda baraja, «puede barajar su pila completa y usarla de nuevo como mazo», salvo efectos. | Ante un robo de mazo vacío, se recicla el descarte barajado salvo un bloqueo expreso. | Silencio en Mítica, físicas 2–4. | `AMBIGUOUS` |
| `N-ZONE-02` | Base p. 8, regla 20 | Mano no visible y mazo boca abajo, salvo efecto que permita verlo. | Mano y mazo son zonas ocultas; revelar o buscar requiere autorización textual. | Silencio en Mítica, físicas 2–4. | `AMBIGUOUS` |
| `N-ZONE-03` | Base p. 7, regla 13 | Equipos «permanecen […] aunque la criatura […] sea destruida». | Al salir la criatura equipada, el Equipo se desanexa y permanece en el tablero. | Silencio en Mítica, físicas 2–4. | `AMBIGUOUS` |

### 3.3 Tokens, costes y Transmutación

| ID | Fuente, página y sección | Texto fuente relevante | Interpretación normalizada | Evidencia Mítica vinculada | Relación |
|---|---|---|---|---|---|
| `N-TOKEN-01` | Base pp. 2–3, «Tipos y subtipos» | Criatura, Equipo, Evento, Recurso Rápido y Leyenda. | Tipo funcional y rango/subtipo son dimensiones distintas; el texto de carta puede especificar excepciones. | Mítica física 3 / interna 2, «Legendarios»: exige subtipo procedente del tipo original. | `CLARIFIES` |
| `N-TOKEN-02` | Base p. 3, «Recursos Rápidos» | «pueden jugarse en cualquier fase o momento del turno» | Los Recursos Rápidos admiten las ventanas de respuesta descritas por la Base. | Mítica no revoca esta ventana; añade inmunidades concretas en física 3 / interna 2. | `EXTENDS` |
| `N-TOKEN-03` | Base p. 7, regla 16 | Si una carta contradice reglas básicas «se aplicará […] el texto». | El texto particular prima en su alcance y la pila sigue determinando resolución. | Mítica física 2 / interna 1 declara cambios a reglas básicas; no altera la prioridad del texto particular. | `SAME` |
| `N-COST-01` | Base p. 3, «Objetivo/barajas»; p. 5, «Estructura» | «valor fijo en “pasos”»; el número indica Fuerza/Resistencia de criatura o coste de bajada. | El coste impreso es el valor base para pagar la carta y, en criatura, la fuente impresa de Fuerza/Resistencia. | Mítica física 2 / interna 1 conserva el «coste en Pasos» y fija 5–50 para cartas Míticas. | `EXTENDS` |
| `N-COST-02` | Base p. 7, regla 17 | Sin Pasos no se juegan tokens, pero se puede transmutar para rellenar la Reserva. | El coste se paga antes de jugar; Transmutación puede generar los Pasos necesarios si no está impedida. | Mítica física 3 / interna 2 añade Drenaje como otra generación de Pasos, sin sustituir Transmutación. | `EXTENDS` |
| `N-COST-03` | Base p. 7, regla 13 | Equipar exige «un número de “pasos” igual al coste de bajada» salvo texto contrario. | El coste ordinario de equipar es el coste impreso del Equipo; una carta puede modificarlo. | Silencio en Mítica, físicas 2–4. | `AMBIGUOUS` |
| `N-TRANSMUTATION-01` | Base p. 3, «Transmutación» | Mandar naipes en juego al descarte, «sacando de ellos su valor en “pasos”». | Transmutar mueve un permanente propio del tablero al descarte y añade su coste impreso a la Reserva. | Mítica física 3 / interna 2: Transmutación «seguirá vigente». | `SAME` |
| `N-TRANSMUTATION-02` | Base p. 3, «Transmutación» | Criaturas, Equipos y Eventos, «siempre en sus fases correspondientes». | La carta obtenida/jugada y la carta transmutada respetan las ventanas expresas de fase. | Mítica física 3 / interna 2 conserva Transmutación y permite expresamente transmutar Divinos. | `EXTENDS` |

### 3.4 Combate y terminación

| ID | Fuente, página y sección | Texto fuente relevante | Interpretación normalizada | Evidencia Mítica vinculada | Relación |
|---|---|---|---|---|---|
| `N-COMBAT-01` | Base pp. 4 y 6, «Combate» / regla 8 | Atacantes y bloqueadores se eligen y se giran. | Sólo criaturas aptas/enderezadas atacan o bloquean; las declaradas quedan giradas. | Mítica física 4 / interna 3 añade Desafío como sustitución del combate normal. | `EXTENDS` |
| `N-COMBAT-02` | Base p. 6, regla 8 | Daño «equivalente a su Fuerza» destruye; «los restantes» van al pasivo. | Daño marcado ≥ Fuerza es letal; el daño atacante que exceda el bloqueo alcanza al defensor. | Mítica física 4 / interna 3 usa «daño letal» en Desafío, sin redefinir el umbral. | `SAME` |
| `N-COMBAT-03` | Base p. 6, regla 8 | «No hay límite al número de criaturas […] bloquear otra carta»; daños restantes al pasivo. | Varios bloqueadores pueden interceptar un atacante. **No se especifica cómo repartir u ordenar daño entre ellos.** | Silencio en Mítica, físicas 2–4. | `AMBIGUOUS` |
| `N-COMBAT-04` | Base p. 7, regla 14 | Una criatura girada por habilidad no ataca salvo que se enderece antes de declarar. | La aptitud para atacar se comprueba al declarar atacantes. | Silencio en Mítica, físicas 2–4. | `AMBIGUOUS` |
| `N-COMBAT-05` | Base p. 3, «Objetivo»; p. 5, regla 2 | «uno o más adversarios» y límite de Heridas común. | La preparación admite 2+ participantes y todos acuerdan el mismo límite. | Mítica alude a «baraja y jugador», pero no modifica expresamente el número de participantes. | `AMBIGUOUS` |
| `N-COMBAT-06` | Base pp. 3–4; regla 18, pp. 7–8 | Concesión vence a «su oponente»; quien llega al límite pierde; empate descrito entre dos. | Para exactamente dos jugadores se aplican derrota/concesión/empate descritos. Para 3+ la continuidad y ganadores no están definidos. | Silencio normativo Mítico, físicas 2–4. | `AMBIGUOUS` |

### 3.5 Legendarios, Divinos y Señores

| ID | Fuente, página y sección | Texto fuente relevante | Interpretación normalizada | Evidencia Mítica vinculada | Relación |
|---|---|---|---|---|---|
| `N-LEGENDARY-01` | Base pp. 5 y 7, «Fase Legendaria» / regla 15 | Se activa al final de Fase Activa y antes de Descarte. | Los efectos legendarios ocurren después de Combate y antes de Descarte; admiten respuesta. | Mítica física 3 / interna 2 mantiene Legendarios y les exige subtipo. | `EXTENDS` |
| `N-LEGENDARY-02` | Base p. 8, regla 19 | Indestructible no va del tablero al descarte; Divino era «inmune completamente incluso al descarte». | Indestructible sólo impide ese movimiento desde tablero; la inmunidad divina base era total. | Mítica física 3 / interna 2, «Divinos»: limita inmunidad a Eventos, Recursos Rápidos y habilidades de criaturas permanentes, y permite Transmutación. | `OVERRIDES` |
| `N-LEGENDARY-03` | Base p. 8, regla 21 | Máximo cinco comunes y cuatro legendarias. | Límite de copias por identidad: cinco no legendarias/comunes y cuatro legendarias. | Mítica física 2 / interna 1, «Copias», repite cinco/cuatro. | `SAME` |
| `N-LEGENDARY-04` | Sin regla Base sobre Señores | — | Los Señores de Abismo, Elíseo y Magia son permanentes con Fuerza inicial igual al coste; a Fuerza cero van al descarte; ordinariamente no atacan ni bloquean y sí pueden ser atacados. | Mítica física 3 / interna 2, secciones de los tres dominios. | `EXTENDS` |
| `N-LEGENDARY-05` | Sin regla Base sobre Señores de Reinos | — | Reinos puede transformarse en criatura para atacar, bloquear y usar habilidades; el texto no concede por sí mismo una acción gratuita de transformación. | Mítica física 4 / interna 3, «Señores de los Reinos». | `EXTENDS` |
| `N-LEGENDARY-06` | Sin regla Base sobre habilidades de Señor | — | Sólo queda confirmada su activación en Fase Activa; «a modo de Eventos» no define tipo, inmunidades, objetivos ni demás consecuencias. | Mítica física 3 / interna 2, «Señores del Abismo». Registro histórico: `M-LORD-EVENT-01`. | `AMBIGUOUS` |
| `N-LEGENDARY-07` | Sin Desafío en Base; combate Base pp. 6–7 | — | Una vez por turno en Fase Activa, Desafío sustituye el combate normal y enfrenta los Señores/criaturas expresamente elegibles; no hay daño sobrante declarado. | Mítica física 4 / interna 3, «Desafío». | `EXTENDS` |

### 3.6 Construcción, puntos y formatos

| ID | Fuente, página y sección | Texto fuente relevante | Interpretación normalizada | Evidencia Mítica vinculada | Relación |
|---|---|---|---|---|---|
| `N-POINTS-01` | Base pp. 3 y 5, «Construcción» / regla 1 | Total = suma de costes; mínimo 50; totales de participantes iguales/aproximados. | **`OPEN/BLOCKED`.** Se conserva el mínimo base y la comparación relacional; no se elige techo Mítico. | Mítica física 2 / interna 1: **200** por baraja; máximo **300–400**; recomendación **aprox. 300**; resumen **300**. | `CONFLICT` |
| `N-COST-04` | Base pp. 3 y 5, «Construcción» / regla 1 | Los puntos se obtienen «sumando […] los valores» / «suma de los costes». | Coste impreso y puntos por copia no son dos atributos: `CardDefinition.cost` continúa siendo la autoridad actual del cálculo de construcción. Esto **no** selecciona presupuesto Mítico. | Mítica física 2 / interna 1: «ajuste […] por puntos o coste en Pasos siguen inalterables». | `SAME` |
| `N-FORMAT-01` | Base p. 8, regla 21 | Cinco copias comunes, cuatro legendarias. | Límites base de copias. | Mítica física 2 / interna 1 repite cinco no legendarias/cuatro legendarias y añade reglas de coste cero. | `EXTENDS` |
| `N-FORMAT-02` | Base no fija tamaño de mazo | — | No existe tamaño universal Base. Para los formatos Míticos descritos: 40–60 cartas. | Mítica física 2 / interna 1, «Tamaño y puntos». | `EXTENDS` |
| `N-FORMAT-03` | Base no define Clásico/Mística | — | Clásico admite ediciones anteriores con límites de coste cero; Mística excluye Alfa/Beta y exige 5–50 Pasos a cartas Míticas. | Mítica física 2 / interna 1, «Formato clásico» y «Formato mística». | `EXTENDS` |

## 4. Revisión expresa de brechas solicitadas

1. **`N-POINTS-01`: `OPEN/BLOCKED`.** Las cuatro formulaciones se conservan
   separadas: 200 (cómputo), 300–400 (intervalo de máximo), aproximadamente 300
   (recomendación) y 300 (resumen). No se armonizan por promedio ni por contexto.
2. **Coste ≠ presupuesto.** `N-COST-04` confirma que cada copia aporta
   `CardDefinition.cost` al total. Esa equivalencia de magnitud no responde cuál
   debe ser el presupuesto Mítico y no crea una segunda propiedad de puntos.
3. **`M-LORD-EVENT-01`.** Se conserva como alias histórico de
   `N-LEGENDARY-06`: `AMBIGUOUS`; sólo Fase Activa está respaldada.
4. **Reparto entre bloqueadores.** `N-COMBAT-03` registra el permiso de bloqueo
   múltiple y, separadamente, el silencio sobre reparto/orden. El orden declarado
   del backend es una normalización técnica, no una regla fuente.
5. **Terminales multijugador.** `N-COMBAT-05` confirma 2+ participantes;
   `N-COMBAT-06` bloquea continuidad, selección y orden de ganadores para 3+.
6. **Conflictos nuevos.** No se halló otro conflicto expreso al cotejar el bloque
   normativo Mítico. Los demás vacíos materiales se clasifican `AMBIGUOUS`, nunca
   como autorización o prohibición inferida.

El detalle de estado, impacto y condición de desbloqueo se mantiene en
[`NORMATIVE_AMBIGUITIES.md`](NORMATIVE_AMBIGUITIES.md).

## 5. Límites técnicos

- El catálogo de producción continúa vacío; las 431 entradas inventariadas no
  se convierten aquí en reglas universales ni contenido ejecutable.
- Las normalizaciones del backend pueden preservar compatibilidad, pero no
  cambian la relación normativa de ninguna fila.
- Los IDs de este documento son permanentes: una aclaración futura cambia estado,
  evidencia o relación, no reutiliza ni renumera el ID.
