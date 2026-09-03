# Matriz de mecánicas universales

## Propósito, alcance y método

Esta es la vista transversal del reglamento y del motor. Complementa, sin
sustituir, la [línea base](RULES_BASELINE.md), la
[trazabilidad](RULES_TRACEABILITY.md), la
[auditoría Mítica](MYTHIC_RULES_AUDIT.md) y el
[inventario de tipos](TOKEN_TYPES_MATRIX.md). Se revisaron las reglas generales
de `Fantasy Tokens.pdf` (pp. físicas 3–8), la actualización general de
`Fantasy Tokens Edicion Mitica.pdf` (físicas 2–4 / internas 1–3), su corpus de
cartas (desde física 4 / interna 3) y los contratos del engine 0.20.1.

Las etiquetas de estado son:

- **NORMATIVO**: regla general confirmada por una fuente primaria.
- **CARTA**: expresión confirmada sólo en texto particular; nunca se generaliza.
- **ENGINE**: normalización o capacidad técnica, no autoridad normativa.
- **GAP**, **PARCIAL** o **BLOQUEADO**: ausente, representado incompletamente o
  pendiente de aclaración, respectivamente.

«Fuente» identifica también la procedencia: dos frases parecidas permanecen en
filas distintas si cambia carta, duración, clase de daño o ventana. Las páginas
Míticas se expresan como **física / interna**. La matriz describe el estado
actual; no promete semántica para keywords guardadas como cadenas.

## 1. Estado canónico de un Token

| Estado | Representación y derivación | Transiciones / caducidad | Fuente y estado real |
|---|---|---|---|
| Zona | `CardInstance.zone`; mazo, mano, tapiz, descarte y exilio son persistentes. Resolución, revelación y vacío son zonas técnicas. | `_move_card` mantiene listas, controlador, anexos, reemplazos y limpieza. | NORMATIVO para zonas base; ENGINE para nombres auxiliares. Implementado. |
| Girado / preparado | `exhausted=True/False`; «preparado» significa en el tapiz, criatura efectiva y no girada cuando se exige aptitud. | Atacar, bloquear, coste `exhaust_source`, efecto `TAP` o regenerar giran; `UNTAP` y Mantenimiento enderezan. | NORMATIVO base pp. 4, 6–8; implementado. |
| Heridas de jugador | `PlayerState.wounds`; no son daño marcado de criatura. | Daño al jugador añade Heridas después de prevención; curar resta hasta cero; el límite puede terminar la partida. | NORMATIVO/ENGINE; implementado. |
| Daño de permanente | `CardInstance.damage`; separado de Heridas y Fuerza. | Se acumula tras prevención y se limpia al final del turno o al regenerar/mover según la operación. | NORMATIVO con normalización ENGINE; implementado. |
| Fuerza | `base_strength` (o coste efectivo para un Señor) + `strength_modifier` + continuos + temporales + Equipo, con suelo cero. | Costes restan modificador; efectos permanentes o hasta fin de turno lo alteran; anexos y continuos se recalculan. | NORMATIVO/ENGINE; implementado. |
| Destruible | No hay bandera positiva: lo es si una destrucción o acción letal puede moverlo y no opera Indestructible/regeneración. | Puede cambiar por keywords efectivas, escudos, forma, Fuerza o zona. | Estado **derivado**, implementado. |
| Indestructible | Keyword efectiva de cadena exacta `INDESTRUCTIBLE`. | Impide `DESTROY` y la acción por daño letal/Fuerza no positiva de criaturas; no impide Transmutación, sacrificio ni el agotamiento a Fuerza 0 de un Señor. | NORMATIVO en los textos que la conceden; soporte ENGINE implementado. |
| Transformado en criatura | `transformed_as_creature`; no equivale a sustituir la definición. | `BECOME_CREATURE`; permanente o hasta fin del turno. Abandonar el tapiz limpia el estado. | NORMATIVO para Señores de Reinos; implementado de forma declarativa. |
| Definición transformada/copiada | `overridden_definition_id`; cambia definición efectiva, no instancia. | `TRANSFORM_DEFINITION`/`COPY_DEFINITION`; permanente o fin de turno; al dejar tapiz vuelve a la original. | ENGINE reutilizable; implementado. Conserva daño, contadores y anexos mientras permanece. |
| Propietario | `owner_id`, inmutable durante la partida. | Los destinos personales de descarte usan el propietario. | NORMATIVO/ENGINE; implementado. |
| Controlador | `controller_id`; determina campo, pago, selección y efectos continuos. | `CHANGE_CONTROL`; permanente o fin de turno. No altera propietario; restauración inversa de cadenas. | ENGINE derivado de control; implementado. |
| Modificadores | `strength_modifier`, `TimedModifier`, `ContinuousEffectDefinition`, parches de texto y definición efectiva. | Permanentes, recalculados continuamente o con expiración de turno según clase. | ENGINE; implementado. No se colapsan porque tienen fuentes y vidas distintas. |
| Prevención | `wound_prevention` del jugador y `damage_prevention` del permanente. | Reservas numéricas consumidas por la siguiente cantidad aplicable; remanentes expiran al final del turno. | ENGINE; implementado. No representa «todo el daño de combate hasta fin de turno». |
| Regeneración | `regeneration_shields` y bloqueo hasta el siguiente chequeo. | Un escudo evita destrucción, limpia daño y gira; un efecto puede negar regeneración. | Normalización ENGINE; implementada. |
| Anexo | `attached_to` en Equipo. | Equipar cambia el enlace; si el huésped deja el tapiz se separa. | NORMATIVO base para Equipo; implementado. |
| Uso por turno | `activated_this_turn`; Drenaje y Desafío usan serial/eventos específicos. | Se limpia o se compara con `turn_serial`. | ENGINE; implementado, pero son tres contratos distintos. |
| Keywords y texto efectivo | Definición/copia + parches + continuos + Equipo. | Concesión/retiro por fuente; parches temporales expiran y todos se limpian al abandonar tapiz. | ENGINE; representación general, resolución semántica parcial. |
| Estados derivados | criatura efectiva, Señor criatura, preparado, Fuerza actual, keyword efectiva, objetivo legal, destruible y elegibilidad de combate/Desafío. | Se calculan al consultar y se vuelven a validar al ejecutar/resolver. | ENGINE; no deben persistirse como verdad paralela. |

