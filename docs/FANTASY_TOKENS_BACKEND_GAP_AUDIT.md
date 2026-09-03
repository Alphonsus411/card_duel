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

La [matriz de conformidad carta por carta](CARD_CORPUS_CONFORMANCE.md)
descompone y clasifica las 431 entradas del corpus, separando incorporación al
catálogo de representabilidad declarativa.

Dos anexos separan el inventario transversal que no debe confundirse con las
reglas particulares de una carta: la
[`matriz canónica de todos los tipos de Token`](TOKEN_TYPES_MATRIX.md) cubre los
431 rótulos impresos y sus contratos universales, y la
[`taxonomía canónica`](CANONICAL_TAXONOMY.md) registra dimensiones, selecciones,
controlador, zona, visibilidad y su correspondencia con el dominio del backend.

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
| `N-COST-01` | Base p. 3, «Objetivo/barajas»; p. 5, «Estructura» | «valor fijo en “pasos”»; el número indica Fuerza/Resistencia de criatura o coste de bajada. | El coste impreso es el valor base para pagar la carta y, en criatura, la fuente impresa de Fuerza/Resistencia. | Mítica física 2 / interna 1 conserva el «coste en Pasos» y fija 5–50 para las cartas de esa edición. | `EXTENDS` |
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
| `N-FORMAT-03` | Base no define Clásico/Mística | — | Clásico admite ediciones anteriores con límites de coste cero; Mística excluye Alfa/Beta y exige 5–50 Pasos a cartas de la edición. | Mítica física 2 / interna 1, «Formato clásico» y «Formato mística». | `EXTENDS` |

## 4. Secuencia de turno y contrato de cada fase

### 4.1 Criterio de lectura

En las tablas siguientes, **activo** es quien tiene el turno y **pasivos** son
los demás participantes. «Puede resolver» describe capacidad mecánica del
backend (un `StackItem` ya creado puede ejecutarse); **no** implica que pueda
anunciarse en esa fase. «Ventana de anuncio» describe exclusivamente qué
comandos admite `_timing_allows_play`, la validación de habilidades y los
comandos especiales. Esta separación evita convertir la capacidad general del
intérprete de efectos en una ampliación de ventanas.

La Base llama «Fase Activa» al conjunto del turno del activo y enumera por
separado Robo, Mantenimiento, Efectos, Combate y Descarte (Base pp. 4–7). La
Mítica ubica Drenaje, habilidades de Señor y Desafío en «Fase Activa», pero no
identifica inequívocamente esa expresión con una sola fase enumerada. El backend
la normaliza de forma conservadora como `Phase.EFFECTS` para esas acciones. Esa
normalización técnica **no resuelve** el silencio normativo: donde el PDF no
precisa ventana, prioridad o respuesta se marca `AMBIGUOUS`.

### 4.2 Cadena completa y evidencia canónica de transición

| Transición | Condición canónica y evidencia | Implementación contrastada | Brecha |
|---|---|---|---|
| inicio de turno → **Robo** | Base p. 4, «Fase de Robo», y regla 5, p. 6: al comienzo del turno el activo roba una carta. | `game.py:399`, `game.py:1771-1781`: el comienzo entra en `DRAW`, entrega prioridad al activo y ejecuta un robo. | El PDF no dice si el robo usa pila, admite respuesta antes/después ni quién recibe prioridad: `AMBIGUOUS`. |
| **Robo → Mantenimiento** | Base pp. 4–5 enumera Robo inmediatamente antes de Mantenimiento. | `phases.py:24-42` exige activo, pila vacía y ventana cerrada; después recorre `rules.phase_sequence`. | El PDF da orden, pero no formaliza condición de salida ni pases: `AMBIGUOUS`. |
| **Mantenimiento → Efectos** | Base pp. 4–5 enumera Mantenimiento antes de Efectos; regla 6, p. 6, asigna enderezado y cinco Pasos a Mantenimiento. | `game.py:1781-1790` aplica ambos al entrar; `phases.py:40-42` avanza tras cierre de prioridad. | Orden canónico; cierre y prioridad son normalización backend: `AMBIGUOUS`. |
| **Efectos → Combate** | Base p. 4 y reglas 7–8, p. 6, colocan bajar Criaturas/Equipos/Eventos antes de declarar atacantes y bloqueadores. | `rules.phase_sequence`, proyectada por `game.py:135-137`, y `phases.py:40-42`; no permite avanzar con pila/prioridad abiertas. | La fuente no define una ventana final de respuestas: `AMBIGUOUS`. |
| **Combate → Legendaria** | Base regla 15, p. 7: la Legendaria se activa al final de la Fase Activa y antes de Descarte; el listado de pp. 4–5 y regla 8 sitúan Combate antes de ese final. Mítica física 3 / interna 2 conserva Legendarios. | `phases.py:29-31` obliga a resolver un combate declarado; `game.py:1791-1792` encola efectos legendarios al entrar. | «Al final de Fase Activa» no determina si Legendaria es subfase de Combate ni su primera prioridad: `AMBIGUOUS`; el orden implementado es explícito y conservador. |
| **Legendaria → Descarte** | Base regla 15, p. 7: Legendaria ocurre «antes de […] Descarte»; regla 9, pp. 6–7, define el ajuste de mano al acabar. | Pila y prioridad deben cerrarse (`phases.py:27-28`); la secuencia entra en `DISCARD`. | El PDF no define si cada Legendaria admite respuesta individual o sólo el conjunto: `AMBIGUOUS`. |
| **Descarte → Robo del siguiente activo** | Base regla 9, pp. 6–7, termina el turno tras ajustar a seis; preparación/turnos y regla 5 hacen comenzar el siguiente con Robo. | `phases.py:32-39` impide salir con exceso, limpia el turno, rota activo y entra o salta `DRAW`. | Prioridad durante el ajuste y posibilidad de responder al descarte no están definidas: `AMBIGUOUS`. |

### 4.3 Matriz por fase

