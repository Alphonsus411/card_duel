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

## 14. Fichas maestras de gaps y bloqueos

### 14.1 Cobertura, vocabulario y separación de responsabilidades

Esta sección es la capa de planificación del registro maestro. Cubre **toda**
fila `PARTIAL` o `MISSING` de la matriz de 431 entradas y todo bloqueo
`AMBIGUOUS` o `CONFLICT` de este documento, sin convertir una carta en una
solución ad hoc:

* una fila `PARTIAL` cuyo lenguaje es `REPRESENTABLE` pertenece a
  `CAP-CATALOG-INGESTION`; si además declara un extremo incompleto, pertenece
  también a la capacidad general correspondiente;
* una fila `MISSING` pertenece a una o más fichas `CAP-*` según sus
  `intrínsecas`, `triggers`, `efectos`, selección, duración y movimientos en
  `CARD_CORPUS_CONFORMANCE.md`; una combinación no crea otra capacidad;
* las filas `AMBIGUOUS` de cartas y las reglas `N-*` ambiguas pertenecen a
  `BLOCK-EDITORIAL`; `N-POINTS-01` pertenece a `BLOCK-POINTS-CONFLICT`;
* `ENGINE_STATUS` usa sólo `ENGINE_DEFECT`, `CAPABILITY_NOT_IMPLEMENTED` o
  `EDITORIAL_BLOCKED`. Un mismo caso puede enlazar varias fichas, pero esas
  responsabilidades nunca se fusionan.

La columna **Cartas afectadas** de cada ficha es un selector exhaustivo sobre la
matriz carta por carta, no una lista manual susceptible de quedar obsoleta. Por
ejemplo, `intrínsecas contiene VUELO` significa *todas* las filas que satisfacen
esa expresión. Los IDs citados después son muestras trazables, no límites. La
coordenada de fuente completa de cada afectada permanece en su fila. Cuando la
fuente no resuelve un dato se escribe `UNKNOWN` o `AMBIGUOUS`; cuando un campo
no pertenece al concepto se escribe `NOT APPLICABLE`.

Cada ficha usa consistentemente los campos solicitados. **Impactos** siempre
informa arquitectura, persistencia, snapshot, replay, atomicidad/rollback,
determinismo/CAS, acciones legales y privacidad.

### 14.2 Capacidad transversal: incorporación declarativa

| Campo | Valor |
|---|---|
| **ID** | `CAP-CATALOG-INGESTION` |
| **CATEGORY** | Catálogo/contenido declarativo compartido |
| **SOURCE_PDF** | `Fantasy Tokens.pdf`; `Fantasy Tokens Edicion Mitica.pdf` |
| **SOURCE_PAGE** | Las coordenadas física/interna de cada fila `PARTIAL` en la matriz |
| **SOURCE_CARD/TOKEN** | Todas las filas `PARTIAL`; por ejemplo `ALPHA-006` El Primigenio y `MITICA-163` Iluminación |
| **SOURCE_TEXT** | El extracto conservado en la fila de cada carta; no se sustituye por una paráfrasis global |
| **NORMALIZED_RULE** | Una definición representable debe incorporarse como datos de contenido, sin ramas por identidad y sin ampliar el significado de sus primitivas |
| **APPLIES_TO** | Toda fila con `Estado=PARTIAL`; las primitivas compartidas se reutilizan entre identidades/reimpresiones |
| **PHASE/WINDOW** | La ventana de la fila; `UNKNOWN` cuando la fila la marca ordinaria/no indicada |
| **ZONES** | Las zonas de la fila; `NOT APPLICABLE` si no hay movimiento |
| **VISIBILITY** | La de la fila: `PÚBLICA` u `OCULTA+REVELADO_NECESARIO` |
| **COST** | Coste impreso y costes adicionales conservados por fila; `UNKNOWN` si el PDF no los completa |
| **TARGET/SELECTION** | Selector declarado por fila; nunca se completa por el nombre o el arte |
| **DURATION** | La de la fila; `UNKNOWN` para `PERMANENTE/NO_INDICADA` cuando ambas lecturas no son equivalentes |
| **INTERACTIONS** | Catálogo, `EffectDefinition`, targeting, timing, presentación y política de mazo |
| **ENGINE_STATUS** | `CAPABILITY_NOT_IMPLEMENTED` (contenido); no es por sí mismo defecto del intérprete |
| **CURRENT_SUPPORT** | Lenguaje `REPRESENTABLE`; sólo 2 entradas están completamente soportadas y el resto del corpus no está incorporado |
| **EXACT_GAP** | Faltan definiciones, validación de datos y pruebas por combinación; una fila que también dependa de una primitiva ausente sigue enlazada a su `CAP-*` |
| **GENERAL_CAPABILITY_REQUIRED** | Pipeline validado de ingestión y registro; no factorías por carta |
| **Impactos** | **Arquitectura:** contenido aislado del motor. **Persistencia/snapshot:** definición y versión del catálogo deben ser resolubles. **Replay:** fijar catálogo/semántica. **Atomicidad/rollback:** alta completa o rechazo sin registro parcial. **Determinismo/CAS:** orden e IDs estables; CAS antes de jugar. **Acciones legales:** sólo cartas realmente registradas y autorizadas. **Privacidad:** no publicar cartas no lanzadas ni datos de mazos. |
| **Cartas afectadas** | Selector: `Estado=PARTIAL` (245 entradas; 212 identidades agregadas al corte) |
| **Dependencias** | Validadores de contenido, taxonomía canónica, versión de catálogo y todas las `CAP-*` adicionales enlazadas por fila |
| **Prioridad** | `P1`, después de las capacidades `P0` necesarias para cada carta |

### 14.3 Capacidades generales aún no implementadas

#### `CAP-RACE-TAXONOMY` — taxonomía racial tipada