**Invariantes.** Propietario y controlador nunca son sinónimos; Heridas, daño
marcado y reducción de Fuerza nunca son el mismo contador; `transformed_as_creature`
y `overridden_definition_id` son transformaciones distintas; estar enderezado
no basta para atacar si no se es criatura efectiva bajo control en el tapiz.

## 2. Giro, enderezado y ventanas

| Operación | Validación previa | Cambio | Ventana y excepciones |
|---|---|---|---|
| Giro al atacar | Fase Combate propia, prioridad cerrada, pila vacía, criatura propia preparada, declaración no vacía/sin duplicados. | Todos los atacantes se giran al aceptar la declaración. | Regla general implementada. CARTA 140 dice «no se gira al atacar»: **GAP**, no existe permiso declarativo. |
| Giro al bloquear | Declaración pendiente, defensor correcto, pila vacía, bloqueador propio preparado y usado una sola vez. | Cada bloqueador usado se gira. | Fase Combate; implementado. |
| Giro como coste | Fuente propia en tapiz, habilidad permitida, prioridad, fuente enderezada; no puede sacrificarse simultáneamente. | `exhaust_source=True` se paga antes de apilar la habilidad. | Sólo en `allowed_phases` si se declara; implementado. Ejemplos distintos: Elfo Cabalista 028 (giro + 5 Pasos) y Arcángel 145 (sólo giro); no se fusionan. |
| Giro por habilidad/efecto | Objetivo legal al anunciar y al resolver. | `TAP` gira al resolverse; no es coste y puede fallar por objetivo ilegal/inmune. | La ventana es la de la carta/habilidad fuente; implementado. |
| Enderezar por regla | Permanente del jugador activo. | Mantenimiento pone `exhausted=False`. | Base p. 4/regla 6; no hay una excepción Mítica general. |
| Enderezar por efecto | Objetivo permanente legal. | `UNTAP` al resolver. | Depende de la ventana de la fuente; implementado. |
| Regenerar | Destrucción permitiendo regeneración y escudo disponible. | Consume escudo, limpia daño y gira. | Ocurre durante el intento de destrucción; no es un `TAP` independiente. |
| Desafío | Señor criatura elegible y enderezado. | **No gira automáticamente** desafiante ni desafiado. | Fase Efectos/Activa, tras cierre de prioridad; una vez por turno. |
| Ataques múltiples | El motor registra una sola declaración de combate normal por turno frente a Desafío, pero no una cuota por criatura. | No hay «ataca dos veces» ni ataque adicional declarativo. | CARTA 142 y otros textos de ataque doble: **GAP**. |

