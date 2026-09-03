# Línea base de reglas 0.20

Esta especificación deriva del reglamento base y de las actualizaciones de la
Edición Mítica. No incluye textos de cartas antiguas.

La auditoría transversal de estados, costes, Transmutación, combate y
habilidades se mantiene en
[`UNIVERSAL_MECHANICS_MATRIX.md`](UNIVERSAL_MECHANICS_MATRIX.md). Esa matriz
separa en cada caso la fuente documental, la semántica confirmada y el soporte
real del motor; no convierte texto particular de carta en regla universal.

## Fuentes primarias

1. `Fantasy Tokens.pdf` es la fuente base verificable.
2. `Fantasy Tokens Edicion Mitica.pdf` (2018-06-13) es la actualización posterior
   y prevalece únicamente ante una modificación expresa.
3. `docs/RULES_SOURCES.json` fija nombre, hash SHA-256, tamaño y número de páginas;
   `docs/RULES_TRACEABILITY.md` registra página física e interna.
4. Código, pruebas y este documento son derivados, no nuevas fuentes normativas.

## Reglas universales incorporadas

- Mano inicial de seis cartas.
- Mulligan: cada repetición reduce en uno la nueva mano, hasta una carta.
- Límite de Heridas configurable; el valor predeterminado de pruebas es 50.
- Cinco Pasos en cada mantenimiento y acumulación en la Reserva.
- Orden de fases: Robo, Mantenimiento, Efectos, Combate, Legendaria, Descarte.
- El jugador que no tiene el turno permanece pasivo.
- Mano máxima de seis al terminar la Fase de Descarte.
- El descarte se recicla cuando debe robarse de un mazo vacío, salvo bloqueo.
- La Transmutación envía un permanente propio al descarte y obtiene su coste
  impreso en Pasos.
- Los Recursos Rápidos podrán disponer de ventanas de respuesta en cualquier
  fase cuando se implemente la pila completa.
- La Fase Legendaria ocurre después del Combate y antes del Descarte.
- El pago de una carta es atómico y se realiza antes de entrar en resolución.
- Las respuestas se resuelven en orden LIFO después de dos pases consecutivos.
- Atacantes y bloqueadores quedan girados; el daño igual a la Fuerza es letal.
- El daño de un atacante que supera a sus bloqueadores alcanza al defensor.
- Las habilidades activadas pagan todos sus componentes como una sola operación.
- Las habilidades y disparos se resuelven en la misma pila LIFO que las cartas.
- Los objetivos se validan al anunciarse y de nuevo al resolverse.
- La prevención se consume antes de añadir daño o Heridas.
- Un permanente indestructible ignora destrucción y daño letal.
- Los modificadores temporales, daño marcado y prevención expiran al terminar turno.
- Un Equipo permanece en el campo y se separa si desaparece la criatura equipada.
- Drenaje puede usarse una vez durante el turno activo: recupera de uno a cinco
  Pasos; el primero no causa Heridas y cada Paso adicional causa tres.
- Un efecto puede exigir un intervalo de objetivos distintos y se aplica a cada
  objetivo que siga siendo legal al resolverse.
- Los efectos continuos pueden seleccionar por controlador, tipo y subtipo.
- Un Divino no puede ser objetivo de Eventos, Recursos Rápidos ni habilidades
  de criaturas permanentes según el tipo efectivo de la fuente; conserva
  Transmutación y sus propias habilidades.
- Los Señores poseen los dominios Abismo, Elíseo, Magia o Reinos. Si su Fuerza
  llega a cero se envían al descarte incluso si son indestructibles.
- Pagar Fuerza forma parte del coste atómico de una habilidad de Señor.
- Un Señor de Reinos sólo es elegible para Desafío cuando ya está transformado
  en criatura y enderezado; el dominio no le concede una transformación gratis.
  Abismo, Elíseo y Magia requieren además la autorización declarativa
  `CAN_CHALLENGE`, que no los reclasifica como Eventos.
- Desafío se declara una vez por turno en Fase de Efectos (Fase Activa) y
  sustituye el combate normal en ambos sentidos: enfrenta un Señor criatura con
  una sola criatura contraria, sin daño sobrante ni giro automático.
- Los disparos simultáneos esperan a que su controlador indique el orden exacto.
- Una zona puede ser objetivo sin mostrar sus cartas; mover desde mazo usa su parte superior.
- Una cantidad de daño puede repartirse entre jugadores y criaturas. Cada parte
  se resuelve independientemente y no cambia si otro objetivo deja de ser legal.