| Campo | Valor |
|---|---|
| **ID** | `CAP-RACE-TAXONOMY` |
| **CATEGORY** | Selección/taxonomía |
| **SOURCE_PDF** | Ambos PDF |
| **SOURCE_PAGE** | Múltiples; coordenada por fila |
| **SOURCE_CARD/TOKEN** | Selector: `tax` no vacío usado mecánicamente; muestras `ALPHA-007`, `MITICA-143`, `MITICA-180` |
| **SOURCE_TEXT** | Bonificaciones, búsquedas o restricciones por Primigenio, Goblin, Elfo, Ángel y demás familias |
| **NORMALIZED_RULE** | La pertenencia racial es una dimensión tipada y multivalor, distinta de tipo funcional, rango, nombre y menciones en efectos |
| **APPLIES_TO** | Definiciones, filtros de objetivo/búsqueda, efectos continuos y construcción |
| **PHASE/WINDOW** | `NOT APPLICABLE` a la pertenencia; la acción consumidora conserva su ventana |
| **ZONES** | Cualquier zona consultada por el efecto; no se presume sólo tablero |
| **VISIBILITY** | Pública en permanentes; en mazo/mano sólo resultado autorizado |
| **COST** | `NOT APPLICABLE`; conserva el coste de la acción consumidora |
| **TARGET/SELECTION** | Predicados por una o varias razas, inclusión/exclusión y controlador |
| **DURATION** | `NOT APPLICABLE` para la identidad; la modificación que la cambie necesita duración explícita |
| **INTERACTIONS** | Búsqueda, lord effects, cambio de tipo, copias, transformación y reimpresiones |
| **ENGINE_STATUS** | `CAPABILITY_NOT_IMPLEMENTED` |
| **CURRENT_SUPPORT** | Existen strings/filtros parciales; no hay contrato racial canónico completo y uniforme |
| **EXACT_GAP** | No se puede distinguir de forma autoritativa pertenencia, mención, alias y combinación racial en todos los filtros |
| **GENERAL_CAPABILITY_REQUIRED** | `CreatureTaxon` normalizado + predicado reusable de audiencia/zona/controlador |
| **Impactos** | **Arquitectura:** valor tipado, no condicional por carta. **Persistencia/snapshot:** serializar vocabulario/versionado. **Replay:** resolver con la taxonomía fijada. **Atomicidad/rollback:** cambios de raza con el efecto completo. **Determinismo/CAS:** ordenar coincidencias por ID estable y revalidar versión. **Acciones legales:** filtrar targets/candidatos en servidor. **Privacidad:** no revelar razas de cartas ocultas no elegidas. |
| **Cartas afectadas** | Selector exhaustivo: filas `PARTIAL`/`MISSING` cuyo efecto depende de `tax`, aunque la mención no atribuya esa raza a la propia fuente |
| **Dependencias** | `CANONICAL_TAXONOMY.md`, targeting y búsqueda |
| **Prioridad** | `P0` |

#### `CAP-CHALLENGE-TRIGGER` — Desafío disparado

| Campo | Valor |
|---|---|
| **ID** | `CAP-CHALLENGE-TRIGGER` |
| **CATEGORY** | Combate/trigger especial |
| **SOURCE_PDF** | `Fantasy Tokens Edicion Mitica.pdf` |
| **SOURCE_PAGE** | Física 4 / interna 3 y cartas enlazadas en la matriz |
| **SOURCE_CARD/TOKEN** | Regla Desafío y filas con conducta al declarar/resolver Desafío |
| **SOURCE_TEXT** | Desafío se usa una vez por turno en Fase Activa y sustituye el combate normal |
| **NORMALIZED_RULE** | Evento tipado de declaración/resolución de Desafío capaz de disparar efectos, sin restringirlo por analogía a Reinos |
| **APPLIES_TO** | Señores y criaturas expresamente elegibles; habilidades que observan Desafío |
| **PHASE/WINDOW** | Fase Activa; normalización técnica actual `EFFECTS`; alcance exacto `AMBIGUOUS` |
| **ZONES** | Tablero; pila si los disparos usan la pila |
| **VISIBILITY** | PÚBLICA |
| **COST** | Una utilización por turno; otros costes `UNKNOWN` salvo carta |
| **TARGET/SELECTION** | Desafiador, defensor y elecciones de orden; restricciones exactas por texto |
| **DURATION** | Una resolución; uso consumido hasta el siguiente turno |
| **INTERACTIONS** | Combate normal, prioridad, daño letal, transformación de Señor y triggers |
| **ENGINE_STATUS** | `CAPABILITY_NOT_IMPLEMENTED` para el trigger; el comando básico de Desafío sí existe |
| **CURRENT_SUPPORT** | Declaración/resolución básica y exclusión mutua; no evento declarativo general para cartas observadoras |
| **EXACT_GAP** | Falta un evento disparable con payload estable y orden respecto de daño/salida |
| **GENERAL_CAPABILITY_REQUIRED** | Event bus tipado de Challenge con batch de triggers |
| **Impactos** | **Arquitectura:** evento de dominio reusable. **Persistencia/snapshot:** uso por turno, challenge pendiente y triggers. **Replay:** registrar participantes/orden. **Atomicidad/rollback:** declarar, consumir uso y encolar como unidad. **Determinismo/CAS:** orden canónico y versión previa. **Acciones legales:** sólo ofrecer con elegibilidad y prioridad vigentes. **Privacidad:** no incluir información oculta en payload/opciones. |
| **Cartas afectadas** | Selector: filas `PARTIAL`/`MISSING` con ventana, texto o trigger de Desafío; IDs exactos en la matriz |
| **Dependencias** | Pila, prioridad, combate, `BLOCK-EDITORIAL` para el alcance de Fase Activa |
| **Prioridad** | `P0` |

#### `CAP-DAMAGE-PREVENTION` — prevención por causa y duración

