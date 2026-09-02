# Gaps mecánicos de la microcolección de fase 2

**Resultado anterior de la microcolección `base`:** **ningún gap requerido por
sus ocho cartas**. La revisión posterior del corpus Mítico aporta por primera
vez evidencia real adicional; no convierte las posibilidades hipotéticas de
esta sección en requisitos.

Esta evaluación se limita a las ocho candidatas reales publicadas por la
microcolección `base`: Ember Initiate, Grove Sentinel, Skyline Duelist,
Stoneback Warden, Ashen Vanguard, Verdant Colossus, First Arena Champion y
Ancient Grove Keeper. No usa cartas hipotéticas ni convierte posibilidades del
motor en necesidades de contenido.

## CARD

`base-c001` a `base-c008`, es decir, las ocho definiciones de
`BASE_CARD_DEFINITIONS`. Las ocho son criaturas permanentes con coste y Fuerza
base; `base-c003` y `base-c007` añaden únicamente `CAN_CHALLENGE`. El resto no
tiene efectos, habilidades ni keywords.

## DESIRED BEHAVIOR

Al jugarse, cada carta debe seguir el flujo ordinario de una criatura, conservar
su coste y Fuerza base y participar en combate conforme a las reglas existentes.
Skyline Duelist y First Arena Champion deben poder declarar Desafío mediante el
permiso declarativo `CAN_CHALLENGE`. Ninguna de las ocho cartas requiere una
resolución particular adicional.

## CURRENT ENGINE LIMITATION

No se encontró una limitación del motor que impida expresar esos
comportamientos. Por tanto, esta revisión no abre un gap ni propone ampliar el
vocabulario mecánico.

Se evitaron deliberadamente capacidades que las ocho cartas no piden: efectos
al entrar o activados, costes alternativos o variables, objetivos y reparto,
búsqueda o movimiento entre zonas, reemplazos, cambios de control, modificación
de texto o definición, efectos continuos, inmunidades, regeneración,
transformación, rangos Legendario/Divino y dominios de Señor. Su existencia en
el motor no justifica agregarlas a esta microcolección y su ausencia en una
carta no constituye un gap.

## IS GENERAL CAPABILITY?

No aplica: no hay una capacidad ausente que generalizar. `CAN_CHALLENGE` ya es
una capacidad declarativa reutilizable y las estadísticas ordinarias ya forman
parte de `CardDefinition`. Se descarta expresamente cualquier solución o rama
de resolución basada en `card_id`: incluso si apareciera una necesidad futura,
debería modelarse por tipos, efectos, keywords o contratos declarativos
reutilizables, nunca por la identidad de una carta particular.

## EVIDENCE

Se cotejaron las ocho `CardDefinition` y sus presentaciones. En el vocabulario
de tipos se inspeccionaron `CardKind` (incluido `CREATURE`), `CardRank`, `Zone`,
`Phase`, `TargetMode`, `EffectDuration`, `TriggerKind`, `LordDomain` y
`MoveReason`. En las definiciones declarativas se revisaron
`EffectDefinition`, `AbilityDefinition`, `ContinuousEffectDefinition`, costes,
filtros, reemplazos de movimiento y parches de texto. También se inspeccionó la
única keyword cerrada, `CAN_CHALLENGE`.

En resolución se revisaron el mapa de resolutores de `EffectManager`, el flujo
de juego de permanentes, combate y Desafío. Los resolutores existentes cubren
heridas, curación, Pasos, robo, daño, Fuerza, agotar/enderezar, destruir,
prevención, transformación en criatura, daño repartido, movimiento, búsqueda y
barajado de zonas, regeneración, supresión de fases, control, copia,
transformación de definición y modificación de texto. Ninguno necesita
expresar algo adicional para estas candidatas: seis son criaturas sin texto
mecánico y las otras dos sólo consumen el permiso `CAN_CHALLENGE`, que el motor
ya interpreta. Por eso no se fuerza un efecto, keyword o resolutor nuevo para
fabricar un gap.

## PROPOSED FOLLOW-UP

No se propone implementar ningún cambio mecánico en esta fase. Si una fase
posterior incorpora cartas reales que sí exijan una capacidad nueva, deberá
abrir un gap sustentado por ese texto y cubrir, como mínimo:

- pruebas unitarias del contrato declarativo y del resolutor, casos inválidos,
  selección de objetivos y atomicidad;
- persistencia completa en snapshots, incluida validación y migración cuando
  cambie el esquema;
- replay de comandos y decisiones, compatibilidad con artefactos anteriores y
  equivalencia del estado y del historial reproducidos; y
- determinismo frente a orden de catálogos, objetivos y colecciones, con toda
  aleatoriedad registrada o derivada de una fuente reproducible.

Ese seguimiento deberá seguir excluyendo condicionales por `card_id`. Esta nota
no reserva una implementación ni convierte las capacidades deliberadamente
evitadas en trabajo pendiente.

### Gaps demostrados por el corpus Mítico

La matriz de `PHASE_2C_MYTHIC_CORPUS.md` es la fuente de clasificación. Los
números siguientes son los tokens originales impresos en el PDF, no IDs de
catálogo. Ninguna de estas cartas se publica mientras falte parte de su
semántica.

