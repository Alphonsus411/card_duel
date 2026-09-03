# Auditoría estática transversal de cobertura de reglas

Fecha: 2026-09-03. Alcance de código: **todos** los módulos de
`src/card_duel_engine/domain/`, `engine/`, `rules/`, `persistence/` y `content/`,
más `application.py`, `service.py`, `presentation.py` y `public_catalog.py`.
Esta auditoría no cambia el motor ni incorpora contenido.

## 1. Método y criterio de cierre

La unidad auditada es cada regla `N-*` del registro normalizado
[`FANTASY_TOKENS_BACKEND_GAP_AUDIT.md`](../FANTASY_TOKENS_BACKEND_GAP_AUDIT.md).
Se siguió, en este orden, el camino completo:

1. enum y modelo declarativo;
2. comando y validación de anuncio/ventana/coste/objetivo;
3. resolutor y enumeración de acciones/opciones legales;
4. zona, duración y privacidad;
5. codec, snapshot y replay;
6. proyección de servicio/aplicación/catálogo público;
7. prueba que demuestre el contrato, no sólo que alcance un handler;
8. contenido realmente registrado en los manifests de producción.

Vocabulario cerrado:

- **`SUPPORTED`**: semántica, ventana, coste, target, duración, zona,
  privacidad, persistencia y replay están cubiertos cuando son aplicables.
- **`PARTIAL`**: existe el efecto o recorrido principal, pero falta al menos una
  restricción temporal, filtro, selección, privacidad, trigger o contrato
  persistente exigido.
- **`MISSING`**: no existe una abstracción general suficiente.
- **`AMBIGUOUS`**: la fuente no determina un extremo necesario; no se rellena
  con el comportamiento actual.
- **`CONFLICT`**: mandatos de fuente incompatibles bloquean la elección.

Una fila no asciende por compartir un `EffectKind`, una prueba aproximada o un
resolutor. `Persistencia común` significa el recorrido genérico dataclass/enum
de `persistence/codec.py`, snapshot v2 y replay v2; sólo cuenta si todos los
campos semánticos necesarios existen. `Pública común` significa observación
filtrada, opciones opacas y CAS en `service.py`/`application.py`; no convierte
en pública una elección secreta.

## 2. Matriz de trazabilidad de todas las reglas normalizadas

Abreviaturas: **E/M** enum/modelo; **C/V** comando/validación; **R** resolutor;
**L** acciones/opciones legales; **P/Rp** persistencia/replay; **Pub** proyección
pública; **T** pruebas existentes.