| Campo | Valor |
|---|---|
| **ID** | `CAP-DAMAGE-PREVENTION` |
| **CATEGORY** | Daño/reemplazo/duración |
| **SOURCE_PDF** | Ambos PDF |
| **SOURCE_PAGE** | Por fila; muestra Base 9/9 |
| **SOURCE_CARD/TOKEN** | Selector: `efectos` contiene `PREVENT` o texto impide daño/destrucción por una causa; muestra `ALPHA-013` Amuleto de Huesos |
| **SOURCE_TEXT** | «prevén todo el daño de combate recibido este turno»; otros textos limitan fuente, receptor o siguiente ocurrencia |
| **NORMALIZED_RULE** | Un escudo filtra causa/tipo/fuente/receptor, cantidad o totalidad y expiración; impedir destrucción no equivale siempre a prevenir daño |
| **APPLIES_TO** | Jugador, criatura o conjunto expresamente indicado |
| **PHASE/WINDOW** | Ventana de la carta y punto de reemplazo antes de aplicar daño |
| **ZONES** | Tablero/estado del jugador; fuente puede estar en resolución |
| **VISIBILITY** | PÚBLICA tras crear el escudo; condiciones ocultas `UNKNOWN` salvo texto |
| **COST** | El de la carta/habilidad; `NOT APPLICABLE` al consumo del escudo salvo texto |
| **TARGET/SELECTION** | Receptor y predicado de causa; objetivos exactos por fila |
| **DURATION** | Fin de turno, siguiente ocurrencia, mientras la fuente permanezca o la indicada; nunca `permanente` por defecto |
| **INTERACTIONS** | Daño de combate/no combate, heridas, letalidad, reemplazos, Dureza e inmunidad |
| **ENGINE_STATUS** | `CAPABILITY_NOT_IMPLEMENTED` |
| **CURRENT_SUPPORT** | Hay prevención cuantitativa temporal limitada, no matriz completa por causa/duración |
| **EXACT_GAP** | El escudo actual no expresa todas las procedencias, alcance total, expiraciones ni orden de reemplazo |
| **GENERAL_CAPABILITY_REQUIRED** | `DamagePreventionRule` tipada y orden de reemplazos determinista |
| **Impactos** | **Arquitectura:** pipeline previo a daño. **Persistencia/snapshot:** saldo, filtros, expiración y orden. **Replay:** registrar elección de reemplazo, no recalcularla. **Atomicidad/rollback:** consumir escudo y aplicar remanente juntos. **Determinismo/CAS:** orden estable y revalidación. **Acciones legales:** ofrecer elecciones sólo al elector. **Privacidad:** no revelar fuente oculta antes de causar daño. |
| **Cartas afectadas** | Selector exhaustivo anterior sobre filas `PARTIAL`/`MISSING` |
| **Dependencias** | Daño tipado, duraciones, reemplazos y `CAP-TYPED-IMMUNITY` |
| **Prioridad** | `P0` |

#### `CAP-COMBAT-KEYWORDS` — Vuelo, Dureza, ataque sin giro y ataque doble

| Campo | Valor |
|---|---|
| **ID** | `CAP-COMBAT-KEYWORDS` |
| **CATEGORY** | Combate/propiedades intrínsecas |
| **SOURCE_PDF** | Ambos PDF |
| **SOURCE_PAGE** | Por fila; muestras Base física/interna 9/9, 10/10 y 12/12; Mítica física 15 / interna 14 |
| **SOURCE_CARD/TOKEN** | `ALPHA-005` Hada Primigenia (Vuelo), `ALPHA-050` Reno Nórdico (Dureza/no giro), `MITICA-142` Ángel de la Justicia (ataque doble) |
| **SOURCE_TEXT** | Vuelo impide bloqueo por terrestres sin la habilidad; Dureza da +2 al bloquear o ser bloqueada; otras cartas no se giran al atacar o atacan dos veces |
| **NORMALIZED_RULE** | Cuatro capacidades independientes: restricción de bloqueo, modificador condicionado, exención del coste de giro y multiplicidad de ataques/daño |
| **APPLIES_TO** | Criatura portadora o criatura equipada mientras conserve la capacidad |
| **PHASE/WINDOW** | Declaración de atacantes/bloqueadores y resolución de cada ataque |
| **ZONES** | Tablero |
| **VISIBILITY** | PÚBLICA |
| **COST** | No giro modifica sólo el giro de atacar; los demás costes son `NOT APPLICABLE` salvo texto |
| **TARGET/SELECTION** | Atacante/bloqueador; ataque doble conserva defensor, salvo que la fuente indique nueva selección (`UNKNOWN`) |
| **DURATION** | Mientras se posea la capacidad; bonificación de Dureza durante la condición de combate |
| **INTERACTIONS** | Aptitud, girado previo, múltiples bloqueadores, pérdida de habilidades, equipos y prevención |
| **ENGINE_STATUS** | `CAPABILITY_NOT_IMPLEMENTED` |
| **CURRENT_SUPPORT** | Los nombres pueden almacenarse; no hay semántica universal completa en enumeración/validación/resolución |
| **EXACT_GAP** | Legal actions y combate no ejecutan uniformemente los cuatro contratos ni su concesión/pérdida dinámica |
| **GENERAL_CAPABILITY_REQUIRED** | Conjunto tipado de capacidades de combate consultado por enumerador y validador autoritativo |
| **Impactos** | **Arquitectura:** predicados compartidos, no flags por identidad. **Persistencia/snapshot:** capacidades concedidas y expiración. **Replay:** registrar declaraciones, no opciones descartadas. **Atomicidad/rollback:** declarar/girar/consumir ataque juntos. **Determinismo/CAS:** validar estado y versión; ordenar ataques. **Acciones legales:** enumerador y ejecutor deben coincidir. **Privacidad:** no filtrar mejoras ocultas antes de revelarse. |
| **Cartas afectadas** | Selector: filas `PARTIAL`/`MISSING` con `VUELO`, `DUREZA`, `NO_GIRO` o texto «ataca dos veces»; incluye capacidades concedidas por Equipos/Eventos |
| **Dependencias** | Combate, efectos continuos, duraciones y targeting |
| **Prioridad** | `P0` |

#### `CAP-TYPED-IMMUNITY` — inmunidades por tipo de fuente/efecto