Las acciones de carta ordinaria usan Fase Efectos; Recursos Rápidos pueden
responder según su temporización; habilidades sólo en sus `allowed_phases` (un
conjunto vacío no añade restricción); combate ordinario sólo en Combate;
Drenaje y Desafío sólo en Efectos/Activa. El perfil de replay 0.19 conserva
ventanas históricas exclusivamente al reproducir, nunca para nuevos comandos.

## 3. Inventario y protocolo de costes

| Clase de coste | Validación | Pago confirmado | Observaciones |
|---|---|---|---|
| Pasos | Reserva `>= steps`. | Resta de `PlayerState.steps`. | Coste impreso al jugar o componente fijo. |
| Giro | Fuente en tapiz y enderezada. | `exhausted=True`. | Sólo habilidades; una carta en mano no puede girarse. |
| Sacrificio | Cantidad exacta, IDs únicos, permanentes en campo propio; incompatible con girar la misma fuente. | Movimiento al descarte del **propietario** con razón `SACRIFICE`. | Indestructible e inmunidad no lo evitan; reemplazos de movimiento sí pueden aplicar. |
| Fuerza | Fuerza actual de fuente `>= strength`. | Resta a `strength_modifier`; después corren acciones basadas en estado. | Sólo habilidades; a Fuerza cero un Señor va al descarte incluso si indestructible. |
| Heridas | Cantidad no negativa declarada; el motor no exige salud restante ni aplica prevención. | Suma directa a `player.wounds`. | Es pago, no `DEAL_WOUNDS`; el límite se revisa después del comando. |
| Descarte | Cantidad exacta, IDs únicos, cartas de mano propia; al jugar no puede incluir la propia carta. | Movimiento al descarte de cada propietario con razón `DISCARD`. | Distinto del descarte de ajuste de fin de turno. |
| Molienda | Mazo propio con al menos la cantidad. | Mueve las cartas superiores al descarte, razón técnica `DISCARD`. | No elige cartas y no equivale a un efecto de descarte. |
| Transmutación | Véase §4: es acción universal, no `CompositeCost`. | Mueve el permanente y luego acredita Pasos. | No debe modelarse como sacrificio. |
| Alternativo | Índice existente; se elige exactamente fijo, dinámico o X. | Se paga sólo el compuesto elegido. | No se suma al coste normal. |
| Compuesto | Todos los componentes válidos simultáneamente. | Pasos, Heridas, Fuerza, giro y movimientos se aplican como unidad. | `CompositeCost` admite los seis componentes más giro. |
| Dinámico | Se calcula al anunciar desde una métrica permitida, multiplicadores, offset, mínimo/máximo. | El resultado congelado se paga como compuesto. | Métricas: Heridas/Pasos y tamaños propios de mano, tapiz, descarte y exilio; tapiz rival; turno. |
| `X` | Entero estricto declarado, dentro de mínimo/máximo; una sola definición de X. | `base + X*multiplier` en un único componente. | `X` queda fijada en pila y también escala efectos mediante `x_multiplier`. |

### 3.1 Validar, pagar y resolver son tres momentos

1. **Anuncio/validación:** comprobar partida, fase, jugador/prioridad, fuente,
   coste elegido y `X`, todos los recursos y elecciones, objetivos e inmunidad.
   No se muta estado.