| Regla | Estado | E/M | C/V | R | L | P/Rp | Pub | T | Motivo decisivo |
|---|---|---|---|---|---|---|---|---|---|
| `N-PHASE-01` preparación inicial | `PARTIAL` | `GameState`, zonas | `new_match` | baraja/roba seis | — | común + mazos iniciales | vista oculta mano rival | `test_setup_and_phases.py`, `test_new_match_transaction.py` | No hay procedimiento general de mulligan ni contrato de prioridad inicial canónico. |
| `N-PHASE-02` mulligan decreciente | `MISSING` | — | — | — | — | — | — | sólo documentación | No hay comando, estado ni replay de mulligan 5→1. |
| `N-PHASE-03` orden de fases | `AMBIGUOUS` | `Phase`, `RuleSet.phase_sequence` | `AdvancePhase` | `PhaseManager` | `LegalActionEnumerator` | común | fase visible | fases/manager | El orden técnico existe; la colocación canónica exacta de Legendaria sigue indeterminada. |
| `N-PHASE-04` robo de turno | `PARTIAL` | `Phase.DRAW` | avance | `_enter_phase`, `_draw` | avance/pases | común | tamaños, mano propia | setup/fases, zonas | Semántica cubierta; fuente no fija pila, prioridad ni ventanas antes/después. |
| `N-PHASE-05` mantenimiento | `PARTIAL` | `MAINTENANCE` | avance | endereza y +5 Pasos | avance/pases | común | estado público aplicable | setup/fases | Orden respecto de disparos y efecto de omitir la fase no está determinado. |
| `N-PHASE-06` Efectos | `PARTIAL` | `EFFECTS`, tipos | `PlayCard`, `TransmutePermanent`, `DrainSteps` | engine/phases | acciones/opciones | común | opciones opacas | recursos, pila, Mítica | «Fase Activa» y respuestas a acciones directas no quedan completamente fijadas. |
| `N-PHASE-07` ajuste a seis | `PARTIAL` | `DISCARD` | `DiscardCards` | `PhaseManager`/movimiento | combinaciones exactas | común | opciones opacas | setup/fases, acciones | Privacidad técnica cubierta; respuesta/prioridad canónica durante el ajuste es ambigua. |
| `N-PHASE-08` pasivo | `PARTIAL` | rol derivado | validadores por comando | engine | enumerador | común | app autentica jugador | fases, acciones | La lista negativa se aplica, pero la fuente no formaliza prioridad universal. |
| `N-PHASE-09` LIFO | `SUPPORTED` | `StackItem`, pila | `PassPriority` | `StackManager` | pasar/responder | snapshot/replay | sólo tamaño de pila | `test_stack_and_priority.py`, persistencia | La regla aplicable es LIFO; las elecciones adicionales se auditan en sus propias filas. |
| `N-PHASE-10` enderezado | `SUPPORTED` | `exhausted`, `UNTAP` | avance/acciones de efecto | fase y efectos | común | común | tablero | setup, advanced mechanics | Mantenimiento y excepciones declarativas conservan zona, duración y replay. |
| `N-ZONE-01` reciclar descarte | `SUPPORTED` | `Zone.DECK/DISCARD` | robo | `_draw` + RNG | indirecta | semilla/estado/log | oculta orden y rival | recursos/zonas, replay | Reciclaje, barajado determinista y privacidad aplicables están cubiertos. |
| `N-ZONE-02` zonas ocultas | `SUPPORTED` | zonas/observación | autorización app | búsqueda/observación | opciones sólo elector | documentos internos completos | DTO filtra mano/mazo/candidatos | hardening, app autenticada, UI | La frontera pública no expone orden ni mano rival; snapshots/replays quedan internos. |
| `N-ZONE-03` Equipo permanece | `SUPPORTED` | `attached_to`, `EQUIPMENT` | `EquipCard` | `ZoneManager` desanexa huésped | equipar elegible | común | tablero | recursos/zonas, paridad zonas | El Equipo queda en tablero y sólo pierde el enlace. |
| `N-TOKEN-01` tipo/rango/subtipo | `PARTIAL` | `CardKind`, `CardRank`, `subtypes` | filtros | `CardFilter`/continuos | opciones filtradas | común | catálogo publica dimensiones | catálogo, taxonomía documental | La abstracción existe, pero numerosos rótulos/razas del corpus no están normalizados ni incorporados. |
| `N-TOKEN-02` Recurso Rápido | `PARTIAL` | `QUICK_RESOURCE` | `_timing_allows_play` | pila | jugar/responder | común | opción opaca | pila, recursos | Ventana amplia implementada; «cualquier momento» y prioridad exacta son ambiguos en fuente. |
| `N-TOKEN-03` texto prima | `PARTIAL` | efectos/parches declarativos | validación común | `apply_text_patch`, engine | recalculadas | común | catálogo separa texto editorial | dynamic rules | Sólo priman excepciones representables; no existe intérprete general de texto. |
| `N-COST-01` coste impreso | `SUPPORTED` | `CardDefinition.cost`, Fuerza | `PlayCard` | pago/Fuerza | opciones costeables | común | coste público | recursos, dominio | Una única magnitud declarativa gobierna pago y Fuerza base cuando aplica. |
| `N-COST-02` pago y generación | `SUPPORTED` | Pasos, costes | jugar/transmutar/drenar | pago atómico | opciones asequibles | común | Pasos propios/opciones | recursos, Mítica, rollback | Pago previo y vías de generación se validan y reproducen atómicamente. |
| `N-COST-03` equipar | `SUPPORTED` | coste/Equipo/anexo | `EquipCard` | engine | targets criatura propios | común | tablero/opción | recursos, acciones | Coste impreso, ventana Efectos, target, zona y replay quedan cubiertos. |
| `N-TRANSMUTATION-01` operación | `SUPPORTED` | `transmutable`, razón/trigger | `TransmutePermanent` | engine/zones/stack | permanentes propios | común | Pasos/tablero, opción opaca | recursos, stack, Mítica | Movimiento, crédito, propietario/controlador, trigger y atomicidad son explícitos. |
| `N-TRANSMUTATION-02` fases/tipos | `AMBIGUOUS` | filtro general | prioridad/control | engine | enumerador | común | común | recursos/zonas | «fases correspondientes» no determina una ventana por tipo; el backend permite una uniforme. |
| `N-COMBAT-01` declarar/girar | `SUPPORTED` | `CombatState`, criaturas | declarar atacantes/bloqueadores | `CombatManager` | enumerador | común | combate/tablero | combate/paridad | Aptitud, ventana, target jugador, zona y giro se revalidan. |
| `N-COMBAT-02` daño/letal/sobrante | `SUPPORTED` | daño/Fuerza/prevención | `ResolveCombat` | combat/effects/SBA | resolución estructural | común | heridas/tablero | combate, resolución | Semántica general, prevención, regeneración y replay cubiertos. |
| `N-COMBAT-03` multibloqueo/orden | `AMBIGUOUS` | asignaciones ordenadas técnicas | `DeclareBlockers` | secuencial | combinaciones | común | combate público | combate | La fuente permite varios bloqueadores pero no decide reparto/orden de daño. |
| `N-COMBAT-04` aptitud al declarar | `SUPPORTED` | `exhausted`, criatura efectiva | validación declaración | combat | sólo preparados | común | tablero/opción | combate | Se revalida en la ventana de declaración. |
| `N-COMBAT-05` 2+ jugadores | `PARTIAL` | lista de jugadores/defensor | declaración elige oponente | combat | defensores enumerados | común | vistas por jugador | simulación/combate | Preparación y combate funcionan, pero el contrato terminal 3+ no está definido. |
| `N-COMBAT-06` terminar/conceder | `AMBIGUOUS` | `MatchStatus`, ganadores | `Concede`/SBA | engine | concesión | común | estado/ganadores | condiciones finales | Dos jugadores cubiertos; continuidad/ganadores para 3+ están bloqueados por la fuente. |
| `N-LEGENDARY-01` fase/efectos | `PARTIAL` | rango/efectos/fase | avance y elecciones trigger | stack/fases | ordenar/targets/pases | común | pila resumida | combate/legendaria, stack | Resolución existe; orden simultáneo, primera prioridad y unidad de respuesta no son canónicos. |
| `N-LEGENDARY-02` indestructible/Divino | `SUPPORTED` | rango + keywords/inmunidad derivada | target validation | destroy/SBA/targeting | filtra targets | perfil de fuente + común | catálogo/tablero | Mítica, advanced mechanics, replay 0.20 | Override Mítico se distingue de Indestructible, Transmutación y fuente de efecto. |
| `N-LEGENDARY-03` copias | `SUPPORTED` | identidad/rango | política de mazo | `DeckConstructionPolicy` | N/A | definición/mazos iniciales | errores sanitizados | deck policy | Cinco estándar/cuatro legendarias se cuentan por identidad. |
| `N-LEGENDARY-04` Señores A/E/M | `SUPPORTED` | `LORD`, dominio, Fuerza | play/ability/challenge | engine/combat/SBA | opciones filtradas | común | catálogo/tablero | Mítica y lord sintético | No combate ordinario, Fuerza inicial, agotamiento y target son generales. |
| `N-LEGENDARY-05` Señor Reinos | `SUPPORTED` | dominio + `transformed_as_creature` | efecto/declaración | `BECOME_CREATURE` | recalculadas | común | estado tablero | Mítica/lord sintético | No presume transformación gratuita y conserva duración declarada. |
| `N-LEGENDARY-06` habilidad como Evento | `AMBIGUOUS` | habilidad/perfil fuente | activación | stack/effects | opciones | común | opaca | Mítica, stack | «A modo de Eventos» no fija tipo, inmunidad, ventana ni respuesta completa. |
| `N-LEGENDARY-07` Desafío | `SUPPORTED` | dominio/keyword/combat state | `DeclareChallenge`/resolver | combat | desafíos elegibles | común | combate/tablero | Mítica, combate | Cuota, ventana, sujetos, target, zona, ausencia de sobrante y replay cubiertos. |
| `N-POINTS-01` presupuesto Mítico | `CONFLICT` | política admite límites | validación sólo si se configura | `deck_points` | N/A | configuración/manifest | error | deck policy/documentación | 200, 300–400, ≈300 y 300 no permiten seleccionar un techo canónico. |
| `N-COST-04` coste = puntos | `SUPPORTED` | `cost` | política | `deck_points` | N/A | definición | coste público | deck policy | No duplica magnitudes ni inventa presupuesto. |
| `N-FORMAT-01` copias/coste cero | `SUPPORTED` | rango/coste/id | políticas classic/mythic | deck validator | N/A | contenido/manifest | error | deck policy | Límites se parametrizan por formato y se prueban. |
| `N-FORMAT-02` 40–60 | `SUPPORTED` | policy min/max cards | validación mazo | deck validator | N/A | política | error | deck policy | Ambos límites forman parte del contrato Mítico configurable. |
| `N-FORMAT-03` Clásico/Mística | `SUPPORTED` | políticas y set metadata | validación set/coste | deck validator | N/A | manifest/provenance | catálogo set | deck policy, registry | Elegibilidad de colección y restricciones quedan separadas por formato. |

