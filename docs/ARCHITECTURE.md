# Arquitectura inicial

## Capas

- `domain`: entidades y enumeraciones sin dependencias externas.
- `rules`: configuración versionada de las reglas universales.
- `engine`: comandos, validación, movimientos y máquina de fases.
- `controllers`: contrato común para humano, máquina, red y AGIX.
- `simulation`: utilidades headless para partidas reproducibles.
- `content`: futuro punto de entrada para colecciones; inicialmente vacío.

## Flujo de una acción

1. Un controlador recibe una observación privada y las acciones legales.
2. Devuelve un comando.
3. El motor valida jugador, prioridad, fase, costes, zona y objetivos.
4. El motor modifica el estado exclusivamente mediante operaciones centrales.
5. Se registran eventos públicos y privados.
6. Se comprueban invariantes y condiciones de finalización.

## Extensibilidad

Las colecciones futuras se cargarán mediante manifiestos versionados. El motor
no importará módulos de una colección concreta. Las mecánicas nuevas se
registrarán a través de catálogos de efectos y palabras clave.

El nombre visible del juego y de sus recursos se resolverá fuera del dominio,
permitiendo el cambio de identidad sin reescribir el motor.

## Capas continuas 0.4

La Fuerza efectiva se calcula sin mutar el valor impreso: Fuerza base, cambio
persistente de la instancia, efectos continuos de permanentes, modificadores
temporales y Equipos. Las palabras clave siguen una evaluación equivalente:
texto base, concesiones o retiradas continuas y concesiones de Equipos.

Los disparos simultáneos no entran silenciosamente en la pila. Se conservan en
`pending_triggers` hasta que su controlador entrega un
`OrderTriggeredAbilities`; el primer identificador indicado será el primero en
resolverse. La observación pública contiene fuente e identificador de habilidad.

## Resolución declarativa 0.5

Los objetivos de zona se representan mediante jugador y zona, nunca mediante la
lista privada de cartas. Los efectos de movimiento publican origen, destino y
cantidad, pero no las identidades de una zona oculta.

El daño repartido viaja como pares objetivo/cantidad. El motor exige objetivos
distintos, cantidades positivas y que la suma sea exactamente la magnitud
impresa. Si un permanente deja de ser legal durante la resolución, solo su
porción fracasa; el daño no se redistribuye silenciosamente.

Los disparos con objetivos se alojan en `pending_triggers` sin objetivos fijados.
Su controlador usa `ChooseTriggeredTargets` y, cuando todos están completos,
decide el orden con `OrderTriggeredAbilities`. Un disparo sin ningún conjunto
legal de objetivos fracasa automáticamente.

Las acciones ofrecidas a controladores se limitan mediante
`legal_action_enumeration_limit`. Así se evitan productos cartesianos enormes;
la validación autoritativa acepta cualquier comando legal aunque no aparezca
entre las primeras alternativas enumeradas.

## Extensibilidad de contenido 0.6

Una búsqueda no entrega al motor externo el contenido de una zona privada. La
resolución queda suspendida en `pending_search`; únicamente el controlador que
elige recibe los identificadores elegibles y responde con
`ResolveSearchChoice`. Después, la misma pieza de pila continúa por el efecto
siguiente. El evento público puede revelar las cartas o solamente su cantidad.

Copiar y transformar no reemplaza ni modifica objetos del catálogo. La instancia
guarda temporalmente otro identificador de definición y todos los cálculos
consultarán esa vista efectiva. De este modo, las colecciones siguen siendo
inmutables y versionables.

El propietario nunca cambia. Un cambio de control mueve la instancia al tapiz
del nuevo controlador y la limpieza puede devolverla al anterior. Las cadenas
de cambios temporales se restauran en orden inverso.

Una definición puede declarar varias sustituciones de movimiento. Se aplica la
primera condición válida según `priority` descendente; en empate se conserva el
orden escrito en la colección. Esta precedencia determinista forma parte del
contenido y evita decisiones implícitas de la interfaz.

## Reglas calculadas y texto efectivo 0.7

`DynamicCostDefinition` combina métricas públicas del estado con
multiplicadores, desplazamiento y límites. El resultado se convierte en un
`CompositeCost` ordinario antes de validar y pagar; la pila nunca conserva una
fórmula pendiente de recalcular. El evento de anuncio registra el valor pagado.

Las cartas que permiten elección de sustitución exponen
`SetReplacementOrder`. El controlador fija una permutación completa mientras
posee prioridad y el motor usa la primera sustitución aplicable de ese orden.
Esta preferencia previa mantiene atómicas las acciones de combate, costes y
estado, y evita introducir callbacks no serializables durante un movimiento.

