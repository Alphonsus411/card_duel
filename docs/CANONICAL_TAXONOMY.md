# Taxonomía canónica respaldada por texto normativo

Fecha de corte: 2026-09-03. Estado: **registro conservador de dimensiones y
selecciones; no amplía el canon ni el catálogo ejecutable**.

## 1. Regla de admisión

Una dimensión o valor entra aquí sólo si una regla o una carta lo utiliza de
forma mecánica: rótulo `Tipo:`, selección, búsqueda, bonificación, prohibición,
inmunidad, coste o transformación. No se acepta una clasificación por
ilustración, nombre aislado, proximidad visual, bloque temático, número de
token, introducción editorial, lista de mazo ni `card_id`.

La palabra empleada por el PDF no siempre designa una dimensión consistente.
Por ello se conserva la evidencia literal y se normaliza únicamente cuando el
texto permite separar con seguridad tipo, rango, dominio o subtipo.

## 2. Dimensiones admitidas

| Dimensión | Valores respaldados | Evidencia normativa | Clasificación del backend |
|---|---|---|---|
| **Tipo funcional** | Criatura, Equipo, Evento, Recurso Rápido, Artefacto, Señor; `Leyenda` queda sin semántica autónoma | Base pp. 2–4 enumera los cuatro primeros y Leyenda; Artefacto y Señor aparecen en `Tipo:` y Mítica físicas 3–4 define Señores. | `CardKind`: todos salvo Leyenda. **Representable**, con esa ausencia/ambigüedad. |
| **Rango** | Estándar/no legendario, Legendario, Divino | Límites de copias Base p. 8 y Mítica física 2; reglas de Legendarios/Divinos en física 3. | `CardRank`: `STANDARD`, `LEGENDARY`, `DIVINE`. **Representable.** |
| **Dominio de Señor** | Abismo, Elíseo, Magia, Reinos | Mítica físicas 3–4 dedica una regla a cada Señor. | `LordDomain`: `ABYSS`, `ELYSIUM`, `MAGIC`, `REALMS`. **Representable.** |
| **Subtipo de carta/criatura** | Primigenio/a, Pixy/Pixie, Elfo, Elfo Oscuro, Duende, Goblin, Enano, Orco, Zombi, Demonio, Aberración, Ángel, Espíritu, Ninfa, Monje y Deidad | Mítica obliga a Legendarios/Divinos a tener subtipo; cartas seleccionan expresamente estos valores mediante «tipo de criatura», «carta de», «todos los» o listas cerradas. | `CardDefinition.subtypes: frozenset[str]` y filtros. **Mecánica representable**, vocabulario no cerrado. |
| **Identidad de carta** | Una carta nombrada expresamente | Cartas dicen «carta llamada…» o nombran una carta a buscar. | `CardFilter.definition_ids`. **Representable**, pero no es taxonomía. |
| **Keyword / habilidad declarativa** | Sólo `CAN_CHALLENGE` está tipada en el enum; el modelo acepta además cadenas | El corpus imprime Vuelo, Dureza, Indestructible, Intangible, Estampida, Cavar y otras capacidades. | `keywords` y `equipment_granted_keywords`. **Representación parcial**: no son raza/clase/categoría. |
| **Edición/formato** | Alpha, Beta, Mítica; Clásico y Mística | Reglas de construcción Mítica física 2. | `set_id` y políticas de mazo. **Editorial/formatística**, no taxonomía mecánica de objetivo durante partida. |

No se encontró una dimensión normativa independiente llamada **raza**,
**familia**, **clase** o **categoría**. Las cartas usan informalmente expresiones
como «de cualquier clase», pero no definen valores, pertenencia ni un selector
de esa dimensión. Etiquetas temáticas como «fuerzas de la Luz», «facción
neutral», «terrenales», Primigenios, Chamanería Tribal o Génesis sólo son
editoriales salvo cuando una carta concreta convierte una palabra en subtipo
seleccionable; no se crean enums de raza/facción/familia a partir de ellas.

## 3. Registro de selecciones taxonómicas

Las zonas se expresan como están autorizadas por el texto: **mazo/baraja**,
**mano**, **tablero**, **Pila de Descartes** o **cualquier zona revelada por el
efecto**. «Visible al resolver» significa que el selector y su resultado deben
ser comprobables para los participantes; no autoriza enseñar el resto de una
mano o mazo (Base p. 8, regla 20).