| Campo | Valor |
|---|---|
| **ID** | `CAP-TYPED-IMMUNITY` |
| **CATEGORY** | Interacción/targeting/resolución |
| **SOURCE_PDF** | Ambos PDF |
| **SOURCE_PAGE** | Por fila; regla Mítica física 3 / interna 2 |
| **SOURCE_CARD/TOKEN** | Selector: `intrínsecas=INMUNIDAD` o `efectos` contiene `IMMUNITY`; muestras `MITICA-166`, `MITICA-169`, `MITICA-179` |
| **SOURCE_TEXT** | Inmunidad a Eventos, Recursos Rápidos, Habilidades y/o Tokens Legendarios, en combinaciones expresas |
| **NORMALIZED_RULE** | La inmunidad es un predicado sobre tipo de fuente, rango y/o clase de efecto; no es invulnerabilidad global ni se infiere por semejanza |
| **APPLIES_TO** | Objeto protegido y sólo categorías enumeradas |
| **PHASE/WINDOW** | Selección de objetivos y revalidación al resolver; `NOT APPLICABLE` como ventana propia |
| **ZONES** | Normalmente tablero; otras zonas `UNKNOWN` salvo texto |
| **VISIBILITY** | PÚBLICA cuando la fuente protegida es pública |
| **COST** | `NOT APPLICABLE` |
| **TARGET/SELECTION** | Excluye targets ilegales y define qué ocurre al resolver si adquiere inmunidad |
| **DURATION** | Mientras se posea o durante la duración concedida |
| **INTERACTIONS** | Divinos, Señores «a modo de Eventos» (`AMBIGUOUS`), habilidades, legendarios, copia y pérdida de habilidades |
| **ENGINE_STATUS** | `CAPABILITY_NOT_IMPLEMENTED` para la matriz general; hay filtros concretos parciales |
| **CURRENT_SUPPORT** | Filtros limitados de targeting; no clasificación completa y uniforme de fuente/efecto |
| **EXACT_GAP** | Falta tipar procedencia y aplicar la misma regla en enumeración, validación y resolución |
| **GENERAL_CAPABILITY_REQUIRED** | `SourceDescriptor` + `ImmunityPredicate` declarativos |
| **Impactos** | **Arquitectura:** clasificación transversal. **Persistencia/snapshot:** inmunidades concedidas y fuente. **Replay:** fijar versión de clasificación. **Atomicidad/rollback:** validar antes de pagar; rollback total si falla. **Determinismo/CAS:** revalidar target/version. **Acciones legales:** paridad enumerador-ejecutor. **Privacidad:** error uniforme; no confirmar una inmunidad oculta. |
| **Cartas afectadas** | Selector exhaustivo anterior sobre filas `PARTIAL`/`MISSING` |
| **Dependencias** | Tipos funcionales/rangos, targeting, pila y `BLOCK-EDITORIAL` (`N-LEGENDARY-06`) |
| **Prioridad** | `P0` |

#### `CAP-ZONE-EXIT` — triggers y reemplazos de salida

| Campo | Valor |
|---|---|
| **ID** | `CAP-ZONE-EXIT` |
| **CATEGORY** | Zonas/triggers/reemplazos |
| **SOURCE_PDF** | Ambos PDF |
| **SOURCE_PAGE** | Por fila |
| **SOURCE_CARD/TOKEN** | Selector: triggers `ON_DESTROYED`, `ON/MOVE_DISCARD`, Transmutación o texto «si fuera a ir/salir»; muestras `ALPHA-035`, `MITICA-134`, `MITICA-142` |
| **SOURCE_TEXT** | Efectos al ser destruida, removida, transmutada o antes de ir a la Pila |
| **NORMALIZED_RULE** | Distinguir evento posterior de salida y reemplazo previo, con origen, destino, causa, instancia y controlador capturados |
| **APPLIES_TO** | Instancia que cambia de zona y observadores expresamente autorizados |
| **PHASE/WINDOW** | Inmediatamente antes (reemplazo) o después (trigger) del movimiento; prioridad exacta `UNKNOWN` salvo texto |
| **ZONES** | Origen/destino tipados; «remover» sin destino es `AMBIGUOUS` |
| **VISIBILITY** | Según origen y momento de revelación; audiencia debe persistirse |
| **COST** | Sacrificio/Transmutación si corresponde; en otro caso `NOT APPLICABLE` |
| **TARGET/SELECTION** | Reemplazo y targets del efecto derivado; elector/orden explícitos |
| **DURATION** | Una transición; efectos derivados según carta |
| **INTERACTIONS** | Destruir, sacrificar, Transmutar, indestructible, regeneración, anexos y limpieza de estado |
| **ENGINE_STATUS** | `CAPABILITY_NOT_IMPLEMENTED` |
| **CURRENT_SUPPORT** | `ON_TRANSMUTED` y reemplazos de movimiento parciales; no trigger universal de salida ni entrada uniforme |
| **EXACT_GAP** | No existe payload causal completo ni orden/batch general; movimientos directos divergen |
| **GENERAL_CAPABILITY_REQUIRED** | `ZoneChangeEvent`/`ZoneChangeReplacement` autoritativos |
| **Impactos** | **Arquitectura:** toda mutación pasa por una puerta de zona. **Persistencia/snapshot:** pendientes, causa, audiencia y last-known-info. **Replay:** registrar reemplazo/orden. **Atomicidad/rollback:** movimiento, limpieza y encolado indivisibles. **Determinismo/CAS:** orden estable y versión previa. **Acciones legales:** elecciones de reemplazo sólo al elector. **Privacidad:** last-known-info proyectada por audiencia. |
| **Cartas afectadas** | Selector exhaustivo anterior sobre filas `PARTIAL`/`MISSING` |
| **Dependencias** | Gestor de zonas, pila, duraciones, snapshots y `CAP-SECRET-CHOICE` |
| **Prioridad** | `P0` |

#### `CAP-SECRET-CHOICE` — elecciones compuestas, ambiguas y ocultas

