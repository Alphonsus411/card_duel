# Matriz canónica de tipos de Token (Base–Mítica)

Fecha de corte: 2026-09-03. Estado: **inventario documental; no modifica el
motor ni da de alta cartas**.

## 1. Alcance y método

Esta matriz recorre las **431/431 cartas/tokens** transcritas en
[`FANTASY_TOKENS_SOURCE_INVENTORY.csv`](FANTASY_TOKENS_SOURCE_INVENTORY.csv),
además de las reglas de `Fantasy Tokens.pdf` (Base) y `Fantasy Tokens Edicion
Mitica.pdf` (Mítica). Se conserva la grafía impresa, pero se agrupan únicamente
variantes inequívocas (`Token Evento`/`Token de Evento`, mayúsculas y erratas de
OCR como `Ev ento`). La localización de página y el extracto breve verificable
están en el inventario; los PDF, no esta tabla, son la autoridad.

Se aplican cuatro límites:

1. una etiqueta en `Tipo:` prueba la clasificación de **esa carta**, no una
   propiedad universal;
2. sólo las reglas generales prueban identidad y propiedades intrínsecas del
   tipo;
3. «Legendario» y «Divino» se registran como rango aunque algunas cartas los
   impriman como si fueran tipos; Mítica física 3 / interna 2 los llama Token y
   exige un subtipo procedente del tipo original;
4. no se infiere clasificación por ilustración, título, bloque visual, número,
   prosa editorial ni `card_id`.

## 2. Censo exhaustivo de rótulos impresos

| Normalización documental | Rótulos encontrados en `Tipo:` | Cantidad | Lectura canónica conservadora |
|---|---|---:|---|
| Criatura | `Token de Criatura` (incluida variante minúscula) | 185 | Tipo funcional. |
| Criatura + Legendario | `Criatura Legendaria` | 2 | Tipo Criatura + rango Legendario. |
| Criatura + Divino | `Criatura Divina/Deidad` | 1 | Tipo Criatura + rango Divino; `Deidad` es subtipo impreso de esa carta, no raza universal. |
| Criatura + Señor de Reinos | `Token de Criatura/Señor de los Reinos` | 7 | Carta con dos clasificaciones expresas; Mítica permite que Reinos se transforme en criatura. |
| Recurso Rápido | `Recurso Rápido`, `Recuso Rápido`; BETA-118 lo imprime sin el prefijo `Tipo:` | 83 | Tipo funcional; la segunda forma es errata inequívoca. BETA-118 se conserva porque el propio rótulo funcional precede a `Efectos:`. |
| Evento | `Token de Evento`, `Token Evento`, `Evento` y dos rótulos con el coste pegado | 84 | Tipo funcional; «Token» no crea otra dimensión. |
| Evento + Legendario | `Evento Legendario` | 10 | Tipo Evento + rango Legendario. |
| Equipo | `Token de Equipo` | 14 | Tipo funcional. |
| Artefacto | `Token de Artefacto`, `Token Artefacto`, `Artefacto` | 9 | Tipo funcional respaldado por cartas, aunque no lo enumera el párrafo Base de tipos. |
| Artefacto + Legendario | `Artefacto Legendario` | 5 | Tipo Artefacto + rango Legendario. |
| Legendario sin tipo original recuperable | `Token Legendario` | 25 | Sólo acredita rango. El tipo/subtipo subyacente queda `UNKNOWN`; no se reconstruye por nombre o efecto. |
| Divino sin tipo original recuperable | `Token Divino` | 1 | Sólo acredita rango. El tipo/subtipo subyacente queda `UNKNOWN`. |
| Recurso + Legendario | `Recurso Legendario` | 1 | Rótulo literal; no se equipara automáticamente a Recurso Rápido. |
| Señor de los Reinos | `Señor de los Reinos` | 3 | Tipo Señor, dominio Reinos. |
| Señor del Abismo | `Señor del Abismo` | 1 | Tipo Señor, dominio Abismo. |
| **Total** |  | **431** | Cobertura completa del corpus de cartas. |

Los Señores de Elíseo y Magia están definidos normativamente como tipos nuevos
en Mítica física 3 / interna 2, aunque ninguna de las 431 líneas `Tipo:` del
corpus use esos dos rótulos. Por ello se incluyen en la matriz mecánica siguiente
sin inventar ejemplares.

## 3. Propiedades universales frente a texto particular

