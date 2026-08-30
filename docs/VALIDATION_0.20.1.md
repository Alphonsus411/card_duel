# Validación candidata de la entrega 0.20.1

Esta guía define cómo producir y validar el conjunto de publicación. Toda
ejecución fuera de GitHub Actions es un **candidato local**, no el artefacto de
CI que se publicará.

## Selección de versión y canales formales

La revisión se inició después de actualizar la rama con `origin/main`, en el
SHA `3d56939f7d479d2bf141d9d260007a4198aa25f1`, el 4 de agosto de 2026. Se
consultaron por separado los tres canales formales verificables, sin considerar
ningún artefacto de GitHub Actions como una publicación:

- `git ls-remote --tags origin 'refs/tags/*'` no devolvió etiquetas estables;
- `GET /repos/Alphonsus411/card_duel/releases` devolvió una lista vacía de
  GitHub Releases;
- el registro configurado, PyPI (`https://pypi.org/simple`, según `uv.lock`),
  respondió HTTP 404 a `GET /pypi/card-duel-engine/json`, por lo que el proyecto
  y la versión 0.20.1 no constan publicados allí.

Las tres consultas fueron concluyentes y ninguna acredita la publicación formal
de 0.20.1. Por tanto, conforme a la regla de selección, se conserva **0.20.1**;
no corresponde avanzar a 0.20.2. Esta evidencia describe el estado observado en
la fecha indicada y no sustituye una nueva consulta antes de publicar.

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

## Contratos persistentes verificados

Snapshot y replay siguen en esquema v2, pero transportan semántica explícita;
la versión de esquema por sí sola no selecciona reglas históricas. Los perfiles
ausentes en v2 antiguos se reconstruyen sólo con información viva inequívoca y
quedan inciertos en los demás casos, de modo conservador. Para entradas nuevas,
el tipo efectivo y la condición de criatura permanente se congelan al crear el
elemento de pila, y las pruebas comparan la enumeración de acciones con su
ejecución real.

La verificación de digest heredado está limitada explícitamente a 0.20.0 y
0.20.1, las versiones que preceden al perfil: puede aceptar la huella antigua
sin ese campo, pero el siguiente snapshot/replay emite la huella completa. Una
versión 0.20.2 o posterior no obtiene la excepción. Los JSON de evidencia están
separados por versión y los de 0.20.0 no acreditan 0.20.1.