| Campo | Valor |
|---|---|
| **ID** | `CAP-SECRET-CHOICE` |
| **CATEGORY** | Selección/orden/privacidad |
| **SOURCE_PDF** | Ambos PDF |
| **SOURCE_PAGE** | Por fila |
| **SOURCE_CARD/TOKEN** | Selector: selección desde mano/mazo, top-N, «elige», alternativas o reordenación; muestras `ALPHA-025`, `ALPHA-034`, `MITICA-157`, `MITICA-162` |
| **SOURCE_TEXT** | Elegir subconjuntos, uno entre modos, cartas de menor coste, primeras N y orden de las restantes |
| **NORMALIZED_RULE** | Elección tipada con elector, audiencia, candidatos, cardinalidad, modo, orden y momento; si el texto admite varias lecturas, queda `AMBIGUOUS` y no se ejecuta una preferida |
| **APPLIES_TO** | Jugador autorizado y objetos elegibles en la zona indicada |
| **PHASE/WINDOW** | Durante anuncio o resolución según texto; si no se determina: `AMBIGUOUS` |
| **ZONES** | Mano, mazo, descarte, tablero y zona temporal; exactamente las indicadas |
| **VISIBILITY** | Privada al elector salvo revelación expresa; resultado/audiencia separados |
| **COST** | Elecciones de coste antes del pago; otras `NOT APPLICABLE` |
| **TARGET/SELECTION** | Mínimo/máximo/exacto, repetición, orden y modos persistibles |
| **DURATION** | Hasta completar/cancelar la elección; efecto resultante según fuente |
| **INTERACTIONS** | Búsqueda, mirar/revelar, replacements, targeting, prioridad y errores públicos |
| **ENGINE_STATUS** | `CAPABILITY_NOT_IMPLEMENTED` para selecciones compuestas; `EDITORIAL_BLOCKED` sólo en cada lectura realmente ambigua |
| **CURRENT_SUPPORT** | Targets congelados, `PendingSearch` y elección de reemplazo; no contrato general de modo/top-N/reordenación/audiencia |
| **EXACT_GAP** | Candidatos y orden se modelan de forma desigual; algunas frases no fijan quién/cómo/cuándo elige |
| **GENERAL_CAPABILITY_REQUIRED** | `PendingChoice` discriminada, opaca y versionada |
| **Impactos** | **Arquitectura:** máquina de estados de elección. **Persistencia/snapshot:** elector, audiencia, candidatos y orden. **Replay:** registrar elección autoritativa. **Atomicidad/rollback:** no revelar antes de validar; conocimiento no se revierte. **Determinismo/CAS:** option token ligado a versión. **Acciones legales:** una opción opaca, revalidada. **Privacidad:** no publicar candidatos/cantidad si crean canal lateral. |
| **Cartas afectadas** | Selector exhaustivo anterior sobre filas `PARTIAL`/`MISSING`; filas `AMBIGUOUS` se enlazan además a `BLOCK-EDITORIAL` |
| **Dependencias** | Zonas, autenticación, opciones, CAS y proyección por audiencia |
| **Prioridad** | `P0` |

#### `CAP-EFFECT-COMPOSITION` — cobertura residual de operaciones y secuencias

| Campo | Valor |
|---|---|
| **ID** | `CAP-EFFECT-COMPOSITION` |
| **CATEGORY** | Intérprete declarativo/composición |
| **SOURCE_PDF** | Ambos PDF |
| **SOURCE_PAGE** | Coordenada individual de cada fila `MISSING` no satisfecha completamente por las fichas anteriores |
| **SOURCE_CARD/TOKEN** | Selector residual: toda fila `Estado=MISSING`; muestras adicionales `ALPHA-004`, `ALPHA-019`, `MITICA-176 (Tambor Chamánico)`, `MITICA-188` |
| **SOURCE_TEXT** | Secuencias, costes compuestos, cantidades variables, restricciones, cambios de control/tipo, creación de fichas, zonas o condiciones terminales conservados por fila |
| **NORMALIZED_RULE** | Componer primitivas generales en orden, con valores capturados y condiciones, sin handlers por `card_id`; una ficha especializada prevalece para su dominio |
| **APPLIES_TO** | Toda operación declarada en una fila `MISSING` que no sea ejecutable con semántica completa |
| **PHASE/WINDOW** | La de cada fila; `UNKNOWN`/`AMBIGUOUS` si la fuente no la fija |
| **ZONES** | Las de cada fila; `NOT APPLICABLE` sin movimiento |
| **VISIBILITY** | La de cada fila y por paso; nunca heredar publicidad entre pasos |
| **COST** | Costes impresos/adicionales de cada fila; orden entre coste y efecto sólo cuando esté determinado |
| **TARGET/SELECTION** | Targets, modos, cantidades y valores X declarados; `AMBIGUOUS` si faltan extremos |
| **DURATION** | La individual; `UNKNOWN` cuando no indicada |
| **INTERACTIONS** | Todas las `CAP-*`, pila, prioridad, zonas, control, copia, fases y fin de partida |
| **ENGINE_STATUS** | `CAPABILITY_NOT_IMPLEMENTED` |
| **CURRENT_SUPPORT** | Existen primitivas atómicas, pero su presencia en la matriz no acredita secuencia, repetición, trigger, duración, selección ni visibilidad completas |
| **EXACT_GAP** | Residuo exacto = campos de la fila que no pueden expresarse tras aplicar las fichas especializadas; debe registrarse al implementar, nunca aproximarse |
| **GENERAL_CAPABILITY_REQUIRED** | AST declarativo de secuencia/condición/valor capturado y registro extensible de operaciones |
| **Impactos** | **Arquitectura:** composición y handlers por operación. **Persistencia/snapshot:** continuación, valores capturados y versión del AST. **Replay:** decisiones/resultados no deterministas registrados. **Atomicidad/rollback:** transacción completa o continuación persistida, sin estado medio invisible. **Determinismo/CAS:** orden estable, RNG derivado y CAS antes de cada continuación. **Acciones legales:** preflight de costes/targets y revalidación. **Privacidad:** proyección por paso/audiencia y errores no-oráculo. |
| **Cartas afectadas** | Selector exhaustivo: `Estado=MISSING` (143 entradas; 132 identidades agregadas al corte), además de las fichas especializadas que correspondan |
| **Dependencias** | Todas las capacidades especializadas, efectos, opciones, codec y transacciones |
| **Prioridad** | `P0` para primitivas compartidas por varias cartas; `P1` para combinaciones ya expresables tras esas primitivas |

### 14.4 Defecto de engine separado