| Fase | Entrada / disparos de comienzo | Activo y pasivos | Acciones permitidas por fuente | Acciones prohibidas por fuente | Salida / disparos de final | Omitir fase |
|---|---|---|---|---|---|---|
| **Robo** | Entra al comienzo del turno; el activo roba una (Base p. 4; regla 5, p. 6). Efectos concretos pueden aumentar o impedir el robo. | Activo: roba. Pasivos: permanecen en Fase Pasiva (regla 10, p. 7). Quién tiene prioridad: `AMBIGUOUS`; backend: activo. | Recurso Rápido «en cualquier fase o momento» (Base p. 3) y respuestas de pasivos (regla 10). | Pasivo no roba, baja Criaturas, Eventos ni Equipo y no endereza (regla 10). Para el activo, jugar permanentes/Eventos fuera de Efectos no tiene autorización general. | La fuente sólo fija que Mantenimiento sigue; disparos/respuestas al final: `AMBIGUOUS`. Backend exige pases, pila vacía y prioridad cerrada. | El PDF reconoce efectos que impiden robar, no define «omitir la Fase de Robo» ni sus otros efectos: `AMBIGUOUS`. Backend `suppressed_phases` omite también el robo automático y emite `PHASE_SKIPPED`. |
| **Mantenimiento** | Al entrar, el activo endereza sus permanentes y suma cinco Pasos (Base p. 4; regla 6, p. 6). Cartas concretas pueden disparar «en cada Mantenimiento», pero no prueban una regla universal de orden. | Activo recibe las operaciones. Pasivos sólo respuestas expresas; prioridad canónica `AMBIGUOUS`, backend: activo. | Recursos Rápidos; respuestas; habilidades sólo si su texto autoriza esa ventana. | Pasivos no enderezan; activo no tiene autorización ordinaria para bajar permanentes/Eventos. | Sigue Efectos. Orden entre enderezar, ganar Pasos y disparos de carta: `AMBIGUOUS`; backend realiza enderezado/Pasos sin pila y después abre prioridad. | La fuente no define si al omitir se pierden enderezado, Pasos y disparos: `AMBIGUOUS`. Backend los pierde todos porque no ejecuta `_enter_phase`. |
| **Efectos** | Sigue a Mantenimiento (Base pp. 4–6). No hay disparo universal canónico de comienzo. | Activo realiza acciones ordinarias. Pasivos responden, transmutan y pueden usar Recurso Rápido (Base p. 3; regla 10, p. 7). Backend rota prioridad entre todos. | Activo: bajar Criaturas, Equipos y Eventos, equipar y Transmutar (Base pp. 3–4, regla 7); Recursos Rápidos de cualquier jugador; Mítica: Drenaje una vez por turno activo y habilidades de Señor/Desafío en Fase Activa (físicas 3–4 / internas 2–3). | Pasivo: no bajar Criatura, Evento o Equipo ni usar Drenaje. | Sigue Combate tras completar acciones/respuestas. No se define disparo universal final ni número de pases: `AMBIGUOUS`. | Omitir Efectos elimina la única ventana backend para cartas no rápidas, equipar, Drenaje y habilidades restringidas; la consecuencia canónica exacta para «Fase Activa»: `AMBIGUOUS`. |
| **Combate** | Tras Efectos; el activo elige y gira atacantes y el pasivo elige/gira bloqueadores (Base p. 4; regla 8, p. 6). | Activo declara atacantes; defensor pasivo declara bloqueadores. Con 3+ jugadores, defensor y orden: `AMBIGUOUS` salvo elección explícita backend. | Declarar ataque/bloqueo; Recursos Rápidos y respuestas; habilidades con ventana compatible. | Pasivo no declara ataque; criaturas no aptas/giradas no atacan; Drenaje no pasivo. Jugar permanentes/Eventos ordinarios carece de autorización. | Debe resolverse el combate declarado; daño y destrucción se aplican según regla 8. Ventanas entre declarar, bloquear y dañar: `AMBIGUOUS`; backend modela comandos separados y prioridad. | Cartas concretas prueban que puede no existir Fase de Combate, no una regla universal de consecuencias. Backend salta toda la fase; un combate pendiente bloquea avance. |
| **Legendaria** | Después de Combate y antes de Descarte (Base regla 15, p. 7). Backend encola al entrar los efectos `legendary_effects` de todos los Legendarios del activo. | Regla 15 dice que el jugador usa efectos legendarios y el contrario puede contrarrestarlos. Activo/controlador exacto y primera prioridad con múltiples efectos: `AMBIGUOUS`; backend entrega al activo y ordena lotes. | Efectos legendarios y respuestas, incluidos Recursos Rápidos. Acciones de Señor, Desafío, Drenaje y cartas ordinarias **no reciben por ello** una ventana nueva. | Pasivo no baja permanentes/Eventos ni usa Drenaje. Backend prohíbe cartas no rápidas y habilidades restringidas a Efectos. | Sale sólo con respuestas/pila concluidas; sigue Descarte. El PDF no define pases, orden simultáneo ni si un efecto sin respuesta resuelve de inmediato: `AMBIGUOUS`. | Fuente no define omisión de Legendaria: `AMBIGUOUS`. Backend no encola sus efectos y pasa a Descarte. |
| **Descarte** | Tras Legendaria; si el activo tiene más de seis, elige el exceso (Base p. 4; regla 9, pp. 6–7). | Activo ajusta mano. Pasivos siguen en Fase Pasiva. Prioridad antes/después del ajuste: `AMBIGUOUS`; backend abre prioridad al activo antes de permitir `DiscardCards`. | Ajuste exacto de mano; Recursos Rápidos por regla general y respuestas pasivas. | Pasivo no realiza el ajuste del activo; cartas ordinarias no rápidas sin autorización; no puede finalizarse con más de seis. | Con mano ≤6 termina el turno y rota activo; backend limpia daño/modificadores temporales y entra en Robo. Respuesta al descarte y disparos de fin: `AMBIGUOUS`. | No existe permiso canónico general de omitir Descarte: `AMBIGUOUS`. Backend, si se suprime, finaliza turno sin forzar límite de mano. |

## 5. Prioridad, anuncio y pila

### 5.1 Tabla de prioridad completa

La Base sólo establece que el oponente puede responder y que se resuelve en
orden inverso (regla 11, p. 7). No describe un sistema formal de prioridad. Por
tanto, los detalles backend siguientes son contrato técnico, y los silencios del
PDF permanecen `AMBIGUOUS`.