## 3. Capacidades generales no equivalen a contenido incorporado

Los manifests de producción Base y Mítica registran sólo definiciones que
declaran su mecánica completa. La existencia de `SEARCH_ZONE`, inmunidad,
`DESTROY`, `PREVENT_DAMAGE`, filtros o costes compuestos no basta para publicar
una carta cuyo texto exige además otra ventana, taxonomía, selección, duración
o trigger. En particular, Mítica revisión 1 incorpora sólo nº023 y nº025 del
subconjunto auditado; nº024, nº026–029 y nº140–145 permanecen fuera.

### Caso obligatorio: `REVEAL_UNTIL` y Mítica nº026

`EffectKind.REVEAL_UNTIL`, `RevealExhaustionPolicy`, los campos de
`EffectDefinition`, el resolutor de `EffectManager` y sus round-trips ya forman
una **capacidad general existente**. Procesa la cima en orden, filtra mediante
`CardFilter`, mueve aciertos/fallos, emite revelaciones y termina con política
explícita al agotar la zona. Las pruebas de `tests/test_reveal_until.py` cubren
resolución, agotamiento, codec, snapshot y replay.

Eso **no vuelve automáticamente representable ni incorporable la carta Mítica
nº026**. Su clasificación de contenido continúa bloqueada por el alcance
editorial completo y por cualquier extremo de carta no declarado en una
definición publicada. Capacidad general y soporte de carta son afirmaciones
distintas.

