# Auditoría de reproducibilidad y contenido del wheel 0.20.1

Fecha de ejecución: 2026-08-27 (UTC).

## Procedimiento

La auditoría se ejecutó contra el commit inmutable
`c332170a39ac966af27e57390edff52ecd7dd617`, con el mismo procedimiento de
`scripts/verify_reproducible_wheel.py`:

1. se obtuvo el `SOURCE_DATE_EPOCH=1787824430` del commit;
2. se creó un worktree separado en modo `detached HEAD`;
3. se invocó dos veces `python -m build --wheel`, cada vez con un directorio de
   salida distinto y sin modificar `pyproject.toml` ni ninguna otra configuración;
4. se aplicó a cada wheel la función de auditoría del script;
5. se compararon tanto los SHA-256 como todos los bytes mediante `cmp`.

El script oficial también se ejecutó de principio a fin y produjo el mismo wheel
final en `dist/`, su `SHA256SUMS` y su informe JSON.

## Artefactos

Los nombres son iguales porque ambos builds corresponden a la misma distribución
y versión; los directorios `first/` y `second/` identifican cada ejecución.

| Build | Nombre de archivo | Tamaño | SHA-256 | Entradas ZIP |
| --- | --- | ---: | --- | ---: |
| primero | `card_duel_engine-0.20.1-py3-none-any.whl` | 91.596 bytes | `256932fdde8f88db181f1b050431483171b5119306814652d65bb3285db0614e` | 44 |
| segundo | `card_duel_engine-0.20.1-py3-none-any.whl` | 91.596 bytes | `256932fdde8f88db181f1b050431483171b5119306814652d65bb3285db0614e` | 44 |

Los SHA-256 coinciden. La comparación directa devolvió éxito (`cmp` con código
0), por lo que los dos archivos son idénticos byte a byte.

## Listado ordenado de entradas

Este orden se registró independientemente para ambos wheels y fue idéntico en los
dos casos:

1. `card_duel_engine/__init__.py`
2. `card_duel_engine/_version.py`
3. `card_duel_engine/application.py`
4. `card_duel_engine/catalog.py`
5. `card_duel_engine/service.py`
6. `card_duel_engine/content/__init__.py`
7. `card_duel_engine/content/manifest.py`
8. `card_duel_engine/content/registry.py`
9. `card_duel_engine/content/signature.py`
10. `card_duel_engine/controllers/__init__.py`
11. `card_duel_engine/controllers/base.py`
12. `card_duel_engine/domain/__init__.py`
13. `card_duel_engine/domain/enums.py`
14. `card_duel_engine/domain/errors.py`
15. `card_duel_engine/domain/models.py`
16. `card_duel_engine/engine/__init__.py`
17. `card_duel_engine/engine/actions.py`
18. `card_duel_engine/engine/combat.py`
19. `card_duel_engine/engine/commands.py`
20. `card_duel_engine/engine/effects.py`
21. `card_duel_engine/engine/game.py`
22. `card_duel_engine/engine/options.py`
23. `card_duel_engine/engine/phases.py`
24. `card_duel_engine/engine/stack.py`
25. `card_duel_engine/engine/zones.py`
26. `card_duel_engine/persistence/__init__.py`
27. `card_duel_engine/persistence/codec.py`
28. `card_duel_engine/persistence/migrations.py`
29. `card_duel_engine/persistence/replay.py`
30. `card_duel_engine/persistence/snapshot.py`
31. `card_duel_engine/rules/__init__.py`
32. `card_duel_engine/rules/config.py`
33. `card_duel_engine/rules/deck.py`
34. `card_duel_engine/rules/resolvers.py`
35. `card_duel_engine/simulation/__init__.py`
36. `card_duel_engine/simulation/agents.py`
37. `card_duel_engine/simulation/runner.py`
38. `card_duel_engine/storage/__init__.py`
39. `card_duel_engine/storage/base.py`
40. `card_duel_engine/storage/sqlite.py`
41. `card_duel_engine-0.20.1.dist-info/METADATA`
42. `card_duel_engine-0.20.1.dist-info/WHEEL`
43. `card_duel_engine-0.20.1.dist-info/top_level.txt`
44. `card_duel_engine-0.20.1.dist-info/RECORD`

## Auditoría de contenido

Resultado: **APROBADA**.

- Rutas bajo `benchmarks/`: ausentes.
- Archivos `*.pdf`: ausentes.
- Rutas bajo `tests/`: ausentes.
- Documentación interna de benchmarks: ausente.
- Rutas ajenas a `card_duel_engine/` y
  `card_duel_engine-0.20.1.dist-info/`: ausentes.
- Contenido permitido: exclusivamente los módulos Python de
  `card_duel_engine` y los cuatro metadatos necesarios (`METADATA`, `WHEEL`,
  `top_level.txt` y `RECORD`).
- Integridad de `RECORD`: aprobada; enumera exactamente las 44 entradas y sus
  tamaños y hashes son correctos.

## Resultado final

| Nombre final | SHA-256 | Entradas | Reproducible | Auditoría de contenido |
| --- | --- | ---: | --- | --- |
| `card_duel_engine-0.20.1-py3-none-any.whl` | `256932fdde8f88db181f1b050431483171b5119306814652d65bb3285db0614e` | 44 | **sí** | **APROBADA** |