| Paso | Evidencia canónica | Backend actual | ¿Puede resolver el efecto? | ¿Permite anunciarlo exclusivamente en esta ventana? | Estado normativo |
|---|---|---|---|---|---|
| **1. Anuncio** | Recursos Rápidos: cualquier fase/momento (Base p. 3); cartas ordinarias y Transmutación: fases correspondientes (Base pp. 3–4); respuestas pasivas (regla 10). | `PlayCard`, `ActivateAbility`, `TransmutePermanent`, `DrainSteps` y acciones de combate son comandos cerrados (`commands.py:8-117`). Sólo actúa `priority_player_id`, salvo comandos de estructura específicos. | Todavía no; sólo se propone una acción. | Sí: `_timing_allows_play` limita no rápidas al activo en `EFFECTS`; las restricciones de habilidad se validan aparte. | Quién obtiene primero prioridad y qué significa «momento»: `AMBIGUOUS`. |
| **2. Validación** | La carta contradice reglas sólo en su texto particular (regla 16, p. 7); no hay protocolo general. | Se valida identidad/prioridad, zona, ventana, objetivos, coste y restricciones antes de mutar (`game.py:910-943`, `1328-1391`). La enumeración de `actions.py` no sustituye esta validación. | El intérprete soporta los `EffectKind` declarados aunque el anuncio resulte ilegal. | No: capacidad de efecto y legalidad temporal son comprobaciones distintas. | Protocolo/orden de validaciones: `AMBIGUOUS`. |
| **3. Pago** | Los Pasos pagan bajada/equipar y Transmutación los repone (Base pp. 3, 6–7). Costes compuestos y posibilidad de responder al pago dependen de texto particular. | Valida coste completo y luego paga atómicamente antes de mover a resolución (`game.py:927-967`, `997-1038`); Drenaje y Transmutación son transacciones directas. | Sí, si posteriormente llega a resolución. | No. Pagar no abre por sí mismo una ventana diferente. | Si el pago admite respuesta o puede revertirse canónicamente: `AMBIGUOUS`. |
| **4. Entrada en pila** | «Última jugada, primera resuelta» (regla 11, p. 7). | Carta pasa a `RESOLUTION`, se crea `StackItem`; permanentes irán a tablero y no permanentes a descarte al resolver (`game.py:953-976`). Disparos y Legendarias también se encolan (`stack.py:42-117`). | Sí; efectos representables quedan pendientes en pila. | No. Entrar en pila presupone que el anuncio ya superó su ventana. | Si Transmutación, Drenaje, equipar o declaraciones usan pila: `AMBIGUOUS`; backend no los apila. |
| **5. Respuestas** | Recursos Rápidos en cualquier momento; pasivo puede responder con Recursos Rápidos y habilidades (Base p. 3; regla 10, p. 7); Legendaria admite contrarrestar (regla 15). | Tras carta/habilidad se reinician pases y prioridad pasa al siguiente jugador (`game.py:977-979`, `1448-1450`). | Sí, tanto la respuesta como el objeto previo si siguen legales al resolver. | Sólo rápidas y habilidades cuya propia restricción permita la fase; no cartas ordinarias. | Qué acciones «responden», y si Drenaje/Transmutación/equipar/desafío admiten respuesta: `AMBIGUOUS`. |
| **6. Pases consecutivos** | Sin regla expresa. | Cada pase incrementa contador y rota; se requieren tantos pases consecutivos como jugadores (`stack.py:28-39`). Una acción reinicia el contador. | No por el pase; al completarse provoca resolución o cierre. | Pasar no anuncia efecto. | `AMBIGUOUS`. |
| **7. Resolución LIFO** | Regla 11, p. 7: la última jugada es la primera resuelta, en retroceso. | `stack.pop()` resuelve el tope (`stack.py:119-143`), ejecuta efectos en orden interno, destino, disparos de entrada y acciones basadas en estado. | Sí. Esta es la separación central: el backend puede resolver cualquier efecto ya apilado compatible. | No. LIFO no amplía el momento en que podía anunciarse. | LIFO: respaldado; objetivos ilegales parciales, orden interno y elecciones durante resolución: `AMBIGUOUS` salvo texto de carta. |
| **8. Recuperación de prioridad** | Sin regla expresa. | Tras resolver un objeto, la ventana queda abierta; si no hay elección pendiente, prioridad vuelve al activo (`stack.py:40-47`). Búsquedas y disparos pueden suspenderla y asignarla al elector/controlador. | Sí, el siguiente objeto espera otra ronda completa. | Se vuelve a aplicar su ventana real; recuperar prioridad no convierte una carta ordinaria en rápida. | `AMBIGUOUS`. |
| **9. Cierre y avance** | El orden de fases es canónico, no el mecanismo de cierre. | Con pila vacía y pases de todos marca `phase_priority_complete`; sólo el activo puede `AdvancePhase` (`stack.py:36-47`, `phases.py:24-42`). | No quedan objetos pendientes. | No; es transición estructural. | Número de pases y facultad exclusiva de avanzar: `AMBIGUOUS`. |

### 5.2 Auditoría de familias en ventanas activas y pasivas

| Familia | Ventana activa canónica | Ventana pasiva canónica | Backend: puede resolver | Backend: permite anunciar exclusivamente | Resultado de brecha |
|---|---|---|---|---|---|
| **Recurso Rápido** | Cualquier fase o momento (Base p. 3). | Sí; regla 10, p. 7, lo incluye como respuesta. | Sí, mediante `StackItem`, en cualquier fase. | Sí en cualquier fase, pero sólo por quien posee prioridad (`game.py:910-979`, `1040-1043`). | La prioridad no está definida por PDF: `AMBIGUOUS`; la ventana amplia sí está respaldada. |
| **Evento no permanente** | Efectos (Base p. 4; regla 7, p. 6). | Pasivo no puede jugar Eventos (regla 10). | Sí en cualquier fase si ya está en pila. | Sólo activo en `EFFECTS`; resuelve a descarte. | Cumple conservadoramente; si un Evento concreto dice otra ventana, manda su texto. |
| **Evento permanente / otros permanentes** | Criatura, Equipo y Evento se bajan en Efectos; equipar paga su coste (Base pp. 3–4, 6–7). | Pasivo no los baja ni equipa. | Sí; la carta entra en tablero al resolver. | Sólo activo en `EFFECTS`; `EquipCard` también exige esa fase (`game.py:1507-1531`). | «Evento permanente» conserva tipo Evento y destino permanente; no obtiene rapidez. |
| **Habilidad activada** | Según texto; las habilidades de Señor sólo están respaldadas en Fase Activa Mítica (física 3 / interna 2). | Regla 10 permite habilidades como respuesta, pero no define cuáles ni sus ventanas. | Sí: se crea objeto de pila y se resuelve LIFO. | Backend permite prioridad en cualquier fase salvo `active_phase_only`, que exige activo en `EFFECTS` (`game.py:1328-1450`). | La regla universal de ventana y si toda activación responde: `AMBIGUOUS`. No se amplía. |
| **Habilidad disparada** | Cuando ocurre su disparador declarado; la Base no formaliza pila de disparos. | Puede dispararse por hechos del pasivo, pero prioridad/controlador no se define. | Sí; backend crea lotes, exige objetivos/orden y los apila (`stack.py:69-117`). | No se «anuncia» libremente: el backend la encola por disparador; sólo se eligen objetivos/orden. | Orden simultáneo, primera prioridad y respuesta: `AMBIGUOUS`. |
| **Drenaje Mítico** | Una vez en turno activo, hasta cinco Pasos; primero gratis y cada adicional cuesta tres Heridas (Mítica física 3 / interna 2). | Expresamente no durante Fase Pasiva. | Es operación directa: el backend puede aplicar ganancia/heridas, no un efecto de pila. | Exclusivamente activo con prioridad en `EFFECTS`, una vez por `turn_serial` (`game.py:1535-1554`). | «Turno activo» frente a fase exacta y si admite respuesta: `AMBIGUOUS`; no se amplía fuera de Efectos. |
| **Transmutación** | Permanentes propios, «siempre en sus fases correspondientes» (Base p. 3); Mítica permite Divinos (física 3 / interna 2). | Regla 10 permite expresamente Transmutación en pasiva. | Operación directa; mueve a descarte, añade coste y puede crear disparos `ON_TRANSMUTED`. | Cualquier fase para quien tiene prioridad y controla un permanente `transmutable` (`game.py:1897-1924`). | La correspondencia exacta por tipo y si admite respuesta: `AMBIGUOUS`. El backend es más uniforme que la frase Base; se registra brecha, no se cambia. |