| Campo | Valor |
|---|---|
| **ID** | `DEF-ZONE-COUNTERS-RESET` |
| **CATEGORY** | Defecto de estado/transición |
| **SOURCE_PDF** | Ambos PDF |
| **SOURCE_PAGE** | `UNKNOWN` como regla universal; fuentes por carta cuando ordenan conservar/eliminar |
| **SOURCE_CARD/TOKEN** | Toda carta con contadores que cambie de zona |
| **SOURCE_TEXT** | No existe regla universal localizada que autorice conservar contadores al abandonar tablero |
| **NORMALIZED_RULE** | `UNKNOWN`; no afirmar conservación canónica |
| **APPLIES_TO** | Instancias con contadores en transición fuera de tablero |
| **PHASE/WINDOW** | Durante movimiento |
| **ZONES** | Tablero → cualquier otra |
| **VISIBILITY** | Según destino |
| **COST** | `NOT APPLICABLE` |
| **TARGET/SELECTION** | `NOT APPLICABLE` |
| **DURATION** | `UNKNOWN` |
| **INTERACTIONS** | Limpieza de instancia, retorno, copia y transformación |
| **ENGINE_STATUS** | `ENGINE_DEFECT` (divergencia interna: se limpian otros estados, pero no `counters`); la conducta normativa final sigue bloqueada por `UNKNOWN` |
| **CURRENT_SUPPORT** | `zones.py` conserva contadores fuera del tablero |
| **EXACT_GAP** | Política técnica inconsistente y no respaldada; corregir requiere primero decisión normativa/versionado |
| **GENERAL_CAPABILITY_REQUIRED** | Política única y versionada de identidad/limpieza por transición |
| **Impactos** | **Arquitectura:** centralizar reset. **Persistencia/snapshot:** migración semántica. **Replay:** perfil legado. **Atomicidad/rollback:** reset con movimiento. **Determinismo/CAS:** misma política por versión y CAS previo. **Acciones legales:** recalcular tras mover. **Privacidad:** no exponer contadores de zona oculta. |
| **Cartas afectadas** | Selector anterior; cantidad exacta `UNKNOWN` hasta inventariar textos de contadores |
| **Dependencias** | Decisión editorial de conservación y `CAP-ZONE-EXIT` |
| **Prioridad** | `P1`, bloqueada para cambio normativo; `P0` para impedir nuevas dependencias |

### 14.5 Decisiones editoriales bloqueadas

#### `BLOCK-EDITORIAL` — lecturas `AMBIGUOUS`

| Campo | Valor |
|---|---|
| **ID** | `BLOCK-EDITORIAL` |
| **CATEGORY** | Decisión normativa, no implementación |
| **SOURCE_PDF** | Ambos PDF según cada regla/fila |
| **SOURCE_PAGE** | La coordenada de cada `N-*`/fila `AMBIGUOUS` |
| **SOURCE_CARD/TOKEN** | Todas las reglas `AMBIGUOUS` de §3 y todas las filas `Estado=AMBIGUOUS` (41 entradas al corte) |
| **SOURCE_TEXT** | El texto conservado individualmente; no existe resumen que resuelva todas las dudas |
| **NORMALIZED_RULE** | `AMBIGUOUS`; conservar lecturas y no escoger mediante código |
| **APPLIES_TO** | El alcance individual de cada regla/carta |
| **PHASE/WINDOW** | `AMBIGUOUS` cuando sea el extremo disputado; en otro caso la ventana individual |
| **ZONES** | Las individuales; `UNKNOWN` si «remover» u otro verbo no fija destino |
| **VISIBILITY** | La individual; `UNKNOWN` si no se determina audiencia |
| **COST** | El individual; `UNKNOWN` si incompleto |
| **TARGET/SELECTION** | La individual; `AMBIGUOUS` si falta elector, cardinalidad, orden o modo |
| **DURATION** | La individual; `UNKNOWN` si no indicada |
| **INTERACTIONS** | Precedencia, fases, pila, reparto de combate, multijugador, Señores y elecciones |
| **ENGINE_STATUS** | `EDITORIAL_BLOCKED` |
| **CURRENT_SUPPORT** | Algunas normalizaciones conservadoras existen, pero no son canon |
| **EXACT_GAP** | Falta aclaración oficial para cada extremo marcado; no es evidencia de defecto |
| **GENERAL_CAPABILITY_REQUIRED** | Registro de decisiones versionado; después se enlaza a la `CAP-*` general que corresponda |
| **Impactos** | **Arquitectura:** no codificar una lectura prematura. **Persistencia/snapshot:** versionar la decisión futura. **Replay:** preservar perfil anterior. **Atomicidad/rollback:** especificar punto de compromiso. **Determinismo/CAS:** fijar orden/elector y revalidar. **Acciones legales:** no ofrecer la conducta bloqueada como canónica. **Privacidad:** decidir audiencia antes de proyectar. |
| **Cartas afectadas** | Selector: `Estado=AMBIGUOUS`; reglas: todos los IDs con relación `AMBIGUOUS` en §3, incluidos los grupos remitidos a `NORMATIVE_AMBIGUITIES.md` |
| **Dependencias** | Aclaración normativa oficial por ID |
| **Prioridad** | `BLOCKED`; triaje `P0` para elecciones/zonas que puedan filtrar información |

#### `BLOCK-POINTS-CONFLICT` — presupuesto Mítico

