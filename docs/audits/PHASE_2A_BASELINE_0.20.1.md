# Baseline autoritativo de Fase 2-A — 0.20.1

## Alcance y referencias

- **Fecha de revisión:** 31 de agosto de 2026 (UTC).
- **Directorio de trabajo:** `/workspace/card_duel`.
- **Rama revisada:** `work`.
- **Commit autoritativo:**
  `0c0f405a77204b6fef046c320f1444f5f0795261`.
- **HEAD fijado antes de iniciar Fase 2-A:**
  `a3b164f7735f55f37b53808160a56ad54861c7c9`.

El objeto autoritativo existe y es de tipo `commit`. La orden
`git merge-base --is-ancestor 0c0f405a77204b6fef046c320f1444f5f0795261
a3b164f7735f55f37b53808160a56ad54861c7c9` terminó con código `0`; además,
`git merge-base` devolvió el propio commit autoritativo. Por tanto, este commit
es ancestro del HEAD previo a Fase 2-A y se adopta como referencia autoritativa
para la revisión final.

## Cambios que ya existían antes de Fase 2-A

El historial exclusivo del rango
`0c0f405a77204b6fef046c320f1444f5f0795261..a3b164f7735f55f37b53808160a56ad54861c7c9`
contenía estos commits:

1. `321385e` — `docs: refrescar evidencia final de fase 1`.
2. `a3b164f` — merge del PR #199, cuyo asunto es
   `Merge pull request #199 from
   Alphonsus411/codex/ejecutar-verificacion-de-lanzamiento-completa`.

La revisión con `git diff --stat`, `git diff --name-status` y el diff completo
del rango identificó **36 inserciones y 30 eliminaciones en cinco archivos**:

- `docs/audits/PHASE_1_FINAL_VERIFICATION_0.20.1.md`;
- `docs/release-results/0.20.1/full-python-3.13.json`;
- `docs/release-results/0.20.1/runtime-python-3.11.json`;
- `docs/release-results/0.20.1/runtime-python-3.12.json`;
- `docs/release-results/0.20.1/runtime-python-3.13.json`.

Esos cambios actualizaron evidencia de Fase 1: el HEAD documentado, cobertura
del 88 % al 89 %, inventarios de seguridad, hash del lockfile y metadatos del
wheel candidato. **Todos son preexistentes y quedan expresamente excluidos de
la atribución de Fase 2-A.**

## Confirmación de versión

La versión pública sigue siendo **`0.20.1`** en todas las superficies
versionadas pertinentes revisadas:

- `pyproject.toml` declara `project.version = "0.20.1"` como fuente canónica;
- `src/card_duel_engine/_version.py` lee y valida esa clave en un checkout y
  usa `importlib.metadata.version("card-duel-engine")` en una instalación;
- `uv.lock` registra el paquete editable `card-duel-engine` con versión
  `0.20.1`;
- `src/card_duel_engine.egg-info/PKG-INFO` registra `Version: 0.20.1`;
- los cuatro informes versionados bajo `docs/release-results/0.20.1/` registran
  `version = "0.20.1"`, y el informe full conserva además ese valor en los
  metadatos del paquete y del wheel.

No se realizó ningún incremento ni modificación de versión.

## Separación de atribución para la revisión final

La revisión final debe usar el commit autoritativo indicado arriba para conocer
el estado heredado, pero debe presentar dos rangos separados:

1. **Preexistente:**
   `0c0f405a77204b6fef046c320f1444f5f0795261..a3b164f7735f55f37b53808160a56ad54861c7c9`.
2. **Fase 2-A:**
   `a3b164f7735f55f37b53808160a56ad54861c7c9..HEAD`.

En esta entrega, el segundo rango incorpora únicamente este informe de
baseline. Antes del commit se debe volver a ejecutar `git status --short` y
confirmar que no haya ningún archivo ajeno a este alcance.
