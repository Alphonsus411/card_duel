# Evidencia de validación de la entrega 0.19.0

Esta acta conserva el resultado de la validación local realizada antes de abrir
el PR de atomicidad observable y rollback transaccional. Los artefactos JSON y
el wheel siguen siendo temporales y no se incorporan al repositorio.

## Resultado

- Los 250 tests finalizaron correctamente.
- La cobertura combinada de sentencias y ramas fue del 87 %, por encima del
  umbral obligatorio del 86 %.
- `mypy` no encontró problemas en los 36 archivos fuente y `compileall` terminó
  correctamente.
- Los perfiles `runtime` finalizaron con estado `ok` en Python 3.11, 3.12 y
  3.13. El perfil `full` también terminó con estado `ok`.
- Las 300 simulaciones ejecutaron 54.000 comandos y produjeron 84.000 eventos.
- Los 30 roundtrips de persistencia conservaron snapshots, replays y estado.
- `resolve_version()` devolvió `0.19.0` desde el checkout.
- El wheel reproducible se llamó
  `card_duel_engine-0.19.0-py3-none-any.whl`; sus dos construcciones fueron
  idénticas y su SHA-256 fue
  `c0fe333b71759a4d1c18a7d2d6d7c648b86b6d6d6b78862dab3b21b498e838fc`.

## Alcance confirmado

La comprobación no requirió cambios en las reglas del juego ni en los formatos
o la lógica de persistencia. Las acciones permanecen fijadas por SHA y usan las
versiones con runtime Node.js 24 que ya estaban confirmadas. La protección de
`main` no pudo comprobarse porque este checkout no tiene un remoto configurado.

## Comandos aprobados

```text
uv sync --locked --extra dev
uv run python -m mypy
uv run python -m compileall -q src tests scripts
uv run coverage run --branch -m unittest discover -s tests -v
uv run coverage report
uv run python scripts/verify_headless_simulations.py --json /tmp/simulations.json
uv run python scripts/verify_persistence_roundtrips.py --json /tmp/persistence.json
uv run python scripts/verify_reproducible_wheel.py
uv run python scripts/verify_release.py --profile full --json /tmp/release-verification.json
uv sync --locked --extra dev --python 3.11
uv run --python 3.11 python scripts/verify_release.py --profile runtime --json /tmp/runtime-3.11.json
uv sync --locked --extra dev --python 3.12
uv run --python 3.12 python scripts/verify_release.py --profile runtime --json /tmp/runtime-3.12.json
uv sync --locked --extra dev --python 3.13
uv run --python 3.13 python scripts/verify_release.py --profile runtime --json /tmp/runtime-3.13.json
uv run python -c 'from card_duel_engine._version import resolve_version; print(resolve_version())'
```
