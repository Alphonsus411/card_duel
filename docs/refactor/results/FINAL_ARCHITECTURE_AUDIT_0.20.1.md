# Auditoría final de arquitectura — 0.20.1

## 1. Decisión e identificación

**GO.** La revisión estática, diferencial y ejecutable confirma la frontera
solicitada sin introducir optimizaciones.

- Fecha de cierre: **2026-08-13 UTC**.
- SHA base anterior a las tres extracciones:
  **`952b1759371eb9c591c7601d906547de4f508449`**.
- SHA final de código de implementación:
  **`5354163c23845e411ab44c2358b72f5dcb757410`**.
- SHA de paridad final de implementación:
  **`2c8a18789d742c242017a8df9afb209b94c1e0d4`**.
- SHA auditado y usado como procedencia del wheel:
  **`8885301cfb8ef47ba9288b0c5b6df950ccd2bcfc`**.
- El SHA de este informe se comunica fuera del propio documento para evitar una
  referencia circular.

## 2. Arquitectura resultante

El constructor de `GameEngine` crea tres colaboradores internos distintos con el
mismo motor como contexto:

```text
GameEngine -> LegalActionEnumerator
GameEngine -> PhaseManager
GameEngine -> ActionOptionResolver
```

No existe una dependencia `LegalActionEnumerator -> ActionOptionResolver` ni una
cadena equivalente que cambie esa topología. `GameEngine.legal_actions` delega la
enumeración general; las fachadas históricas de opciones delegan directamente en
`ActionOptionResolver`; y la ejecución de `AdvancePhase` entra desde el dispatcher
autoritativo del motor y delega únicamente la coordinación de transición a
`PhaseManager`.

Los tres colaboradores sólo guardan `_context`. No poseen una copia de
`GameState`, reglas, repositorio, reloj, cola de eventos ni identificadores propios.

## 3. Autoridad conservada en `GameEngine`

`GameEngine` sigue siendo la única autoridad de ejecución y la frontera pública
que recibe comandos. Conserva:

1. el dispatcher de comandos y la validación final;
2. la comprobación de prioridad y timing;
3. el cálculo autoritativo y pago de costes;
4. la revalidación autoritativa de targets;
5. la mutación de `GameState` y zonas;
6. la emisión ordenada de eventos;
7. la interacción autoritativa con stack y resolución;
8. la producción/restauración de datos persistibles mediante las fronteras ya
   existentes.

`LegalActionEnumerator` sólo construye comandos candidatos y su propia docstring
declara que no valida ni ejecuta. `ActionOptionResolver` sólo enumera opciones a
partir del contexto. `PhaseManager` coordina la transición, pero toda consulta,
cleanup, entrada de fase y emisión vuelve al motor; no adquiere estado de dominio.
Las pruebas diferenciales comparan estado y eventos y el perfil full incluye
simulaciones y roundtrips persistentes.

## 4. Funciones movidas y expresamente no movidas

### Movidas mecánicamente

| Grupo | Cuerpo extraído | Destino | Conteo |
|---|---|---|---:|
| Enumeración general | cuerpo anterior de `GameEngine.legal_actions` | `LegalActionEnumerator.legal_actions` | 1 |
| Fases | `advance_phase`, `_finish_turn`, `_enter_phase_or_skip` | `PhaseManager.advance_phase`, `finish_turn`, `enter_phase_or_skip` | 3 |
| Opciones | `_card_cost_options`, `_target_selections`, `_zone_target_selections`, `_allocation_selections`, `_positive_compositions` | cinco métodos equivalentes de `ActionOptionResolver` | 5 |
| **Total** |  |  | **9** |

Las fachadas privadas compatibles de las cinco opciones permanecen en
`GameEngine`; por tanto se movió su algoritmo, no se eliminó su punto interno de
entrada histórico.

### No movidas

Las ocho funciones prohibidas continúan definidas en
`src/card_duel_engine/engine/game.py`, tanto en la base como en el SHA final:

- `_legal_plays`;
- `_legal_ability_activations`;
- `_trigger_target_commands`;
- `_card_cost_for_option`;
- `_play_card`;
- `_activate_ability`;
- `_validate_effect_targets`;
- `_card_can_be_targeted`.

**Conteo: 8 de 8 confirmadas; 0 movidas.** Las apariciones homónimas en los
`Protocol` son contratos tipados de consulta, no implementaciones trasladadas.

## 5. Restricciones negativas

La comparación `952b175..2c8a187` y la inspección de los módulos confirman:

