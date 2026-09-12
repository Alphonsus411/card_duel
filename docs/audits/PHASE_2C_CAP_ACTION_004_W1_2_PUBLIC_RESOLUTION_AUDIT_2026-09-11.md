# CAP-ACTION-004 — auditoría W1.2 de resolución pública

## A — HEAD inicial

La baseline local recibida es el commit `c54928d3d1a3369d70eb94e006640b80ce8404e7`,
con tree `43042d51d023ed3f39da06ae8a370b041256597d` y paquete `0.20.1`.
La copia local no contiene la referencia `origin/main`; por ello esta evidencia no
se presenta como equivalencia con el estado remoto.

Antes de implementar desde esta auditoría se debe ejecutar `git fetch --prune
origin` en un entorno de Code y volver a registrar HEAD, tree, todos los commits
posteriores y el CI correspondiente al SHA efectivo.

## B — Arquitectura previa

W1.1 dejó un único `GameState.pending_decision` autoritativo y el lifecycle
interno `None -> PENDING -> CLOSED`. W1.2 reutiliza esa autoridad: añade la
frontera autenticada, DTO público y persistencia CAS, sin crear otra tabla,
contador o representación autoritativa.

## C — Alcance

Se acredita sólo la resolución remota de una decisión ya abierta por medios
internos. No se acredita apertura pública, consumo, segunda decisión, mecánica de
cartas, cardinalidad compuesta, ordenación, búsqueda, revelación simultánea ni
mulligan. La apertura usada en las pruebas es preparación de fixture.

## D — Autorización

La aplicación exige identidad válida, vínculo a la partida y la capability
`RESOLVE_PENDING_DECISION`, independiente de `SUBMIT_COMMAND`. El servicio
revalida que el actor sea `authorized_elector`; actor, decisión u opción
incorrectos terminan en errores públicos uniformes y sin mutación.

## E — Proyecciones

`PublicPendingDecision` publica únicamente `decision_id`, `semantic_family`,
`status` y referencias públicas opacas. No publica elector, origen,
`state_version` ni tokens internos. Las decisiones `CLOSED` conservan metadatos,
pero tienen una colección de opciones vacía.

## F — HMAC

Cada `decision_option_id` se deriva mediante HMAC de dominio separado y queda
ligado a partida, jugador, versión CAS observada, `decision_id`, vínculo
`state_version`, índice y opción interna. La resolución usa comparación constante.
El identificador es una referencia opaca revocable, no una nueva autoridad ni un
vehículo que revele el token interno.

## G — Privacidad

La política es deliberadamente *fail-closed*: sólo el elector de una decisión
`ELECTOR` pendiente obtiene opciones resolubles. `INTERNAL` nunca las publica.
`OPPONENT` y `SPECTATOR` quedan sin opciones resolubles hasta que exista una
semántica pública normativa para esas audiencias. Esto acredita `INV-08` sólo en
la proyección/DTO y resolución cubiertos; no hace afirmaciones sobre futuros
eventos, logs o transportes.

## H — Resolución

La aplicación traduce exclusivamente una referencia pública vigente a una opción
interna; el servicio vuelve a cargar y revalidar antes de ejecutar
`PENDING -> CLOSED`. Un identificador manipulado, inexistente, de otro jugador,
partida, decisión o versión se rechaza sin inspección pública de secretos.

No se añade un bloqueo global de comandos mientras `semantic_family` no defina
normativamente si la decisión es obligatoria. En particular, W1.2 no bloquea
`Concede`.

## I — CAS

`StoredMatch.version` y el argumento `expected_version` constituyen la única
autoridad CAS. Se valida la versión antes del cierre y `store.save` confirma el
agregado mediante compare-and-swap. Una versión obsoleta produce rechazo o
invalidación por versión obsoleta, sin introducir estados `EXPIRED` ni
`CANCELLED`.

## J — Carrera

La carrera determinista de dos resoluciones hace que ambas candidatas carguen y
cierren sus copias antes de guardar: exactamente una confirma la versión siguiente
y la otra recibe conflicto. La evidencia existe tanto para memoria como SQLite.
Así, `INV-07` se acredita en el alcance exacto de dos cierres W1.2 sobre un único
agregado; no acredita despliegues distribuidos ni backends no probados.