## 6. Fase Legendaria: auditoría específica

| Aspecto | Evidencia canónica | Contrato backend observado | Estado / gap |
|---|---|---|---|
| **Señores** | Mítica físicas 3–4 / internas 2–3: son permanentes; Abismo, Elíseo y Magia no atacan/bloquean ordinariamente; Reinos puede transformarse. | Se representan como permanentes con dominio; Reinos sólo combate transformado y los demás requieren autorización declarativa para Desafío. | La transformación gratuita no existe; ventana exacta más allá de texto de habilidad: `AMBIGUOUS`. |
| **Fuerza** | Fuerza inicial del Señor igual a su coste y variable al usar capacidades (Mítica física 3 / interna 2). | Fuerza efectiva se resuelve desde definición/modificadores; no se cambia en esta auditoría. | Momento de actualización y uso como coste: `AMBIGUOUS` si la carta no lo declara. |
| **Heridas** | A Fuerza cero va al descarte; puede ser atacado y dañado salvo protección (Mítica física 3 / interna 2). | Daño marcado y acciones basadas en estado pueden destruir/mover permanentes; heridas de jugador son magnitud separada. | El PDF alterna Fuerza/daño sin detallar estado: `AMBIGUOUS`. |
| **Pasos** | Capacidades pueden consumir Pasos; la Fuerza inicial deriva del coste. | Costes de habilidad se validan y pagan antes de apilar. | Si gastar Pasos reduce Fuerza por regla general: no está definido; `AMBIGUOUS`, sólo texto concreto puede hacerlo. |
| **Recursos Rápidos** | Afectan normalmente a Legendarios salvo inmunidad; Divinos son inmunes (Mítica física 3 / interna 2). | Se anuncian con prioridad durante Legendaria; filtrado de objetivos aplica inmunidad. | Ventana respaldada por «cualquier fase»; primera prioridad: `AMBIGUOUS`. |
| **Eventos** | Legendarios reciben Eventos salvo inmunidad; Divinos no. | Un Evento ordinario **no puede anunciarse** en `LEGENDARY`, aunque un Evento ya en pila puede resolver allí. | Capacidad ≠ ventana. La fuente no autoriza bajar Evento ordinario en Legendaria. |
| **Habilidades** | Regla 15 Base permite contrarrestar efectos legendarios; Mítica sitúa habilidades de Señor en Fase Activa «a modo de Eventos». | Habilidades no restringidas pueden anunciarse con prioridad; `active_phase_only` sólo en `EFFECTS`. | Tipo, ventana exacta y condición de respuesta de «a modo de Eventos»: `AMBIGUOUS` (`N-LEGENDARY-06`). |
| **Desafío** | Una vez por turno en Fase Activa, sustituye combate normal (Mítica física 4 / interna 3). | Sólo se declara en `EFFECTS`, con prioridad/elegibilidad y exclusión mutua con combate normal. No se declara en Legendaria. | Que «Fase Activa» incluya Legendaria no está definido: `AMBIGUOUS`; no se amplía. |
| **Transmutación** | Continúa vigente y los Divinos pueden transmutarse (Mítica física 3 / interna 2); Base permite al pasivo y exige fases correspondientes. | Puede anunciarse con prioridad también en `LEGENDARY`; se ejecuta directamente y encola disparos derivados. | Tipo de Señor/fase correspondiente y respuesta a la propia Transmutación: `AMBIGUOUS`. |
| **Prioridad** | La regla 15 permite que el contrario contrarreste; no asigna prioridad ni pases. | Activo recibe prioridad al entrar; efectos legendarios se encolan, objetivos/orden se eligen y todos pasan por rondas de pases. | Mecánica backend, no canon: `AMBIGUOUS`. |
| **Finalización** | Legendaria está antes de Descarte (Base regla 15). | Sólo activo avanza cuando pila vacía y ventana cerrada; efectos legendarios pendientes bloquean otras acciones. | Condición canónica de «todos resueltos» y disparo final: `AMBIGUOUS`. |
| **Transición a Descarte** | Expresa en Base regla 15, p. 7. | `PhaseManager` entra en `DISCARD`; después exige mano ≤ límite para cerrar turno. | Orden respaldado; mecanismo de prioridad/cierre: `AMBIGUOUS`. |

## 7. Contraste de fronteras y conclusión técnica

| Archivo solicitado | Papel comprobado | Consecuencia para esta auditoría |
|---|---|---|
| `engine/phases.py` | Exige activo, pila vacía, prioridad cerrada, combate resuelto y mano ajustada; aplica saltos y rotación. | Define transición técnica, no evidencia canónica. La omisión salta todos los efectos de entrada. |
| `engine/stack.py` | Pases por todos, LIFO, lotes disparados, elecciones de búsqueda y recuperación de prioridad. | Puede resolver efectos sin concederles una ventana de anuncio. Sus detalles de prioridad son `AMBIGUOUS` normativamente. |
| `engine/actions.py` | Enumera únicamente acciones candidatas según pendientes, fase y prioridad. | La UI no debe inferir permisos adicionales; enumerar tampoco reemplaza validar. |
| `engine/commands.py` | Vocabulario cerrado de comandos ejecutables. | No existe un comando genérico que permita saltarse temporización. |
| `engine/game.py` | Valida y ejecuta atómicamente anuncio, objetivos, pago, pila, Drenaje, Transmutación y entradas de fase. | Es autoridad técnica actual; mantiene separadas resolución y ventana. |
| `engine/options.py` | Construye selecciones acotadas de objetivos, zonas, costes y distribuciones para opciones legales. | Expande elecciones de una acción ya autorizada; no crea ventanas. |
| `application.py` | Publica sólo discriminador e `option_id` ligado a partida/jugador/versión y resuelve la opción vigente. | Evita que un cliente remoto fabrique parámetros o reutilice una ventana antigua. |
| `service.py` | Consulta `engine.legal_actions`, valida el tipo cerrado, ejecuta y guarda con CAS. | La frontera vuelve a ejecutar validación autoritativa; una vista no garantiza que una opción siga vigente. |

**Conclusión:** el backend implementa una prioridad formal más precisa que los
PDF y, en algunos puntos (notablemente Transmutación), una ventana uniforme que
la fuente no termina de definir. Este documento registra esas diferencias sin
convertirlas en canon. Durante esta tarea **no se ha ampliado ninguna ventana
del motor** ni se ha modificado código ejecutable.