| Selector / selección | Dimensión | Controlador o propietario | Zona | Visibilidad y observación |
|---|---|---|---|---|
| Criatura, Evento, Recurso Rápido, Equipo | Tipo | Normalmente «tu»/controlador; algunas cartas dicen objetivo | Mazo, mano, tablero o descarte según el verbo de la carta | Tipo del resultado visible; sólo se revela lo necesario. |
| Artefacto o Equipo | Tipo | Propietario de «tu mazo» o «tu Pila» | Mazo (p. ej. BETA-106, MITICA-040) o descarte (MITICA-148) | Elección/resultados visibles; mazo restante oculto y se baraja cuando se ordena. |
| Evento o Recurso Rápido | Tipo | Propietario de la zona indicada | Mazo (BETA-046, MITICA-068) o descarte (MITICA-147) | Resultado visible; descarte ya es público y el mazo no. |
| «tipo de permanente»: criatura, Evento, legendario, Equipo, etc. | Tipo/rango mezclados por la carta | Todos los permanentes que cumplan; ALPHA-100 no limita controlador en su extracto | Tablero | Selección anunciada públicamente. «Legendario» se evalúa como rango, no se convierte en tipo backend. |
| «un tipo de criatura» | Subtipo | ALPHA-095 afecta las criaturas elegidas; MITICA-012 prohíbe jugar el tipo nombrado | Tablero y/o futuras cartas jugadas, según carta | Nombre del subtipo público. Los ejemplos de MITICA-012 son Goblin, Enano, Demonio y Aberración; «etc.» no autoriza valores inventados. |
| Primigenio/a | Subtipo | Frecuentemente permanentes bajo tu control; algunas cartas buscan/afectan sin esa limitación | Principalmente tablero; MITICA-180 busca en tu mazo | Público en tablero; al buscar, se muestra el resultado y no el mazo completo. |
| Pixy/Pixie, Elfo, Duende | Subtipo | «Todas» bajo el alcance de la carta o propietario de tu mazo | Tablero (ALPHA-078/BETA-080/MITICA-155) y mazo (MITICA-003, MITICA-143) | Selección/lista pública; ortografías Pixy/Pixie se conservan como posible alias, no se fusionan normativamente. |
| Elfo Oscuro, Goblin, Orco | Subtipo | Controlador indicado por la bonificación o propietario de la baraja | Tablero (MITICA-124/125/129) y baraja de tipo Señor (MITICA-132) | Público al aplicar o revelar el resultado. |
| Zombi, Demonio | Subtipo | Propietario de la baraja | Baraja de tipo Señor (MITICA-132) | Se revela la carta elegida; el resto sigue oculto y se mezcla. |
| Ángel | Subtipo | Propietario de «tu mazo» | Mazo (MITICA-003/143/145); también elegibilidad de daño en MITICA-133 | Selector público; resultado revelado. |
| Espíritu | Subtipo | Controlador al sacrificar o al comprobar daño | Tablero (MITICA-133/137) | Público por estar en tablero. |
| Ninfa | Subtipo | Permanentes bajo el alcance de MITICA-155 | Tablero | Público. El nombre de varias cartas Ninfa, por sí solo, no prueba pertenencia; la selección mecánica sí prueba el valor. |
| Monje | Subtipo | «todos los Tokens de tipo Monje» (MITICA-167) | Tablero | Público. |
| Deidad | Subtipo impreso individual | MITICA-108 | La zona actual de esa carta | Visible cuando lo sea la carta; no se extrapola a otros nombres mitológicos. |
| Legendario / no legendario | Rango | Construcción: dueño del mazo; efectos: controlador/propietario indicado | Mazo al construir; tablero/otras zonas cuando una carta lo seleccione | Lista de mazo verificable en validación; rango visible de cartas reveladas. |
| Divino | Rango | Controlador del permanente | Tablero para inmunidad y Transmutación | Público al comprobar inmunidad/acción. |
| Señor de Abismo, Elíseo, Magia o Reinos | Tipo + dominio | Controlador del Señor; Desafío identifica participantes elegibles | Tablero | Dominio, Fuerza y transformación relevantes son públicos. |
| Carta por nombre / «carta llamada» | Identidad, **no taxonomía** | Propietario/controlador que indique el texto | Mazo, mano, tablero o descarte según carta | Sólo identidad/resultados necesarios; no convierte palabras del nombre en subtipo. |

### 3.1 Controlador, zona y ocultación

`CardFilter` sólo contesta si una definición coincide; no codifica por sí solo
quién elige, de quién es la carta, en qué zona se busca o quién puede verla.
Esos ejes pertenecen a la acción/efecto (`ZoneTarget`, objetivos y alcance de
controlador). Por tanto, dos selecciones con el mismo subtipo —«tus Elfos en
tablero» y «un Elfo de tu mazo»— no son intercambiables.