## 4. Búsqueda de lógica por identidad

Se inspeccionaron rutas de resolución, validación y acciones legales con
comparaciones de `card_id`, nombre, token, texto editorial, raza/subtipo y
`rules_text`. Resultado:

| Precedente | Ruta | Clasificación |
|---|---|---|
| `CardFilter.definition_ids` compara `definition.card_id` | `domain/models.py`; consumido por targeting, búsqueda y `REVEAL_UNTIL` | **Gap arquitectónico por identidad.** Es una abstracción general parametrizada, no un `if` de una carta concreta, pero permite que la resolución dependa de identidad y debe registrarse. No se corrige aquí. |
| Conteo por `card.card_id` | `rules/deck.py` | Identidad legítima para límites de copias (`N-LEGENDARY-03`/`N-FORMAT-01`), no resolución de efectos. |
| `card_id` en `game.py`, comandos, acciones y zonas | engine | Identidad de **instancia**, pertenencia a zona, ownership o integridad referencial; no compara un ID editorial concreto. No es precedente de lógica de carta. |
| `card_id` en catálogo, registry, presentación, manifest y replay | content/presentation/persistence | Clave de definición, unión mecánica-editorial, deduplicación o reconstrucción; no decide efectos. |
| `subtypes` en `CardFilter` y continuos | dominio/engine | Filtro mecánico declarativo general. Sigue siendo `PARTIAL` para cartas cuya raza editorial no fue normalizada; no se encontró comparación ad hoc con una raza literal en resolutores. |
| nombre, token y `rules_text` | presentación/contenido/catálogo público | Sólo validación editorial y proyección. **No se hallaron** comparaciones en resolución, validación de comandos ni acciones legales. |