## 8. Revisión expresa de brechas solicitadas

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

## 9. Límites técnicos

- El catálogo de producción continúa vacío; las 431 entradas inventariadas no
  se convierten aquí en reglas universales ni contenido ejecutable.
- Las normalizaciones del backend pueden preservar compatibilidad, pero no
  cambian la relación normativa de ninguna fila.
- Los IDs de este documento son permanentes: una aclaración futura cambia estado,
  evidencia o relación, no reutiliza ni renumera el ID.

## 10. Matriz maestra de zonas confirmadas

### 10.1 Convenciones

Esta matriz usa **propietario** para la identidad a la que pertenece físicamente
la carta y **controlador** sólo para quien decide sobre ella mientras está en
juego. «Acceso» significa quién puede inspeccionar las identidades, no quién
puede ordenar un movimiento. Cuando los PDF no fijan un extremo se escribe
literalmente `UNKNOWN`; una práctica del backend no rellena ese silencio. Las
referencias a cartas concretas acreditan que el lugar o movimiento existe, pero
no convierten su texto en regla universal.

| Zona canónica | Evidencia PDF | Propietario | Controlador | Visibilidad | Orden | Acceso / búsqueda / selección | Entrada canónica | Salida canónica | Barajado | Persistencia canónica |
|---|---|---|---|---|---|---|---|---|---|---|
| **Mazo / baraja de Recursos** | Base pp. 3–4 y regla 20, p. 8; cartas de ambas ediciones con «busca», «mira», «encima» y «baraja». | Dueño de la baraja. | `UNKNOWN`; los textos dicen «tu» o «del jugador objetivo», no transfieren control de la zona. | Oculta, boca abajo; sólo un efecto permite verla. | Ordenada: hay cima/«primeras» cartas. Orientación física exacta: `UNKNOWN`. | Dueño u otro jugador sólo según el texto. Buscar puede filtrar/elegir; mirar no autoriza mover. El resto debe seguir oculto. | Construcción/preparación; devolver o barajar desde mano, tablero o Pila cuando lo ordene un texto; reciclaje Base p. 4. | Robar; mirar sin mover; buscar/moler/revelar o poner en juego según texto. | Sí al inicio, al reciclar la Pila y cuando una carta lo ordena. Algoritmo/entropía: `UNKNOWN`. | Las reglas exigen conservar el mazo durante la partida; representación, semilla y serialización: `UNKNOWN`. |
| **Mano** | Base pp. 4 y 6–8, en especial reglas 4, 9 y 20; numerosas cartas Base/Mítica. | Dueño de las cartas. | `UNKNOWN` fuera del uso ordinario por su dueño. | Oculta al oponente, boca abajo; un efecto puede autorizar mirarla. | Sin orden canónico relevante; colocación física sobre el tablero. | Dueño conoce toda su mano. Oponente sólo mira/busca/elige si una carta lo manda. | Robo, búsqueda/recuperación y devolución; mulligan. | Jugar/poner en juego, descarte, devolución al mazo o movimiento fuera de juego según texto. | No como operación propia; puede mezclarse con el mazo si un texto lo ordena. | Debe durar mientras la partida la contenga; formato técnico: `UNKNOWN`. |
| **Tablero / en juego / mesa** | Base pp. 3–8 (Transmutación, fases, combate, Equipos); Mítica físicas 3–4 / internas 2–3 (Divinos y Señores). | Dueño original; cambio por estar en juego: no indicado. | Quien lo bajó/controla, salvo efecto expreso de cambio de control. Duración/reversión exacta depende del texto. | Pública por disposición física y por requerir objetivos, combate, Fuerza y estado; orientación girada visible. | Posición relativa sin orden canónico. Anexos sí expresan relación Equipo–portador. | Jugadores pueden seleccionar objetivos legales; control limita atacar, transmutar, sacrificar y costes. | Jugar/bajar, poner directamente, devolver/retornar o transformación que permanezca en juego. | Destruir, sacrificar, transmutar, devolver, retirar o mandar a la Pila/mazo/mano. | No. | Permanece hasta que regla/texto lo mueva; qué estado sobrevive al cruce de zona es `UNKNOWN`. |
| **Pila de Descartes / Pila** | Base pp. 3–8; Mítica física 3 / interna 2 y corpus de cartas. | Dueño de cada carta. | `UNKNOWN`; estar en Pila no otorga control. | El texto la trata como zona consultable y desde la que se eligen/recuperan cartas; si es íntegramente pública y su orientación: `UNKNOWN`. | Se denomina pila, pero relevancia de cima/fondo y libertad de reordenar: `UNKNOWN`. | Buscar/recuperar o transmutar desde ella sólo cuando la regla o carta lo permita. Selección ordinaria del descarte ajeno: `UNKNOWN`. | Descartar, destrucción, sacrificio, Transmutación, resolución de no permanentes y movimientos expresos. | Recuperar/devolver/retornar/poner en juego; reciclaje completo cuando debe robarse de mazo vacío salvo bloqueo. | Sí al reciclarla; algunas cartas ordenan barajarla en el mazo. | Persiste hasta reciclaje/movimiento; representación técnica: `UNKNOWN`. |
| **Fuera de juego** | Mítica, física 6 / interna 5, carta nº 033: ordena enviar copias «fuera de juego» y prohíbe recuperarlas. | `UNKNOWN`. | `UNKNOWN`. | La identidad movida debe poder verificarse; visibilidad permanente de toda la zona: `UNKNOWN`. | `UNKNOWN`. | Sólo el texto particular determina qué se retira; acceso, búsqueda y selección posteriores: `UNKNOWN` (algún texto prohíbe recuperar esas cartas concretas). | «Retirar/remover fuera de juego» cuando una carta lo ordena. | Sólo si un texto lo autoriza; regla universal de retorno: `UNKNOWN`. | `UNKNOWN`. | Duración normalmente inferida hasta fin de partida, pero el PDF no formula contrato general: `UNKNOWN`. |
| **Apartadas / cartas mostradas durante mirar o revelar** | Cartas Base/Mítica dicen «déjalas aparte», «volteadas», mirar las primeras N, elegir y devolver/mandar el resto. | Conservan dueño: el texto no declara transferencia. | `UNKNOWN`. | Visible sólo en el alcance que ordene el texto; diferencia entre elector y todos: `UNKNOWN` salvo formulación concreta. | Conserva el orden original o permite «cualquier orden» únicamente si lo dice la carta; en otro caso `UNKNOWN`. | Sólo el elector indicado puede mirar/elegir; candidatos y no elegidas no se publican más allá del mandato. | Operación temporal de mirar/revelar desde una zona. | Destinos y orden exactos del texto particular. | Sólo si el mismo texto manda mezclar/barajar. | Si es una zona estable o sólo una condición física durante resolución: `UNKNOWN`; por tanto no se generaliza como zona persistente. |

