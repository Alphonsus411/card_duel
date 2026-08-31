# Contrato implementado de integración de UI 0.20.1

## Propósito, alcance y estado

Este documento fija el contrato de integración de UI **implementado y validado**
en 0.20.1 por `application.py`, `public_catalog.py` y la frontera interna de
`service.py`. La Fase 1 está cerrada: ya no es una propuesta pendiente. Los DTO
y casos de uso descritos aquí son la superficie estable en proceso sobre la que
podrá construirse un transporte, pero no constituyen por sí mismos un protocolo
remoto ni autorizan uno.

El diseño es deliberadamente neutral respecto del transporte. No introduce ni
selecciona HTTP, REST, FastAPI, WebSocket, JWT, infraestructura o *deployment*.
Una decisión posterior deberá definir por separado alcance, amenazas,
dependencias y criterios propios antes de habilitar cualquier transporte.

Este contrato cierra para 0.20.1 la deuda **«Identidad pública de alternativas legales para un transporte futuro»** de
[`ENGINEERING_BACKLOG.md`](ENGINEERING_BACKLOG.md#identidad-pública-de-alternativas-legales-para-un-transporte-futuro)
y conserva las invariantes de **R-06 — Frontera autenticada; transporte fuera
de alcance** de [`ARCHITECTURE.md`](ARCHITECTURE.md#r-06--frontera-autenticada-transporte-fuera-de-alcance).
No cambia reglas, cartas ni mecánicas, ni decide o desbloquea los asuntos
normativos `N-POINTS-01`, `M-LORD-EVENT-01`, R-02, R-03B o R-05.

## Flujo público implementado

El recorrido que debe consumir una UI es, literalmente:

```text
identity
  → AuthenticatedMatchApplication
  → PublicMatchView
  → option_id + expected_version
  → submit_option()
  → PublicMatchView
```

La infraestructura autenticadora produce `identity`; la aplicación resuelve de
ella el actor autorizado. `view()` entrega un `PublicMatchView`. El cliente
elige un `option_id` de `legal_actions` y lo devuelve junto con
`expected_version=PublicMatchView.version`. `submit_option()` vuelve a cargar y
enumerar el estado autoritativo, valida el CAS, resuelve la referencia y, si la
operación tiene éxito, devuelve el **snapshot público autoritativo posterior a
la operación**, incluida su nueva versión, estado y nuevas acciones legales.
No es una predicción, un acuse ni un delta. No se necesita ni existe en este
contrato un `PublicMatchResult`: tanto lectura como escritura convergen en
`PublicMatchView`.

## Esquema público estable 0.20.1

Los nombres siguientes son el esquema estable de 0.20.1. Su orden aquí coincide
con el DTO, aunque los consumidores no deben atribuir semántica al orden de las
claves JSON.

| DTO | Nombres exactos de campos |
| --- | --- |
| `PublicMatchView` | `match_id`, `version`, `status`, `observation`, `legal_actions` |
| `PublicPlayerObservation` | `player_id`, `active_player_id`, `phase`, `own_hand`, `own_steps`, `own_wounds`, `opponent_hand_sizes`, `public_event_count`, `own_battlefield`, `opponent_battlefields`, `stack_size` |
| `PublicLegalAction` | `option_id`, `action` |
| `PublicCard` | `card_id`, `mechanical_name`, `kind`, `cost`, `rank`, `base_strength`, `set_id`, `revision`, `keywords`, `subtypes`, `token`, `name`, `rules_text`, `art` |
| `PublicCardCatalog` | `cards` |

Cualquier eliminación, cambio de nombre o cambio futuro incompatible de esos
campos requiere una modificación explícita de este contrato. Esta garantía no
introduce todavía versionado de protocolo: 0.20.1 es una versión del producto y
`PublicMatchView.version` es exclusivamente la versión CAS de la partida.

## DTO de partida

### DTO de salida

Los tres DTO de partida son dataclasses inmutables. La conversión a diccionario
produce únicamente valores simples, listas, diccionarios y enteros aptos para
una serialización exterior; que sean serializables no implica que hoy
constituyan un protocolo de red.

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

#### `PublicMatchView` y decisión terminal

Agrupa `match_id`, `version`, `status`, una `PublicPlayerObservation` y la tupla
`legal_actions`. Se construye exclusivamente desde un `MatchView` autorizado.
`version` es la versión observada que participa en el contrato CAS; no debe
confundirse con una versión de esquema o del producto.

La decisión implementada para terminalidad es publicar **un único campo exacto,
`status`**, cuyos valores del dominio son `running`, `finished` y `blocked`.
`finished` representa una partida terminada con resultado determinado;
`blocked`, un estado terminal sin ganador determinable (por ejemplo, ciertos
casos multijugador); `running`, una partida todavía operable. En estados
terminales `legal_actions` es una lista vacía. No se publican `winner_ids`,
`winner_id`, causa, snapshot ni estado interno, y la frontera nunca inventa un
ganador. Ésta es deliberadamente toda la información terminal pública 0.20.1.

`to_dict()` conserva la forma estable enumerada arriba: identificador, versión
CAS, estado, observación pública y una lista de acciones legales.

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

## Autoridad del backend y reparto de confianza

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

## Catálogo estático independiente del estado dinámico

`PublicMatchView` es el snapshot **dinámico**, por identidad y partida: cambia
con cada transición y contiene observación y opciones del actor. En cambio,
`PublicCardCatalog` es una referencia **estática**, independiente de partida,
identidad, versión, zonas, cantidades, posiciones y pertenencia a una partida.
No se incrusta uno en otro ni se exige que tengan el mismo ciclo de vida. El
cliente puede usar los `card_id` públicos para relacionar visualmente ambos,
pero el catálogo no concede visibilidad, pertenencia, legalidad ni autoridad y
la vista no transporta el catálogo.

## Catálogo público de cartas

La Fase 1-B incorpora una proyección pública, determinista y serializable que
combina la definición mecánica con metadatos editoriales. Su alcance termina en
el modelo y en sus validaciones: no aporta una colección de producción, una UI,
un transporte remoto ni infraestructura de cliente.

### Presentación editorial pasiva y fuentes de autoridad

`CardDefinition` permanece como la verdad mecánica inmutable consumida por las
reglas, el catálogo mecánico y el motor. `CardPresentation` es exclusivamente
metadato editorial pasivo con cinco campos: `card_id`, `token`, `name`,
`rules_text` y `art`. Ninguno es ejecutable: ni el texto se evalúa, ni el arte o
el token codifican comportamiento, ni la presentación determina costes,
efectos, habilidades, legalidad o resultados. Modificar un dato editorial no
puede modificar la mecánica proyectada.

`CardPresentationCatalog` registra esas entradas editoriales y exige unicidad
global de `card_id` y de `token` dentro del catálogo completo. Su
`CardPresentationSnapshot` es una fotografía inmutable y desacoplada: posteriores
altas en el registro no cambian el snapshot ya obtenido. Tanto el catálogo como
el snapshot enumeran presentaciones en orden determinista ascendente por
`card_id`.

La unión entre las fuentes es **exclusivamente por igualdad de `card_id`**. El
`token`, cualquiera de los nombres y los demás campos no son claves de unión ni
pueden seleccionar una definición. Antes de construir el catálogo público,
`validate_card_presentations()` comprueba cobertura completa en ambas
direcciones: rechaza presentaciones editoriales huérfanas, sin definición
mecánica, y definiciones mecánicas sin presentación. Por tanto, cada
`card_id` mecánico tiene exactamente una presentación y cada presentación
corresponde exactamente a una definición.

### Campos publicados por `PublicCard`

Cada `PublicCard` publica exactamente los siguientes campos:

| Procedencia | Campos públicos |
| --- | --- |
| `CardDefinition` | `card_id`, `mechanical_name`, `kind`, `cost`, `rank`, `base_strength`, `set_id`, `revision`, `keywords`, `subtypes` |
| `CardPresentation` | `token`, `name`, `rules_text`, `art` |

La política de nombres es explícita: `mechanical_name` procede de
`CardDefinition.name`, mientras que `name` procede de `CardPresentation.name`.
Ambos pueden diferir legítimamente. El nombre editorial sirve para presentación
humana y nunca controla reglas, búsquedas mecánicas, unión, legalidad o
resultados; la autoridad mecánica sigue siendo `CardDefinition`.

La proyección copia sólo datos declarativos necesarios y deliberadamente no
copia efectos, habilidades, costes dinámicos ni otros *internals*. Esos datos
pueden contener estructura ejecutable, estado contextual o detalles del dominio
que permitirían duplicar o inferir reglas fuera de la frontera autoritativa. El
`cost` publicado es únicamente el coste base declarativo de la definición; no
es el resultado de aplicar modificadores ni autoriza al consumidor a calcular
un coste efectivo.

### Determinismo, serialización y aislamiento

`PublicCardCatalog` valida primero la cobertura y construye sus cartas en orden
ascendente por `card_id`, con independencia del orden de registro de cualquiera
de las fuentes. En la proyección, los `frozenset` mecánicos `keywords` y
`subtypes` se ordenan y se copian como tuplas inmutables; los valores enum de
`kind`, `rank` y, cuando corresponde, `keywords` se convierten en cadenas
estables en minúsculas. En `to_dict()`, esas tuplas se materializan como listas,
de modo que el resultado contiene sólo diccionarios, listas, cadenas, enteros y
`null`, todos JSON-safe, sin enums, `frozenset`, tuplas u objetos de dominio.

Finalmente, `PublicCardCatalog` contiene nuevas instancias de `PublicCard` con
copias de los valores públicos; no conserva referencias a `CardDefinition`,
`CardPresentation`, sus catálogos ni sus snapshots autoritativos. Sus tuplas
internas son inmutables y cada llamada a `to_dict()` crea colecciones públicas
nuevas, por lo que mutar la carga resultante no modifica el catálogo público ni
ninguna fuente.

## Errores públicos seguros

`AuthenticatedMatchApplication` expone esta taxonomía pública completa y
estable. Cada clase tiene exactamente el código y mensaje seguro indicados:

| Código | Clase pública | Mensaje público exacto |
| --- | --- | --- |
| `application_error` | `ApplicationError` | `La operación no pudo completarse` |
| `authentication_required` | `AuthenticationRequired` | `Se requiere una identidad autenticada` |
| `invalid_identity` | `InvalidIdentity` | `La identidad autenticada no es válida` |
| `access_denied` | `AccessDenied` | `La identidad no está autorizada para esta operación` |
| `resource_not_found` | `ResourceNotFound` | `El recurso solicitado no existe` |
| `write_conflict` | `WriteConflict` | `La versión de escritura ya no es vigente` |
| `invalid_expected_version` | `InvalidExpectedVersion` | `La versión esperada no es válida` |
| `command_rejected` | `CommandRejected` | `El comando fue rechazado` |
| `option_rejected` | `OptionRejected` | `La alternativa pública fue rechazada` |
| `invalid_deck` | `InvalidDeck` | `La definición de los mazos no es válida` |
| `malformed_command` | `MalformedCommand` | `El comando no tiene un formato válido` |
| `internal_load_failure` | `InternalLoadFailure` | `No se pudo cargar el recurso solicitado` |
| `invalid_match_id` | `InvalidMatchId` | `El identificador de partida no es válido` |

La traducción actual elimina la causa interna (`from None`) y cada error sólo
conserva un mensaje público predeterminado. Todo error futuro, incluidos los de
resolución de alternativas, deberá tener código y mensaje públicos seguros,
sin propagar texto de excepciones, argumentos, trazas, objetos, comandos,
acciones legales, snapshots ni estado interno. Cuando distinguir causas revele
existencia, autorización o información privada, deberán compartir un rechazo
indistinguible y no observable más allá de lo necesario.

## Reglas JSON-safe y neutralidad de transporte

Los métodos `to_dict()` producen árboles formados sólo por diccionarios con
claves de texto, listas, cadenas, enteros y `null`. Tuplas y `frozenset` se
materializan como listas; enums se proyectan a cadenas estables; no aparecen
bytes, objetos de dominio, comandos, excepciones, `repr`, snapshots ni motores.
Cada llamada crea contenedores desacoplados: mutar el resultado serializado no
modifica el DTO ni sus fuentes. `bool` no es una versión válida aunque sea
subclase de `int`; `expected_version` debe ser un `int` exacto mayor o igual que
uno.

El contrato es neutral respecto del transporte y se prueba en proceso. Ninguna
semántica depende de HTTP, REST, WebSocket, códigos HTTP, JSON Web Tokens,
FastAPI, Expo o React Native. Un adaptador futuro deberá preservar identidad,
campos, CAS, taxonomía de errores y privacidad sin convertir detalles de
transporte en reglas del juego.

## Matriz de aceptación satisfecha

Fase 1 se considera aceptada porque las pruebas automatizadas de contrato y
frontera demuestran simultáneamente:

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

Estos criterios describen el contrato ya implementado en 0.20.1. No autorizan
iniciar la Fase 2, crear un frontend, inicializar Expo, añadir contenido real ni
escoger un transporte.