`—` significa «la fuente no concede una regla universal»; no significa
imposibilidad. `Texto` significa que el dato depende de la carta concreta.

| Tipo / combinación | Identidad mecánica e intrínsecos | Zonas válidas y modo de juego | Coste y ventana | Permanencia, resolución y destino | Objetivos y estados | Transmutación | Visibilidad |
|---|---|---|---|---|---|---|---|
| **Criatura** | Permanente con Fuerza/Resistencia impresa igual al valor indicado; puede atacar y bloquear si está apta. | Mazo → mano → resolución → tablero; descarte al ser destruida. Se juega ordinariamente en Efectos. | Coste impreso en Pasos, antes de jugar; activo en Efectos. | Permanece; daño ≥ Fuerza la destruye. Atacar, bloquear o pagar giro la deja girada; se endereza normalmente en Mantenimiento. | Objetivo legal cuando un texto diga criatura/permanente; controlador y demás estados dependen del estado de partida. | Sí como permanente propio; produce su coste. Excepciones sólo por texto. | Oculta en mazo/mano; pública en resolución/tablero/descarte. |
| **Equipo** | Permanente anexable; equipar es una operación adicional. No es Criatura. | Mazo → mano → resolución → tablero; se anexa a criatura. Si ésta sale, el Equipo permanece desanexado. | Jugar: coste impreso; equipar: nuevamente ese coste salvo texto. Ventana ordinaria: Efectos del activo. | Permanece tras resolver y tras perder portador. Bonificaciones, giros y destrucción son `Texto`. | La criatura a equipar es la selección universal; otras selecciones/estados son `Texto`. | Sí como permanente propio; valor impreso, salvo prohibición particular. | Régimen general de zonas. Anexo y controlador son públicos en tablero. |
| **Evento no permanente** | Efecto de una sola resolución; no adquiere por ello rapidez. | Mazo → mano → resolución/pila → descarte. | Coste impreso; activo en Efectos, salvo texto específico. | Resuelve LIFO y va al descarte. | Todo objetivo, duración o estado es `Texto`. | No hay permanente que transmutar después de resolver. La frase Base «normalmente […] Eventos» deja ambiguo el caso de Evento permanente. | Oculto en mazo/mano; público al anunciarse y en descarte. |
| **Evento permanente** | Conserva tipo Evento; la permanencia sólo existe cuando la carta lo declara. | Como Evento al jugar; tras resolver queda en tablero. | Misma ventana/coste de Evento; ser permanente no lo vuelve rápido. | Permanece hasta que un movimiento o texto lo retire. | `Texto`; girado, indestructible, contadores y habilidades no son universales de Evento. | La Base incluye normalmente Eventos ya en juego; fase exacta por tipo queda `AMBIGUOUS`. | Régimen general; tablero público. |
| **Recurso Rápido** | No permanente ordinario con ventana ampliada. | Mazo → mano → resolución/pila → descarte. | Coste impreso; cualquier fase o momento, sujeto a respuesta/prioridad. | Resuelve LIFO y normalmente va a descarte según las cartas; la regla no declara un destino distinto universal. | Objetivo, duración y efectos son `Texto`. | No: ordinariamente nunca queda como permanente; una excepción necesitaría texto. | Oculto en mazo/mano; público desde el anuncio. |
| **Artefacto** | Tipo impreso por cartas, pero sin definición universal Base/Mítica. Las cartas que dicen «permanente» sólo lo prueban individualmente. | `UNKNOWN` universal; los ejemplares documentados suelen entrar al tablero por texto. | Coste impreso; ventana general `UNKNOWN` (el PDF a veces lo agrupa con Equipo, pero no dicta equivalencia completa). | `Texto`; no se universalizan indestructible, giro ni habilidades. | `Texto`. | `UNKNOWN`; no se hereda automáticamente la regla de Equipo. | Sólo régimen general de zona; modo de entrada no definido universalmente. |
| **Legendario** (rango) | Rango transversal, no identidad funcional suficiente. Máximo cuatro copias. Tiene efecto/fase legendaria; Mítica exige subtipo original. | Depende del tipo original. | Coste impreso; la ventana de jugar depende del tipo. Los efectos legendarios ocurren después de Combate y antes de Descarte. | Depende del tipo; Legendario no significa permanente ni indestructible. | Puede recibir Eventos/Recursos/Habilidades salvo inmunidad textual o Divino. | Depende del tipo/permanencia; no hay prohibición universal. | Depende de zona, no del rango. |
| **Divino** (rango) | Rango transversal. Mítica sustituye la inmunidad Base: inmune a Eventos, Recursos Rápidos y habilidades de criaturas permanentes. Requiere subtipo original. | Depende del tipo original. | Coste y ventana por tipo. | No equivale a indestructible salvo que el texto de carta también lo diga. | La inmunidad anterior sí es universal; otros estados son `Texto`. | Expresamente permitido por Mítica. | Depende de zona. |
| **Señor: Abismo / Elíseo / Magia** | Permanente, Fuerza inicial = coste; no ataca ni bloquea ordinariamente, puede ser atacado; a Fuerza 0 va al descarte. Dominio es una dimensión aparte. | Se juega como permanente; regla Mítica no precisa completamente su tránsito por pila. | Coste impreso. Habilidades y Drenaje sólo quedan respaldados en Fase Activa (backend conserva lectura Efectos). | Permanece; sus capacidades consumen/modifican Fuerza según texto. | Objetivo de ataque/Desafío; estados adicionales son `Texto`. | Vigente, pero fase/destino exactos para Señor son `AMBIGUOUS`. | Régimen general; tablero público. |
| **Señor: Reinos** | Señor terrenal que puede transformarse en Criatura para atacar, bloquear y usar habilidades. No se presume transformación gratuita. | Permanente; cuando el efecto lo transforma adquiere modo de Criatura en el alcance declarado. | Coste impreso; ventana exacta de transformación es `Texto`/`AMBIGUOUS`. | Permanece; a Fuerza 0 rige la regla de Señor salvo modificación expresa. | Elegible para Desafío y, transformado, combate normal. | Vigente; extremos de fase siguen `AMBIGUOUS`. | Régimen general; transformación pública en tablero. |
| **Leyenda** | La Base la enumera entre tipos/subtipos, pero no ofrece contrato autónomo que permita distinguirla con seguridad de Legendario. | `UNKNOWN`. | `UNKNOWN`. | `UNKNOWN`. | `UNKNOWN`. | `UNKNOWN`. | Régimen general. |

