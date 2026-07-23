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
