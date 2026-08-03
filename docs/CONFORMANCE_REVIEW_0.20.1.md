# Revisión de conformidad del estado 0.20.1

Fecha de revisión: **2026-08-02**.

## Decisión sobre la base

El objeto de esta revisión es el SHA
`f757ac2e70f5e4c4766a1c901cb0ce403973a467`. Era una candidata previa 0.20.1,
no una demostración de conformidad ni una base desde la que repetir el desarrollo:

- `pyproject.toml` y la entrada del paquete en `uv.lock` declaran `0.20.1`;
- el commit es el merge del cambio que preparó esa versión y contiene todos los
  merges funcionales y documentales realizados desde la preparación de 0.20.0;
- la base que todavía declaraba `0.20.0` fue
  `dcbc34cf4a41ad032e641c9d401a1a2084a86f03`, ya registrada por el diagnóstico
  de Fase 1, y no debe recuperarse para duplicar el trabajo ya integrado.

Por tanto, el encargo queda reformulado como **revisión de conformidad de
0.20.1**. Se autoriza expresamente trabajar desde `f757ac2` y no volver a
incrementar la versión durante esta revisión.

## Procedencia del corpus 0.19.0

No se modificó ningún archivo de `tests/artifacts/0.19.0/`. La procedencia de
los cuatro replays adicionales se comprobó de forma reproducible:

1. se abrió un worktree separado en
   `3f21a1e2e9ba3c05b7bede3c5a7dc375d71ae39d`;
2. se confirmó que su `pyproject.toml` declaraba `0.19.0`;
3. se copió allí `generate_legacy_019_replays.py` y se ejecutó con aquel motor;
4. `cmp` confirmó igualdad byte a byte entre los cuatro resultados y los
   fixtures versionados actuales.

Esto verifica la afirmación de procedencia del README sin regenerar,
sobrescribir ni duplicar el corpus bajo control de versiones. Los fixtures
anteriores `replay-v2.json` y `snapshot-v1.json` se mantienen separados: el
generador auditado no pretende producirlos.

## Inspección estática del alcance solicitado

La inspección cubrió todos los archivos rastreados bajo
`src/card_duel_engine/`, `tests/`, `docs/` y `.github/workflows/`, además de
`pyproject.toml` y `uv.lock`.

| Criterio | Evidencia encontrada | Resultado |
|---|---|---|
| Metadatos 0.20.1 coherentes | Proyecto, lock, pruebas de release, changelog y guía de validación nombran 0.20.1. | Implementado. |
| Reglas Míticas | Se corrigieron procedencia de habilidades al resolver la pila y clasificación explícita de conjuntos Míticos; Drenaje, Desafío y objetivos Divinos conservan regresiones específicas. | Corregido y verificado, con bloqueos normativos pendientes. |
| Compatibilidad exacta con replays 0.19.0 | El adaptador se limita a ejecución de replay 0.19.0; la prueba final cubre cinco fixtures, diez repeticiones de observables por fixture, continuación y dos roundtrips. | Corregido y verificado. |
| Trazabilidad normativa | Baseline, auditoría Mítica, roadmap y matriz de trazabilidad distinguen reglas implementadas, interpretaciones y decisiones bloqueadas. | Implementado. |
| Calidad y runtimes | `mypy`, `compileall`, suite con cobertura de ramas y simulaciones forman parte de los perfiles; CI ejecuta runtime en 3.11/3.12/3.13 y full en 3.13. | Implementado. |
| Wheel reproducible | El perfil full construye dos veces, audita igualdad y contenido, publica un solo wheel y sus tres informes. | Implementado. |
| Fuente única de dependencias | El proyecto no declara dependencias runtime; el extra de desarrollo y `uv.lock` están alineados. | Implementado. |

La inspección inicial no bastaba para cerrar la candidata: después se localizaron
defectos de resolución de pila, compatibilidad semántica, clasificación Mítica y
procedencia de construcción. La candidata sólo se selecciona como **0.20.1**
tras integrar las correcciones y ejecutar sus pruebas. Siguen fuera del cierre
`N-POINTS-01`, `M-LORD-EVENT-01`, los finales multijugador no definidos y los
límites de alcance sobre catálogo, transporte y formatos persistentes nuevos.

## Causas, correcciones y regresiones

- **Bloqueo de pila y procedencia de habilidades.** Al sacar el elemento superior
  antes de resolverlo, la revalidación consultaba la carta fuente viva. Si esa
  fuente había abandonado el tapiz, se perdían su tipo efectivo y su condición de
  habilidad propia; la selección podía rechazarse y dejar la resolución sin una
  procedencia estable. `AbilitySourceProfile` congela al crear el elemento la
  identidad, tipo efectivo, permanencia y relación con el objetivo. Las pruebas de
  pila cubren la salida de la fuente, la inmunidad Divina y el vaciado LIFO; las de
  persistencia cubren el perfil en snapshot y su derivación compatible al leer v2.
- **Semántica legacy 0.19.** Usar sólo `RuleSet(version="0.19.0")` no restauraba el
  significado histórico de Drenaje, Desafío, elegibilidad y habilidades de Señor.
  El replay conserva ahora `EngineSemantics.LEGACY_019` en el motor restaurado,
  incluso al continuarlo y volverlo a serializar. `R-COMPAT-019-REPLAY` se mantuvo
  como «requiere corrección» durante el trabajo y pasó a «ya cumple» únicamente
  después de quedar verdes los cinco fixtures, diez repeticiones por fixture, la
  continuación y el segundo roundtrip de `test_replay_legacy_019.py`.
- **Clasificación Mítica.** Un filtro general de colecciones permitidas no prueba
  que una colección sea Mítica; aplicarle implícitamente el intervalo 5–50 podía
  clasificar contenido futuro o privado sin autorización. La fábrica exige ahora
  `mythic_set_ids` o `mythic_set_predicate` cuando el universo permitido es mixto,
  materializa iterables una sola vez y rechaza clasificadores incoherentes. Las
  regresiones de `test_deck_construction_policy.py` enlazan esos casos. Esto no
  incorpora ningún catálogo Mítico.
- **Procedencia del wheel.** La construcción anterior podía tomar el árbol de
  trabajo mutable mientras atribuía el artefacto a `HEAD`. El constructor crea
  ahora un worktree *detached* del commit auditado, deriva de ese commit
  `SOURCE_DATE_EPOCH`, construye dos veces allí y sólo copia el wheel auditado.
  `test_release_scripts.py` verifica aislamiento, igualdad y coherencia de los
  tres informes; no se afirma reproducibilidad entre commits distintos.

## Auditorías técnicas integradas

Estas tareas sí se implementaron y probaron en la rama revisada; no autorizan
reglas nuevas:

- **AUD-01:** `verify_release_metadata.py` compara proyecto, lock, changelog,
  validación vigente y alcance del README; sus casos de deriva están probados.
- **AUD-02:** `verify_repository_security.py` y reglas versionadas inspeccionan
  el checkout para secretos, ejecución dinámica y `shell=True`; el perfil de
  release y sus pruebas ejercitan aceptación y rechazo.
- **AUD-03:** `RELEASE_ROLLBACK.md` define y prueba un procedimiento no
  destructivo, parametrizado por versión, que preserva replays, snapshots,
  manifiestos y artefactos de evidencia.

Ninguna requirió elevar la versión ni modificar manualmente los replays
heredados.
