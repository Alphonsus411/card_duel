# Evidencia de validación de la entrega 0.20.0

Esta nota solo recoge ejecuciones realizadas para esta entrega. No traslada cifras
ni resultados de `VALIDATION_0.19.0.md`.

## Resultados obtenidos

- `uv sync --locked --extra dev`: resolución bloqueada correcta, sin dependencias
  de ejecución añadidas.
- `uv run python -m mypy src/card_duel_engine`: 37 archivos fuente comprobados,
  sin errores.
- `uv run python -m unittest discover -s tests -v`: 298 pruebas correctas; una
  inspección del wheel quedó omitida porque todavía no se había construido.
- `uv run python scripts/verify_reproducible_wheel.py`: dos construcciones
  binarias idénticas; wheel universal 0.20.0 auditado, sin dependencias runtime
  ni los dos PDF.
- `uv run python -m unittest tests.test_release_020 -v`, después de construir el
  wheel: 4 pruebas correctas, incluida su inspección efectiva y la compatibilidad
  de artefactos 0.19.0.

- `uv run python scripts/verify_release.py --profile full --json release-verification.json`:
  perfil completo correcto contra el commit candidato; 88 % de cobertura, dos
  fuentes verificadas, 300 simulaciones (54.000 comandos y 84.000 eventos), 30
  pares persistentes, wheel reproducible e instalación en Python 3.11–3.13.