### 10.2 Correspondencia con el backend solicitado

| `Zone` técnica | Correspondencia canónica | Contraste de implementación |
|---|---|---|
| `DECK`, `HAND`, `BATTLEFIELD`, `DISCARD`, `EXILE` | Las primeras cuatro corresponden directamente. `EXILE` es la normalización de «fuera de juego». | `domain/models.py:463-469` crea una lista por jugador. `zones.py:249-255` inserta al final y el motor interpreta `[-1]` como cima; esa orientación y la lista de exilio son contratos técnicos, no detalle PDF. |
| `REVEAL` | Aproxima cartas apartadas/reveladas, sin que el PDF confirme una zona estable universal. | Es lista por jugador, pero `REVEAL_UNTIL` mueve directamente a los destinos de éxito/fallo y no la utiliza (`effects.py:275-305`). No debe presentarse como canon adicional. |
| `RESOLUTION` | No es una zona nombrada por los PDF; representa la carta anunciada/en resolución. | Lista global en `GameState`; `stack.py:219-226` la saca al destino de resolución. La pila LIFO contiene `StackItem`, no las cartas como zona canónica. |
| `VOID` | No es sinónimo probado de «fuera de juego». | Lista global auxiliar. No se expone como zona PDF ni debe reemplazar automáticamente `EXILE`. |

El movimiento central de `zones.py:117-275` preserva el mismo `instance_id`,
pero al abandonar `BATTLEFIELD` restablece controlador al propietario, desanexa,
limpia daño, Fuerza modificada, prevención, activaciones, transformación,
regeneración, definición sustituida, orden de reemplazos y cambios de control.
**No limpia `counters`.** Esta es la semántica técnica actual; en ausencia de un
mandato de carta, los PDF dejan cada una de esas conservaciones en `UNKNOWN`.

## 11. Inventario separado de transiciones canónicas

### 11.1 Movimiento, causas y disparadores

«Trigger de salida» y «trigger de entrada» describen primero el canon. El motor
sólo declara `ON_ENTER_BATTLEFIELD` y `ON_TRANSMUTED`; no existe un disparador
general de abandonar zona. Un evento del log no equivale a una habilidad
disparada.

| Transición | Origen → destino | Causas confirmadas por PDF | Trigger salida | Trigger entrada | Contraste técnico |
|---|---|---|---|---|---|
| **Robar** | Mazo → mano | Preparación (seis), comienzo de turno (una), mulligan y cartas. | `UNKNOWN`. | `UNKNOWN`. | `_draw` toma `DECK[-1]`; si está vacío recicla descarte y emite eventos, sin triggers de zona. |
| **Mirar** | Sin movimiento, o zona → apartada temporal → zona/destino textual | Efectos que autorizan mano, cima o primeras N. | No hay salida si sólo se mira; si se aparta: `UNKNOWN`. | `UNKNOWN`. | No hay `EffectKind` general `LOOK`; `REVEAL_UNTIL` no modela privacidad de «mirar». Brecha. |
| **Revelar** | Zona oculta → información pública y, cuando lo dice la carta, otro destino | Texto particular, incluida revelación hasta coincidencia. | `UNKNOWN`. | `UNKNOWN`. | `REVEAL_UNTIL` emite `CARD_REVEALED` y mueve cada carta; `Zone.REVEAL` no interviene. |
| **Buscar** | Inspección de una zona; normalmente mazo → mano/juego u otro destino textual | Carta/habilidad con zona, filtro y destino; a menudo seguida de barajar. | `UNKNOWN`. | El «cuando entre» del destino sólo está confirmado si el texto de esa carta lo trata como entrar; regla universal: `UNKNOWN`. | `SEARCH_ZONE` pausa en `PendingSearch`, valida IDs elegibles, mueve y opcionalmente baraja; sólo encola `ON_ENTER_BATTLEFIELD` para la fuente resuelta, no para toda búsqueda. |
| **Seleccionar/elegir** | No implica movimiento | Objetivos, descartes, subconjuntos mirados/buscados, atacantes/bloqueadores y reemplazos. | No aplica salvo movimiento posterior. | No aplica salvo movimiento posterior. | Objetivos se congelan en `StackItem`; búsquedas y reemplazos crean elecciones pendientes. Selección es operación, no zona. |
| **Descartar** | Mano → Pila de Descartes | Ajuste final a seis, costes y efectos. | `UNKNOWN`. | `UNKNOWN`. | `MoveReason.DISCARD`; no hay trigger tipado de descarte. |
| **Recuperar** | Pila → mano/juego/mazo según texto; «recuperar» también puede modificar Heridas/Fuerza sin mover | Sólo texto particular. | `UNKNOWN`. | `UNKNOWN`. | `MOVE_CARDS` puede representar el cruce si está declarado; no hay razón `RECOVER` ni verbo inequívoco. Debe distinguirse curación/modificación. |
| **Devolver** | Tablero/Pila/mano → zona indicada, o cambio de controlador al anterior | Sólo texto particular. | `UNKNOWN`. | `UNKNOWN`. | Movimiento genérico o expiración de `ControlChange`; `MoveReason.RULE`. |
| **Poner en juego** | Normalmente mano/mazo/Pila → tablero | Pago y resolución ordinarios o carta que evita coste. | `UNKNOWN`. | Cartas particulares usan «cuando entre en juego»; no se generaliza obligatoriedad. | Resolución a `BATTLEFIELD` encola `ON_ENTER_BATTLEFIELD`; movimientos genéricos directos no lo hacen de forma uniforme. Brecha relevante. |
| **Destruir** | Tablero → Pila de Descartes | Daño letal, efecto «destruye», Fuerza cero para Señores; indestructible/reemplazos pueden impedirlo. | `UNKNOWN`. | `UNKNOWN`. | `_destroy_permanent`, razón `DESTROY` o `STATE_BASED`; admite regeneración y reemplazos. |
| **Sacrificar** | Permanente propio/controlado → Pila | Coste o efecto particular. | `UNKNOWN`. | `UNKNOWN`. | Coste con `MoveReason.SACRIFICE`; no hay trigger tipado `ON_SACRIFICED`. |
| **Transmutar** | Permanente propio en tablero → Pila; Reserva + coste impreso | Acción Base, incluida en pasiva; Mítica confirma Divinos. | El PDF permite reacciones textuales a Transmutación; orden universal: `UNKNOWN`. | `UNKNOWN`. | Operación directa, razón `TRANSMUTE`, después encola `ON_TRANSMUTED`; no usa pila para el movimiento. |
| **Retirar/remover** | Contextualmente tablero → Pila o → fuera de juego | Regla/texto particular; el corpus usa «remover a la Pila» y «fuera de juego», por lo que el verbo solo no fija destino. | `UNKNOWN`. | `UNKNOWN`. | Debe expresarse como destino explícito (`DISCARD`/`EXILE`); no existe `MoveReason.REMOVE`. |
| **Retornar/regresar** | Pila/mazo/mano → tablero, o cartas miradas → mazo | Texto particular. | `UNKNOWN`. | `UNKNOWN`; algunos textos concretos sí disparan «entrar». | Movimiento genérico; no hay `MoveReason.RETURN`. Aplicar `ON_ENTER_BATTLEFIELD` de forma uniforme requeriría decisión futura. |
| **Barajar/mezclar** | Misma zona reordenada; o Pila/mano incorporadas al mazo antes de mezclar | Preparación, mulligan, reciclaje y cartas. | No hay cambio de zona por mezclar; al incorporar cartas, trigger: `UNKNOWN`. | `UNKNOWN`. | RNG derivado de semilla/turno/eventos; emite `ZONE_SHUFFLED`. El reciclaje usa otra derivación. |
| **Colocar arriba o abajo** | Zona → cima/fondo del mazo, o reubicación dentro del mazo | Cartas concretas confirman cima/encima; fondo/abajo aparece sólo donde el texto lo indique. | `UNKNOWN`. | `UNKNOWN`. | `list.append` equivale a cima. No hay primitiva declarativa para fondo ni posición, y `MoveReplacementDefinition` prohíbe destinos técnicos pero no codifica posición. |
| **Reordenar** | Misma zona ordenada | Cartas permiten poner cartas miradas «en cualquier orden»; también puede ordenar reemplazos, que no son una zona. | No aplica. | No aplica. | Sólo hay barajado aleatorio y `replacement_order`; falta una transición de orden de cartas con elección persistible. |