| Gap general | Evidencia PDF (nº original) | Abstracción mínima a estudiar |
|---|---|---|
| Taxonomía mecánica declarativa, separada de identidad editorial | 024, 029, 143, 145 | Etiquetas/tipos mecánicos validados y filtros sobre ellos |
| Revelar desde la cima hasta coincidencia, procesando fallos | 026 | `REVEAL_UNTIL` con filtro, destinos y agotamiento explícitos |
| Desafío iniciado por habilidad y por criatura no-Señor | 027 | Permiso de iniciador y acción disparada con ventana/objetivos |
| Prevención/protección por causa y duración | 028, 140 | Escudo continuo con causa `COMBAT_DAMAGE` y expiración |
| Keywords de combate ejecutables (Vuelo, Dureza, no girar, doble ataque) | 140–145 (doble ataque: 142; no girar: 140) | Keywords cerradas integradas en acciones, combate y estado |
| Inmunidad según procedencia mecánica del efecto | 029, 140–145 | Perfil de fuente tipado y filtro de inmunidad, sin leer texto/nombre |
| Disparo al salir o antes de mover a descarte | 142 | Trigger/reemplazo de movimiento con objetivo y orden definidos |

#### Impacto transversal mínimo

- **Persistencia:** todo permiso, escudo, trigger pendiente, taxonomía y estado
  de revelación debe serializarse y validarse con versión/migración.
- **Replay:** las elecciones, revelaciones, movimientos, fuentes de efecto y
  declaraciones de combate deben quedar registradas; no se vuelven a sortear
  ni a inferir desde texto editorial.
- **Acciones legales:** `actions.py` debe enumerar únicamente ventanas y
  objetivos válidos y ocultar información privada del mazo.
- **Seguridad/privacidad:** el servidor valida IDs de instancia y permisos; no
  expone candidatos ocultos ni acepta nombre, token, raza, `rules_text` o
  `card_id` como autoridad mecánica.

### Ambigüedades editoriales (no son gaps)

Quedan separadas deliberadamente: quién elige el descarte de nº144, el alcance
gramatical de “o” en la inmunidad de nº145, el máximo de Fuerza al “recuperar”
en nº029 y la terminación de nº026 si no queda coincidencia necesitan decisión
de reglas. Una lectura posible del PDF no justifica reabrir el motor. Sólo tras
resolver editorialmente cada contrato se decidirá si una abstracción general
ya existente basta.

### Prohibición de identidad como lógica

`rules_text`, nombre, token, raza y `card_id` no pueden participar en la
resolución mecánica. Son presentación, procedencia o identidad; no capacidades.
Los gaps anteriores sólo podrán cerrarse mediante enums, filtros, efectos,
keywords, triggers y costes declarativos generales. Se prohíben comparaciones
de cadenas, inferencias por raza editorial y condicionales para números o IDs
concretos.

## Conformidad de construcción de mazos

La suma de los costes de las cartas para obtener los puntos del mazo ya existía
de forma embebida en la validación. Fase 2-B la convirtió en la API reusable
`deck_points()`, manteniendo `CardDefinition.cost` como única fuente del coste
en Pasos y de los puntos de construcción.

El mínimo base confirmado de 50 necesitaba modelado declarativo: ahora se
expresa mediante `min_points=50` exactamente en `classic_deck_policy()` y
`mythic_deck_policy()`, no como límite universal de una política genérica. La
igualdad multideck necesitaba una validación separada porque relaciona varios
mazos; `validate_deck_group()` sólo la exige si el formato activa
`require_equal_points=True`, fuera de `DeckConstructionPolicy`.

El presupuesto Mítico continúa bloqueado por `N-POINTS-01`. La discrepancia
entre 200, 300 y 400 es una **ambigüedad normativa, no un defecto de software**:
el código no selecciona esas cifras ni ninguna otra como presupuesto Mítico
predeterminado. La síntesis, referencias y límites se documentan en
`PHASE_2_DECK_POINTS_CONFORMANCE.md`.
### Capacidad general cerrada: revelar desde la cima hasta coincidencia

La entrada Mítica nº026 aporta evidencia inequívoca: «mira la primera carta de
tu mazo», mueve a la mano si cumple el tipo, descarta en caso contrario y
«continua este proceso» hasta encontrarlo. La revisión de Fase 2-C clasificó
esta conducta como `GAP` y como capacidad general reutilizable, no como una
excepción de carta.

La abstracción mínima es `EffectKind.REVEAL_UNTIL`: reutiliza `CardFilter`,
declara el destino del primer acierto, el destino de cada fallo y una política
explícita de agotamiento. La resolución consume la cima en orden, emite una
revelación y un movimiento por carta y termina limpiamente si se agota la zona.
No compara `card_id`, nombre, token, raza, texto editorial ni catálogo.

No se añade estado autoritativo pendiente: el proceso es automático y ocurre
dentro de la transacción de resolución de la pila. Por ello snapshots y replays
mantienen sus esquemas actuales; el codec declarativo conserva los campos y el
enum nuevos de forma determinista, mientras que documentos anteriores, que no
los contienen, conservan sus valores por defecto. Tampoco aparecen nuevas
acciones legales u opciones públicas: prioridad, pila y objetivos de zona usan
los contratos existentes, y no se exponen identificadores seleccionables del
mazo a `MatchService`, `PublicMatchView` ni `PublicLegalAction`.