Los parches de texto viven en `GameState` y se aplican después de resolver copia
o transformación. `_definition` devuelve una vista derivada que puede cambiar
palabras clave, subtipos, habilidades y Transmutación; el objeto registrado en
`CardCatalog` permanece intacto. Los parches temporales expiran en limpieza y
todos desaparecen cuando la instancia abandona el tapiz.

## Transacciones y variables 0.8

`XCostDefinition` delimita los valores legales de `X` y transforma el elegido en
un componente de `CompositeCost`. El comando conserva la elección y la pieza de
pila almacena el número ya pagado. Cada efecto puede sumar un múltiplo de ese
valor a su magnitud; ninguna respuesta posterior puede recalcularlo.

`EffectPatchDefinition` selecciona por índice un efecto principal, legendario o
de habilidad. La vista efectiva puede cambiar su magnitud, modo de objetivo y
límites mínimo y máximo. Cada vista derivada vuelve a pasar por las validaciones
del dominio, por lo que un parche incompatible fracasa sin corromper la carta.

Una carta con `deferred_replacement_choice` no usa una preferencia anticipada.
Cuando `_move_card` encuentra varias sustituciones aplicables, interrumpe la
transacción antes de mutar la carta. El motor restaura una copia del estado
anterior, publica `ResolveMoveReplacement` al controlador afectado y reejecuta
el comando original con la elección fijada. Si aparece otra decisión durante la
misma acción, conserva las anteriores y repite el proceso. Así funcionan igual
la pila, el combate, los costes y las acciones basadas en estado.

## Persistencia y contenido externo 0.9

El codec de persistencia no importa nombres de módulos indicados por un archivo.
Solo reconstruye enumeraciones, modelos, comandos y `RuleSet` incluidos en un
registro interno. Conserva también el orden de los diccionarios porque puede
afectar al orden de jugadores y a la enumeración determinista de acciones.

Una instantánea contiene configuración, catálogo, estado completo y los dos
contadores de identidad del motor. El sobre incorpora una huella SHA-256 y la
restauración termina ejecutando todas las invariantes. La huella detecta
corrupción; no sustituye una firma criptográfica de origen.

`command_history`, `setup_mulligans` e `initial_decks` permiten construir un
registro más pequeño que una instantánea. La reproducción crea la partida con
la misma semilla, repite la preparación y entrega los comandos por el contrato
normal del motor. Si la huella final diverge, la reproducción se rechaza.
Mutaciones administrativas directas del estado no forman parte del registro.

Los manifiestos de colección reutilizan el mismo codec autorizado para cada
`CardDefinition`. Exigen esquema, identidad, revisión, motor mínimo y
pertenencia coherente de todas las cartas. Los conflictos se detectan antes de
registrar la primera definición, evitando catálogos parcialmente modificados.

## Endurecimiento 0.10

El cálculo de costes dinámicos, costes `X` y parches de texto reside ahora en
`rules/resolvers.py`. Son funciones puras: reciben definiciones y estado, y
devuelven nuevos valores sin conocer prioridad, pila, eventos ni almacenamiento.
`GameEngine` conserva adaptadores mínimos para traducir errores al contrato de
comandos. Esta es la primera partición del antiguo coordinador monolítico.

Los formatos persistentes usan esquema 2. `migrations.py` contiene una cadena
cerrada de transformaciones y nunca intenta inferir una conversión ausente. Las
instantáneas incorporan una segunda huella solo para el estado; las
reproducciones declaran su número de comandos; los manifiestos añaden metadatos
y dependencias sin romper documentos del esquema 1.

`InMemoryMatchStore` guarda texto de instantánea, no referencias mutables. Para
varios hilos o procesos, `SQLiteMatchStore` activa WAL y actualiza con
compare-and-swap: el escritor indica `expected_version` y solo confirma si la
fila conserva ese número. Una versión obsoleta produce `VersionConflict`, por
lo que nunca sobrescribe silenciosamente el turno de otro proceso.

Las pruebas generativas utilizan semillas fijas para conservar reproducción.
Exploran fórmulas con coeficientes positivos y negativos y secuencias aleatorias
de comandos legales, comprobando invariantes, instantáneas y replay durante el
recorrido.

## Servicios y componentes 0.11

`GameEngine` conserva la transacción, la máquina de fases y la coordinación. La
implementación de combate vive en `CombatManager`; prioridad y resolución en
`StackManager`; y movimiento y sustituciones en `ZoneManager`. Los componentes
operan sobre el mismo `GameState`: no mantienen una segunda copia del estado.