2. **Pago indivisible:** aplicar todos los componentes y sólo entonces colocar
   carta/habilidad en resolución/pila. El pago no es un efecto, no usa la pila,
   no puede prevenirse y no se devuelve porque luego un objetivo falle.
3. **Efecto posterior:** los rivales reciben prioridad; al resolver se valida
   cada objetivo de nuevo. Un objetivo ilegal hace fallar esa parte, no retrocede
   un pago válido ni las partes independientes ya resueltas.

`GameEngine.execute` toma una instantánea transaccional del estado, historial,
contadores y RNG. Cualquier excepción durante **el comando completo** restaura
todo, incluidos eventos y movimientos. Las elecciones diferidas de reemplazo
son una interrupción controlada: la acción original no deja pagos parciales y
se reproduce completa después de elegir. Persistencia externa usa CAS para que
un conflicto tampoco confirme parcialmente el comando. Estos requisitos de
rollback no convierten el fallo normal de un objetivo al resolver en error
transaccional.

## 4. Transmutación (contrato completo)

### 4.1 Acción, sujetos, zona y ventana

- **Sujeto válido:** cualquier permanente en el tapiz bajo control del jugador
  que tenga `transmutable=True` en su definición **efectiva**.
- **Exclusiones:** cartas en otra zona, permanentes contrarios, definiciones o
  parches con `transmutable=False`. CARTA 142 confirma una exclusión particular;
  no crea una prohibición por tipo.
- **Zona inicial/destino:** del tapiz al descarte del propietario, con
  `MoveReason.TRANSMUTE`. Una sustitución aplicable puede cambiar el destino.
- **Ventana:** el jugador debe poseer prioridad. En la línea base se usa en la
  Fase Activa/Efectos y las respuestas rápidas históricas se conservan según la
  regla base; el comando técnico no impone por sí mismo una fase adicional.
- **Prioridad:** la acción pone `phase_priority_complete=False`; no crea por sí
  sola un elemento de pila. Los disparos que genere sí entran en el flujo de
  pila/prioridad.

### 4.2 Valor, Pasos y destino

Los Pasos obtenidos son exactamente `CardDefinition.cost` de la definición
efectiva consultada al anunciar, no Fuerza actual, coste alternativo, dinámico,
`X`, valor pagado al jugar, bonificaciones ni contadores. El crédito se realiza
después del movimiento. Que una sustitución lleve la carta a mano, mazo, exilio
o de vuelta al tapiz no cancela los Pasos: sigue siendo una Transmutación
aceptada. `N-POINTS-01` no afecta este valor; sólo bloquea el presupuesto total
de construcción Mítico.

### 4.3 Interacciones que no deben confundirse

| Interacción | Resultado actual |
|---|---|
| Indestructible | No interviene: Transmutación no destruye. |
| Sacrificio | Es otra razón de movimiento y otro coste; no dispara `ON_TRANSMUTED`. |
| Divino/inmunidad | Mítica permite expresamente transmutar Divinos; no es selección por Evento/Recurso/habilidad. |
| Anexos | Si la carta huésped deja el tapiz, el Equipo se desanexa; si se transmuta el Equipo, desaparece su enlace al moverse. |
| Heridas del jugador | No se pagan ni previenen; sólo cambian si un disparo posterior lo ordena. |
| Daño, prevención y regeneración | No salvan de Transmutación. El estado se limpia conforme a movimiento/reemplazo; un regreso al tapiz puede conservar o limpiar daño según la sustitución declarada. |
| Propietario/controlador | Actúa el controlador y recibe los Pasos; el destino ordinario pertenece al propietario. Para `ON_TRANSMUTED` se conserva temporalmente el controlador anterior como controlador del disparo y luego se restaura el propietario fuera del campo. |
| Reemplazos | Pueden ser ordenados previamente o elegidos de forma diferida. Nunca se aplican parcialmente. |
| `ON_TRANSMUTED` | Se encola después de mover y acreditar; los objetivos automáticos se eligen y los disparos simultáneos pueden requerir orden. |
| Respuestas | No hay respuesta «entre» movimiento y crédito. Se responde a elementos que entren en pila, no a la mitad de la transacción. |

