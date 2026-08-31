# Informe de verificación final de Fase 1 — 0.20.1

## Identificación y alcance

- **Fecha de ejecución:** 31 de agosto de 2026 (UTC).
- **Directorio de trabajo:** `/workspace/card_duel`.
- **Rama verificada:** `work`.
- **HEAD verificado:** `6b4d348`.
- **Base de comparación solicitada:**
  `3fe33c6ac8fce6997036bdc36717f0e0fb481b4d`.
- **Versión resuelta en todas las superficies:** `0.20.1`.

Este informe registra una verificación local posterior a la implementación de
Fase 1-C. No presenta los artefactos locales como artefactos publicados ni
sustituye la ejecución de GitHub Actions.

## Entorno reproducido

Se utilizó `uv 0.7.22`, la versión fijada por `.github/workflows/tests.yml`. Para
cada intérprete se instaló la versión de Python correspondiente y se reconstruyó
el entorno con el lockfile y el extra de desarrollo:

```bash
uv python install 3.11
uv sync --locked --extra dev --python 3.11
uv python install 3.12
uv sync --locked --extra dev --python 3.12
uv python install 3.13
uv sync --locked --extra dev --python 3.13
```

Los perfiles oficiales se ejecutaron con la misma matriz del workflow:

```bash
uv run --python 3.11 python scripts/verify_release.py \
  --profile runtime \
  --json docs/release-results/0.20.1/runtime-python-3.11.json
uv run --python 3.12 python scripts/verify_release.py \
  --profile runtime \
  --json docs/release-results/0.20.1/runtime-python-3.12.json
uv run --python 3.13 python scripts/verify_release.py \
  --profile runtime \
  --json docs/release-results/0.20.1/runtime-python-3.13.json
uv run --python 3.13 python scripts/verify_release.py \
  --profile full \
  --json docs/release-results/0.20.1/full-python-3.13.json
```

**Resultado:** los cuatro perfiles terminaron con `status = "ok"`. Cada perfil
runtime completó metadata, lockfile, seguridad y calidad. El perfil full añadió
fuentes normativas, simulaciones, persistencia y auditoría de paquete. Los JSON
ya conservados coincidieron con el resultado generado, por lo que no fue
necesario modificarlos.

## Suite completa, tipos y cobertura

### Pytest

```bash
uv run --python 3.13 python -m pytest -q
```

**Resultado:** `635 passed, 785 subtests passed`.

### Mypy

```bash
uv run --python 3.13 python -m mypy src/card_duel_engine
```

**Resultado:** `Success: no issues found in 42 source files`.

### Coverage con ramas

```bash
uv run --python 3.13 python -m coverage erase
uv run --python 3.13 python -m coverage run --branch \
  -m unittest discover -s tests -v
uv run --python 3.13 python -m coverage report
```

**Resultado:** cobertura total mostrada del **89 %**. La ejecución respetó
`branch = true` y superó `fail_under = 88` de `pyproject.toml`. Los perfiles de
release registraron un total formateado del **88,0 %**, también aceptado por el
umbral configurado.

## Pruebas focales

Se ejecutaron juntas las pruebas focales de CAS, privacidad, persistencia,
replay, engine y simulación:

```bash
uv run --python 3.13 python -m pytest -q \
  tests/test_expected_version_contract.py \
  tests/test_new_match_transaction.py \
  tests/test_authenticated_application_r06.py \
  tests/test_ui_integration_contract_phase_1c.py \
  tests/test_hardening_v0100.py \
  tests/test_public_card_catalog.py \
  tests/test_presentation.py \
  tests/test_persistence_v090.py \
  tests/test_replay_legacy_019.py \
  tests/test_replay_legacy_020_profile.py \
  tests/test_setup_and_phases.py \
  tests/test_resources_and_zones.py \
  tests/test_stack_and_priority.py \
  tests/test_combat_and_legendary.py \
  tests/test_advanced_mechanics.py \
  tests/test_simulation.py
```

**Resultado:** `181 passed, 347 subtests passed`.

También se ejecutaron directamente las comprobaciones especializadas:

```bash
uv run --python 3.13 python scripts/verify_headless_simulations.py
uv run --python 3.13 python scripts/verify_persistence_roundtrips.py
```

**Resultados:** 300 simulaciones, 54.000 comandos y 84.000 eventos; 30 pares
snapshot/replay verificados.

## Metadata, release, seguridad y fuentes normativas

```bash
uv lock --check
uv run --python 3.13 python -m pytest -q tests/test_release_metadata.py
uv run --python 3.13 python scripts/verify_release_metadata.py
uv run --python 3.13 python scripts/verify_repository_security.py
uv run --python 3.13 python scripts/verify_rules_sources.py
```

**Resultados:**

- lockfile resuelto sin cambios;
- `16 passed, 36 subtests passed` en metadata de release;
- coincidencia exacta de `0.20.1` en `pyproject.toml`, `uv.lock`, changelog,
  alcance del README y validación;
- checkout aceptado por la inspección de seguridad;
- ambos PDF normativos aceptados por la verificación de fuentes.

Una comprobación adicional resolvió `0.20.1` desde `project.version`,
`scripts.project_metadata.read_project_version`,
`card_duel_engine.__version__` y `RuleSet().version`. No cambió la versión ni
ninguna fuente de metadata.

## Higiene y auditoría del diff

```bash
git diff --check
git diff --name-status \
  3fe33c6ac8fce6997036bdc36717f0e0fb481b4d...HEAD
git diff --no-ext-diff --unified=3 \
  3fe33c6ac8fce6997036bdc36717f0e0fb481b4d...HEAD
```

`git diff --check` terminó correctamente. La revisión completa del rango previo
a este informe mostró únicamente los ocho archivos esperados de documentación,
frontera de aplicación/servicio y pruebas:

```text
M  docs/FRONTEND_AND_CONTENT_ROADMAP.md
M  docs/UI_INTEGRATION_CONTRACT_0.20.1.md
M  src/card_duel_engine/application.py
M  src/card_duel_engine/service.py
A  tests/json_contract_helpers.py
M  tests/test_authenticated_application_r06.py
M  tests/test_public_card_catalog.py
A  tests/test_ui_integration_contract_phase_1c.py
```

Se realizó además una comparación por rutas protegidas. No hay cambios en:

- engine;
- modelos de dominio ni `CardDefinition`;
- reglas;
- persistencia ni replay;
- contenido de producción ni manifests;
- frontend;
- adaptadores de transporte;
- dependencias runtime o de desarrollo;
- `uv.lock`;
- versión del proyecto o sus consumidores.

Los cambios de `application.py` y `service.py` pertenecen a la frontera Python
en proceso documentada por Fase 1-C; no añaden HTTP, REST, WebSocket, Expo,
frontend ni otro transporte. No se detectó ningún cambio accidental que hubiera
que revertir.

## Veredictos

Todas las verificaciones requeridas terminaron satisfactoriamente. Por tanto se
registran los veredictos finales:

> **GO — PHASE 1-C COMPLETE**

> **GO — PHASE 1 COMPLETE**