### 3.1 Lo que **no** se ha universalizado

Vuelo, Dureza, Indestructible, Intangible, Estampida, Cavar, inmunidades no
divinas, «no se gira al atacar», entrar girado, atacar dos veces, producir
fichas, costes alternativos, contadores, anexarse, impedir fases y
transformaciones son habilidades o efectos impresos. Que se repitan no los
convierte en propiedades del tipo, rango, dominio o subtipo.

Asimismo, destinos como «remueve esta carta a la Pila», costes de Heridas,
sacrificios o cartas del mazo, y objetivos como jugador, criatura, permanente,
mano o baraja proceden de cartas concretas. La matriz sólo atribuye al tipo lo
que una regla general respalda.

## 4. Correspondencia con el dominio actual

| Concepto fuente | Representación actual | Estado |
|---|---|---|
| Criatura, Evento, Recurso Rápido, Equipo, Artefacto, Señor | `CardKind` contiene `CREATURE`, `EVENT`, `QUICK_RESOURCE`, `EQUIPMENT`, `ARTIFACT`, `LORD`. | **Mecánica representable.** |
| Legendario, Divino, ordinario | `CardRank.LEGENDARY`, `DIVINE`, `STANDARD`. | **Mecánica representable**, aunque «Token Legendario/Divino» sin tipo original conserva una pérdida de información fuente. |
| Abismo, Elíseo, Magia, Reinos | `LordDomain` contiene los cuatro dominios y `CardDefinition.lord_domain`. | **Mecánica representable.** |
| Leyenda como clasificación autónoma | No existe miembro separado. | **Taxonomía ausente/ambigua**; no debe añadirse sin aclarar su relación con rango. |
| Combinación Criatura/Señor de Reinos | `kind` es singular; transformación puede cambiar el perfil efectivo, pero no expresa dos tipos impresos simultáneos. | **Representación parcial.** |
| Contratos intrínsecos | `CardDefinition` dispone de Fuerza, permanencia, transmutabilidad, efectos, habilidades, costes y dominio. | **Representable**, pero muchos defaults son técnicos y no evidencia normativa. |

Véase la separación completa de dimensiones, selectores y brechas en
[`CANONICAL_TAXONOMY.md`](CANONICAL_TAXONOMY.md).