**Atomicidad.** Validación, movimiento, crédito, evento y creación de disparos
pertenecen al mismo comando. Un fallo revierte todos. Una elección diferida
revierte/suspende la tentativa completa hasta que exista una selección válida.

## 5. Combate ordinario

1. **Declaración:** sólo jugador activo en Combate, pila vacía, ventana de
   prioridad cerrada y sin combate pendiente; al menos un atacante propio,
   criatura efectiva, enderezada y sin duplicados; se elige otro jugador.
2. **Giro:** los atacantes se giran atómicamente al declarar. El permiso «ataca
   sin girarse» observado en CARTA 140 está ausente del engine.
3. **Respuesta:** prioridad pasa al defensor. Tras resolverse respuestas, éste
   declara bloqueadores propios preparados; cada uno sólo bloquea un atacante,
   varios pueden bloquear el mismo y todos los usados se giran.
4. **Daño:** tras otra ventana cerrada, un atacante no bloqueado causa Heridas
   iguales a Fuerza. Con bloqueadores, asigna secuencialmente hasta la Fuerza de
   cada uno; todos los bloqueadores supervivientes infligen simultáneamente al
   atacante la suma de su Fuerza.
5. **Sobrante:** la Fuerza restante después del último bloqueador causa Heridas
   al defensor. Es conducta general del engine; el orden declarado de
   bloqueadores importa.
6. **Prevención:** se consume primero `damage_prevention` para permanentes o
   `wound_prevention` para jugador. Son depósitos distintos.
7. **Letal:** en el chequeo posterior, criatura con Fuerza `<=0` o daño marcado
   `>=` Fuerza es destruida. Indestructible evita esa destrucción; un Señor a
   Fuerza cero se mueve por agotamiento de Señor y la ignora.
8. **Regeneración:** si está permitida y hay escudo, éste se consume, limpia
   daño y gira antes de considerar reemplazos. Daño con
   `allows_regeneration=False` bloquea el escudo para ese chequeo.

**Ataques múltiples:** una declaración admite muchas criaturas, pero el engine
no implementa «esta criatura ataca dos veces» ni un permiso general de segundo
combate. **Daño no combativo:** `DEAL_DAMAGE` daña permanentes,
`DEAL_WOUNDS` jugadores y `DEAL_HARM` reparte entre entidades; conservan
procedencia, objetivos, prevención y `allows_regeneration`, pero no usan
bloqueo ni sobrante de combate. No deben fusionarse con daño de combate.

## 6. Desafío (auditoría independiente)

| Etapa | Contrato confirmado |
|---|---|
| Declaración | Una vez por turno del activo, en Fase Efectos/Activa, pila vacía, prioridad cerrada y sin combate. Sustituye combate normal en ambos sentidos. |
| Iniciador | Señor ya transformado en criatura y enderezado. Reinos queda autorizado por dominio; Abismo, Elíseo y Magia requieren además `Keyword.CAN_CHALLENGE`. El permiso no transforma ni reclasifica como Evento. |
| Objetivo | Una criatura efectiva en el tapiz del oponente indicado. El objetivo no necesita estar enderezado. No existen bloqueadores elegidos: el objetivo ocupa internamente la única posición enfrentada. |
| Giro | No gira automáticamente a ninguno de los dos. Estar enderezado sólo es requisito del iniciador. |
| Ventana | Tras declarar, prioridad pasa al jugador desafiado; la resolución exige pila vacía y prioridad cerrada. |
| Daño | Ambos permanentes se hacen daño igual a su Fuerza actual. Se aplican prevención, letal, Indestructible y regeneración mediante los contratos comunes. |
| Sobrante | Nunca alcanza al jugador; no hay Heridas de combate por exceso. |
| Persistencia | `CombatState.is_challenge=True`; el límite se deriva del evento `CHALLENGE_DECLARED` con `turn_serial`. |

