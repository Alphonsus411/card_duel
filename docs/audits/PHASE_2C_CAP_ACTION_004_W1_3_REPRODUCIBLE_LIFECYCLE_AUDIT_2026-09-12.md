# CAP-ACTION-004 — auditoría W1.3 de lifecycle reproducible

## 1. Identidad y límites de la evidencia

La baseline solicitada es el commit
`65ffcd087470c9ab10bd698a506d07a1fd1be44b`, cuyo tree es
`26e206475a7ab9e072075a398c9c8c1d4a6287c1`. La inspección local no encontró
una referencia `main` ni ningún remoto configurado; por ello no se afirma
paridad con un HEAD remoto, ni se atribuyen resultados locales a un SHA de PR o
de merge.

La implementación W1.3 inspeccionada culmina localmente en
`19c92511dfe44d754b95a0dc705baad1fbc4a4f3` (tree
`3977516e1c87b325be13197ea832bfa57a2d6567`). Los resultados de runtime
registrados abajo corresponden exactamente a ese SHA limpio. La prueba
documental se volvió a ejecutar sobre el cambio documental posterior, que no
modifica runtime; no se presenta ese working tree como un commit distinto.

El paquete permanece en `0.20.1`. **Phase 2C permanece `IN PROGRESS` y
`CAP-ACTION-004` permanece `PARTIAL / READY`: no se declara `SUPPORTED`, no se
inicia W1.4 y no se desbloquea `CAP-TIME-002`.**

## 2. Arquitectura W1.2 encontrada

W1.2 dejó un único slot autoritativo `GameState.pending_decision`, una frontera
pública autenticada para observar y resolver una decisión previamente abierta,
opciones HMAC opacas, revalidación del elector y CAS en memoria/SQLite. La vista
de éxito sólo se publica después de confirmar el CAS. `StoredMatch.version` y
`expected_version` son la autoridad de concurrencia; `state_version` sigue
siendo un vínculo determinista de la decisión y no un contador CAS paralelo.

La privacidad encontrada es deliberadamente *fail-closed*: únicamente el
`ELECTOR` autorizado obtiene opciones resolubles. `OPPONENT` y `SPECTATOR` no
las reciben; sus semánticas y otras audiencias quedan aplazadas.

## 3. Insuficiencia de replay v2 y diseño tipado elegido

Replay v2 sólo conservaba `command_history`. Podía reconstruir comandos, pero no
sabía en qué posición relativa se habían abierto, cerrado o consumido decisiones;
por tanto no podía explicar el estado del slot ni reproducir el lifecycle
completo sin sintetizar hechos inexistentes.

W1.3 elige una unión tipada `GameHistoryEntry`: `ExecutedCommand` o
`DecisionTransitionEntry`. Esta última contiene exactamente una transición
`DecisionOpened`, `DecisionClosed` o `DecisionConsumed`. El formato evita
discriminadores libres y valida tipos, contadores y la proyección de comandos.

Se usa **una sola secuencia total `history`** para fijar por construcción el
orden relativo entre comandos y transiciones. Dos secuencias independientes
exigirían otra autoridad de intercalado y permitirían divergencia; timestamps o
wall-clock harían el resultado no determinista. `command_history` se conserva
sólo como proyección compatible y debe coincidir exactamente con los
`ExecutedCommand` de la historia total.

## 4. Lifecycle y política de `CLOSED`

El lifecycle de estado sigue siendo exactamente:

```text
PENDING → CLOSED
```

El lifecycle del único slot es:

```text
None → PENDING → CLOSED → None
```

Abrir registra `OPENED`; cerrar registra `CLOSED`; consumir registra `CONSUMED`
y sólo entonces libera el slot. `CLOSED` es terminal, permanece observable,
conserva la opción seleccionada y bloquea otra apertura hasta un consumo interno
explícito. No se borra automáticamente al resolver, observar, reconectar ni
serializar. `CONSUMED` es un hecho de historia, no un tercer
`PendingDecisionStatus`; tampoco existen `EXPIRED` ni `CANCELLED`.

Apertura, cierre y consumo construyen un candidato, validan todas las
precondiciones y sólo después sustituyen el estado. Cualquier identidad, actor,
opción, versión u orden inválidos dejan slot, historias y observables sin
mutación.

## 5. Replay v3, migraciones y snapshot v4

Las nuevas escrituras usan replay v3. El documento contiene `history` y
`history_count`, además de `commands` y `command_count` por compatibilidad. El
reproductor ejecuta la única secuencia en orden y verifica que la proyección de
comandos, los tipos, los recuentos y el digest final coincidan.

La migración replay v1→v2 conserva su contador histórico; replay v2→v3 envuelve
cada comando como `ExecutedCommand`. Es suficiente porque un replay v2 nunca
declaró lifecycle de decisión. No se inventan aperturas, cierres o consumos.

Adoptar el campo persistente `GameState.history` hace **técnicamente necesario
snapshot v4**: snapshot v3 no tenía ese campo ni `history_prefix_complete` y no
puede afirmar el mismo schema después de cambiar el agregado/digest. Las
migraciones quedan encadenadas snapshot v1→v2→v3→v4.