No se encontraron condicionales para números Míticos concretos ni comparaciones
con nombres/textos en `engine/`. El único precedente mecánico de identidad de
definición es `CardFilter.definition_ids`; queda expresamente abierto como gap,
sin modificar código en esta auditoría.

## 5. Inventario exhaustivo de módulos inspeccionados

| Área | Módulos | Contrato contrastado |
|---|---|---|
| Dominio | `domain/__init__.py`, `enums.py`, `errors.py`, `models.py` | vocabulario, invariantes, costes, filtros, efectos, cartas, estado, pila, elecciones y combate |
| Engine | `engine/__init__.py`, `actions.py`, `combat.py`, `commands.py`, `effects.py`, `game.py`, `options.py`, `phases.py`, `stack.py`, `zones.py` | comandos, validación, pago, targets, resolución, acciones/opciones, fases, prioridad, movimientos, privacidad derivada e invariantes |
| Rules | `rules/__init__.py`, `config.py`, `deck.py`, `resolvers.py` | configuración de partida, construcción, costes dinámicos/X y parches |
| Persistence | `persistence/__init__.py`, `codec.py`, `migrations.py`, `replay.py`, `snapshot.py` | tipos serializados, migraciones, checksums, digest, replay y compatibilidad heredada |
| Content | `content/__init__.py`, `base_set.py`, `manifest.py`, `mythic_set.py`, `registry.py`, `signature.py` | contenido efectivamente publicado, procedencia, manifests, confianza y firmas |
| Fronteras | `application.py`, `service.py`, `presentation.py`, `public_catalog.py` | autenticación, CAS, DTO público, opciones opacas y separación mecánica/editorial |

## 6. Brechas de capacidad general (sin corrección)

Continúan `MISSING` como abstracción general suficiente: mulligan; mirar sin
revelar con alcance de privacidad; trigger general de salida/sacrificio/
descarte; entrada al tablero uniforme para movimientos indirectos; colocar al
fondo y reordenar cartas con elección persistible; Vuelo, Dureza, Intangible,
Estampida, Cavar e Infectar; atacar sin girarse y atacar dos veces; prevención
ilimitada filtrada por combate; protección de destrucción por causa; Desafío
iniciado por no-Señor; recuperación acotada de Fuerza; y descarte forzado con
elector declarativo. Las inmunidades de cadena y taxonomías editoriales
incompletas permanecen `PARTIAL`, no soporte general demostrado.

## 7. Conclusión

La cobertura fuerte se concentra en el ciclo técnico ya declarado: costes,
Transmutación, combate ordinario, Desafío, zonas base, pila LIFO, formatos y
persistencia genérica. Las filas temporales respaldadas sólo por una
normalización conservadora permanecen `PARTIAL` o `AMBIGUOUS`; el presupuesto
Mítico permanece `CONFLICT`. No se promovió ninguna carta por analogía con un
resolutor y no se cambió ninguna regla, enum, modelo ni contrato ejecutable.