| Campo | Valor |
|---|---|
| **ID** | `BLOCK-POINTS-CONFLICT` (`N-POINTS-01`) |
| **CATEGORY** | Construcción/decisión normativa conflictiva |
| **SOURCE_PDF** | Ambos PDF |
| **SOURCE_PAGE** | Base pp. 3 y 5; Mítica física 2 / interna 1 |
| **SOURCE_CARD/TOKEN** | Reglas de construcción; `NOT APPLICABLE` a una carta individual |
| **SOURCE_TEXT** | Base: mínimo 50/equivalencia; Mítica: 200, máximo 300–400, aproximadamente 300 y 300 |
| **NORMALIZED_RULE** | `CONFLICT`; no elegir presupuesto Mítico |
| **APPLIES_TO** | Formatos/barajas Míticas cuyo presupuesto dependa de esa cifra |
| **PHASE/WINDOW** | Construcción prepartida |
| **ZONES** | `NOT APPLICABLE` |
| **VISIBILITY** | PÚBLICA como regla de formato; listas de mazo siguen privadas según producto |
| **COST** | Suma de `CardDefinition.cost`; techo/presupuesto `AMBIGUOUS` por conflicto |
| **TARGET/SELECTION** | Selección de formato/política, no target de partida |
| **DURATION** | Toda la validación de esa baraja/formato |
| **INTERACTIONS** | Límites de copias, tamaño, emparejamiento y formatos Clásico/Mística |
| **ENGINE_STATUS** | `EDITORIAL_BLOCKED` |
| **CURRENT_SUPPORT** | Cálculo de puntos y políticas opcionales; por defecto `point_budget=None` |
| **EXACT_GAP** | Fuente ofrece cifras/funciones incompatibles sin precedencia suficiente |
| **GENERAL_CAPABILITY_REQUIRED** | Política declarativa por formato una vez exista resolución oficial |
| **Impactos** | **Arquitectura:** configuración, no constante global. **Persistencia/snapshot:** guardar policy ID/versión. **Replay:** incluir política inicial. **Atomicidad/rollback:** validar mazo completo. **Determinismo/CAS:** misma política para ambos rivales y alta versionada. **Acciones legales:** rechazar inicio, no acciones durante partida. **Privacidad:** comunicar totales/errores sin revelar lista rival. |
| **Cartas afectadas** | `NOT APPLICABLE`; afecta barajas/formato, no semántica individual |
| **Dependencias** | Aclaración oficial de cifra, naturaleza y formato |
| **Prioridad** | `BLOCKED` |

### 14.6 Criterio de cierre y control de regresión

Una ficha sólo puede cerrarse cuando (1) todas sus filas afectadas dejan de
depender del gap, (2) enumerador y ejecutor de acciones legales son equivalentes,
(3) snapshot/replay versionados reproducen las decisiones, (4) CAS y rollback
han sido probados en el punto de compromiso y (5) las proyecciones públicas no
revelan candidatos, orden ni identidad ocultos. Resolver una carta de muestra no
cierra la capacidad. Un bloqueo editorial sólo se cierra con evidencia normativa
nueva; una prueba que cristaliza una lectura no cuenta como evidencia.

## 15. Fuentes auxiliares y política de fusión

Este registro es el **documento maestro**; los detalles exhaustivos se mantienen
en auxiliares y aquí sólo se publican sus resultados y dependencias, sin copiar
sus tablas completas:

* [inventario verificable de fuentes](FANTASY_TOKENS_SOURCE_INVENTORY.csv) y
  [metadatos/hash de las fuentes](RULES_SOURCES.json);
* [matriz de tipos de Token](TOKEN_TYPES_MATRIX.md) y
  [taxonomía canónica](CANONICAL_TAXONOMY.md);
* [matriz de mecánicas universales](UNIVERSAL_MECHANICS_MATRIX.md),
  [conformidad de las 431 cartas](CARD_CORPUS_CONFORMANCE.md) y
  [auditoría estática de las reglas](audits/STATIC_RULE_COVERAGE_AUDIT_2026-09-03.md);
* [ambigüedades y conflictos](NORMATIVE_AMBIGUITIES.md).

La fusión es por referencia: el ID `N-*` enlaza regla y evidencia; la entrada
`ALPHA-*`, `BETA-*` o `MITICA-*` enlaza carta y capacidades. Ante discrepancia
se conserva el peor estado y se aplica la precedencia de §2. Ningún resumen de
este documento sustituye la fila fuente.

## 16. Denominadores auditables

| Universo | Denominador y unidad de conteo |
|---|---|
| Reglas | **39** reglas `N-*` distintas de §3; una regla cuenta una vez, aunque cite varias páginas o contratos. |
| Tokens | **431** entradas impresas: 103 Alpha + 147 Beta + 181 Mítica; una reimpresión sigue contando como entrada. |
| Cartas | **431** entradas para cobertura y **386** identidades nominales sólo para la vista deduplicada; nunca se mezclan ambas sumas. |
| Habilidades | No se inventa un total independiente: la unidad trazable es cada cláusula mecánica descompuesta dentro de las **431** filas; una carta puede tener cero, una o varias. Los patrones compartidos se agrupan sólo para planificar capacidades. |
| Taxonomías | Las dimensiones admitidas son las **6** filas de §2 de la taxonomía auxiliar (tipo, rango, dominio, subtipo, identidad y keyword); sus valores no se suman como cartas y un objeto puede pertenecer a varias dimensiones. |
| Zonas | La unidad es cada zona canónica/técnica de §10.2; no cada aparición de una zona en una carta. |
| Transiciones | La unidad es cada verbo/fila canónica de §11.1; causas, reemplazos y disparadores no crean movimientos duplicados. |

Así, los estados de reglas usan 39; la representabilidad del corpus usa 431.
Los censos de Tokens y cartas comparten filas físicas, pero responden preguntas
distintas y no deben sumarse entre sí.

## 17. Cobertura exacta de reglas

Resultado de la auditoría estática enlazada:

| Estado | Reglas | Comprobación |
|---|---:|---|
| `SUPPORTED` | 21 | |
| `PARTIAL` | 11 | |
| `MISSING` | 1 | |
| `AMBIGUOUS` | 5 | |
| `CONFLICT` | 1 | |
| **Total** | **39** | **21 + 11 + 1 + 5 + 1 = 39** |

`AMBIGUOUS` y `CONFLICT` describen autoridad normativa, no déficit técnico.
El único `CONFLICT` es `N-POINTS-01`; la única regla `MISSING` es el mulligan
decreciente (`N-PHASE-02`).

## 18. Cobertura exacta del corpus

| Medida por entrada impresa | Cartas | Comprobación |
|---|---:|---|
| Auditadas | **431** | **103 + 147 + 181 = 431** |
| Completamente representables | **247** | 2 `SUPPORTED` + 245 `PARTIAL` cuyo lenguaje es `REPRESENTABLE` |
| Parcialmente representables | **41** | lenguaje `AMBIGUA`; requieren decisión antes de afirmar representación completa |
| No representables | **143** | lenguaje `NO_REPRESENTABLE` |
| **Total de representabilidad** | **431** | **247 + 41 + 143 = 431** |

La clasificación de incorporación, que es otra partición sobre el mismo
denominador, también cierra: **2 `SUPPORTED` + 245 `PARTIAL` + 143 `MISSING` +
41 `AMBIGUOUS` + 0 `CONFLICT` = 431**. En identidades deduplicadas la
verificación separada es **2 + 212 + 132 + 40 + 0 = 386**; no se usa 386 para
calcular cobertura de entradas.