Mazo y mano permanecen ocultos salvo autorización textual. Una búsqueda por
taxonomía implica comprobar/revelar la carta elegida, no publicar toda la zona.
El tablero y la Pila son observables; las zonas técnicas `RESOLUTION`, `REVEAL`
y `VOID` del backend no aparecen como taxonomías en los PDF.

## 4. Contraste preciso con `src/card_duel_engine/domain/`

| Pieza del dominio | Qué puede expresar | Brecha frente al corpus |
|---|---|---|
| `CardKind` | Seis tipos funcionales: Criatura, Evento, Recurso Rápido, Equipo, Artefacto y Señor. | No expresa Leyenda autónoma ni dos tipos impresos simultáneos. |
| `CardRank` | Estándar, Legendario y Divino, ortogonales al tipo. | Es la normalización correcta de rangos, pero los 26 rótulos sin tipo original (`Token Legendario`/`Token Divino`) siguen incompletos en fuente. |
| `LordDomain` | Los cuatro dominios normativos. | No hay brecha de valores; la conducta del dominio vive en reglas del motor, no en el enum. |
| `CardDefinition.subtypes` | Conjunto abierto de cadenas; admite múltiples subtipos y modificaciones de texto. | No distingue especie, profesión, familia o cualquier dimensión futura; tampoco controla alias (`Pixy`/`Pixie`) ni vocabulario canónico. |
| `CardFilter` | Intersección por `kinds`, `ranks`, `subtypes` o identidades `definition_ids`. | No filtra dominio, keywords, controlador, zona, visibilidad ni coincidencia exacta de subtipo; `subtypes` usa «cualquiera coincide». |
| `keywords` | Conjunto de enums/cadenas y concesión/retiro por efectos/equipos. | El enum sólo cierra `CAN_CHALLENGE`; capacidades impresas no deben degradarse a subtipos para poder filtrarlas. |
| `CardDefinition` | Coste, Fuerza, permanencia, Transmutación, habilidades, efectos, rango, tipo, subtipos y dominio. | No guarda la grafía taxonómica original ni evidencia/procedencia; `permanent=True` y `transmutable=True` por defecto son decisiones técnicas, no universales del PDF. |

## 5. Resultado por categoría de brecha

### 5.1 Taxonomía mecánica representable

- tipos funcionales enumerados por `CardKind`;
- rango mediante `CardRank`;
- los cuatro dominios de Señor mediante `LordDomain`;
- subtipos normativos mediante `subtypes` y selección básica mediante
  `CardFilter`;
- identidad exacta mediante `definition_ids` (sin llamarla taxonomía).

### 5.2 Taxonomía ausente o sólo parcialmente representada

- `Leyenda` como posible tipo distinto de rango: significado fuente
  `UNKNOWN`;
- carta Criatura/Señor simultánea: `CardKind` sólo admite un valor efectivo;
- filtros por `LordDomain`, keyword, controlador, zona y visibilidad;
- registro cerrado/alias/procedencia de subtipos;
- tipo original de los 25 `Token Legendario` y el `Token Divino` que no lo
  imprimen: **dato ausente en fuente**, no rellenable desde el nombre.

### 5.3 Taxonomía meramente editorial o no demostrada

- raza, familia, clase y categoría como dimensiones independientes;
- Luz, neutral, terrenal, tribal, temático, facción y agrupaciones de mazos;
- pertenencia deducida de ilustración, nombre, bloque, numeración, edición,
  párrafo promocional o `card_id`.

Estas etiquetas pueden conservarse como metadatos editoriales en el futuro,
pero no deben afectar objetivos, construcción o resolución sin una fuente
normativa adicional.

## 6. Reglas de implementación derivadas (no nuevas reglas de juego)

1. Modelar `kind`, `rank`, `lord_domain` y `subtypes` por separado.
2. No introducir `Race`, `Class`, `Family` o `Category` sólo para acomodar
   títulos o arte.
3. Toda selección debe transportar por separado filtro, controlador/propietario,
   zona y política de revelado.
4. Una keyword repetida sigue siendo habilidad impresa, no subtipo.
5. Ante un rótulo compuesto, conservar la literalidad y marcar pérdida de
   representación; no escoger una categoría por intuición.
6. Ante `Token Legendario` o `Token Divino` sin tipo original, usar `UNKNOWN`
   documental y bloquear cualquier migración que pretenda inferirlo.

La identidad mecánica completa de cada tipo está en
[`TOKEN_TYPES_MATRIX.md`](TOKEN_TYPES_MATRIX.md); las reglas normalizadas y la
precedencia Base–Mítica permanecen en
[`FANTASY_TOKENS_BACKEND_GAP_AUDIT.md`](FANTASY_TOKENS_BACKEND_GAP_AUDIT.md).