## K — No ghost publication

La aplicación construye la vista pública de éxito sólo después de que el CAS haya
confirmado. La prueba concurrente observa una sola llamada de publicación: el
perdedor recibe `WriteConflict` y no produce una vista de éxito fantasma.

## L — Versiones

`PendingDecision.state_version` es un vínculo determinista definido por quien
abre la decisión. `StoredMatch.version`/`expected_version` es la única autoridad
CAS. W1.2 no afirma igualdad entre ambos espacios ni introduce derivación,
incremento coordinado o sincronización automática entre ellos.

## M — CLOSED

`CLOSED` sigue siendo terminal y observable, conserva la opción seleccionada y
ocupa el slot. No existen `EXPIRED` ni `CANCELLED`. El segundo cierre se rechaza;
W1.2 no define consumo, retirada, reapertura ni sustitución del registro cerrado.

## N — Replay

Se mantiene `REPLAY_SCHEMA_VERSION = "2"`. `INV-10` continúa pendiente porque la
apertura interna aún no se registra como comando/evento reproducible y, por tanto,
el replay integral no puede reconstruir el lifecycle W1.2. No se amplían escapes
legacy para ocultar esa divergencia.

## O — Snapshot

Se mantiene snapshot v3. El snapshot persiste el único agregado, incluidas
decisiones `PENDING` y `CLOSED`, y participa en checksum/digest. Snapshot acredita
restauración, pero no sustituye la evidencia ausente de replay.

## P — Pruebas

La evidencia nueva reside en `tests/test_pending_decision_w1_2.py` y
`tests/test_pending_decision_service.py`: DTO sin secretos, audiencias, HMAC,
autorización, entradas inválidas, vínculo de referencias, cierre único, CAS en
memoria/SQLite, carrera y ausencia de publicación fantasma. Las suites W0/W1.1 y
legacy verifican que no se cambien replay v2 ni snapshot v3.

## Q — Cobertura

La cobertura es contractual, negativa y concurrente para la frontera pública
W1.2. No constituye cobertura normativa de `OPPONENT`/`SPECTATOR`, apertura,
consumo, replay integral, obligatoriedad por familia ni todos los backends. Sólo
esta evidencia nueva autoriza los cambios de estado documental.

## R — Archivos

Superficies acreditadas: `application.py` (capability, DTO, HMAC y traducción),
`service.py` (revalidación y CAS), `controllers/base.py` y `engine/game.py`
(proyección), stores existentes y las dos suites W1.2. Esta auditoría y los tres
documentos de planificación se actualizan sin modificar runtime.

## S — Invariantes

| Invariante | Reevaluación W1.2 | Límite exacto |
|---|---|---|
| `INV-01` | acreditado | Un agregado/slot persistido; la proyección no es autoridad. |
| `INV-02` | acreditado en snapshot y frontera pública | Replay integral sigue fuera. |
| `INV-03` | acreditado | Capability más revalidación del elector. |
| `INV-04` | acreditado | HMAC vigente y pertenencia interna revalidada. |
| `INV-05` | acreditado | Un cierre confirmado; segundo intento rechazado. |
| `INV-06` | acreditado | Rechazos probados sin cambio de versión/snapshot. |
| `INV-07` | acreditado sólo para W1.2 | Un ganador CAS en memoria y SQLite; sin generalizar a otros backends. |
| `INV-08` | acreditado sólo para W1.2 | DTO/proyección resoluble sólo para elector; otras audiencias fail-closed. |
| `INV-09` | acreditado | Snapshot v3 restaura el registro autoritativo. |
| `INV-10` | pendiente | La apertura no es replayable; replay v2 no reconstruye el lifecycle. |
| `INV-11` | parcial | `expected_version` malformada/obsoleta falla cerrada; falta semántica completa de versiones futuras en todas las superficies. |
| `INV-12` | acreditado | Ninguna autorización o transición usa wall-clock. |
| `INV-13` | preservado, no cerrado | Familia versionada presente, sin dispatch mecánico ni reglas de obligatoriedad. |
| `INV-14` | acreditado | El cierre sólo registra opción/estado; no añade historia mecánica. |