Para un snapshot v3 sin decisión en el slot, v4 materializa como historia la
proyección tipada de `command_history` y marca completo el prefijo. Si el
snapshot histórico contiene `PENDING` o `CLOSED`, su lifecycle previo no es
explicable: se restaura conservadoramente el estado, se establece
`history_prefix_complete = false` y `dump_replay` rechaza la exportación. Este
tratamiento *fail-closed* evita fabricar historia o presentar un replay parcial
como completo.

## 6. Atomicidad CAS y privacidad

W1.3 no debilita W1.2: la resolución pública sigue revalidando actor, opción,
estado y versión; `store.save(expected_version=...)` decide atómicamente el
único ganador. El perdedor de una carrera no persiste ni publica un éxito
fantasma. Las transiciones internas de lifecycle también son atómicas respecto
del agregado: slot e historia cambian juntos o no cambian.

La audiencia efectiva continúa limitada a `ELECTOR`; las opciones internas y el
elector no se filtran en DTOs públicos. `OPPONENT`, `SPECTATOR` y audiencias
adicionales permanecen sin opciones resolubles hasta contar con contrato
normativo y pruebas específicas.

## 7. Pruebas y resultados locales

Evidencia ejecutada sobre el SHA local exacto
`19c92511dfe44d754b95a0dc705baad1fbc4a4f3` tras sincronizar el lock:

| Comando | Resultado |
|---|---|
| `uv sync --locked --extra dev` | PASS: entorno sincronizado desde `uv.lock`. |
| `uv run pytest -q tests/test_pending_decision_w1_3.py tests/test_phase_2c_engine_evolution_roadmap.py` | PASS: 41 pruebas. |

La primera invocación anterior a `uv sync` falló durante collection con
`ModuleNotFoundError: card_duel_engine`; se clasifica como limitación de entorno,
no como fallo funcional, y quedó resuelta al instalar el proyecto bloqueado.
Sobre el working tree documental derivado se repitió `uv run pytest -q tests/test_phase_2c_engine_evolution_roadmap.py tests/test_pending_decision_w1_3.py`: PASS, 42 pruebas. También pasaron `uv run python -m mypy src/card_duel_engine` (44 archivos) y `uv run pytest -q` (suite completa). Estos resultados validan el cambio no comprometido y no se reasignan retroactivamente al SHA anterior.

## 8. Riesgos residuales y asuntos expresamente aplazados

Permanecen los riesgos de que un futuro consumidor libere `CLOSED` demasiado
pronto, se separen de nuevo los órdenes de comandos y transiciones, se acepte un
snapshot con prefijo incompleto como replay íntegro, o se confundan
`state_version` y la versión CAS. También faltan golden fixtures y backends para
cualquier superficie que se añada después de este alcance.

Se aplazan expresamente:

- apertura pública arbitraria y dispatch mecánico de familias;
- **bloqueo selectivo por familia** (`semantic_family`), sin bloqueo global de
  comandos y conservando `Concede`;
- **decisiones simultáneas**, múltiples slots/electores y su orden normativo;
- **audiencias adicionales** y la semántica de `OPPONENT`/`SPECTATOR`;
- candidatos de cartas, cardinalidad/selección compuesta, ordenación,
  revelación simultánea y búsquedas;
- integración con mulligan y promoción de cualquier dependent.

## 9. Veredicto

W1.3 acredita el lifecycle interno reproducible, la historia total tipada,
replay v3, snapshot v4 y sus migraciones conservadoras. No acredita apertura
pública universal, políticas por familia, decisiones simultáneas ni nuevas
audiencias. En consecuencia, Phase 2C sigue `IN PROGRESS`, `CAP-ACTION-004`
sigue `PARTIAL / READY`, la versión sigue `0.20.1`, no se declara `SUPPORTED` y
no se inicia W1.4.

## 10. Verificación integral de entrega (2026-09-13)

La entrega se volvió a verificar desde `/workspace/card_duel`, partiendo del
parent limpio `1704ae36c738a51a158dabe8d029b881e62d8943`, sin tag, release ni cambio
de versión. La sincronización bloqueada, todas las suites focalizadas de W0 a
W1.3, las regresiones de replay/persistencia/CAS, la prueba documental de Phase
2C y `mypy` finalizaron correctamente. La suite completa instrumentada obtuvo
`926 passed, 1 skipped, 816 subtests passed`.

El informe de cobertura con ramas registró **90%**, por encima del mínimo
contractual de **88%** que aplica `scripts/verify_release.py`; el perfil `full`
terminó con `OK: perfil full completado`. También pasó `git diff --check`. No
fue necesario alterar runtime ni relajar digest, checksum, migraciones,
privacidad o CAS para obtener estos resultados.

Esta comprobación local no sustituye la evidencia CI asociada por SHA: los
resultados de `runtime Python 3.11`, `runtime Python 3.12`, `runtime Python
3.13` y `full` deben pertenecer al commit exacto del PR. Si el PR se fusiona,
el SHA de merge y su propia ejecución CI deben registrarse por separado, sin
reutilizar los checks del SHA del PR.