`MatchService` crea partidas, entrega observaciones y acciones legales, valida
comandos mediante el motor y persiste con versión esperada. `MatchStore` alterna
memoria y SQLite; `CommandSource` permite conectar humanos, simuladores o un
futuro adaptador AGIX sin incorporar AGIX al dominio.

## R-06 — Frontera de red aprobada

Esta especificación se aprueba antes de implementar un adaptador HTTP concreto:

- **Transporte:** HTTPS 1.1 o superior con cuerpos JSON UTF-8 y una API REST
  versionada. TLS termina en infraestructura de confianza; no se admiten
  credenciales ni datos privados sobre texto claro. El adaptador limita tamaño,
  tipos y campos antes de construir objetos de aplicación.
- **Autenticación:** OAuth 2.0 Bearer con tokens JWT emitidos mediante OpenID
  Connect. El adaptador verifica firma, algoritmo permitido, `iss`, `aud`, `exp`
  y `nbf` contra configuración local antes de crear una identidad. El motor, los
  modelos de dominio y `MatchService` nunca reciben ni almacenan tokens, cookies
  o sesiones.
- **Identidad externa:** la clave estable es el par exacto (`iss`, `sub`) del
  token validado. Un nombre, correo, IP o valor `player_id` enviado por el cliente
  no es identidad y no participa en la autorización.
- **Asociación:** una tabla o política externa relaciona (`iss`, `sub`,
  `match_id`, capacidad) con un único `player_id`. La capa de aplicación resuelve
  esa asociación para observar o enviar; sus operaciones públicas no aceptan un
  `player_id` elegible por el cliente y rechazan comandos cuyo autor difiera.
- **Autorización:** `create_match` es una capacidad global; `observe` y
  `submit_command` son capacidades de jugador y partida independientes;
  `administer` es una capacidad de partida separada y no concede implícitamente
  observación privada ni juego. Denegar una capacidad no consulta ni muta la
  partida.
- **Concurrencia y errores:** toda escritura requiere `expected_version` y llega
  al CAS de `InMemoryMatchStore` o `SQLiteMatchStore`. La frontera convierte
  partida ausente, conflicto de versión y acción ilegal en códigos públicos
  estables, sin incluir excepciones internas, snapshots, acciones legales u
  observaciones privadas.

`AuthenticatedMatchApplication` materializa estos casos de uso en una capa
separada y agnóstica del transporte. Un futuro router HTTPS solo debe decodificar
JSON, autenticar, invocarla y serializar su resultado seguro; no decide reglas
del juego ni accede directamente a `GameEngine` o al almacén.

### Contrato de salida y confinamiento del motor

`MatchService.get_match()` es una operación **exclusivamente interna** de
administración y persistencia. Devuelve un `StoredMatch` con el `GameEngine`
deserializado para uso dentro del proceso; jamás es una respuesta para clientes
remotos ni puede serializarse en R-06. El acceso al motor deserializado queda
confinado a la aplicación y a las implementaciones de `MatchStore`.

Las respuestas de observación y escritura de R-06 son `PublicMatchView`,
`PublicPlayerObservation` y `PublicLegalAction`. Se construyen únicamente desde
el `MatchView` ya autorizado y su `PlayerObservation`: contienen primitivas JSON,
la mano propia, tamaños de manos rivales y zonas públicas. Nunca contienen
`GameEngine`, `GameState`, snapshots, mazos o manos rivales, ni los campos de una
acción que puedan codificar elecciones privadas. La aplicación solo publica el
discriminador de cada acción legal; el comando recibido se valida por separado
contra la identidad autenticada.


## Contratos de componentes (0.12.0)

`CombatManager`, `StackManager` y `ZoneManager` reciben un contexto estructural
tipado y específico (`CombatContext`, `StackContext` y `ZoneContext`). Los contratos
enumeran solamente las consultas y operaciones coordinadas que cada componente
necesita. No existe delegación mediante `Any`, `__getattr__` o `__setattr__`: las
llamadas al contexto son visibles y comprobables. `GameEngine` implementa esos
contratos estructuralmente y conserva la coordinación; el único objeto de estado
mutable sigue siendo `GameState`, por lo que no hay sincronización ni estado espejo.

## Contratos verificables (0.13.0)

`mypy` comprueba por separado `CombatContext`, `StackContext` y `ZoneContext`, y un
testigo de asignación estática garantiza que `GameEngine` satisface los tres. El gestor
de zonas no conoce la secuencia ni el cursor internos del replay: solicita la siguiente
elección mediante `_consume_replacement_replay_choice`, que devuelve `None` al agotarse.