### 11.2 Conservación de estado por transición

Valores: **Sí/No** sólo cuando la fuente lo determina; `N/A` cuando la magnitud
no pertenece a una carta; `UNKNOWN` cuando el PDF guarda silencio. «Identidad»
es la identidad de la **instancia física**, no el nombre/definición impresa.

| Transición | Heridas | Contadores | Fuerza | Girado | Anexos | Control | Transformación | Identidad de instancia | Determinación de la fuente |
|---|---|---|---|---|---|---|---|---|---|
| Robar | N/A | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | Sí, es la misma carta física | Sólo origen/destino. |
| Mirar | N/A | Sí | Sí | Sí | Sí | Sí | Sí | Sí | Mirar por sí solo no cambia la carta; si se mueve después aplica esa transición. |
| Revelar | N/A | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | Sí | Revelar información no prueba cómo reinicia estado al mover. |
| Buscar | N/A | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | Sí | El texto fija elegibilidad/destino, normalmente no continuidad de estado. |
| Seleccionar | N/A | Sí | Sí | Sí | Sí | Sí | Sí | Sí | Elegir no muta por sí mismo. |
| Descartar | N/A | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | Sí | `UNKNOWN` salvo carta concreta. |
| Recuperar | N/A si mueve; si sana, el propio texto cambia Heridas | `UNKNOWN` | Puede cambiar Fuerza si lo dice el texto; en otro caso `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | Sí | «Recuperar» es polisémico y exige leer la carta. |
| Devolver | N/A | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | Puede devolver control si ése es el objeto textual; si mueve, `UNKNOWN` | `UNKNOWN` | Sí | Sólo texto particular. |
| Poner en juego | N/A | `UNKNOWN` | Coste/Fuerza base cuando corresponda; modificadores previos `UNKNOWN` | Sólo entra girada cuando el texto lo ordena; en otro caso `UNKNOWN` | `UNKNOWN` | Controlador indicado/ordinario; cambios anteriores `UNKNOWN` | `UNKNOWN` | Sí | No hay regla universal de «objeto nuevo». |
| Destruir | N/A | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | **No permanece anexado al objeto destruido**; el Equipo permanece en tablero (Base regla 13) | `UNKNOWN` fuera del tablero | `UNKNOWN` | Sí | Única conservación transversal expresa aquí: destino del Equipo, no sus otros estados. |
| Sacrificar | N/A | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | Sí | Sólo texto particular. |
| Transmutar | N/A | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | Sí | La Base fija movimiento y ganancia de Pasos, no reinicio de instancia. |
| Retirar | N/A | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | Sí | Incluso la posibilidad de retorno depende del texto. |
| Retornar | N/A | `UNKNOWN` | `UNKNOWN` | Puede entrar girada si la carta lo ordena; en otro caso `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | Sí | No se presume «instancia nueva». |
| Barajar | N/A | Sí mientras no haya además cambio de zona: `UNKNOWN` si se incorpora desde otra | Igual | Igual | Igual | Igual | Igual | Sí | Reordenar solo no altera estado; movimientos combinados no están definidos. |
| Colocar arriba/abajo | N/A | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | Sí | Fuente fija posición, no estado residual. |
| Reordenar | N/A | Sí | Sí | Sí | Sí | Sí | Sí | Sí | Reordenar por sí solo sólo cambia orden. |

El backend aplica una única política de limpieza a casi todos los movimientos
fuera del tablero, con independencia del verbo. Por ello actualmente contradice
la prudencia documental en un punto (conserva contadores aun cuando el canon es
`UNKNOWN`) y decide técnicamente los restantes silencios (los limpia). No se
modifica ese contrato en esta auditoría.

## 12. Auditoría de exposición de información

### 12.1 Superficies revisadas