- Los disparos automáticos eligen objetivos antes de que su controlador ordene la pila.
- Una sustitución puede cambiar el descarte de un permanente por mano, mazo,
  exilio o regreso al campo con cambios de Fuerza y estado.
- La regeneración se consume antes de una sustitución: evita una destrucción,
  elimina el daño marcado y gira el permanente.
- Un efecto puede declarar que no permite regeneración.
- Las fases pueden omitirse una vez, hasta el final del turno o mientras exista
  un efecto continuo que las suprima.
- Buscar en una zona oculta suspende la resolución hasta que el jugador indicado
  complete una selección válida; solo ese jugador ve los candidatos.
- Una búsqueda puede filtrar por tipo, rango, subtipo o identidad, revelar o no
  el resultado y barajar explícitamente al terminar.
- Barajar usa el estado reproducible de la partida y no revela identidades.
- Una carta puede ofrecer costes alternativos; se elige exactamente uno y todos
  sus componentes se validan antes de modificar el estado.
- Moler como coste mueve cartas de la parte superior del mazo propio al descarte.
- Si varias sustituciones son aplicables, vence la de mayor prioridad declarada;
  un empate conserva el orden de la definición.
- Cambiar el control no cambia el propietario. Si es temporal, se restaura al
  final del turno y las cadenas se deshacen en orden inverso.
- Copiar o transformar cambia la definición efectiva de una instancia, no la
  definición inmutable del catálogo. El daño, los contadores y anexos permanecen.
- Un coste dinámico se calcula al anunciar la acción y después se valida y paga
  como un coste compuesto indivisible.
- Las métricas admitidas son Heridas, Pasos, tamaños de zonas propias,
  permanentes rivales y número de turno; cada fórmula puede limitar el resultado.
- El controlador de una carta que lo permita puede ordenar todas sus
  sustituciones mientras posee prioridad. La primera aplicable es la elegida.
- Un parche de texto puede conceder o retirar palabras clave, subtipos,
  habilidades o Transmutación. No altera la definición impresa.
- Los parches temporales expiran al final del turno; cualquier parche desaparece
  cuando la carta deja el tapiz.
- Un coste `X` exige declarar un entero dentro del intervalo de la definición.
  Su coste completo se valida antes de modificar el estado.
- El valor de `X` queda fijado al anunciar una carta o habilidad y viaja con ella
  en la pila.
- Un efecto puede sumar un múltiplo de `X` a su magnitud; el daño repartido debe
  coincidir exactamente con el total calculado.
- Un parche de efecto puede cambiar magnitud, modo de objetivo y límites de
  objetivos de un efecto principal, legendario o de habilidad.
- Si una carta exige elección diferida y varias sustituciones son aplicables, su
  controlador elige antes de que ocurra el movimiento.
- La acción interrumpida no produce pagos, daño, eventos ni movimientos
  parciales; se reproduce completa después de cada elección.

## Reglas de formato

- Clásico y Mística se representan mediante `DeckConstructionPolicy` optativas;
  una partida sin política mantiene el contrato histórico de `RuleSet`.
- La legalidad de colección se inyecta antes de crear la partida y no incorpora
  cartas al catálogo distribuido.
- `N-POINTS-01` impide fijar un presupuesto: las fuentes mencionan 200, 300,
  300–400 y aproximadamente 300 puntos sin una única cifra autoritativa.

## Normalizaciones del motor

- `wounds` representa Heridas acumuladas; curar reduce este contador.
- `DISCARD` representa tanto "Pila" como "Pila de Descartes".
- `EXILE` representa "fuera de juego".
- Los términos visibles podrán cambiarse en la capa de presentación.
- En Drenaje se interpreta “hasta 1 Paso” como el primer Paso gratuito y el
  máximo de cinco como cuatro Pasos adicionales a tres Heridas cada uno.
- En partidas actuales Drenaje sólo se acepta en Fase de Efectos (Fase Activa).
  La semántica 0.19 fuera de esa fase existe únicamente durante la reproducción
  de fixtures históricos y nunca habilita comandos nuevos.
- Se exige que el Señor que inicia Desafío esté enderezado, por herencia de las
  condiciones generales para declarar combate.
- “Regenerar criaturas” aparece en las reglas generales, pero Mítica no define
  un procedimiento universal. La versión 0.5 lo normaliza como un escudo
  consumible que elimina daño y gira; los retornos o pérdidas de Fuerza se
  modelan mediante sustituciones separadas.
- Una sustitución hacia el mazo coloca la carta en la parte superior. Barajar
  requiere un efecto posterior explícito para conservar la reproducción exacta.
