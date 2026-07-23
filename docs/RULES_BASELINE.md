# Línea base de reglas 0.10

Esta especificación deriva del reglamento base y de las actualizaciones de la
Edición Mítica. No incluye textos de cartas antiguas.

## Reglas incorporadas

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
- Un Divino no puede ser objetivo de Eventos, Recursos Rápidos ni habilidades,
  pero conserva Transmutación y sus propias habilidades.
- Los Señores poseen los dominios Abismo, Elíseo, Magia o Reinos. Si su Fuerza
  llega a cero se envían al descarte incluso si son indestructibles.
- Pagar Fuerza forma parte del coste atómico de una habilidad de Señor.
- Un Señor no criatura solo puede iniciar Desafío mientras esté transformado.
- Desafío sustituye el combate normal: enfrenta un Señor criatura con una sola
  criatura contraria, sin daño sobrante al jugador y sin girarlas automáticamente.
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

## Normalizaciones internas

- `wounds` representa Heridas acumuladas; curar reduce este contador.
- `DISCARD` representa tanto "Pila" como "Pila de Descartes".
- `EXILE` representa "fuera de juego".
- Los términos visibles podrán cambiarse en la capa de presentación.
- En Drenaje se interpreta “hasta 1 Paso” como el primer Paso gratuito y el
  máximo de cinco como cuatro Pasos adicionales a tres Heridas cada uno.
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

- La regla antigua afirmaba que un Divino era inmune incluso al descarte. Mítica
  especifica inmunidad frente a Eventos, Recursos Rápidos y habilidades, y dice
  expresamente que puede transmutarse. La versión 0.5 aplica la formulación de
  Mítica por ser posterior y más específica.

## Pendientes explícitos

- La versión 0.2 distribuye el daño entre bloqueadores en el orden declarado;
  esta normalización debe revisarse si aparece una aclaración normativa.
- Firma de colecciones distribuidas por terceros y política de confianza.
- Nuevas migraciones cuando aparezcan futuros esquemas 3 o posteriores.
- Servicio de red, autenticación y autorización sobre el almacén de partidas.
- Extracción de pila, combate y movimientos a resolutores especializados.
- Registro formal de las contradicciones entre reglamento base y Mítica.

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
