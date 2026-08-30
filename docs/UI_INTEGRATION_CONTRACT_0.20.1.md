# Contrato conceptual de integración de UI 0.20.1

## Propósito, alcance y estado

Este documento describe, por inspección, la frontera pública existente en
`application.py` y la frontera interna de servicio en `service.py`. Además fija
los requisitos conceptuales de una **Fase 1** de integración de interfaz. No
modifica ni implementa el contrato 0.20.1, no convierte los DTO actuales en un
protocolo remoto y no autoriza un adaptador de transporte.

El diseño es deliberadamente neutral respecto del transporte. No introduce ni
selecciona HTTP, REST, FastAPI, WebSocket, JWT, infraestructura o *deployment*.
Una decisión posterior deberá definir por separado alcance, amenazas,
dependencias y criterios propios antes de habilitar cualquier transporte.

Este contrato desarrolla, sin cerrarla, la deuda **«Identidad pública de alternativas legales para un transporte futuro»** de
[`ENGINEERING_BACKLOG.md`](ENGINEERING_BACKLOG.md#identidad-pública-de-alternativas-legales-para-un-transporte-futuro)
y conserva las invariantes de **R-06 — Frontera autenticada; transporte fuera
de alcance** de [`ARCHITECTURE.md`](ARCHITECTURE.md#r-06--frontera-autenticada-transporte-fuera-de-alcance).
No cambia reglas, cartas ni mecánicas, ni decide o desbloquea los asuntos
normativos `N-POINTS-01`, `M-LORD-EVENT-01`, R-02, R-03B o R-05.

## Contrato público actual observado

### DTO de salida

Los tres DTO son dataclasses inmutables. La conversión a diccionario produce
únicamente valores simples, listas, diccionarios y enteros aptos para una
serialización exterior; que sean serializables no implica que hoy constituyan
un protocolo de red.

#### `PublicPlayerObservation`

Es la observación autorizada de **un solo jugador**. Se construye desde
`PlayerObservation`, sin inspeccionar el motor o el estado, y contiene:

- `player_id`, `active_player_id` y el nombre textual de `phase`;
- `own_hand`, `own_steps`, `own_wounds` y `own_battlefield`;
- `opponent_hand_sizes` y `opponent_battlefields`;
- `public_event_count` y `stack_size`.

`to_dict()` materializa las tuplas como listas y copia los mapas, incluidos los
tapices rivales públicos. No incluye la identidad de cartas en manos rivales.

#### `PublicLegalAction`

Contiene `option_id` y `action`. `option_id` es la referencia opaca seleccionable
y `action` es el nombre presentable del tipo del `GameCommand` legal interno. No
publica los campos del comando ni las elecciones que esos campos pudieran
codificar.

#### `PublicMatchView`

Agrupa `match_id`, `version`, una `PublicPlayerObservation` y la tupla
`legal_actions`. Se construye exclusivamente desde un `MatchView` autorizado.
`version` es la versión observada que participa en el contrato CAS; no debe
confundirse con una versión de esquema o del producto.

`to_dict()` conserva una forma explícita y estable: identificador y versión de
partida, observación pública y una lista de objetos con los campos `option_id` y
`action`.

### Casos de uso de `AuthenticatedMatchApplication`

La aplicación valida primero la identidad y el identificador de partida, aplica
la autorización correspondiente, delega reglas y persistencia al servicio,
traduce fallos internos conocidos y sólo entonces construye DTO públicos.

| Método público | Capacidad y resultado actuales |
| --- | --- |
| `create_match(identity, match_id, decks, seed=0, auto_start=True)` | Exige identidad válida y capacidad global `CREATE_MATCH`; delega la creación con mazos de `CardDefinition` y devuelve la versión inicial. Es una API en proceso, no un contrato para cargar objetos mecánicos desde un cliente remoto. |
| `view(identity, match_id)` | Resuelve mediante `OBSERVE` el `player_id` asociado a la identidad; devuelve `PublicMatchView` para ese jugador. El llamador no elige `player_id`. |
| `submit(identity, match_id, command, expected_version=...)` | Exige `SUBMIT_COMMAND`, CAS válido, un tipo cerrado de `GameCommand` y que el autor del comando coincida con el jugador asociado; devuelve la vista pública posterior. Aceptar hoy un objeto interno en proceso **no** autoriza aceptarlo desde una UI remota. |
| `submit_option(identity, match_id, option_id, expected_version=...)` | Exige `SUBMIT_COMMAND` y CAS, vuelve a enumerar la legalidad del jugador resuelto y sólo ejecuta el miembro cuyo ID opaco coincide. La UI no aporta jugador, comando ni campos internos. |
| `submit_from(identity, match_id, source, expected_version=...)` | Resuelve jugador y vista, verifica la misma versión antes de pedir a `CommandSource` una elección, valida tipo y autor y somete con CAS. Es un adaptador en proceso para fuentes de decisión, no una resolución de identificadores públicos. |
| `administrative_version(identity, match_id)` | Exige `ADMINISTER` para esa partida y devuelve sólo su versión; no concede observación ni expone el `StoredMatch`. |

`ExternalIdentity` representa el resultado estable de un autenticador de
confianza (`issuer`, `subject`, `authenticated`). La validación rechaza ausencia,
tipo incorrecto, indicador de autenticación falso o campos vacíos. La política
`IdentityAuthorization` decide capacidades globales, asociaciones de jugador y
capacidades administrativas por partida.

## Frontera interna del servicio

### `MatchService`, `MatchView` y `CommandSource`

`MatchService` coordina creación, consulta y ejecución sin ofrecer estado
mutable como salida pública. Construye un `GameEngine`, valida opcionalmente los
mazos, carga y guarda mediante `MatchStore`, obtiene observaciones y enumera
acciones legales. `validate_command()` limita la entrada al conjunto cerrado de
tipos ejecutables y exige un `player_id` textual no vacío.

`MatchView` es una estructura **interna** que reúne `match_id`, versión,
`PlayerObservation` y comandos `GameCommand` legales completos. Es el insumo de
la sanitización de `PublicMatchView`; no es un DTO para atravesar la frontera.

`CommandSource` es un puerto mínimo en proceso. Recibe una observación y la
tupla interna de comandos legales, y devuelve un comando. `submit_from()` exige
que su `player_id` corresponda al jugador resuelto y usa la versión de la vista
como CAS. Por contener comandos internos, este puerto tampoco es por sí mismo
un protocolo de UI.

### CAS obligatorio y confinamiento de `GameEngine`

Toda escritura pasa un `expected_version` válido. `MatchService.submit()` carga
la partida y compara la versión **antes** de ejecutar; si difiere, rechaza por
conflicto. Tras ejecutar, `MatchStore.save()` vuelve a recibir esa versión
esperada y realiza el compare-and-swap de persistencia. Esta segunda defensa
evita que una escritura concurrente sea sobrescrita entre carga y guardado.

`GameEngine` queda confinado al servicio, al almacén y a la composición interna:

- `view()` sólo obtiene del motor `observe(player_id)` y
  `legal_actions(player_id)` para formar un `MatchView`;
- `submit()` valida y ejecuta dentro del servicio;
- `get_match()` devuelve un `StoredMatch` con motor deserializado únicamente
  para administración/persistencia dentro del proceso;
- ni `GameEngine`, ni `GameState`, ni un `StoredMatch` pueden ser respuesta de
  aplicación o material serializable para una UI.

## Trust boundary y reparto de autoridad

La frontera se rige por estas responsabilidades no intercambiables:

1. **La identidad determina al jugador.** La infraestructura de confianza
   autentica y entrega una identidad; la política asocia exactamente esa
   identidad y partida con un jugador. Un nombre, dirección o `player_id`
   aportado por el cliente nunca determina el actor.
2. **La aplicación autoriza.** Comprueba identidad, capacidad, partida, versión
   y correspondencia del actor antes de delegar. La capacidad administrativa no
   implica jugar u observar, y cada capacidad de jugador es independiente.
3. **El servidor observa, enumera y resuelve.** Sólo componentes autoritativos
   consultan el estado, calculan la observación permitida, enumeran legalidad,
   resuelven una elección y ejecutan reglas.
4. **La UI presenta y solicita.** Sólo muestra la observación y las opciones
   públicas emitidas, y solicita la selección de una de ellas. No reconstruye
   legalidad, no fabrica comandos, no decide reglas y no accede al almacén.

## Alternativas legales públicas (Fase 1-A implementada)

`PublicLegalAction` publica `option_id` y `action`. `action` conserva el tipo
general para presentación; `option_id` distingue inequívocamente cada miembro
del conjunto legal, incluso cuando varias alternativas comparten ese tipo. El
`option_id` es un MAC opaco ligado a partida, jugador autorizado, versión CAS e
índice autoritativo. No contiene una carga decodificable ni serializa el
`GameCommand`.

No debe resolverse esa ambigüedad aceptando parámetros de `GameCommand`,
serializando comandos internos, haciendo que la UI replique la enumeración ni
exponiendo elecciones ocultas. `submit_option(identity, match_id, option_id,
expected_version=...)` vuelve a cargar la vista, exige el mismo CAS, recalcula
los `option_id` exclusivamente sobre `MatchView.legal_actions` y ejecuta exactamente el
comando coincidente. Las APIs en proceso `submit()` y `submit_from()` permanecen.

## Identidad de alternativa

La Fase 1-A incorpora una identidad **opaca, única por cada alternativa legal
emitida**. Su representación es una cadena autenticada no decodificable y el
secreto pertenece a la instancia de aplicación. Mantiene estas propiedades:

- el identificador distingue cada alternativa del conjunto, incluso si varias
  comparten el mismo tipo general;
- queda vinculado a `match_id`, al actor autorizado derivado de la identidad y
  a la versión CAS observada;
- no permite inferir el comando interno, objetivos ocultos, cartas privadas,
  contadores, orden del estado ni otra información no incluida expresamente en
  la presentación pública;
- no es transferible entre partidas, jugadores o versiones y no concede por sí
  mismo autorización;
- sólo el servidor puede resolverlo contra el conjunto legal exacto que emitió
  para ese actor, partida y versión;
- toda opción caduca cuando cambia la versión, haya sido o no elegida, y su uso
  exige siempre el CAS observado;
- un identificador inexistente, alterado, reutilizado, ajeno o caducado se
  rechaza de manera segura y sin indicar qué parte secreta no coincidió.

Resolver significa recuperar o reconstruir **en el servidor** la alternativa
interna ya autorizada y volver a someterla a las comprobaciones autoritativas
pertinentes. Nunca significa deserializar un tipo interno indicado por el
cliente. No se aceptarán `GameCommand` arbitrarios, nombres dinámicos de clase,
campos internos ni cargas que pretendan sustituir el conjunto legal emitido.

## Observación pública y confidencialidad

La respuesta para un jugador puede incluir su propia mano y recursos, el
jugador activo, fase, recuentos públicos, tamaño de pila, tamaño —no contenido—
de manos rivales y zonas públicas como los tapices que las reglas permitan
observar. Las alternativas presentadas sólo podrán incluir información que ese
jugador esté autorizado a conocer en ese momento.

Queda prohibido exponer directa o indirectamente:

- contenido de manos rivales y de cualquier zona oculta no autorizada;
- mazos o su orden, salvo el dato público que una regla permita expresamente;
- snapshots, `StoredMatch`, `GameState`, `GameEngine` o historial interno;
- comandos, excepciones, objetos, representaciones (`repr`) o tipos internos;
- elecciones privadas rivales, incluidos candidatos, objetivos u opciones
  cuya mera existencia revele información oculta.

Los tamaños, tiempos, orden, mensajes de rechazo e identificadores opacos no
deben convertirse en canales laterales que revelen esas categorías. Las pruebas
de frontera deben comprobar tanto campos presentes como ausencia de campos y
variaciones privadas.

## Catálogo mecánico y presentación pública

`CardDefinition` permanece como la verdad mecánica, inmutable y consumida por
reglas, catálogo y motor. No se redefine para satisfacer necesidades visuales,
no se convierte en carga confiable de cliente y no debe serializarse sin filtro
como catálogo de UI.

Un futuro catálogo/presentación pública será una proyección separada, segura y
serializable para el jugador. Podrá ofrecer identidad pública estable y datos
de presentación autorizados —por ejemplo, rótulos, texto visible y recursos
visuales— sin entregar estructuras ejecutables, efectos internos, información
de zonas ocultas ni objetos de dominio. La presentación nunca reemplaza a
`CardDefinition` para determinar costes, efectos o legalidad; el servidor sigue
siendo autoritativo y define explícitamente qué proyección corresponde al
contexto del jugador.

## Errores públicos seguros

`AuthenticatedMatchApplication` expone actualmente esta taxonomía estable:

| Código | Clase pública | Significado seguro |
| --- | --- | --- |
| `application_error` | `ApplicationError` | Fallo público genérico. |
| `authentication_required` | `AuthenticationRequired` | Falta identidad autenticada. |
| `invalid_identity` | `InvalidIdentity` | La identidad no satisface el contrato. |
| `access_denied` | `AccessDenied` | La identidad carece de capacidad o no corresponde al actor. |
| `resource_not_found` | `ResourceNotFound` | La partida solicitada no existe. |
| `write_conflict` | `WriteConflict` | El CAS observado ya no es vigente. |
| `invalid_expected_version` | `InvalidExpectedVersion` | El valor CAS no satisface el contrato. |
| `command_rejected` | `CommandRejected` | El motor rechazó la acción por ilegal. |
| `invalid_deck` | `InvalidDeck` | Las definiciones de mazo son inválidas o incompatibles. |
| `malformed_command` | `MalformedCommand` | El objeto no pertenece al vocabulario cerrado admitido. |
| `internal_load_failure` | `InternalLoadFailure` | La partida existe pero no pudo cargarse con seguridad. |
| `invalid_match_id` | `InvalidMatchId` | El identificador de partida no es válido. |
| `option_rejected` | `OptionRejected` | La referencia no corresponde a una alternativa pública vigente. |

La traducción actual elimina la causa interna (`from None`) y cada error sólo
conserva un mensaje público predeterminado. Todo error futuro, incluidos los de
resolución de alternativas, deberá tener código y mensaje públicos seguros,
sin propagar texto de excepciones, argumentos, trazas, objetos, comandos,
acciones legales, snapshots ni estado interno. Cuando distinguir causas revele
existencia, autorización o información privada, deberán compartir un rechazo
indistinguible y no observable más allá de lo necesario.

## Criterios verificables de aceptación de Fase 1

Fase 1 sólo podrá considerarse aceptada cuando pruebas automatizadas de contrato
y frontera demuestren simultáneamente:

1. **Vistas públicas estables:** los DTO públicos tienen esquema documentado,
   determinista y compatible; contienen sólo la observación del actor resuelto.
2. **Catálogo público:** existe una proyección segura, estable y serializable,
   separada de `CardDefinition`, suficiente para presentar los elementos que el
   jugador puede conocer.
3. **Alternativas distinguibles:** dos o más comandos legales del mismo tipo se
   presentan con identificadores opacos distintos, sin publicar sus objetos
   internos ni información privada.
4. **Resolución autoritativa:** únicamente el servidor traduce un identificador
   emitido al miembro exacto de su conjunto legal para la misma partida, actor
   y versión; la UI no puede aportar o reconstruir el comando.
5. **CAS obligatorio:** toda selección exige la versión observada, llega al CAS
   de persistencia y una opción expira ante cualquier cambio de versión.
6. **Rechazo seguro:** identificadores falsos, alterados, caducados, repetidos,
   de otra partida o de otro actor, así como entradas malformadas, se rechazan
   sin mutación y mediante errores públicos estables no reveladores.
7. **Ausencia de filtraciones privadas:** pruebas con estados que sólo difieren
   en manos, mazos o elecciones privadas rivales verifican que vistas,
   catálogo, opciones, IDs y errores no revelan esos datos.
8. **Serialización estable:** rondas de serialización de vistas, catálogo,
   opciones y errores conservan exclusivamente primitivas documentadas, sin
   `repr`, nombres internos accidentales ni objetos de dominio o motor.
9. **Pruebas de frontera:** se cubren identidad ausente/inválida, capacidades
   separadas, suplantación de jugador, acceso cruzado entre partidas, comandos
   internos arbitrarios, concurrencia entre lectura y escritura, CAS obsoleto y
   confinamiento de `GameEngine`, `GameState`, `StoredMatch` y snapshots.
10. **Neutralidad y no regresión:** las pruebas no requieren ni presuponen un
    transporte concreto y la suite 0.20.1 conserva legalidad, persistencia,
    observaciones y traducciones de error existentes.

Estos criterios son condiciones de diseño verificables, no una autorización de
implementación. Cualquier entrega futura deberá respetar la deuda registrada y
R-06, y obtener antes la decisión documental que corresponda.