## T — Riesgos

Persisten cinco riesgos explícitos: apertura reproducible, consumo de `CLOSED`,
replay integral, semántica de audiencias no electorales y reglas de bloqueo por
familia. También debe evitarse confundir el vínculo `state_version` con el CAS.

## U — Capability

`CAP-ACTION-004` permanece `PARTIAL / READY`. W1.2 acredita la frontera pública,
privacidad fail-closed, autorización, CAS, carrera y no ghost publication, pero
no cierra la capability. La matriz sólo se modifica con esta evidencia probada.

## V — Siguiente slice

El siguiente slice debe diseñar primero una apertura expresada por comando/evento
determinista y su replay, y definir el consumo reproducible de `CLOSED`. Las
semánticas de audiencia y obligatoriedad/bloqueo deben resolverse por
`semantic_family`, sin excepciones por carta y sin bloquear `Concede` por defecto.

## W — Veredicto

**W1.2 acredita la frontera pública y CAS de una decisión previamente abierta,
pero no desbloquea `CAP-TIME-002`.** También permanece pendiente
`CAP-TIME-005`; por tanto, el mulligan no puede consumir esta infraestructura
como contrato completo hasta cerrar sus demás prerequisites y la semántica
normativa correspondiente.

## X — Revalidación local de entrega (2026-09-12)

### Identidad de la evidencia

- **SHA local de entrada:** `5e6179076a649caf28d24990e88ace2eddfcfa82`.
- **Árbol probado:** ese SHA más el ajuste documental de la fila
  `CAP-ACTION-004` que restaura literalmente «expiración» y las exclusiones del
  contrato exigidas por el test del roadmap.
- **SHA del PR:** se registrará por la plataforma al crear el PR; los resultados
  locales de esta sección no se trasladan a ese SHA.
- **SHA de merge:** no existe durante esta auditoría y no se le atribuye ninguna
  evidencia local ni del PR.
- `git fetch --prune origin` no pudo contrastar `origin/main`: el checkout no
  tiene ningún remoto configurado. Por tanto, no se afirma que la baseline sea
  el HEAD remoto ni que haya sido posible rebasar sobre él.

### Comandos y resultados locales

| Comando | Resultado |
|---|---|
| `git fetch --prune origin` | `WARN`: no existe el remoto `origin`; contraste/rebase remoto imposible. |
| `uv sync --locked --extra dev` | `PASS`: lock resuelto e instalación dev completada. |
| `uv run pytest -q tests/test_pending_decision_w0.py` | `PASS`: 58 pruebas. |
| `uv run pytest -q tests/test_pending_decision_w1_1.py` | `PASS`: 43 pruebas. |
| `uv run pytest -q tests/test_pending_decision_w1_2.py` | `PASS`: 27 pruebas. |
| `uv run pytest -q tests/test_replay_legacy_019.py tests/test_replay_legacy_020_profile.py tests/test_persistence_v090.py tests/test_expected_version_contract.py` | `PASS`: 43 pruebas y 159 subtests. |
| `uv run pytest -q tests/test_phase_2c_engine_evolution_roadmap.py` | `PASS`: 15 pruebas tras restaurar el contrato documental; la primera ejecución detectó correctamente los términos ausentes. |
| `uv run python -m mypy src/card_duel_engine` | `PASS`: 44 archivos sin incidencias. |
| `uv run coverage run --branch -m pytest -q` | `PASS`: 887 pruebas, 816 subtests y 1 omitida. |
| `uv run coverage report -m` | `PASS`: 91 % total con branch coverage, sobre el mínimo exigido de 88 %. |
| `uv run python scripts/verify_release.py --profile full` | `PASS`: perfil full completado. |
| `git diff --check` | `PASS`: sin errores de whitespace. |

### Estado de entrega

La revalidación no modifica versión, tag, release ni despliegue. El único ajuste
de alcance recupera vocabulario normativo ya exigido por el roadmap; no amplía
runtime ni declara cerrado replay. `CAP-ACTION-004` continúa **`PARTIAL / READY`**
y conserva como pendientes apertura reproducible, consumo de `CLOSED`, replay
integral, audiencias no electorales y bloqueo por `semantic_family`.