**Permisos de Señor:** Abismo, Elíseo y Magia no atacan/bloquean ordinariamente
por su condición general salvo transformación autorizada; Reinos puede hacerlo
cuando ya es criatura. `CAN_CHALLENGE` sólo autoriza iniciar Desafío en los tres
primeros dominios. CARTA 027 solicita Desafío disparado por un no-Señor:
**GAP** y no queda cubierto por `CAN_CHALLENGE`.

## 7. Keywords y patrones de habilidad repetibles

### 7.1 Keywords/capacidades nominales encontradas

| Expresión exacta o familia | Fuente confirmada | Parámetros, targets, duración, fase y zonas | Interacciones que deben conservarse | Engine 0.20.1 |
|---|---|---|---|---|
| `CAN_CHALLENGE` | Contrato técnico; BASE-003/007 y Señores auditados | Fuente Señor en tapiz; sin target propio; consulta al declarar en Efectos. | Dominio, transformación, preparado y cuota de turno. | **Implementada y tipada**; única miembro de `Keyword`. |
| Indestructible | Corpus base/Mítico y reglas derivadas | Fuente permanente; duración según fuente. | Evita destruir/letal, no sacrificio, Transmutación ni Señor a cero. | **Implementada** como cadena efectiva. |
| Inmunidad a Eventos | CARTAS 140, 143, 144 y otras del corpus | Permanente objetivo; procedencia Evento; mientras fuente exista salvo texto. | No equivale a Recurso Rápido/habilidad/descarte/daño. | **Implementación parcial** mediante `IMMUNE_EVENT`; corpus bloqueado si no está declarado. |
| Inmunidad a Recursos Rápidos | CARTAS 141, 142, 144 y otras | Procedencia `QUICK_RESOURCE`. | Separada de Eventos y habilidades. | **Parcial**, cadena `IMMUNE_QUICK`. |
| Inmunidad a habilidades | CARTAS 029, 144 y otras | Habilidad como procedencia; el perfil congela tipo efectivo. | La inmunidad Divina más estrecha distingue habilidad propia y criatura permanente. | **Parcial**, cadena `IMMUNE_ABILITIES`; no generalizar sintaxis ambigua. |
| Inmunidad Divina Mítica | Regla Mítica física 3 / interna 2 | Divino en tapiz como objetivo; Evento, Rápido o habilidad de criatura permanente. | Permite propia habilidad, Transmutación y fuentes permanentes no criatura. | **Implementada específicamente**; no se fusiona con las tres inmunidades textuales. |
| Vuelo | Corpus base/Mítico; CARTAS 140–145 | Capacidad de combate impresa; parámetros no formalizados aquí. | Debe alterar aptitud de bloqueo sin inferir Dureza. | **GAP semántico**; sólo cadena posible. |
| Dureza | Corpus; CARTAS 141–145 salvo 140 | Capacidad impresa de criatura. | No equivale a Indestructible, prevención o regeneración. | **GAP semántico**. |
| Intangible | Corpus (incluidos Espíritus inventariados) | Capacidad impresa; ventana/alcance dependen de cada texto. | No convertir en Vuelo o inmunidad. | **GAP semántico**. |
| Estampida | Corpus | Capacidad impresa de combate. | No asumir que es el sobrante normal ya implementado. | **GAP semántico**. |
| Cavar | Corpus | Capacidad nominal repetida; parámetros según carta. | No equiparar a molienda, búsqueda o Transmutación sin texto expreso. | **GAP semántico**. |
| Infectar | Corpus Zombi | Capacidad nominal particular. | Cambio persistente de Fuerza/coste requiere contrato propio. | **GAP semántico**. |
| Drenaje | Regla universal Mítica física 3 / interna 2 | Jugador activo, 1–5 Pasos, una vez/turno, Efectos; sin target ni carta fuente. | Primer Paso 0 Heridas; restantes 3 cada uno; pago/ganancia atómicos. | **Implementada**, pero no es `Keyword`. |
| No girarse al atacar | CARTA 140 y otras expresiones del corpus | Modifica giro de esa fuente al declarar ataque; duración estática. | No concede ataque extra ni evita otros giros. | **GAP**. |
| Atacar dos veces | CARTA 142 y otras | Cuota de ataque de esa criatura por turno. | No equivale a dos atacantes, Desafío o daño doble. | **GAP**. |
| No puede transmutarse | CARTA 142 y otros textos | Fuente permanente, todas las ventanas. | No evita sacrificio/destrucción. | **Implementada** con `transmutable=False`. |

