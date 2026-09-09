# CAP-ACTION-004 traceability — 2026-09-07

## Control record

```yaml
version: 0.20.1
phase_2c: IN_PROGRESS
phase_3: PENDING
status: MISSING
gate: READY
contract_status: READY
runtime_authorization: FORBIDDEN
task_baseline_sha: 9543806234a1b5af47dc1e40514323b2c5fc4324
report_input_sha: f80bc858221c8842dbe9ce0542e8a93b2141bfb6
audited_task_head_sha: c878265d96c7ed44269cce9ec0b855746b2e62d9
files:
  modified:
    - docs/audits/PHASE_2C_CAP_ACTION_004_CONTRACT_AUDIT_2026-09-07.md
  added:
    - docs/audits/PHASE_2C_CAP_ACTION_004_TRACEABILITY_2026-09-07.md
```

`task_baseline_sha` es el inicio de la tarea completa. `report_input_sha` es el
`HEAD` anterior a la última subentrega de informes. `audited_task_head_sha` es el
estado acumulado auditado antes de esta microcorrección; constituye evidencia
histórica y no intenta referenciar el commit que contiene la corrección actual,
evitando así una autorreferencia imposible. Todas las filas trazan un requisito
individual y no afirman implementación runtime.

## Alcance de los compares

El diff acumulado de la tarea
`9543806234a1b5af47dc1e40514323b2c5fc4324 → c878265d96c7ed44269cce9ec0b855746b2e62d9`
abarca exactamente dependencias (`docs/ENGINE_CAPABILITY_DEPENDENCIES.md`),
roadmap (`docs/PHASE_2C_ENGINE_EVOLUTION_ROADMAP.md`), ambos informes de
auditoría (`docs/audits/PHASE_2C_CAP_ACTION_004_CONTRACT_AUDIT_2026-09-07.md` y
`docs/audits/PHASE_2C_CAP_ACTION_004_TRACEABILITY_2026-09-07.md`) y el test
documental (`tests/test_phase_2c_engine_evolution_roadmap.py`).

En cambio, el diff específico de la última subentrega documental
`f80bc858221c8842dbe9ce0542e8a93b2141bfb6 → c878265d96c7ed44269cce9ec0b855746b2e62d9`
abarca exclusivamente los dos informes de auditoría citados. Este segundo
conjunto es un **`report-only diff`** y no representa el diff acumulado de toda
la tarea. Ninguno de los dos compares incluye rutas bajo
`src/card_duel_engine/`.

## Requirement traceability matrix

