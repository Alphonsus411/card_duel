# Lista de comprobación de una entrega

Este procedimiento prepara una entrega sin publicar en PyPI ni fusionarla.

## 1. Versión y rama

- Partir del commit de `main` que corresponde a la última entrega y crear una rama.
- Actualizar conjuntamente `pyproject.toml`, `card_duel_engine.__version__`,
  `RuleSet.version`, README, CHANGELOG, arquitectura y reglas base.
- Confirmar que `dependencies = []`, `license = "Apache-2.0"` y los formatos v2
  permanecen intactos.

## 2. Entorno y lockfile

```bash
uv lock
uv sync --locked --extra dev
git diff --exit-code -- uv.lock
```

El último comando se ejecuta después de sincronizar y debe demostrar que `uv` no
reescribió el lockfile ya confirmado.

## 3. Calidad, pruebas y cobertura

```bash
uv run python -m mypy
uv run python -m compileall -q src tests scripts
uv run coverage run --branch -m unittest discover -s tests -v
uv run coverage report
```

No se reduce el umbral de cobertura ni se omiten motor, gestores, servicio o
persistencia para superar la comprobación.

## 4. Carga y persistencia

```bash
uv run python scripts/verify_headless_simulations.py --json simulations.json
uv run python scripts/verify_persistence_roundtrips.py --json persistence.json
uv run python scripts/verify_release.py --json release-verification.json
```

Revisar que consten 300 simulaciones, 54.000 comandos, 84.000 eventos y 30
rondas con huellas de snapshot, replay y estado original idénticas. Los JSON son
temporales y no se confirman.

## 5. Wheel reproducible y auditoría

```bash
rm -rf dist
uv run python scripts/verify_reproducible_wheel.py
cat dist/SHA256SUMS
cat dist/wheel-audit.json
```

La herramienta construye dos veces con `SOURCE_DATE_EPOCH`, exige identidad
binaria y audita SHA-256, versión, licencia, dependencias, etiqueta universal,
purelib, `RECORD`, rutas, duplicados, secretos, contenido, orden, timestamps y
permisos. `dist/`, `SHA256SUMS` y `wheel-audit.json` son artefactos temporales.

## 6. Instalación y CI

Instalar el wheel con `--no-deps` en entornos limpios de Python 3.11, 3.12 y
3.13, importar el paquete y comprobar la versión. Verificar también que
`pip install .` funciona. Esperar a que todos los trabajos de GitHub Actions
estén verdes y descargar el artefacto para cotejar su SHA-256.

## 7. Publicación manual posterior

- Abrir únicamente un **Draft PR**, sin autofusión, y revisarlo sin fusionar.
- Tras aprobación humana, crear manualmente un tag firmado `v0.16.0` sobre el
  commit definitivo.
- Volver a construir desde ese tag, registrar el hash definitivo del wheel y
  contrastarlo con `SHA256SUMS` antes de cualquier publicación manual.
- La creación del tag, la fusión y la publicación quedan siempre fuera de esta
  automatización.