### 7.2 Habilidades parametrizables que el motor sí repite

Cada fila es un contrato distinto aunque comparta resolutor.

| Habilidad | Fuente | Parámetros / objetivos / duración | Fase, zonas y coste | Interacciones y estado |
|---|---|---|---|---|
| Habilidad activada | `AbilityDefinition` de la carta efectiva | ID, secuencia de efectos, objetivos y `once_per_turn`. | Fuente propia en tapiz, prioridad, `allowed_phases`; coste fijo/dinámico/X. | Perfil de procedencia congelado; **implementada**. |
| Entrada al tapiz | `ON_ENTER_BATTLEFIELD` (p. ej. Mítica 023/025) | Efectos y targets de cada carta. | Se dispara tras entrar; sin coste. | Orden/elección de objetivos y pila; **implementada**. |
| Al transmutarse | `ON_TRANSMUTED` | Efectos propios, controlador anterior. | Tras movimiento y crédito; sin coste. | No se dispara por sacrificio/destrucción; **implementada**. |
| Efecto legendario | `legendary_effects` | Secuencia propia de la carta. | Fase Legendaria, permanente aplicable en tapiz; sin coste. | Comparte pila/targets; **implementada**. |
| Herir jugador / curar | `DEAL_WOUNDS` / `HEAL_WOUNDS` | Cantidad, jugador propio/elegido, permanente o X. | Ventana de fuente; cualquier zona sólo si la fuente ya está apilada. | Prevención sólo al herir; curación limitada a Heridas presentes; **implementada**. |
| Dañar permanente | `DEAL_DAMAGE` | Cantidad, fuente/elegido, permiso de regeneración. | Ventana de fuente; target en tapiz. | Prevención, letal, procedencia; **implementada**. |
| Repartir daño | `DEAL_HARM` | Total fijo/X y asignaciones positivas exactas a entidades. | Targets fijados al anunciar. | Cada porción resuelve sola; jugador recibe Heridas, criatura daño; **implementada**. |
| Prevenir Heridas | `PREVENT_WOUNDS` | Reserva numérica sobre jugador. | Duración real hasta consumo/fin de turno. | Sólo Heridas, no daño de criatura; **implementada**. |
| Prevenir daño | `PREVENT_DAMAGE` | Reserva numérica sobre permanente. | Hasta consumo/fin de turno. | No filtra combate/procedencia ni representa «todo»; **parcial** para CARTA 028. |
| Modificar Fuerza | `MODIFY_STRENGTH` | Delta fijo/X; fuente u objetivo. | Permanente o fin de turno. | Separado de coste de Fuerza y continuo; **implementada**. |
| Bonificación continua | `ContinuousEffectDefinition` | Delta, keywords, alcance de controlador, tipos/subtipos, exclusión y fases suprimidas. | Mientras fuente esté en tapiz. | Recalculada, no `TimedModifier`; **implementada**, taxonomía racial pendiente. |
| Girar / enderezar | `TAP` / `UNTAP` | Permanente fuente/elegido. | Al resolver en ventana de fuente. | No son el giro pagado; **implementadas**. |
| Destruir | `DESTROY` | Permanente y permiso de regeneración. | Al resolver. | Indestructible, regeneración y reemplazo; **implementada**. |
| Regenerar | `ADD_REGENERATION` | Número de escudos. | Al resolver; escudo persiste hasta uso. | No es Indestructible; **implementada**. |
| Convertirse en criatura | `BECOME_CREATURE` | Permanente fuente/elegido, permanente/fin de turno. | Al resolver. | Conserva definición y habilita contratos de Señor; **implementada**. |
| Cambiar control | `CHANGE_CONTROL` | Permanente elegido; permanente/fin de turno. | Tapiz. | No cambia propietario; **implementada**. |
| Copiar definición | `COPY_DEFINITION` | La fuente copia definición efectiva del objetivo. | Tapiz; permanente/fin de turno. | Conserva estado de instancia; **implementada**. |
| Transformar definición | `TRANSFORM_DEFINITION` | Objetivo y `transform_definition_id`. | Tapiz; permanente/fin de turno. | Distinto de convertirse criatura; **implementada**. |
| Modificar texto | `MODIFY_TEXT` | Keywords, subtipos, habilidades, Transmutación y parches de efecto. | Permanente/fin de turno; target en tapiz. | Después de copia/transformación; **implementada**. |
| Robar / ganar Pasos | `DRAW_CARDS` / `GAIN_STEPS` | Cantidad y jugador. | Ventana de fuente. | Robo puede reciclar descarte; ganar no es Drenaje/Transmutación; **implementadas**. |
| Mover cartas | `MOVE_CARDS` | Zona objetivo, cantidad, destino. | Al resolver; cima para mazo. | No es coste ni búsqueda; **implementada**. |
| Buscar y barajar | `SEARCH_ZONE` / `SHUFFLE_ZONE` | Filtro, 0..N, destino, visibilidad, zona/jugador. | Resolución puede suspenderse por elección. | Sólo jugador autorizado ve candidatos; **implementadas**. |
| Revelar hasta | `REVEAL_UNTIL` | Filtro, destino acierto/fallo, agotamiento. | Procesa cima en orden. | No equivale a búsqueda; **implementada** como capacidad general. |
| Omitir fase | `SKIP_PHASE` o continuo | Fase; próxima ocurrencia, fin de turno o mientras fuente. | Afecta entrada futura de fase. | Tres duraciones distintas; **implementada**. |

