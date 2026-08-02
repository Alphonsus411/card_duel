# Revisión de conformidad del estado 0.20.1

Fecha de revisión: **2026-08-02**.

## Decisión sobre la base

El objeto de esta revisión es el SHA
`f757ac2e70f5e4c4766a1c901cb0ce403973a467`. Es una implementación previa y
completa de la candidata 0.20.1, no una base desde la que repetir el desarrollo:

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
| Reglas Míticas | Las políticas Clásica/Mítica, Drenaje, Desafío, objetivos Divinos, capacidades declarativas y eventos con serial tienen implementación y regresiones específicas. | Implementado. |
| Compatibilidad exacta con replays 0.19.0 | El adaptador se limita a ejecución de replay 0.19.0; las pruebas cubren los cuatro fixtures históricos, restauración del modo y rechazo de versiones desconocidas. | Implementado. |
| Trazabilidad normativa | Baseline, auditoría Mítica, roadmap y matriz de trazabilidad distinguen reglas implementadas, interpretaciones y decisiones bloqueadas. | Implementado. |
| Calidad y runtimes | `mypy`, `compileall`, suite con cobertura de ramas y simulaciones forman parte de los perfiles; CI ejecuta runtime en 3.11/3.12/3.13 y full en 3.13. | Implementado. |
| Wheel reproducible | El perfil full construye dos veces, audita igualdad y contenido, publica un solo wheel y sus tres informes. | Implementado. |
| Fuente única de dependencias | El proyecto no declara dependencias runtime; el extra de desarrollo y `uv.lock` están alineados. | Implementado. |

No se hallaron carencias funcionales o de release que obliguen a cambiar la
candidata 0.20.1. En particular, no se crean tareas para criterios ya cubiertos
ni se reabre una decisión normativa bloqueada.

## Tareas separadas para carencias reales no bloqueantes

Estas tareas son mejoras de ingeniería observadas estáticamente; no cambian la
conclusión de conformidad ni autorizan reglas nuevas:

- **AUD-01 — deriva de versión:** automatizar la comparación entre
  `project.version`, `uv.lock`, el encabezado de `CHANGELOG.md` y el documento
  de validación vigente. Hoy existen comprobaciones parciales, pero no una sola
  comprobación cerrada de los cuatro valores.
- **AUD-02 — seguridad del repositorio:** añadir a CI análisis estático de
  seguridad y detección de secretos del checkout con reglas versionadas. La
  auditoría actual detecta secretos dentro del wheel, que es una frontera más
  estrecha.
- **AUD-03 — rollback de publicación:** documentar y ensayar cómo retirar o
  sustituir un artefacto publicado sin alterar formatos persistidos. El
  checklist cubre construcción/publicación, no ese procedimiento operativo.

Estado posterior: **AUD-01, AUD-02 y AUD-03 completadas**. La comprobación de
metadatos y el análisis de seguridad forman ahora parte del verificador de
release; el procedimiento de rollback incluye un ensayo local no destructivo.
Ninguna tarea elevó la versión ni tocó los replays heredados.
