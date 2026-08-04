# Validación candidata de la entrega 0.20.1

Esta guía define cómo producir y validar el conjunto de publicación. Toda
ejecución fuera de GitHub Actions es un **candidato local**, no el artefacto de
CI que se publicará.

## Comandos, en orden

```bash
rm -rf dist
uv sync --locked --extra dev
uv run python scripts/verify_release.py \
  --profile full --json docs/release-results/0.20.1/full-python-3.13.json
(cd dist && sha256sum --check SHA256SUMS)
python -m json.tool dist/wheel-audit.json >/dev/null
python -m json.tool docs/release-results/0.20.1/full-python-3.13.json >/dev/null
```

El perfil completo invoca una sola vez el constructor reproducible. Este crea
dos wheels temporales del mismo `HEAD`, audita ambos, exige igualdad byte a
byte, copia exactamente uno de ellos a `dist/` y solo entonces escribe, en este
orden, `SHA256SUMS` y `wheel-audit.json`. El resumen
`docs/release-results/0.20.1/full-python-3.13.json` se escribe al terminar; no hay otra construcción
posterior.

## Criterios de aceptación

- Los dos builds del mismo commit son binariamente idénticos. El timestamp
  reproducible procede de ese commit y no es una constante elegida
  arbitrariamente; no se exige igualdad entre commits distintos.
- `SHA256SUMS`, `wheel-audit.json` y `release-verification.json` identifican el
  mismo nombre y SHA-256 del wheel copiado.
- La versión procede de `project.version` en `pyproject.toml`; el wheel tiene
  etiqueta `py3-none-any`, `Root-Is-Purelib: true` y `RECORD` íntegro.
- La lista cerrada contiene únicamente los módulos Python de producción y los
  metadatos del wheel: no contiene ninguno de los dos PDF, fixtures, cartas de
  producción ni declaraciones `Requires-Dist` runtime.
- El artefacto del job `full` contiene exactamente el wheel, `SHA256SUMS`,
  `wheel-audit.json` y `release-verification.json`.

## Evidencia conservada

Los cuatro resúmenes de esta entrega se conservan exclusivamente en:

- `release-results/0.20.1/runtime-python-3.11.json`;
- `release-results/0.20.1/runtime-python-3.12.json`;
- `release-results/0.20.1/runtime-python-3.13.json`;
- `release-results/0.20.1/full-python-3.13.json`.

## Resultados candidatos locales

Una ejecución local correcta debe informar estado `ok`, dos builds iguales y
las instalaciones aisladas en Python 3.11, 3.12 y 3.13. El nombre y el digest
se consultan directamente, sin transcribirlos a esta nota:

```bash
cat dist/SHA256SUMS
python -c 'import json; print(json.load(open("dist/wheel-audit.json"))["sha256"])'
```

Cualquier valor mostrado por esos comandos queda rotulado literalmente como
**candidato local**. El hash autoritativo pertenece exclusivamente al artefacto
generado por CI para el SHA probado, y debe cotejarse descargando conjuntamente
los cuatro archivos del job `full`.

## Resultado real de la revisión

La versión seleccionada continúa siendo **0.20.1**. La suite integrada confirma
el perfil congelado de procedencia de habilidades en pila, la clasificación
Mítica explícita y el puente semántico 0.19 con cinco fixtures, diez repeticiones
por fixture, continuación y segundo roundtrip. El constructor de wheel usa un
worktree *detached* de `HEAD`; sólo declara reproducibilidad de dos builds del
mismo commit.

El resultado no cierra `N-POINTS-01` ni `M-LORD-EVENT-01`, no define finales
multijugador, no añade esquemas, cartas, catálogo o transporte y no modifica los
PDF normativos. Los hashes generados localmente siguen siendo candidatos y no se
presentan como artefactos publicados.
