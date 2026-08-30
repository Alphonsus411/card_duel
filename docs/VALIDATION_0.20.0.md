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

- `uv run python scripts/verify_release.py --profile full --json
  docs/release-results/0.20.0/full-python-3.13.json`:
  perfil completo correcto contra el commit candidato; 88 % de cobertura, dos
  fuentes verificadas, 300 simulaciones (54.000 comandos y 84.000 eventos), 30
  pares persistentes, wheel reproducible e instalación en Python 3.11–3.13.

## Revalidación final de la entrega

La revalidación partió del SHA
`30ea7dbf91bcb935b0d0d495fe44f2adaeb3c571` en la rama `work`. Se ejecutó
`uv sync --locked --extra dev` antes de cualquier comprobación. El verificador
de fuentes confirmó ambos originales, `compileall` no encontró errores, mypy
comprobó 37 archivos y la suite completa terminó con 298 pruebas correctas y
una omisión esperada. La cobertura de líneas y ramas fue del **88 %**, por
encima del umbral obligatorio del 86 %.

Los resúmenes de máquina se conservan, sin reinterpretarlos, en:

- `release-results/0.20.0/runtime-python-3.11.json`;
- `release-results/0.20.0/runtime-python-3.12.json`;
- `release-results/0.20.0/runtime-python-3.13.json`;
- `release-results/0.20.0/full-python-3.13.json`.

Cada runtime ejecutó lockfile, mypy, `compileall`, suite completa y cobertura
con el intérprete indicado. El perfil full de Python 3.13 añadió las dos
fuentes, 300 simulaciones (54.000 comandos y 84.000 eventos), 30 pares de
snapshot/replay, auditoría de wheel e instalación aislada del artefacto en
Python 3.11, 3.12 y 3.13.

## Repeticiones dirigidas

- Las cinco pruebas de Drenaje se ejecutaron en cinco rondas: **25/25**
  ejecuciones correctas.
- Desafío, rollback y replay se ejecutaron en tres rondas. Cada ronda cubrió
  las semillas 3, 19 y 71 de Desafío, además de las semillas 2000–2019 de las
  secuencias generadas con replay: **9/9** pruebas de alto nivel correctas.

## Fuentes y artefacto distribuible

| Archivo | SHA-256 |
|---|---|
| `Fantasy Tokens.pdf` | `1c51dabe2023626ad532368e2567d2084c47ec137c7a738bd8c0e0b707f86b21` |
| `Fantasy Tokens Edicion Mitica.pdf` | `61243b30d219dd12d8897a206ed664d95a5e3c38b6670a818933f6d90904af36` |

`scripts/verify_reproducible_wheel.py` produjo dos builds binariamente
idénticos. El resultado auditado previo al commit de esta evidencia fue
`card_duel_engine-0.20.0-py3-none-any.whl`, con SHA-256
`011dea0ca6df85598f0a30e04bf5a37ecbea141ab339ef5b14378e5074a71496`,
41 entradas, `RECORD` íntegro, etiqueta universal purelib y **cero dependencias
runtime**. La lista cerrada de entradas y la inspección ZIP confirman que
ninguno de los dos PDF está incluido.

## Límites confirmados

Esta revalidación no importó cartas concretas ni utilizó su corpus para crear
reglas universales; no resolvió `N-POINTS-01`; no creó un esquema v3 ni cambió
los formatos persistentes v2; no alteró las condiciones terminales de partidas
multijugador; y no implementó transporte. Los PDF permanecen exclusivamente
como fuentes del repositorio y no entran en el wheel.