| Requisito | Evidencia | Capability | Invariante | Superficie futura | Test | Estado |
|---|---|---|---|---|---|---|
| Baseline: SHA de tarea/input/estado auditado | Control record y audit identity | `CAP-ACTION-004` | — | Git/documentación | `git rev-parse HEAD`; status/diff | `PASS` |
| Baseline: versión/fases/status/gate | `pyproject.toml`, `uv.lock`, roadmaps y matriz | `CAP-ACTION-004` | — | Release/roadmap | test documental Phase 2C | `PASS` |
| Mecanismo `PendingSearch` | Matriz forense; models/stack/options/game/codec | `CAP-SEARCH-001`; `CAP-ACTION-004` | INV-01/03/04/05/08/09/10 | Modelo, engine, snapshot, replay | Auditoría estática + suite existente | `PASS` |
| Mecanismo `PendingMoveReplacement` | Matriz forense; models/zones/game/codec | `CAP-ZONE-004`; `CAP-ACTION-004` | INV-01/03/04/05/06/09/10 | Modelo, zones, transacción | Auditoría estática + suite existente | `PASS` |
| Targets play/ability | Matriz forense; commands/options/stack | `CAP-TARGET-001` | INV-03/04/14 | Commands, targeting | Auditoría estática | `PASS` |
| Targets de triggers | Matriz forense; pending triggers/options | `CAP-TRIGGER-001` | INV-03/04/05/14 | Stack, options | Auditoría estática | `PASS` |
| Orden de triggers | Matriz forense; `OrderTriggeredAbilities` | `CAP-TRIGGER-001` | INV-03/04/05/14 | Stack, commands | Auditoría estática | `PASS` |
| Orden persistente de replacements | Matriz forense; `SetReplacementOrder` | `CAP-ZONE-004` | INV-14 | Zones, commands | Auditoría estática | `PASS` |
| Action option IDs | Matriz forense; application/service | `CAP-ACTION-002`; `CAP-PRIVACY-001` | INV-03/04/07/08 | Application, service | Auditoría estática | `PASS` |
| Contrato universal/campos autoritativos | Tabla de contrato universal | `CAP-ACTION-004` | INV-01–14 | Todas las superficies W0 | Validación de términos | `PASS` |
| `CAP-ACTION-004-INV-01` fuente única | Tabla de invariantes | `CAP-ACTION-004` | `CAP-ACTION-004-INV-01` | Modelo/persistencia | Futuro contract/property | `TRACED` |
| `CAP-ACTION-004-INV-02` identidad estable | Tabla de invariantes | `CAP-ACTION-004` | `CAP-ACTION-004-INV-02` | Modelo/API/replay | Futuro golden replay | `TRACED` |
| `CAP-ACTION-004-INV-03` elector único | Tabla de invariantes | `CAP-ACTION-004` | `CAP-ACTION-004-INV-03` | Commands/service | Futuro auth negative | `TRACED` |
| `CAP-ACTION-004-INV-04` opción autorizada | Tabla de invariantes | `CAP-ACTION-004` | `CAP-ACTION-004-INV-04` | Validation/API | Futuro token fuzz | `TRACED` |
| `CAP-ACTION-004-INV-05` cierre único | Tabla de invariantes | `CAP-ACTION-004` | `CAP-ACTION-004-INV-05` | Transaction/replay | Futuro idempotency/race | `TRACED` |
| `CAP-ACTION-004-INV-06` rechazo inmutable | Tabla de invariantes | `CAP-ACTION-004` | `CAP-ACTION-004-INV-06` | App/service/storage | Futuro rollback property | `TRACED` |
| `CAP-ACTION-004-INV-07` CAS loser | Tabla de invariantes | `CAP-ACTION-004` | `CAP-ACTION-004-INV-07` | Storage/concurrency | Futuro two-client race | `TRACED` |
| `CAP-ACTION-004-INV-08` audiencia | Tabla de invariantes/privacidad | `CAP-ACTION-004` | `CAP-ACTION-004-INV-08` | Projections/API | Futuro non-interference | `TRACED` |
| `CAP-ACTION-004-INV-09` snapshot fiel | Tabla de invariantes/histórico | `CAP-ACTION-004` | `CAP-ACTION-004-INV-09` | Snapshot/codec | Futuro round-trip | `TRACED` |
| `CAP-ACTION-004-INV-10` replay fiel | Tabla de invariantes/histórico | `CAP-ACTION-004` | `CAP-ACTION-004-INV-10` | Replay/events | Futuro golden legacy/new | `TRACED` |
| `CAP-ACTION-004-INV-11` versión desconocida | Tabla de invariantes/histórico | `CAP-ACTION-004` | `CAP-ACTION-004-INV-11` | Codec/service | Futuro unknown-version | `TRACED` |
| `CAP-ACTION-004-INV-12` sin wall-clock | Tabla de invariantes | `CAP-ACTION-004` | `CAP-ACTION-004-INV-12` | Jobs/storage/replay | Futuro deterministic clock | `TRACED` |
| `CAP-ACTION-004-INV-13` familia, no carta | Tabla de invariantes | `CAP-ACTION-004` | `CAP-ACTION-004-INV-13` | Handler registry | Futuro dispatch contract | `TRACED` |
| `CAP-ACTION-004-INV-14` cierre sin mecánica | Tabla de invariantes | `CAP-ACTION-004` | `CAP-ACTION-004-INV-14` | Events/composition | Futuro separation test | `TRACED` |
| Arista `CAP-ACTION-002 → CAP-ACTION-004` | Dependency edges; matriz/dependencias | `CAP-ACTION-002`; `CAP-ACTION-004` | INV-04 | Options/validation | Test reciprocidad | `PASS` |
| Arista `CAP-PRIVACY-001 → CAP-ACTION-004` | Dependency edges; matriz/dependencias | `CAP-PRIVACY-001`; `CAP-ACTION-004` | INV-08 | Projection/API | Test reciprocidad | `PASS` |
| Arista `CAP-ACTION-004 → CAP-SECRET-002` | Dependency edges; matriz/dependencias | `CAP-ACTION-004`; `CAP-SECRET-002` | INV-13/14 | Secret specialization | Test reciprocidad | `PASS` |
| Arista `CAP-ACTION-004 → CAP-TIME-002` | Dependency edges/readiness | `CAP-ACTION-004`; `CAP-TIME-002` | INV-05 | Setup/mulligan | Test reciprocidad | `PASS` |
| Compatibilidad snapshot legacy | Histórico: legacy produce `None` | `CAP-ACTION-004` | INV-09/11 | Snapshot/codec | Futuro legacy fixture | `TRACED` |
| Compatibilidad replay legacy/nuevo | Histórico: decoder declarado, no reescritura | `CAP-ACTION-004` | INV-02/10/11 | Replay/events | Futuro golden pair | `TRACED` |
| Migración histórica | W0 e histórico: explícita/transaccional/idempotente | `CAP-ACTION-004` | INV-01/06/09 | SQLite/stores | Futuro migration property | `TRACED` |
| Privacidad del elector | Tabla de audiencias | `CAP-PRIVACY-001`; `CAP-ACTION-004` | INV-08 | DTO/projection | Futuro visibility positive | `TRACED` |
| Privacidad adversario/público | Tabla de audiencias y error uniforme | `CAP-PRIVACY-001`; `CAP-ACTION-004` | INV-08 | API/log/replay | Futuro non-interference | `TRACED` |
| CAS exactly-once | Sección CAS | `CAP-ACTION-003`; `CAP-ACTION-004` | INV-05/06/07 | Store/service | Futuro carrera dos clientes | `TRACED` |
| Modelos existentes independientes | Existing-model strategy | `CAP-ACTION-004` | INV-01/10/14 | Models/snapshot/replay | Futuro equivalence gate | `TRACED` |
| Matriz W0 completa | W0 impact matrix | `CAP-ACTION-004` | INV-01–14 | 13 superficies | Revisión de vocabulario | `PASS` |
| Planificación sin implementación | Implementation planning | `CAP-ACTION-004` | INV-01–14 | W0/W1 futuro | Diff paths | `PASS` |
| Prohibición de cambios runtime | Files changed; `runtime_authorization: FORBIDDEN` | `CAP-ACTION-004`; `CAP-TIME-002` | INV-14 | `src/`, runtime tests | `git diff --name-only` | `PASS` |
| Blockers de mulligan inalterados | Remaining blockers/readiness | `CAP-TIME-002`; `CAP-TIME-005` | — | Setup/mulligan futuro | Test documental Phase 2C | `PASS` |
| Resultado de verificaciones reales | Real verification results: 13 tests y perfil full | `CAP-ACTION-004` | — | Documentación | Comandos capturados tras edición | `PASS` |
| Veredicto final exacto | Última línea del contract audit | `CAP-ACTION-004` | INV-01–14 | Gate documental | Validación shell exacta | `PASS` |

## Status semantics

- `PASS`: evidencia documental vigente comprobada en esta entrega.
- `TRACED`: obligación futura individualizada; no afirma runtime existente.
- `PENDING`: sólo se usaría antes de ejecutar el comando real; no quedan filas
  pendientes tras las verificaciones capturadas.

No hay filas `IMPLEMENTED`: `CAP-ACTION-004` continúa `MISSING` y
`runtime_authorization` continúa `FORBIDDEN`.
