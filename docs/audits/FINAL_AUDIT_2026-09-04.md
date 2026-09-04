# Auditoría final solicitada — 2026-09-04

## Dictamen

**AUDIT INCOMPLETE — NO-GO**

No se declara Phase 2-C completa. El dictamen no puede elevarse a
`AUDIT READY FOR HUMAN REVIEW`: `mypy` falló, los dos perfiles de release no
llegaron a ejecutarse porque la invocación solicitada omite el argumento de
`--json`, no se midió cobertura y el commit que incorpora este registro aún no
puede tener CI oficial asociado.

## Registro reproducible de comandos (UTC)

El SHA de código auditado fue siempre
`0acab866c1d357403a417de035540eedcb2e2eb9`. Se conservaron los códigos de salida
reales; una dependencia instalada no se confunde con una prueba superada.

| # | Inicio (UTC) | Comando exacto | Salida | Resumen real |
|---:|---|---|---:|---|
| 1 | 2026-09-04T08:55:04Z | `uv sync --locked --extra dev` | 0 | 16 paquetes resueltos; 14 instalados; lock respetado. |
| 2 | 2026-09-04T08:55:14Z | `uv run mypy src tests` | 1 | **FAIL**: 1518 errores en 56 archivos; 100 archivos comprobados. |
| 3 | 2026-09-04T08:55:32Z | `uv run python -m compileall -q src tests` | 0 | Compilación silenciosa completada. |
| 4 | 2026-09-04T08:55:38Z | `uv run python -m unittest discover -s tests -v` | 0 | 480 pruebas en 106.916 s; OK; 1 omitida. |
| 5 | 2026-09-04T08:57:30Z | `uv run python scripts/verify_release.py --profile runtime --json` | 2 | **NO EJECUTADO el perfil**: argparse exige una ruta después de `--json`. |
| 6 | 2026-09-04T08:57:41Z | `uv run python scripts/verify_release.py --profile full --json` | 2 | **NO EJECUTADO el perfil**: argparse exige una ruta después de `--json`. |
| 7 | 2026-09-04T08:57:47Z | `uv run python scripts/verify_reproducible_wheel.py` | 0 | Dos builds idénticos; wheel 0.20.1 de 48 archivos; SHA-256 `72dd19179a851df25e6970b1407e7e9c0f1daddfeb74276006953ef6a5b17ba2`; sin PDF, fixtures, cartas de producción ni dependencias runtime. |

## Lista de 21 elementos exigidos

1. **SHA inicial:** `0acab866c1d357403a417de035540eedcb2e2eb9`.
2. **SHA final del código auditado:** el mismo SHA; no hubo cambio de código
   durante la ejecución. El commit puramente documental de este informe queda
   fuera de ese objeto auditado y requiere su propio CI.
3. **Árbol inicial:** `git diff --name-status`, `git diff --stat` y
   `git status --porcelain=v1` no produjeron entradas: estaba limpio.
4. **Archivos finales:** sólo se añade este documento de auditoría. Se rechazan
   expresamente cambios en `src/`, `tests/`, `pyproject.toml`, `uv.lock` y
   archivos de versión.
5. **Versión:** `pyproject.toml` conserva `version = "0.20.1"`; el wheel también
   declara 0.20.1.
6. **Esquema persistente:** no se modificó ningún archivo de implementación.
   Continúan snapshot=2, replay=2, manifest=2 y sobre de firma=1.
7. **Dependencias:** el sync locked terminó correctamente; el wheel declara
   cero dependencias runtime. `pypdf` se usó de forma efímera mediante
   `uv run --with pypdf` para recorrer los PDF y no alteró lock ni proyecto.
8. **Tipado:** FAIL, 1518 errores/56 archivos. Es un bloqueo, no un PASS.
9. **Compilación:** PASS para todos los módulos bajo `src` y `tests`.
10. **Suite:** PASS, 480 ejecutadas y una omitida. La omisión corresponde a la
    inspección del wheel que se realiza después por el verificador dedicado.
11. **Cobertura:** no se solicitó ni ejecutó un comando con `coverage`; porcentaje
    desconocido y gap explícito.
12. **Perfil runtime:** pendiente; el comando exacto falló en la interfaz CLI
    antes de comenzar el perfil.
13. **Perfil full:** pendiente por la misma causa; no hay JSON local generado.
14. **Reproducibilidad:** PASS; 2/2 builds binariamente idénticos, integridad
    RECORD válida y árbol fuente limpio.
15. **PDF base:** recorrido íntegro de 31/31 páginas, todas con texto extraíble
    (96 180 caracteres); SHA-256
    `1c51dabe2023626ad532368e2567d2084c47ec137c7a738bd8c0e0b707f86b21`.
16. **PDF Mítico:** recorrido íntegro de 18/18 páginas, todas con texto extraíble
    (57 204 caracteres); SHA-256
    `61243b30d219dd12d8897a206ed664d95a5e3c38b6670a818933f6d90904af36`.
17. **Denominadores de reglas:** 21 `SUPPORTED` + 11 `PARTIAL` + 1 `MISSING` +
    5 `AMBIGUOUS` + 1 `CONFLICT` = **39/39**. El conflicto normativo es
    `N-POINTS-01`; el gap técnico es el mulligan decreciente `N-PHASE-02`.
18. **Denominadores de corpus:** 103 Alpha + 147 Beta + 181 Mítica = **431/431**;
    2 `SUPPORTED` + 245 `PARTIAL` + 143 `MISSING` + 41 `AMBIGUOUS` +
    0 `CONFLICT` = **431**. Por identidad: 2 + 212 + 132 + 40 + 0 = **386**;
    431 − 386 = **45** reimpresiones/variantes.
19. **Conflictos y gaps:** siguen abiertos el conflicto y las ambigüedades
    normativas anteriores, 143 entradas `MISSING`, el tipado, ambos perfiles de
    release, la cobertura y el CI del commit documental final.
20. **Privacidad y seguridad:** la suite verde incluye contratos de observación,
    credenciales, búsquedas ocultas y DTO públicos; el wheel excluye fuentes
    primarias y fixtures. Esto es evidencia de regresión, no afirmación de
    ausencia absoluta de vulnerabilidades.
21. **Alcance funcional:** no se añadió código, esquema, catálogo ni mecánica
    nueva; no se afirma que Phase 2-C esté completa.

## CI oficial remoto

Consulta realizada contra la API pública de GitHub para el SHA auditado. El
workflow oficial `tests` (`.github/workflows/tests.yml`), ejecución
[#953](https://github.com/Alphonsus411/card_duel/actions/runs/33855671711), terminó
en `success` para ese SHA, con cuatro checks verdes: `runtime (3.11)`,
`runtime (3.12)`, `runtime (3.13)` y `full (3.13)`.

Esa evidencia corresponde **exactamente al SHA de código auditado**, pero no al
commit posterior que agrega este informe. Por tanto no satisface el requisito
de CI verde del SHA final de la rama tras registrar la auditoría.

## Criterios pendientes para revisión humana

- corregir o aceptar formalmente la línea base de 1518 errores de `mypy`;
- repetir runtime y full con una ruta JSON válida acordada;
- medir y registrar cobertura;
- obtener CI oficial verde exactamente para el commit documental final;
- volver a comprobar que el diff final sólo contiene auditoría documental.