- Las búsquedas filtradas se revelan por defecto para que el filtro sea
  verificable; una carta futura puede declarar una selección privada.
- La transformación completa conserva el estado de la instancia. Si abandona el
  campo, recupera inmediatamente su definición original.
- El coste impreso sigue siendo el valor de Transmutación aunque la carta tenga
  un coste dinámico para jugarse.
- Las preferencias de sustitución son públicas y persistentes mientras la carta
  permanezca en el tapiz. Si no existe una preferencia válida, rige la prioridad
  declarada por la colección.
- Los parches se aplican después de copia o transformación y en el orden en que
  se resolvieron.
- Los valores de `X` ofrecidos a un controlador están acotados por el límite de
  enumeración, pero la validación autoritativa acepta cualquier valor del
  intervalo aunque no aparezca entre las primeras propuestas.
- Una carta debe elegir entre orden previo y elección diferida de sustituciones;
  ambos modelos no pueden coexistir en la misma definición.
- Una instantánea válida restaura exactamente reglas, catálogo, zonas, pila,
  elecciones pendientes, historial y próximos identificadores.
- Una reproducción válida comienza con la misma semilla, orden, mazos y
  mulligans, y debe producir la misma huella final.
- Solo los comandos aceptados por el motor forman parte del historial. Una
  operación rechazada no modifica la reproducción.
- Una colección externa debe declarar esquema, identidad, revisión y versión
  mínima del motor; todas sus cartas deben usar esa identidad de colección.
- La carga de una colección es atómica frente a identificadores duplicados o ya
  registrados.
- Los documentos del esquema 1 se migran explícitamente al esquema 2 antes de
  reconstruir objetos del dominio.
- Una ruta de migración desconocida se rechaza; el motor no completa campos
  futuros mediante suposiciones.
- Guardar una partida exige una versión esperada. Solo una actualización
  concurrente puede confirmar cada versión del estado.
- Un conflicto de versión no modifica el estado persistido.

## Precedencia normativa

- `Fantasy Tokens.pdf` es la fuente base. `Fantasy Tokens Edicion Mitica.pdf`
  (2018-06-13) prevalece solo donde modifica expresamente la base; una adición no
  es por sí sola contradicción. Las contradicciones y ambigüedades quedan
  bloqueadas. Este documento, el código y las pruebas son derivados, no prueba
  normativa.
- La regla antigua afirmaba que un Divino era inmune incluso al descarte. Mítica
  (física 3 / interna 2) especifica inmunidad frente a Eventos, Recursos Rápidos
  y habilidades, y permite expresamente la Transmutación. La versión 0.5 aplica
  esa formulación por ser una modificación posterior expresa.
- La frase sobre habilidades de Señor «a modo de Eventos» (Mítica, física 3 /
  interna 2) solo respalda su temporización en Fase Activa; no respalda su
  reclasificación universal como Eventos. La cuestión sigue bloqueada.
- La auditoría y sus categorías A–E están en `MYTHIC_RULES_AUDIT.md`.

## Reglas bloqueadas

No se infieren reglas para `N-POINTS-01`, la posible reclasificación universal de
habilidades de Señor, el reparto ambiguo entre bloqueadores ni las condiciones
terminales con tres o más participantes. Los esquemas persistentes siguen siendo
v1/v2; no existe ni se anticipa un esquema v3.

## Contenido de cartas

El catálogo de producción continúa vacío. Las cartas concretas del PDF no son
reglas universales ni se transcriben al paquete; solo existen definiciones
sintéticas bajo `tests/fixtures.py`. Un futuro corpus pertenece a R-03B.4 y deberá
cargarse externamente mediante manifiestos, no como tarea inmediata.

## Pendientes explícitos

La política de confianza y firma de colecciones de R-04 y la frontera autenticada
de aplicación de R-06 ya están entregadas. Esta última es agnóstica del
transporte: autentica y autoriza los casos de uso, pero no incluye un adaptador
HTTP ni otro servicio de red concreto. Por decisión de alcance, ningún transporte
es una entrega futura habilitada ni un pendiente implementable. Si otra decisión
lo habilitase, deberá conservar `AuthenticatedMatchApplication` como frontera
autoritativa: nunca podrá aceptar `player_id`, exponer `GameEngine` o `GameState`,
omitir `expected_version`/CAS ni reinterpretar comandos.

