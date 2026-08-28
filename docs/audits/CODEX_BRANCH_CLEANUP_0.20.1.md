# Cierre de limpieza de ramas Codex — 0.20.1

- **Fecha UTC:** `2026-08-28`.
- **Resultado:** **NO-GO**.
- **Motivo:** no fue posible autenticar una escritura HTTPS contra GitHub; la
  primera eliminación controlada devolvió exit `128` y no se continuó con
  operaciones que estaban destinadas a fallar por la misma causa global.

## Inventario inicial

Se empleó el mismo criterio del inventario anterior: referencias bajo
`refs/remotes/origin`, excluyendo únicamente la referencia simbólica
`origin/HEAD`; para Codex se contaron las referencias bajo
`refs/remotes/origin/codex`.

| Dato | Valor |
|---|---:|
| `BASE_MAIN_SHA` (`git rev-parse origin/main`) | `f3ba821843a6e29e7f298826381066e6c2b1de79` |
| Ramas remotas antes | 168 |
| Ramas `origin/codex/*` antes | 166 |
| SHA registrado de `origin/Bella-2.0` | `851bc963692c7c2e0e70d34c8e09b67781da1ac4` |

## Eliminación

El intento de borrar
`codex/actualiza-allowed_content-y-mejora-validaciones` falló sin modificar el
remoto:

```text
fatal: could not read Username for 'https://github.com': No such device or address
```

Por tanto:

- ramas eliminadas: **0**;
- ramas Codex eliminadas: **0**;
- la rama intentada queda **KEEP/DELETE_FAILED**;
- no se intentaron más borrados tras identificar el impedimento global.

## Verificación posterior

Después del intento se ejecutó `git fetch --all --prune` correctamente. A
continuación se repitieron los conteos con exactamente el criterio inicial.

| Comprobación | Evidencia | Resultado |
|---|---|---|
| `FINAL_MAIN_SHA` mediante `git rev-parse origin/main` | `f3ba821843a6e29e7f298826381066e6c2b1de79` | Igualdad literal con `BASE_MAIN_SHA`: **PASS** |
| Ramas remotas después | 168 | `168 = 168 - 0`: **PASS** |
| Ramas `origin/codex/*` después | 166 | `166 = 166 - 0`: **PASS** |
| Única verificación de `origin/Bella-2.0` | existe con `851bc963692c7c2e0e70d34c8e09b67781da1ac4` | **Bella-2.0: UNTOUCHED / KEEP** |
| Versión declarada en `pyproject.toml` | `0.20.1` | **PASS** |

No se editaron `pyproject.toml`, `uv.lock`, el changelog ni notas de release.
Tampoco se modificaron `src/`, `tests/`, `benchmarks/`, `scripts/` ni
`.github/workflows/`. No se ejecutó la suite funcional completa porque esta
entrega sólo registra evidencia documental y no cambia código.

## Decisión

Las invariantes de cierre y la inmovilidad de `main`, `Bella-2.0` y la versión
quedaron verificadas. Sin embargo, el objetivo operativo de eliminar ramas no
se cumplió por falta de credenciales de escritura. En consecuencia, este
cierre se declara **NO-GO** y no presenta como exitosa una limpieza de cero
ramas.