### 7.3 Expresiones de carta que siguen separadas

- CARTA 028: «girar + 5 Pasos» para prevención ilimitada **de combate hasta fin
  de turno**; sólo coste/target están soportados.
- CARTA 029: pagar 5 Fuerza para transformarse; pagar 10 Fuerza para bonificar
  tres categorías hasta fin de turno; pagar 5 Heridas para recuperar 5 Fuerza.
  Son tres habilidades, con costes, targets y resultados no intercambiables.
- CARTA 140: pagar 5 Pasos para impedir destrucción **por daño de combate**; no
  equivale a Indestructible general ni a prevención numérica.
- CARTA 141: pagar 5 Pasos para recuperar 5 Heridas de criatura **o jugador**;
  el modelo actual no unifica Heridas de jugador con daño marcado de criatura.
- CARTA 142: disparo «si fuera a ir al descarte, destruye criatura objetivo»;
  falta un trigger/reemplazo de salida y no puede degradarse a `DESTROY` suelto.
- CARTA 143: pagar 5 Pasos, buscar una de cuatro categorías y barajar; falta
  taxonomía, aunque búsqueda/barajado existan.
- CARTA 144: pagar 10 Pasos, destruir sin Transmutación y provocar descarte;
  quién elige el descarte está **BLOQUEADO** y la operación compuesta no existe.
- CARTA 145: girar para buscar Ángel y bonificación continua a Ángeles; ambas
  dependen de taxonomía confirmada y son habilidades distintas.

## 8. Deudas y criterio de cierre

No están resueltos por esta documentación: Vuelo, Dureza, Intangible,
Estampida, Cavar, Infectar, inmunidades tipadas generales, ataque sin giro,
ataque doble, prevención ilimitada filtrada por daño de combate, protección
contra destrucción por causa, trigger de salida, Desafío iniciado por no-Señor,
taxonomía racial, recuperación acotada de Fuerza y descarte forzado ambiguo.

Una futura implementación sólo podrá marcar una fila como soportada cuando
conserve **fuente, parámetros, targets, duración, fase, zonas, coste,
procedencia del daño, interacciones, persistencia, replay y rollback**. Compartir
palabras o un handler no basta para fusionar contratos.