| Superficie | Datos que contiene/publica | Resultado y rutas de riesgo |
|---|---|---|
| `service.py::MatchView` | `PlayerObservation` completo y comandos `GameCommand` completos. | **Interna, sensible.** `observe` incluye IDs de la mano propia, fuentes/IDs de objetos de pila, triggers, candidatos de búsqueda sólo para el elector y candidatos de reemplazo. `legal_actions` contiene parámetros, IDs de cartas y combinaciones. `MatchService.view(match_id, player_id)` no autentica: cualquier adaptador que lo exponga o acepte un `player_id` no autorizado revelaría mano/candidatos. `get_match` revelaría estado, orden de todos los mazos e historial; su docstring prohíbe expresamente usarlo remotamente. |
| Observación (`controllers/base.py`, construida en `engine/game.py:576-647`) | Mano propia; tamaños de manos rivales; tableros; pila/triggers; búsqueda y reemplazo pendientes condicionados. | No expone mano rival ni mazo directamente. Sí expone `source_card_id` de pila/triggers a todos y fases suprimidas: correcto sólo si esos objetos ya son públicos. Una habilidad disparada desde zona oculta o una fuente que aún no deba revelarse filtraría identidad derivada. El elector recibe todos los `eligible_card_ids`, no sólo los N primeros: correcto para «buscar», incorrecto si se reutiliza para «mirar» o selección limitada. |
| `application.py::PublicPlayerObservation` / `PublicMatchView` | Sólo mano propia, Pasos/Heridas propios, tamaños rivales, tableros, tamaño de pila y contador de eventos. | **Frontera remota conservadora:** elimina `stack_items`, triggers, fases suprimidas, candidatos y reemplazos. Los IDs propios y de permanentes públicos son deliberados. No publica el log, por lo que eventos con `card_id` privado no salen por esta ruta. |
| `application.py::PublicLegalAction` | MAC opaco `option_id` y nombre de clase del comando. | Oculta parámetros e IDs y liga opción a partida/jugador/versión. **Canal derivado residual:** cantidad y discriminadores de opciones pueden revelar cuántos candidatos/combinaciones existen. Para una búsqueda sólo llega al elector autenticado; cualquier futura vista espectadora o acción cuya legalidad dependa de mano/mazo rival deberá agrupar/ocultar opciones. |
| Autorización de `AuthenticatedMatchApplication` | Traduce identidad a jugador autorizado y vuelve a resolver la opción del servidor. | Evita suplantar jugador y fabricar parámetros. Mantener `MatchService` detrás de esta frontera es condición de seguridad; no entregar índices, comandos ni el mapa interno de opciones. Errores se traducen sin mensaje/cadena interna. |
| `presentation.py` | Presentaciones editoriales estáticas por `card_id`. | No consulta partidas ni instancias. No filtra orden, mano o candidatos. Riesgo sólo de configuración: registrar texto/arte de contenido todavía no publicado. |
| `public_catalog.py` | Definición mecánica y presentación completas, ordenadas por `card_id`. | Publica IDs **de definición**, reglas, estadísticas y metadatos del conjunto, no IDs de instancia ni presencia en una partida. Es seguro únicamente para un catálogo ya publicable; no debe construirse desde catálogo secreto, mazos de jugadores o definiciones desbloqueadas. El orden alfabético del catálogo no es orden de mazo. |
| `codec.py`, `snapshot.py`, `replay.py` | Estado completo, catálogo, semilla, `initial_decks`, historial, pendientes y listas ordenadas. | **Secretos de servidor.** Nunca son DTO públicos. Snapshot revela todas las zonas y el orden exacto; replay revela mazos iniciales y comandos/elecciones. Logs, backups, respuestas de error y herramientas de administración deben conservar la misma frontera. |

### 12.2 Hallazgos accionables sin cambio de contrato

1. **Alta severidad si se publica:** `MatchService.get_match`, snapshots y replays
   contienen orden de mazo, manos rivales, candidatos y semillas. Deben permanecer
   exclusivamente internos y con control de acceso.
2. **Alta severidad si se omite autorización:** `MatchService.view` confía en el
   `player_id`; sólo `AuthenticatedMatchApplication` debe enlazar identidad y
   jugador antes de invocarlo.
3. **Media, dependiente de contenido futuro:** `PlayerObservation.stack_items` y
   `pending_triggers` revelan IDs de fuente. No crear objetos observables desde
   una zona oculta antes del momento de revelación canónico.
4. **Media, canal lateral:** el número/tipo de `PublicLegalAction` puede codificar
   información privada. Las búsquedas actuales lo limitan al elector, pero una
   futura enumeración basada en mano rival, cima desconocida o candidato secreto
   debe usar una sola acción opaca o una selección autenticada posterior.
5. **Media, semántica:** `CARD_DRAWN` y algunos eventos internos llevan `card_id`;
   hoy sólo se publica el recuento. No exponer `event_log` sin una proyección por
   audiencia y por momento de revelación.
6. **Baja/organizativa:** el catálogo público no filtra publicaciones. Su entrada
   debe ser ya una colección pública; no usarlo como mecanismo de autorización.

No se encontró en `PublicMatchView.to_dict()` una ruta directa para IDs de mazo,
mano rival, candidatos privados ni orden del mazo. Esa conclusión no convierte
`MatchView`, `PlayerObservation`, snapshots, replays o catálogo fuente en DTO
públicos.

## 13. Impacto futuro (sin modificar contratos)

| Área | Impacto de completar zonas/transiciones | Condición de diseño segura |
|---|---|---|
| **Snapshot** | Posición cima/fondo, zona temporal revelada, audiencia de revelación y política de conservación tendrían que persistirse; cambiar la limpieza de instancia altera el digest semántico. | Nueva versión/migración explícita; nunca inferir `UNKNOWN` al cargar. Snapshots siguen siendo privados. |
| **Replay** | Mirar, reordenar, barajar, selección secreta y reemplazos deben reproducir exactamente decisión, orden y RNG, sin recalcular sobre estado divergente. | Registrar decisiones autoritativas y su audiencia; verificar digest antes de continuar; replay no público. |
| **CAS** | Una elección depende de la versión y del orden/identidad vigentes. Dos movimientos concurrentes pueden invalidar candidatos o cima. | Comprobar versión antes de ejecutar, mantener token ligado a partida/jugador/versión y no devolver detalles al conflicto. |
| **Selección pendiente** | Buscar, mirar N, ordenar y escoger reemplazo necesitan distintos contratos de visibilidad; no deben compartir automáticamente `eligible_card_ids`. | Guardar elector, audiencia, mínimo/máximo, orden permitido y sólo candidatos autorizados. Publicar una opción opaca; revalidar al resolver. |
| **Rollback transaccional** | Un fallo tras mover/revelar/barajar podría dejar información conocida aunque el estado se restaure; el conocimiento del jugador no es reversible. | Validar antes de revelar, ejecutar movimiento/trigger/persistencia atómicamente y no emitir respuestas parciales. Si ya se reveló, tratarlo como hecho auditable, no fingir que se deshizo. |
| **Errores públicos seguros** | Diferenciar «no existe», «no elegible», «zona cambió» o «carta secreta» crea un oráculo sobre contenido oculto. | Código/mensaje estable no revelador (`CommandRejected`, `WriteConflict`); detalles sólo en telemetría interna protegida y sin volcar snapshots. |
| **Identidad de instancia** | Decidir si un cambio de zona crea «objeto nuevo» afectaría anexos, contadores, triggers, efectos continuos, opciones y hashes. | Resolver normativamente cada estado hoy `UNKNOWN`, versionar semántica y mantener IDs externos opacos; no reutilizar IDs para otra carta. |
| **Catálogo público** | Nuevas cartas pueden revelar contenido antes de publicación y sus filtros pueden facilitar inferencias sobre búsquedas. | Separar catálogo publicable del catálogo mecánico de servidor; no incluir disponibilidad por partida, copias, propietario ni orden. |

Esta sección es un registro de impacto, no una especificación de migración. En
particular, **no cambia** snapshot v2, replay v2, CAS, selección pendiente,
rollback ni el esquema de errores públicos seguros existente.
