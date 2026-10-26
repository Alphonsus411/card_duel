# CAP-SECRET-001 / S2 — Modelo mínimo de mirada privada

Fecha: 2026-10-26
Estado: diseño de extensión mínima; sin cambio de runtime
Capability: `MISSING / READY`

## Decisión

S2 no incorpora todavía una ruta, comando, DTO, campo de estado ni tipo
persistido. El inventario S1 no identifica una regla cerrada que autorice una
mirada de contenido oculto distinta de la mano propia ya proyectada. Crear una
API genérica del tipo `look(observer_id, owner_id, zone)` convertiría los
identificadores recibidos desde transporte en una autorización y violaría S0.

La extensión mínima admisible para una futura especialización es un *grant* de
mirada privado, interno, efímero y ligado a su origen. Sólo la capability que
defina la regla concreta podrá construirlo; la capa de transporte no lo recibe,
no lo elige y no lo puede serializar.

## Forma propuesta

El grant futuro debe expresar, como mínimo, los siguientes valores tipados:

| Componente | Significado | Restricción |
| --- | --- | --- |
| `observer` | jugador al que se permite observar | se deriva de la identidad autorizada, nunca de un parámetro remoto libre |
| `audience` | receptores de la salida | empieza con el único `observer`; ampliar la audiencia exige contrato propio |
| `scope` | zona o subconjunto ya determinado por la regla originadora | no acepta filtro, orden, límite ni selector suministrado por cliente |
| `origin` | regla/resolución que emitió la autorización | permite revalidar que sigue vigente sin revelar el motivo del rechazo |

El resultado asociado será una vista privada inmutable de las cartas que el
alcance ya autoriza. Es un valor de retorno local de la misma operación: no es
un ID público, token reutilizable, capacidad serializable ni una decisión.

## Ciclo de uso permitido

1. Una capability especializada y cerrada determina la regla, el observador y
   el alcance sin tomar esos valores de la petición remota.
2. En la frontera autenticada se resuelve la identidad; el adaptador invoca la
   especialización, no una lectura genérica de zona.
3. La especialización revalida `origin`, audiencia y zona antes de construir la
   vista privada.
4. La vista se entrega sólo a `audience` y se descarta al terminar la llamada.

No hay transición de `GameState` en ese ciclo. En particular, el grant y la
vista no pueden entrar en snapshot, replay, digest, historial, evento, acción
legal ni proyección pública. Si una regla necesita pausarse o que el jugador
elija después, deja de pertenecer a S2 y debe usar el contrato de decisión
autorizada de `CAP-ACTION-004` y la especialización de `CAP-SECRET-002`.

## No reutilización obligatoria

| Elemento existente | Motivo de exclusión |
| --- | --- |
| `PendingSearch` | persiste candidatos y culmina en una elección |
| `PendingMoveReplacement` | persiste una continuación y destinos a resolver |
| `PlayerObservation` / `PublicPlayerObservation` | mezclan proyección de estado actual y transporte; no representan un alcance temporal autorizado |
| token opaco o ID de carta expuesto | sería durable o reutilizable y podría actuar como oráculo |

La mano propia continúa siendo una proyección existente de `CAP-PRIVACY-001`;
no se rediseña como grant ni acredita la mirada de otra zona.

## Compatibilidad y pruebas que deberá exigir el runtime

La primera implementación que tenga una capability originadora deberá demostrar:

1. dos estados que sólo difieran en contenido oculto producen exactamente la
   misma salida para quien no pertenece a `audience`;
2. una identidad no autorizada recibe el mismo rechazo estable sin conocer si
   la zona, carta o elegibilidad existen;
3. la operación no altera estado, acciones legales, eventos, replay, snapshot
   ni digest; y
4. el grant no puede conservarse ni reutilizarse entre llamadas o tras cambiar
   la condición que lo originó.

## Salida de S2

S2 deja explícito que falta una capability originadora antes de añadir runtime.
La siguiente subfase puede caracterizar esta decisión mediante pruebas de
frontera y no interferencia sobre las rutas actuales, sin fabricar todavía una
lectura de mazo. S2 no desbloquea `CAP-SECRET-002` ni cambia persistencia,
replay, esquema, decisiones o visibilidad pública.