## Construcción reproducible y validación (0.16.0)

El lockfile de `uv` es la fuente única para desarrollo y CI. El wheel se construye
con un `SOURCE_DATE_EPOCH` obtenido del commit y `scripts/verify_reproducible_wheel.py`
exige dos artefactos idénticos, sin alterar los contratos del motor o persistencia.
La auditoría valida además metadatos, `RECORD`, seguridad y determinismo del ZIP;
los scripts de verificación reúnen simulaciones y rondas snapshot/replay repetibles.

## Resolución y entrega (0.17.0)

`EffectManager` recibe un `EffectContext` estructural y despacha cada `EffectKind`
mediante un registro cerrado. No conserva una copia de `GameState`: `GameEngine`
sigue siendo coordinador y autoridad única. `engine/game.py` baja de 2.596 a
2.331 líneas (265 líneas, 10,2 %) sin comprimir artificialmente el código; la
normalización de objetivos, el despacho y la ejecución pasan al gestor.

El verificador ofrece `runtime` y `full`, manteniendo `full` como predeterminado.
CI usa la matriz sólo para runtime y reserva simulaciones, persistencia y wheel
reproducible con instalaciones multiversión para una ejecución en Python 3.13.

## Registro de colecciones (0.18.0)

`CollectionRegistry` coordina un único `CardCatalog` vacío por defecto. Valida primero el lote completo, ordena su grafo de dependencias topológicamente con desempate lexicográfico y solo entonces incorpora cartas y procedencia inmutable. Una excepción de validación o confianza no deja estado parcial. El contenido canónico del manifiesto v2 se identifica con SHA-256; este digest aporta integridad, no autenticidad. Las firmas y decisiones de confianza pertenecen a una capa externa mediante `CollectionTrustPolicy`; el motor no carga módulos ni ejecuta contenido de colecciones.

El formato de versión que admite el manifiesto v2 es exclusivamente
`MAJOR.MINOR.PATCH`, con exactamente tres componentes decimales enteros no
negativos (por ejemplo, `0.1.0` o `2.0.3`). Tanto `engine_min_version` como la
versión del motor de la aplicación deben usar ese formato. No se admiten
espacios, componentes ausentes o adicionales, signos, prereleases ni metadatos
de compilación de SemVer; los productores de colecciones deben omitir esos
sufijos.

## Endurecimiento transaccional (0.18.1)

La preparación de una partida materializa y valida todos los mazos antes de
registrar definiciones o sustituir el estado vigente. Cuando se inyecta un
`CollectionRegistry`, el motor solo admite las definiciones exactas que ya
pertenecen a su catálogo autoritativo; no existe una vía lateral de registro a
través de un mazo. Esta corrección no cambia ninguna mecánica del reglamento.

El almacén SQLite conserva el modelo de conexiones cortas. Para `:memory:` usa
una base compartida identificada de forma privada y una conexión de
mantenimiento, liberable mediante `close()`, porque una conexión independiente a
`:memory:` representaría otra base vacía.

## Autenticidad de colecciones (0.19.0)

El manifiesto v2 continúa siendo el documento de contenido compatible y su única
representación canónica es `dump_manifest(manifest, indent=None)`. Esos bytes se
usan tanto para `manifest_sha256` como para la firma. El digest demuestra
**integridad** (identidad de los bytes), pero cualquiera puede recalcularlo; una
firma válida aporta **autenticidad** respecto de una clave que la aplicación haya
decidido confiar.

`CollectionSignatureEnvelope` es un formato separado, versión 1, con exactamente
cinco campos de texto: versión, manifiesto canónico completo, identificador de
clave, algoritmo y firma. La firma queda fuera del manifiesto, por lo que cambiar
el sobre no cambia su digest. El lector rechaza campos extra, ausentes, de otro
tipo, versiones desconocidas y manifiestos no canónicos. El esquema v2 del
manifiesto no cambia y los manifiestos sin sobre siguen pudiendo leerse y, bajo
una política explícitamente permisiva o sin política por compatibilidad, cargarse.

La política estricta incluida admite únicamente algoritmos configurados (por
defecto `hmac-sha256`), resuelve `TrustedKey` por `key_id` mediante un objeto
inyectado y rechaza ausencia de firma, algoritmos desconocidos, claves ausentes o
revocadas y firmas inválidas. Ni el sobre ni el manifiesto pueden indicar módulos,
resolutores o código: las claves y toda decisión de confianza proceden de objetos
creados por la aplicación. El registro termina la validación de firmas,
dependencias y colisiones de todo el lote antes de tocar el catálogo o la
procedencia.