- **0** caches y **0** mecanismos de memoización nuevos;
- **0** cambios de evaluación eager a lazy en la API observable;
- **0** generadores públicos exportados: `positive_compositions` vive en una clase
  interna no reexportada y conserva exactamente el generador privado preexistente;
- **0** podas o heurísticas nuevas; se conservan límites, orden, `islice`,
  `combinations` y `product`;
- **0** cambios en llamadas o política de `deepcopy`;
- **0** cambios a los `__init__.py` exportadores y, por ello, **0** cambios de API
  pública;
- **0** referencias o integración AGIX nuevas.

## 6. Archivos de la implementación

La frontera funcional y sus pruebas está formada por:

```text
src/card_duel_engine/engine/actions.py
src/card_duel_engine/engine/game.py
src/card_duel_engine/engine/options.py
src/card_duel_engine/engine/phases.py
tests/test_legal_action_enumerator_parity.py
tests/test_phase_manager_parity.py
tests/test_action_option_resolver_parity.py
```

La serie también añadió sus diagnósticos e informes bajo `docs/refactor/` y ajustó
la infraestructura de desarrollo/release (`pyproject.toml`, `uv.lock`,
`scripts/verify_release.py` y sus pruebas) para incluir la evidencia. El diff
completo base–paridad tiene **20 archivos, 3.844 inserciones y 281 eliminaciones**;
la mayoría son pruebas e informes. Este cierre añade únicamente el presente
informe y no modifica código, fixtures, snapshots, PDF ni artefactos de release.

## 7. Resultados y conteos reproducibles

Tras sincronizar exactamente el lockfile, el perfil `full` terminó con
`status=ok` y ocho etapas correctas:

| Evidencia | Resultado |
|---|---:|
| Cobertura branch integral | 89 % (mínimo 88 %) |
| mypy / compileall | OK / OK |
| Fuentes normativas | 2 verificadas |
| Simulaciones | 300 |
| Comandos simulados | 54.000 |
| Eventos observados | 84.000 |
| Roundtrips persistentes | 30 |
| Python de instalación del wheel | 3.11, 3.12 y 3.13 |
| Archivos Python analizados por seguridad | 90 |
| Archivos versionados escaneados | 150 |

El primer intento del perfil full falló antes de ejecutar la verificación porque
el entorno virtual no tenía `mypy`. `uv sync --locked --extra dev` instaló las
dependencias bloqueadas; la repetición exacta terminó con código 0. No se cambió
código ni se relajó ninguna política para resolver esa limitación ambiental.

## 8. Wheel, PDF e informes

- Wheel: `card_duel_engine-0.20.1-py3-none-any.whl`.
- SHA-256: `9f79daaa5fe527c7a7d322ae95dd4168fbc3ff593fb7a3bed098a3ab58c28b9c`.
- Dos builds comparados y binariamente idénticos.
- 44 entradas, `RECORD` íntegro, `py3-none-any`, purelib, sin dependencias runtime,
  fixtures, cartas de producción ni PDF.
- Procedencia: worktree detached limpio del SHA auditado.

| PDF normativo | SHA-256 | Estado |
|---|---|---|
| `Fantasy Tokens.pdf` | `1c51dabe2023626ad532368e2567d2084c47ec137c7a738bd8c0e0b707f86b21` | idéntico, no modificado |
| `Fantasy Tokens Edicion Mitica.pdf` | `61243b30d219dd12d8897a206ed664d95a5e3c38b6670a818933f6d90904af36` | idéntico, no modificado |

Los informes detallados anteriores permanecen en:

- `LEGAL_ACTIONS_REFACTOR_RESULTS_0.20.1.md` y
  `LEGAL_ACTIONS_FINAL_VALIDATION_0.20.1.md`;
- `PHASE_MANAGER_REFACTOR_RESULTS_0.20.1.md` y
  `PHASE_MANAGER_PARITY_CLOSURE_0.20.1.md`;
- `ACTION_OPTION_RESOLVER_REFACTOR_RESULTS_0.20.1.md`.

## 9. Hotspots y única recomendación posterior

Los hotspots ya caracterizados están en la enumeración combinatoria:

1. `combinations` de targets, descartes y sacrificios;
2. `product` al construir comandos candidatos;
3. `islice` y el límite de enumeración, cuyo orden es observable;
4. rangos de X y composiciones positivas para asignaciones distribuidas.

Para una iteración posterior se recomienda **únicamente crear benchmarks de esos
cuatro hotspots ya medidos/caracterizados**, conservando corpus, límites, orden y
perfiles semánticos. Esta rama no implementa caching, memoización, lazy evaluation,
poda, heurísticas ni ninguna otra optimización.