- El reglamento permite enfrentarse a uno o más adversarios y exige que todos
  los participantes acuerden el mismo límite de Heridas (`Fantasy Tokens.pdf`,
  pp. 3 y 5). Sin embargo, solo formula concesión, derrota por Heridas y empate
  simultáneo en singular o para dos jugadores (pp. 3–4 y regla 18, pp. 7–8).
  Quedan sin definir la continuidad de una partida multijugador y la selección
  y orden de sus ganadores; no debe inferirse una condición terminal.
- La versión 0.2 distribuye el daño entre bloqueadores en el orden declarado;
  esta normalización debe revisarse si aparece una aclaración normativa.
- Nuevas migraciones cuando aparezcan futuros esquemas 3 o posteriores.
- Extracción de pila, combate y movimientos a resolutores especializados.
- La auditoría base–Mítica está completada en `MYTHIC_RULES_AUDIT.md`; los puntos
  de mazo (`N-POINTS-01`) y la posible reclasificación de habilidades de Señor
  (`M-LORD-EVENT-01`) siguen bloqueados hasta una aclaración oficial.

Nada de lo anterior debe completarse mediante suposiciones silenciosas.

## Compatibilidad 0.11

La extracción no modifica reglas. La fase Legendaria conserva posición,
disparos, pila y prioridad. Ante ambigüedades se mantiene el comportamiento
observable de 0.10.0: esta entrega cambia arquitectura, no reglamento.


## Compatibilidad 0.12.0

La extracción de contratos es exclusivamente arquitectónica. No cambia la secuencia
de fases (incluida Legendaria), la prioridad, el combate, los movimientos, las
sustituciones ni la reproducción determinista. Los snapshots, replays y manifiestos
continúan en esquema v2 y mantienen las migraciones desde v1.

## Compatibilidad 0.13.0

La verificación estática y la encapsulación del cursor de replay no alteran reglas ni
formatos. Se conservan la fase Legendaria, los documentos v2, las migraciones v1 y el
orden determinista de las sustituciones.

## Compatibilidad 0.16.0

La ampliación del tipado y la construcción reproducible no cambian reglas, fase
Legendaria, formatos v2, migraciones v1, replays ni determinismo de partidas.

## Compatibilidad 0.17.0

La extracción y los perfiles no cambian reglas observables. Se conservan fase
Legendaria, documentos v2, migraciones v1 y ambigüedades. La trazabilidad en
`RULES_TRACEABILITY.md` no añade interpretaciones normativas.

## Compatibilidad 0.18.0

La línea base de reglas, incluida la fase Legendaria, permanece sin cambios respecto de 0.17.0. El catálogo de producción continúa vacío; el registro solo añade procedencia y transacciones a la carga explícita de colecciones.

## Compatibilidad 0.18.1

Se valida que toda configuración conserve los dos participantes mínimos y la
secuencia normativa Robo, Mantenimiento, Efectos, Combate, Legendaria y
Descarte. El endurecimiento transaccional de mazos y el soporte SQLite en memoria
no añaden cartas ni interpretaciones a las reglas vigentes.

## Compatibilidad 0.18.2

Se conserva el mínimo de dos participantes porque el reglamento permite
explícitamente enfrentarse a uno o más adversarios. La versión solo registra esa
evidencia y la ausencia de una condición terminal multijugador completa: no
normaliza concesiones, eliminaciones, empates ni ganadores para tres o más.

## Compatibilidad 0.18.3

Una concesión o la llegada al límite de Heridas en una partida de tres o más
participantes bloquea la ejecución sin declarar ganadores. `BLOCKED` expresa que
falta una decisión normativa y no constituye una condición terminal nueva. Las
partidas de dos jugadores conservan exactamente sus condiciones de victoria.

## Compatibilidad 0.19.0

La autenticación de colecciones es infraestructura y no modifica ninguna regla,
carta ni resultado. El manifiesto y los documentos persistentes permanecen en
esquema v2; el sobre de firma usa su propio esquema v1 separado.


## Compatibilidad 0.20.0

La deserialización de documentos v1/v2 y la reproducción semántica son garantías
distintas. `R-COMPAT-019-REPLAY` activa sólo durante replays cuyo `RuleSet` es
0.19 la conducta histórica necesaria para los fixtures generados con el commit
documentado en `tests/artifacts/0.19.0/README.md`; después restaura el modo
normal. En partidas actuales Drenaje exige Fase de Efectos y Desafío exige Fase
Activa, uso único, exclusión de combate y elegibilidad declarada. El puente
legacy tiene vida limitada y sólo podrá retirarse mediante una decisión de
compatibilidad versionada. No se crea v3, no se añaden cartas de producción y
no cambian las condiciones terminales multijugador.