## 19. Dominio, Tokens y propiedades

El dominio separa definición e instancia, tipo funcional, rango, subtipo y
dominio de Señor. Las propiedades universales pertenecen al tipo sólo cuando
una regla general lo demuestra; Fuerza, giro, daño, controlador y zona son
estado de instancia. Una habilidad repetida no se vuelve propiedad universal.
El censo exacto de los 431 rótulos y sus propiedades permanece en los dos
auxiliares de Tokens/taxonomía enlazados en §15.

## 20. Fases, activo/pasivo, Legendaria y prioridad

La dependencia es: secuencia de fases → identidad del activo/pasivo → ventanas
de anuncio → prioridad/pases → pila → resolución. Legendaria se conserva entre
Combate y Descarte, pero sus extremos canónicos de prioridad siguen ambiguos.
Por ello una wave no debe mezclar correcciones de fase con cartas individuales.

## 21. Zonas, privacidad y transiciones

La dependencia es: zona tipada → audiencia/visibilidad → movimiento único →
reemplazo → disparador → proyección pública. Primero debe cerrarse la puerta
autoritaria de movimiento y la audiencia; después pueden añadirse búsquedas,
elecciones secretas o triggers de salida sin crear filtraciones ni rutas
divergentes.

## 22. Giro, estados y costes

Girar como coste se valida y paga antes de apilar; girar por efecto ocurre al
resolver. Pasos, Heridas, descarte, sacrificio, Fuerza y giro necesitan un
preflight común, compromiso atómico y rollback. Daño, prevención, Fuerza,
anexos y contadores se limpian o conservan mediante políticas de transición,
no mediante excepciones por carta.

## 23. Pasos y Transmutación

Los Pasos son reserva de partida y coste, mientras que los puntos de mazo son
la suma prepartida de `cost`; compartir número impreso no fusiona ambos estados.
Transmutación mueve un permanente propio al descarte y acredita su coste
impreso. Sus ventanas por tipo siguen ambiguas (`N-TRANSMUTATION-02`) y no deben
resolverse eligiendo una lectura ad hoc.

## 24. Combate, Desafío y habilidades

Combate depende de fases/prioridad, aptitud/giro y estados; después puede
generalizarse prevención y keywords. Desafío reutiliza esos fundamentos, pero
su trigger desde no-Señor sigue siendo una capacidad aparte. Las habilidades
se cuentan como cláusulas del corpus, no como 431 unidades exclusivas, y se
implementarán mediante coste, ventana, selección, fuente tipada, duración y
efecto componible.

## 25. Conflictos y comparación con el backend

El backend se compara por el recorrido completo modelo → comando → validación →
resolución → acciones legales → persistencia/replay → proyección → prueba. Que
exista un enum o handler no basta. Los vacíos técnicos son `PARTIAL`/`MISSING`;
los silencios son `AMBIGUOUS`; mandatos incompatibles son `CONFLICT`. Sólo
`N-POINTS-01` está en conflicto y continúa **`OPEN/BLOCKED`**.

## 26. Gaps y dependencias

Los gaps se agrupan por capacidades generales: fase/prioridad, zona/audiencia,
acción/coste, combate/estado y habilidad/composición. Taxonomía racial,
selecciones secretas, eventos de cambio de zona, keywords, inmunidad tipada y
composición dependen de esos fundamentos. No se acepta un resolutor por
`card_id` ni se cierra una capacidad implementando sólo una carta de muestra.

## 27. Riesgos

Orden de riesgo: (1) fuga de información oculta; (2) pago o movimiento parcial
sin rollback; (3) divergencia entre opciones y ejecutor; (4) replay/snapshot no
versionado; (5) orden no determinista; (6) cristalizar una ambigüedad editorial;
(7) publicar contenido aproximado. Cada wave debe probar CAS, atomicidad,
determinismo y audiencia antes de ampliar corpus.

## 28. Waves futuras por capacidad

| Wave | Capacidad general | Dependencias que deja listas |
|---|---|---|
| **W1** | Fases y prioridad: mulligan persistible, ventanas y protocolo de pases | Base temporal para acciones, triggers, Legendaria y Desafío. |
| **W2** | Zonas y privacidad: movimiento único, audiencia, elección secreta y last-known-information | Búsqueda, reemplazos y triggers sin fugas. |
| **W3** | Costes y acciones: preflight común, pago/rollback y paridad enumerador-ejecutor | Habilidades y secuencias compuestas seguras. |
| **W4** | Combate y estados: keywords, prevención causal, limpieza y política de contadores | Combate/Desafío ampliables y deterministas. |
| **W5** | Habilidades: fuente/inmunidad tipada, triggers, taxonomía y AST de composición | Incorporación posterior de familias completas del corpus. |

El orden maximiza reglas desbloqueadas con menor riesgo: no está ordenado por
cartas, razas ni colecciones. W2 sigue a W1 porque toda elección necesita una
ventana; W3 sigue a ambas porque no debe pagar antes de validar audiencia y
momento; W4 consume esas acciones; W5 compone todos los contratos anteriores.

## 29. Siguiente bloque recomendado (sin implementación)

El siguiente bloque recomendado es **W1 — fundamentos de fases y prioridad**,
empezando por un contrato persistible de mulligan y un protocolo explícito de
ventanas/pases que preserve las ambigüedades normativas. Es el único
`MISSING` del denominador de reglas y desbloquea más validaciones posteriores
sin tocar contenido. Esta auditoría **no lo implementa**, no cambia contratos
ejecutables y no selecciona una interpretación canónica ausente.

## 30. Estado y conclusión

La cobertura documental queda aritméticamente cerrada, pero no equivale a
finalización del producto: **Phase 2 sigue `IN PROGRESS`; Phase 2-C sigue `IN
PROGRESS`; Phase 3 sigue `PENDING`; y `N-POINTS-01` sigue `OPEN/BLOCKED`**.
No se incorpora ninguna carta, no se implementa la wave recomendada y la
versión permanece **`0.20.1`**.
