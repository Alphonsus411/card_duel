# Diagnóstico de Fase 1 para 0.20.1

Fecha de ejecución: **2026-08-02**. Esta nota registra el estado anterior a
cualquier cambio funcional para cerrar las regresiones Míticas de 0.20.1.

## Punto de partida y rama

- `git fetch --all --prune` terminó sin salida, pero el clon entregado no tenía
  remotos configurados ni una referencia `main`; su única rama era `work`.
- Por ello se creó `main` localmente en el único `HEAD` disponible. El intento
  requerido de `git pull --ff-only` no pudo encontrar información de seguimiento.
- `git rev-parse HEAD`: `dcbc34cf4a41ad032e641c9d401a1a2084a86f03`.
- `git log -1 --oneline`: `dcbc34c Merge pull request #66 from
  Alphonsus411/codex/ejecutar-tareas-de-verificacion-y-documentacion`.
- Antes de tocar archivos, `git status --short` no produjo salida y
  `pyproject.toml` contenía exactamente una declaración `version = "0.20.0"`.
- Se creó `codex/cerrar-regresiones-miticas-0.20.1` desde ese `main` local, sin
  reutilizar la rama `work`.

## Fuentes y lectura normativa directa

Los SHA-256 calculados con `sha256sum` son:

| Fuente | SHA-256 |
|---|---|
| `Fantasy Tokens.pdf` | `1c51dabe2023626ad532368e2567d2084c47ec137c7a738bd8c0e0b707f86b21` |
| `Fantasy Tokens Edicion Mitica.pdf` | `61243b30d219dd12d8897a206ed664d95a5e3c38b6670a818933f6d90904af36` |

Se leyó directamente el texto extraído de las páginas físicas 2–3 / internas
1–2 de `Fantasy Tokens Edicion Mitica.pdf`. Bajo `INTROITOS`, el documento
presenta primero como cambios de construcción las barajas de 40–60 cartas y
los máximos de cinco copias para cartas no Legendarias y cuatro para
Legendarias. Solo después crea apartados diferenciados para formato Clásico y
formato Mística. Por estructura y redacción, **40–60 y 5/4 son límites
generales de construcción de la actualización, no límites exclusivamente
Místicos**. Las restricciones exclusivas de Mística son, entre otras, las
ediciones admitidas, la prohibición de cartas de coste cero y el intervalo de
coste 5–50 para cartas de Edición Mítica.

## Diagnóstico de ejecución anterior a cambios

Se ejecutaron los siguientes comandos de Fase 1:

```text
uv --version
uv python find 3.11
uv python find 3.12
uv python find 3.13
uv lock
uv sync --locked --extra dev
git diff --exit-code -- uv.lock
uv run python scripts/verify_release.py --profile runtime --json /tmp/runtime-before.json
uv run python scripts/verify_release.py --profile full --json /tmp/full-before.json
uv run python -m unittest discover -s tests
```

Resultados:

- `uv 0.7.22`; antes del aprovisionamiento del perfil completo, la
  disponibilidad real era Python 3.12.13 en `.venv/bin/python3`; no se
  encontraron 3.11 ni 3.13.
- `/tmp/runtime-before.json` se conservó con estado `ok`, lockfile sin cambios,
  `mypy` y `compileall` correctos, y cobertura de ramas/líneas del **88 %**.
- `/tmp/full-before.json` se conservó con estado `ok`: dos fuentes verificadas,
  **300** simulaciones, **54.000** comandos, **84.000** eventos y **30** pares
  persistentes.
- La suite explícita ejecutó **298 pruebas** en 17,306 s, todas correctas.
- El perfil completo instaló y comprobó realmente el wheel en Python **3.11,
  3.12 y 3.13**.
- El wheel candidato es
  `dist/card_duel_engine-0.20.0-py3-none-any.whl`, de 81.115 bytes, con SHA-256
  `b47fef9e0617dc499f4ded41614b1e06f8409cb4d480f7d920c4ac88210902c5`.
- `dist/wheel-audit.json` registra dos builds binariamente idénticos, 41
  entradas, `RECORD` íntegro, `Root-Is-Purelib: true`, etiqueta
  `py3-none-any`, licencia Apache-2.0 y cero dependencias de ejecución.

Los JSON de `/tmp` y los artefactos de `dist/` son evidencia temporal y no se
incorporan al control de versiones.

## Inventario de artefactos heredados de 0.19.0

| Artefacto | Tamaño | SHA-256 | Contenido relevante |
|---|---:|---|---|
| `tests/artifacts/0.19.0/replay-v2.json` | 6.460 bytes | `a11ba2ee664d31cfc81dfc92ab7c6859b2f91d89c47fb79bfdbf5f7936b9e71d` | Esquema 2, motor 0.19.0, semilla 1900 y tres comandos: `PlayCard`, `PassPriority`, `PassPriority`. |
| `tests/artifacts/0.19.0/snapshot-v1.json` | 52.087 bytes | `0a5d16e915afdc7e881b894dee5394553cc6c03e60fbf27117f21fbe1d9473b2` | Esquema 1 y motor 0.19.0. |

La búsqueda literal y la inspección estructural confirman que el replay
existente **no cubre Drenaje, Desafío ni el evento `ATTACKERS_DECLARED`**. El
snapshot tampoco contiene esos marcadores; por tanto, ninguno debe citarse
como evidencia histórica de esas rutas Míticas.
