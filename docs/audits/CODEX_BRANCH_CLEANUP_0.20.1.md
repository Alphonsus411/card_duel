# Limpieza auditada de ramas Codex — 0.20.1

## Identidad

| Campo | Valor |
|---|---|
| Repositorio | `Alphonsus411/card_duel` |
| Fecha UTC | `2026-08-28` |
| `BASE_MAIN_SHA` | `16d2c09464d801662490b699b490f404e3f82a1e` |
| Rama de auditoría | `maintenance/cleanup-codex-branches-0.20.1` |
| Final documentation SHA | **No se incrusta para evitar circularidad: el identificador autoritativo es el SHA del commit que contiene este documento; ese mismo SHA se registra en la descripción de la PR.** |

## Estado inicial

Se ejecutó `git fetch --prune origin` y se excluyó únicamente una eventual referencia simbólica `origin/HEAD` de los conteos.

| Dato | Valor |
|---|---:|
| Ramas remotas totales | 169 |
| Ramas `codex/*` | 167 |
| SHA leído de `Bella-2.0` | `851bc963692c7c2e0e70d34c8e09b67781da1ac4` |
| PR abiertas | 0 |

## Metodología y salvaguardas

1. Se fijó `BASE_MAIN_SHA` antes de clasificar o intentar borrar.
2. Para cada `codex/*` se ejecutó `git merge-base --is-ancestor <tip> origin/main`; sólo exit `0` habilita A. Todo exit distinto de `0` obliga a conservar.
3. Se ejecutó `git rev-list --left-right --count origin/main...<tip>`: la columna izquierda se registra como `behind_by` y la derecha como `ahead_by`.
4. Para tips no ancestrales, `git cherry origin/main <tip>` sólo distinguió B (todos los parches equivalentes); nunca habilitó un borrado.
5. Antes de cada borrado previsto debían releerse por `git ls-remote --heads` el SHA exacto de la rama y el SHA de `main`, exigir coincidencia literal con inventario/base y repetir la prueba de ancestralidad. Esta doble validación se completó para el único intento.
6. La API pública de GitHub se consultó antes de borrar. Toda coincidencia con una PR abierta prevalecería como `KEEP_OPEN_PR`; se observaron 0 PR abiertas y 0 coincidencias.
7. El primer `git push origin --delete` falló por ausencia de credenciales HTTPS. Se registró `DELETE_FAILED` y se detuvo el lote para no presentar intentos destinados al mismo fallo global como eliminaciones.

## Categorías A, B, C, D y E

### A — SAFE_TO_DELETE
161 ramas ancestrales. Resultado operativo: 0 eliminadas; 1 `DELETE_FAILED` y 160 no intentadas tras el fallo global.

### B — PATCH_EQUIVALENT_ONLY
2 ramas no ancestrales cuyos parches son equivalentes. Se conservan siempre.

### C — UNMERGED
0 ramas no integradas sin divergencia. Se conservarían siempre.

### D — DIVERGED / UNCERTAIN
4 ramas con historia divergente o incierta. Se conservan siempre.

### E — SPECIAL
1 rama especial (`Bella-2.0`). Se conserva sin analizar ni tocar.

## Inventario completo

`ahead_by` y `behind_by` se muestran en el orden semántico solicitado, aunque la salida bruta de `rev-list --left-right --count` sea izquierda=`behind_by`, derecha=`ahead_by`.

| Rama | Tip SHA | Fecha | Asunto | exit ancestralidad | `ahead_by` | `behind_by` | Categoría | Resultado |
|---|---|---|---|---:|---:|---:|---|---|
| `Bella-2.0` | `851bc963692c7c2e0e70d34c8e09b67781da1ac4` | — | — | — | — | — | E — SPECIAL | KEEP — UNTOUCHED |
| `codex/actualiza-allowed_content-y-mejora-validaciones` | `a5151b8947dab727e6d5773254a7cce1dde140dd` | 2026-08-01T11:21:08+02:00 | fix: sincronizar política de contenido del wheel | 0 | 0 | 248 | A — SAFE_TO_DELETE | KEEP/DELETE_FAILED |
| `codex/actualizar-acciones-en-tests.yml` | `70194f7862c80eb73acea65a9c8277ca09249b3e` | 2026-08-01T13:55:54+02:00 | ci: pin actions to Node 24 releases | 0 | 0 | 216 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/actualizar-backend-a-version-0.11.0` | `190bf8e9591daff284a690eb96dc5ef27feb3ba4` | 2026-07-23T10:13:12+02:00 | feat: advance backend to 0.11.0 | 0 | 0 | 330 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/actualizar-documentacion-y-mantener-requerimientos` | `c8ddf2f73bf050c8bf4ec030cff52c120dbc5829` | 2026-08-03T16:59:28+02:00 | docs: document 0.20.1 conformance corrections | 0 | 0 | 151 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/actualizar-documentacion-y-restricciones-en-reglas` | `2599d9c1638c19a15a47374897fa3dd73592ea8f` | 2026-08-02T12:25:24+02:00 | Align mythic rules traceability | 0 | 0 | 184 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/actualizar-documento-de-rollback-y-pruebas` | `00dd708cd27b57b35249d6f9580ba177f48e92c2` | 2026-08-03T16:39:36+02:00 | Parametrize rollback wheel selection | 0 | 0 | 153 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/actualizar-estado-de-r-04-en-readme.md` | `8dd6a0fd76d9d8ef510afbf1724a09ddf0e2d6bf` | 2026-07-31T12:13:26+02:00 | Align release roadmap metadata | 0 | 0 | 282 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/actualizar-flujo-de-trabajo-tests.yml` | `d0237df9e4398396e1fb025ccbdd24dccac6cb4b` | 2026-08-01T11:27:22+02:00 | ci: derive release artifact name from project metadata | 0 | 0 | 246 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/actualizar-gestion-de-versiones-en-el-proyecto` | `2eb7930a21e91247663fb671374254ebacfc2741` | 2026-08-01T11:38:37+02:00 | Derive release version from project metadata | 0 | 0 | 244 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/actualizar-historial-de-validacion-y-scripts` | `8369ee97482c4e18d3228960be44720fa6846f16` | 2026-08-04T10:37:32+02:00 | Archive release evidence by version | 0 | 0 | 125 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/actualizar-logica-de-acciones-legales-y-pruebas` | `eee04108308f89ba83ed6bce7f57d4b737441cf3` | 2026-07-30T11:11:38+02:00 | Handle terminal match views without legal actions | 0 | 0 | 310 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/actualizar-patrones-de-secretos-y-pruebas` | `d01d17d29e4f2367f831bcfaed785dd8db231e1d` | 2026-08-03T14:50:16+02:00 | Detect fine-grained GitHub tokens in security scan | 0 | 0 | 159 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/actualizar-patrones-de-seguridad-y-pruebas` | `2b0bd5a59551931ce221fadf6b8b599349141307` | 2026-08-03T15:40:47+02:00 | Tighten fine-grained GitHub token detection | 0 | 0 | 157 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/actualizar-reconstruccion-de-fuentes-en-snapshot.py` | `386f6f626d0ea35d4642506f170bdfa33a4720f0` | 2026-08-03T20:22:28+02:00 | Restore legacy ability source profiles deterministically | 0 | 0 | 143 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/actualizar-reglas-de-seguridad-y-pruebas` | `d1b4abdd49966a664fb8bd62bfea6f101f581dba` | 2026-08-04T09:26:37+02:00 | Refine fine-grained GitHub token boundary | 0 | 0 | 129 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/actualizar-reglas-en-documentacion` | `80f0acce19fc167367248d4a2903b5bb3d7d0185` | 2026-07-31T19:20:05+02:00 | docs: actualiza pendientes de R-04 y R-06 | 0 | 0 | 264 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/actualizar-roadmap.md-y-documentacion-asociada` | `d20a094a457f3f65cc9e2a8f1960d6dc99cba716` | 2026-07-30T13:53:16+02:00 | Actualiza el estado de la hoja de ruta | 0 | 0 | 302 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/actualizar-script-de-benchmark-para-guardar-resultados` | `c39a5642fce2e03b314e79c9b4d83181dee8690c` | 2026-08-14T13:47:49+02:00 | Add reproducible benchmark reports and profiles | 0 | 0 | 55 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/actualizar-version-a-0.20.0-en-pyproject.toml` | `261b46ae497fe9335bd9c2eadf81ace8d6160eef` | 2026-08-02T10:32:23+02:00 | release: prepare version 0.20.0 | 0 | 0 | 198 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/actualizar-version-y-regenerar-uv` | `ce2ba1af55ff3976e2b27afa4bd39cbf655634b6` | 2026-08-02T13:31:33+02:00 | release: prepare version 0.20.1 | 0 | 0 | 180 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/actualizar-version-y-sincronizar-archivos` | `98d0c23552ee5935568d80a632413dbf17c928f5` | 2026-08-03T14:36:00+02:00 | Synchronize 0.20.1 release metadata | 0 | 0 | 161 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/add-engine-semantics-handling-in-replay` | `7624a27bd06e5e6e5758851427de4c916ea3fe27` | 2026-08-03T20:40:04+02:00 | Preserve engine semantics in replay logs | 0 | 0 | 141 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/add-immutable-tuple-executable_command_types` | `4d3f4a84d071647524d09dade8150af02a7d19d9` | 2026-08-01T12:12:11+02:00 | Add closed executable command registry | 0 | 0 | 236 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/add-legacy-state-digest-extraction-and-comparison` | `f823dc4edd6a34e92b7524d2e8c47e900a2ffc5c` | 2026-08-03T19:53:19+02:00 | Support pre-source-profile 0.20 replay digests | 0 | 0 | 147 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/add-r-06-specifications-to-architecture.md` | `3c1b50595e69418a5bc1237d9b806a7f85345a7d` | 2026-07-30T17:52:47+02:00 | Add authenticated application boundary for R-06 | 0 | 0 | 290 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/add-section-estado-posterior-de-la-decision` | `6e9f9f2aac61e7a415f7866ab52c86edbeeb308e` | 2026-08-13T11:05:16+02:00 | docs: aclarar estado posterior del diagnóstico | 0 | 0 | 91 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/agregar-pruebas-para-targeting-local-cache` | `4aa6cccceeff6d7cb22a052422ab4080829d61a2` | 2026-08-23T08:45:27+02:00 | Merge pull request #151 from Alphonsus411/codex/corrige-errores-en-la-prueba-de-paridad | 1 | 2 | 43 | B — PATCH_EQUIVALENT_ONLY | KEEP |
| `codex/amplia-la-validacion-de-match_id` | `0c811859ecfe9b3e960f54a07e607097b46f7cdb` | 2026-07-31T20:37:31+02:00 | Harden match identifier validation | 0 | 0 | 256 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/ampliar-documentacion-de-reglas-y-creacion-de-catalogo` | `7ec4495e9f65a739743e1000d5cd828cdc8dd3d8` | 2026-08-02T09:34:32+02:00 | docs: ampliar trazabilidad de reglas Míticas | 0 | 0 | 206 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/anadir-benchmarks-para-gameengine` | `15a30ab9446f7a51b4162380b1bf898bdc64f5f2` | 2026-08-14T12:11:46+02:00 | Expand legal action engine benchmarks | 0 | 0 | 57 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/anadir-capacidad-can_challenge-y-pruebas-asociadas` | `3b7654dccbf3f5be00b7862404a5a41218dc8e08` | 2026-08-02T12:13:50+02:00 | Add declarative challenge capability | 0 | 0 | 186 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/anadir-casos-de-prueba-para-actionoptionresolver` | `96464ec9bf9f5099650ae223aa45fd9a75ebf907` | 2026-08-14T11:08:57+02:00 | Expand action option microbenchmarks | 0 | 0 | 59 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/anadir-casos-de-prueba-para-ruleset` | `1bf4e15edeb4860bb2cc600ffb5c08a3f8399c44` | 2026-08-12T19:26:19+02:00 | test: characterize small legal action limits | 0 | 0 | 109 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/anadir-engine_semantics-a-snapshots` | `e73c2e82d303be1203a32587ffc411b40219ead0` | 2026-08-03T20:08:27+02:00 | Persist engine semantics in snapshots | 0 | 0 | 145 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/anadir-entrada-de-deuda-arquitectonica` | `5b59aacbe8913d46f81f64be9687885dbea47d0b` | 2026-08-01T12:17:23+02:00 | docs: registrar deuda de alternativas legales remotas | 0 | 0 | 234 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/anadir-matriz-diferencial-de-cierre-a-documentacion` | `e2931504c5ef883e1da6285fd23476a8bac4e31e` | 2026-08-13T11:39:18+02:00 | docs: add phase manager closure matrix | 0 | 0 | 89 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/anadir-prueba-e2e-para-reemplazo-diferido` | `f0e67995a98187e2314fe5b9a52fb8f4f61371d1` | 2026-07-30T14:26:26+02:00 | test: cover replay of deferred replacements | 0 | 0 | 298 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/anadir-pruebas-en-test_legal_action_enumerator_parity` | `c7e7539e1f2b21bc0c5303daad1b05f029a1e14c` | 2026-08-12T20:34:57+02:00 | test: cover legal action privacy boundaries | 0 | 0 | 107 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/anadir-pruebas-en-tests/test_new_match_transaction.py` | `694e20c657065ba1a1109ffb3aa16b89977bdc69` | 2026-08-01T13:43:01+02:00 | Test atomic new match failures | 0 | 0 | 220 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/anadir-pruebas-y-paralelizar-verificaciones-legales` | `2c8a18789d742c242017a8df9afb209b94c1e0d4` | 2026-08-13T15:43:44+02:00 | test resolver legal action parity scenarios | 0 | 0 | 73 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/anadir-seccion-decision-en-phase_manager_diagnostic` | `b69c3ef6ed9b3c9b0235f1887b8f2a1b38e3c4cd` | 2026-08-13T09:22:24+02:00 | docs: decide phase manager diagnostic | 0 | 0 | 97 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/auditar-artefactos-de-construccion-de-wheels` | `27c561a2e8bd576c7cec2def4a3ccd3f5744bf71` | 2026-08-27T13:04:07+02:00 | docs: record reproducible wheel audit | 0 | 0 | 21 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/auditar-y-corregir-logica-de-drenaje` | `7510bd5f5e4bc82630bb3efab7f02956dc04d32c` | 2026-08-02T09:57:39+02:00 | Corrige Drenaje y objetivos Divinos | 0 | 0 | 202 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/auditar-y-crear-pruebas-para-motor-de-juego` | `2dfb02b4f528dc54b5d04499f6daf218ae4c8432` | 2026-08-02T10:12:43+02:00 | Ajusta Señores y Desafío a la fase activa | 0 | 0 | 200 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/automatiza-revision-y-creacion-de-pr` | `85753dc8a9313840fbef554c50119cfd9b6efe31` | 2026-08-01T12:40:54+02:00 | Corrige CI de release y endurece contratos técnicos | 0 | 0 | 228 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/avanza-en-la-hoja-de-ruta-del-proyecto` | `b1f1e88076a6982cad25c424a66df7370bcdc35b` | 2026-07-30T12:52:10+02:00 | Bloquea finales multijugador sin reglas definidas | 0 | 0 | 304 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/capturar-perfil-de-acciones-legales-con-cprofile` | `6f1f5e9a3e67005526b7522ab1b16f75599e9d8b` | 2026-08-23T09:54:13+02:00 | Merge pull request #152 from Alphonsus411/codex/fix-issues-from-codex-review-#146 | 1 | 2 | 35 | D — DIVERGED / UNCERTAIN | KEEP |
| `codex/confirmar-y-auditar-implementacion-de-0.20.1` | `e996a20c65a3ebe6cb3b49603a80da9e31e0bad3` | 2026-08-02T15:09:16+02:00 | docs: audit 0.20.1 conformance | 0 | 0 | 178 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/confirmar-y-auditar-implementacion-de-0.20.1-6qor6d` | `431f6ae3d408c6034954e8ecf7c56d873eec6706` | 2026-08-03T10:35:15+02:00 | Merge branch 'main' into codex/confirmar-y-auditar-implementacion-de-0.20.1-6qor6d | 0 | 0 | 175 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/conservar-historia-en-conformance-review` | `bdcf997d8bea5a5c954cc08eef5a542a296f7abf` | 2026-08-04T13:31:44+02:00 | docs: cerrar revisión de conformidad 0.20.1 | 0 | 0 | 123 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/consulta-hilos-de-revision-de-prs` | `e6b51b795ae960a366e9eea56f29a0131a422ea8` | 2026-08-04T15:07:29+02:00 | Audit review threads and restore CI provenance | 0 | 0 | 119 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/consultar-configuracion-de-repositorio-en-github` | `aa3447c819e3858ae6be0f9244b9c98bc5c66d72` | 2026-08-28T08:54:09+02:00 | docs: refresh main and 0.20.1 audit | 0 | 0 | 13 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/consultar-reglas-de-proteccion-y-estado-de-repositorio` | `c348734c39307132e6a31d7bb0295e03d8ec4251` | 2026-08-27T20:26:44+02:00 | docs: audit main governance and 0.20.1 release | 0 | 0 | 17 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/consultar-y-clasificar-pr-abiertas` | `1cbd45c1470f31cf284a23d5f75da78a55718e5d` | 2026-08-28T14:42:55+02:00 | docs: audit open PRs and main governance | 0 | 0 | 5 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/corrige-defectos-de-la-edicion-mitica` | `0edc513c974e296fabb579ee3096b89459c29be7` | 2026-08-03T11:03:47+02:00 | docs: sincroniza elegibilidad actual de Desafío | 0 | 0 | 173 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/corrige-errores-de-revision-de-codex` | `9c627ed6b94cebdc1408f5e6033e9b209d5d5fb0` | 2026-08-22T16:37:34+02:00 | Reject unregistered cards from collection registries | 1 | 1 | 315 | D — DIVERGED / UNCERTAIN | KEEP |
| `codex/corrige-errores-en-la-prueba-de-paridad` | `20248530cbeaefc52b44d9adfbc8bb7d82cb7422` | 2026-08-23T08:39:57+02:00 | test: register targeting cache parity with unittest | 1 | 1 | 43 | B — PATCH_EQUIVALENT_ONLY | KEEP |
| `codex/corrige-la-hoja-de-ruta-y-documentacion` | `b6b61c93ca5ab018f750fbddde387f293646f520` | 2026-07-31T20:15:26+02:00 | Align R-07.2 release status | 0 | 0 | 260 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/crear-actionoptioncontext-y-actionoptionresolver` | `d830d7282544f1156996d188ed931b74d12c15b4` | 2026-08-13T13:22:27+02:00 | Add typed action option context | 0 | 0 | 81 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/crear-archivo-mythic_rules_audit.md` | `d63f0eede006efd32c9bc9c03815c6810cae4a5b` | 2026-08-02T09:26:04+02:00 | docs: audit mythic rules sources | 0 | 0 | 208 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/crear-benchmark-de-accion-con-cli-y-mediciones` | `4a6d932ab0e4a4d3e8f27fd5e03418e400167f1f` | 2026-08-14T10:56:27+02:00 | Add deterministic action options benchmark runner | 0 | 0 | 61 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/crear-commit-y-actualizar-informe-de-evidencia` | `8d878c23dc0af0b8e8e509b6eede6c82bd3b03bd` | 2026-08-13T20:08:17+02:00 | docs: record final resolver wheel evidence | 0 | 0 | 67 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/crear-documentacion-de-refactorizacion` | `6cbf6d7ccea106a33dde012af49530d607e29776` | 2026-08-13T17:22:31+02:00 | docs: record action option resolver refactor | 0 | 0 | 71 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/crear-documentacion-de-rendimiento-y-comparacion` | `43b5060ee6761b7aa817904c3888568d7e13d613` | 2026-08-15T11:02:59+02:00 | docs: record post-targeting performance baseline | 0 | 0 | 31 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/crear-documento-de-auditoria-de-integracion` | `8b5154fa73301c601342942ae6cc3ea5cb8a2c66` | 2026-08-28T09:28:33+02:00 | docs: record audited integration content commit | 0 | 0 | 11 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/crear-documento-de-benchmarks-de-rendimiento` | `2695c1aae83a64a1bca6ce176d76bb90bd186b90` | 2026-08-14T14:12:27+02:00 | docs: document action option benchmark baseline | 0 | 0 | 53 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/crear-documento-para-auditoria-de-integracion` | `b8b163310efd41e3d13258e8e5bdcb12a6d5abb1` | 2026-08-28T06:10:27+02:00 | docs: record audited content commit | 0 | 0 | 15 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/crear-engineering_backlog.md-y-documentar-requisitos` | `bd8a2f55a8bfd6d2157ba1efa26edc56e79bdab1` | 2026-08-01T12:22:58+02:00 | docs: estructurar backlog tecnico | 0 | 0 | 232 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/crear-fixtures-de-benchmarks-con-constructores` | `cdf47c626e0c5b3c2d0e5edea0e2f03d0bd91c7a` | 2026-08-14T10:14:05+02:00 | Add deterministic benchmark scenario fixtures | 0 | 0 | 63 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/crear-informes-de-diagnostico-y-refactorizacion` | `0d28bb8cbb664f9a7353b512667e539e9d80ff1f` | 2026-08-12T20:42:11+02:00 | Merge pull request #110 from Alphonsus411/codex/anadir-pruebas-en-test_legal_action_enumerator_parity | 0 | 0 | 106 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/crear-informes-de-diagnostico-y-refactorizacion-cayjbe` | `ff0895697e3925135f103c4cab3d562c97659001` | 2026-08-13T06:01:02+02:00 | docs: document legal action refactor evidence | 0 | 0 | 105 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/crear-legalactioncontext-y-legalactionenumerator` | `206cd759f9aebd7d4a4ec24e5bf0e340689261a3` | 2026-08-12T17:17:46+02:00 | refactor: extract legal action enumeration | 0 | 0 | 115 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/crear-modulo-de-tests-para-adaptador-r-06` | `8ddd4a2ac935c0a0e6863ad7016b543860c93875` | 2026-07-31T11:08:19+02:00 | Expand R-06 authenticated adapter contract tests | 0 | 0 | 284 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/crear-rama-audit/phase-manager-parity-completion` | `6dc599f4df8aeede00eeae58d189bb1943a227a4` | 2026-08-13T10:55:20+02:00 | test: complete phase manager parity coverage | 0 | 0 | 93 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/crear-rama-para-card-duel-engine-0.18.0` | `532cf10560d85b9754a1864a2d98ab7a999a95eb` | 2026-08-22T16:52:57+02:00 | Merge pull request #150 from Alphonsus411/codex/corrige-errores-de-revision-de-codex | 1 | 2 | 315 | D — DIVERGED / UNCERTAIN | KEEP |
| `codex/crear-tests-para-action_option_resolver` | `f16c0cf662eaaee63b0d9ce026d9e31693cecdf4` | 2026-08-13T14:44:24+02:00 | test action option resolver parity | 0 | 0 | 75 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/crear-tests-para-legalactionenumerator` | `deaacd79393fa54810a579974f027b9f68ebf988` | 2026-08-12T18:57:52+02:00 | test: capture legal action enumerator parity | 0 | 0 | 111 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/declarar-protocol-y-mantener-helpers-temporalmente` | `fd028d4068a18c296eb2c98d3ff5b7dd03e8fd52` | 2026-08-12T18:04:35+02:00 | refactor: define legal action query boundary | 0 | 0 | 113 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/definir-clasificacion-de-errores-en-application.py` | `f8703cddb40e10994379168a2e9f21836b061cad` | 2026-08-01T09:56:26+02:00 | Add safe public validation errors | 0 | 0 | 254 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/definir-excepcion-invaliddeckdefinition-y-manejar-errores` | `f7747cf444794ec0eb47d2f51c45ce4e65b8f610` | 2026-08-01T11:56:46+02:00 | Handle only expected invalid deck definitions | 0 | 0 | 240 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/definir-funciones-de-conjuntos-miticos` | `1fadd1cb2be29e28078536df6452bcec3226275d` | 2026-08-04T08:30:51+02:00 | Stabilize mythic deck policy classifiers | 0 | 0 | 135 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/dividir-r-03-en-inventario-y-modificacion` | `c0b50a02e80a1a691109bcbfa5faf4af4722efa0` | 2026-08-01T10:39:24+02:00 | docs: separar inventario y decisión normativa R-03 | 0 | 0 | 250 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/documentar-operacion-get_match-y-restricciones-dto` | `c3a06d3e7aab7f18269742e8d10fcf8dd90ca9ca` | 2026-07-31T09:20:52+02:00 | Secure R-06 public response DTOs | 0 | 0 | 288 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/documentar-y-verificar-optimizacion-de-rendimiento` | `96f13b4bc05b6b7b56da8ded6e12c93d39c1047a` | 2026-08-15T09:42:31+02:00 | docs: close local targeting cache optimization | 0 | 0 | 39 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/ejecutar-pruebas-y-crear-documentacion` | `53e8ce7180d8b483c7cf6a4d1a216bee7fa7650d` | 2026-08-13T10:29:28+02:00 | docs: record phase refactor implementation evidence | 0 | 0 | 95 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/ejecutar-pruebas-y-crear-documentacion-de-resultados` | `e4da60c98925054f4edc337205c4e56ddbc7af14` | 2026-08-13T12:03:09+02:00 | docs: record phase manager parity closure | 0 | 0 | 87 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/ejecutar-secuencia-de-comandos-y-validaciones` | `40d8e0080d68ed555d5e940458dd93346dbdebd5` | 2026-08-01T12:33:49+02:00 | chore: registrar verificacion de release 0.19.0 | 0 | 0 | 230 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/ejecutar-tareas-de-verificacion-y-documentacion` | `82fa8e7ca4144248f6f17514f6970555d171486c` | 2026-08-02T10:49:59+02:00 | docs: registra la validación final de 0.20.0 | 0 | 0 | 196 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/ejecutar-verificacion-de-release-y-documentar-resultados` | `5b139cc62f21bfd95c0f3b8fd48e9d03a34d8280` | 2026-08-13T08:56:48+02:00 | docs: record final legal actions validation | 0 | 0 | 101 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/ejecutar-verificacion-final-y-pruebas` | `c36f277c359edc4464ac5e12a1d2d7031bd0284b` | 2026-08-03T18:55:53+02:00 | docs: record 0.20.1 release verification | 0 | 0 | 149 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/ejecutar-y-verificar-benchmarks-de-rendimiento` | `e672ccb328ebf533a7fbac3297ac497980502e8b` | 2026-08-14T17:15:52+02:00 | benchmarks: establish action option hotspot baseline | 0 | 0 | 49 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/ejecutar-y-verificar-proceso-de-benchmarks` | `a6f305d2ee7c1d64543c893593886b3cf3bdab28` | 2026-08-15T11:25:47+02:00 | benchmarks: establish post-targeting baseline | 0 | 0 | 29 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/extender-pruebas-para-registro-de-colecciones` | `060c717683d86526ea07848377bf2a25e146b408` | 2026-08-01T13:30:15+02:00 | Extiende pruebas concurrentes del registro | 0 | 0 | 224 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/extraer-autoridad-y-anadir-pruebas` | `25d097fcb654ea40dba3d2812640d85e50f8c273` | 2026-08-04T08:07:05+02:00 | Unify ability activation source authority | 0 | 0 | 137 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/extraer-funcion-para-enumerar-bloqueadores` | `eecf32f7a5f8d338760fda067a8a00b86e8eaeda` | 2026-07-31T14:06:06+02:00 | Enumerate legal blocker declarations | 0 | 0 | 274 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/extraer-validacion-de-combate-a-combat.py` | `6771eed25d94e87adfe48cd033dd7bfa0c47a88e` | 2026-07-31T19:01:09+02:00 | Complete R-07.1 combat action extraction | 0 | 0 | 268 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/extraer-y-actualizar-logica-del-juego` | `c1bbfd9b4eafe190a4f268eb5f92257d3b8bcd95` | 2026-07-31T10:30:23+02:00 | Extract stack trigger coordination | 0 | 0 | 286 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/fix-issues-from-codex-review-#146` | `e706d3baee4ed3612485d7c47d2e209732f76d7f` | 2026-08-23T09:44:20+02:00 | benchmarks: handle optional profile baselines | 1 | 1 | 35 | D — DIVERGED / UNCERTAIN | KEEP |
| `codex/fortalecer-validez-de-externalidentity` | `d3458a5dc8f13eb6d2dc60e6489627f0b6f23282` | 2026-07-31T20:23:26+02:00 | Validate external identity field types | 0 | 0 | 258 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/implementar-actionoption-en-gameengine` | `5354163c23845e411ab44c2358b72f5dcb757410` | 2026-08-13T14:29:59+02:00 | refactor: preserve action option engine facades | 0 | 0 | 77 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/implementar-cambios-y-abrir-pr-en-borrador` | `9b93f55f15e78e4f30b3a1986315677ef59b751d` | 2026-08-04T16:00:36+02:00 | docs: cerrar ventana de compatibilidad persistente | 0 | 0 | 117 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/implementar-compatibilidad-con-replays-v2-en-0.19.0` | `b16e0384e06923ecce3df0800e54b9da111caf74` | 2026-08-02T11:40:55+02:00 | Add exact 0.19 replay compatibility | 0 | 0 | 192 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/implementar-contexto-privado-en-legal_actions` | `185962d2c135d0e1ac24d30aed8221f93263437c` | 2026-08-14T19:40:21+02:00 | Optimize legal action targeting queries | 0 | 0 | 45 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/implementar-eliminacion-controlada-de-ramas` | `b7d80fcffbcdd7e24de53e60cd877480c5f406fd` | 2026-08-28T15:41:53+02:00 | docs: record conservative remote branch cleanup | 0 | 0 | 3 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/implementar-mejoras-en-abilitysourceprofile` | `78bc87c9e96e7549c72d048773885cdd2b234836` | 2026-08-04T06:56:22+02:00 | Freeze effective ability source definitions | 0 | 0 | 139 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/implementar-mejoras-en-el-motor-de-duelo` | `4a98539cb7de32d1eb91d0bbde062f8404d57d57` | 2026-07-30T14:40:29+02:00 | Add signed collection trust envelopes | 0 | 0 | 296 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/implementar-modelo-abilitysourceprofile-y-mejoras` | `c0c1ee153db4925f7588cec23cc793c0e5f50682` | 2026-08-03T12:56:05+02:00 | Fix ability target revalidation after source leaves play | 0 | 0 | 171 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/implementar-politica-de-construccion-de-mazos` | `9714cdd7952d98ee9b7c651ef5e7e71fbeb154d7` | 2026-08-02T09:43:33+02:00 | Add configurable deck construction policies | 0 | 0 | 204 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/implementar-proceso-de-integracion-de-pdfs` | `a4942e6d8e9501578d9f9b3e192777ea3fd4056e` | 2026-08-02T09:20:01+02:00 | Integrar fuentes normativas de Edición Mítica | 0 | 0 | 210 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/implementar-pruebas-de-rendimiento-en-gameengine` | `9ce3278ee8babb30a31749479ab8cc922a9341eb` | 2026-08-14T18:07:12+02:00 | docs: diagnose local targeting cache scope | 0 | 0 | 47 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/implementar-rlock-y-pruebas-concurrentes` | `20ae3af91d18bc2c11ea4ee8a4f78d4092d38ba1` | 2026-08-01T12:01:53+02:00 | Serialize collection batch registration | 0 | 0 | 238 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/implementar-validacion-de-version-en-dominio` | `3089e9bb8670a4c579e13c331474fd0878ed3b5b` | 2026-08-01T11:49:00+02:00 | Validate CAS versions across application layers | 0 | 0 | 242 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/incorporar-gestion-de-ciclo-de-vida-en-sqlitematchstore` | `196e52f47d62d1d3be39e4b24156bcba62837b6e` | 2026-07-30T11:16:13+02:00 | Define SQLite store lifecycle after close | 0 | 0 | 308 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/inspeccionar-secuencia-de-fases-y-documentar` | `497855b9b206065d559444de6728bbbec8235355` | 2026-08-13T09:11:43+02:00 | docs: diagnose phase manager boundaries | 0 | 0 | 99 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/inspeccionar-y-comparar-cambios-de-pr-#151` | `1ba7da1bfa7e84e95ba6ecbaf945a0bb69f9e1c5` | 2026-08-27T10:28:44+02:00 | test: register targeting cache parity with unittest | 0 | 0 | 25 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/inspeccionar-y-comparar-cambios-del-pr` | `83e2daf525bae4fec0bc1daf3e2e0ff8a4854411` | 2026-08-27T10:15:18+02:00 | test registry authority during match setup | 0 | 0 | 27 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/inspeccionar-y-validar-el-pr` | `985bef1dbcb6ec9492477a66fd9824c63e74c90d` | 2026-08-27T11:44:26+02:00 | benchmarks: restore optional profile baselines | 0 | 0 | 23 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/inventariar-responsabilidades-de-combate` | `850b063599f0f22faf1ed98e8628bc915297f012` | 2026-07-31T14:21:31+02:00 | Close combat manager parity milestone | 0 | 0 | 272 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/localiza-y-reemplaza-prueba-de-metadata` | `079032e401432a1bd4f2168c977544c8d5f4d495` | 2026-08-04T09:01:02+02:00 | test: audit synthetic wheel metadata | 0 | 0 | 131 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/localizar-y-actualizar-detector-de-afirmaciones` | `79d5928205780a0c56654a910b1a569548d59b4f` | 2026-08-03T16:24:51+02:00 | Tighten stale challenge documentation detection | 0 | 0 | 155 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/localizar-y-validar-versionado-en-manifest.py` | `9abc5f7ad890e12c123ddea36ea7c4159d2d5e47` | 2026-07-30T15:02:03+02:00 | Validate collection engine versions strictly | 0 | 0 | 292 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/medir-rendimiento-de-deepcopy-en-gamestate` | `5283cfe4e600c6cfe2ad2734b74528286f93a0d4` | 2026-08-15T10:45:29+02:00 | benchmarks: measure GameState deepcopy cost | 0 | 0 | 33 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/mejorar-mecanicas-del-proyecto` | `8eacd77ecb7478f0e77e02939e94ea2df4bdb322` | 2026-07-30T11:01:19+02:00 | Harden match setup and SQLite memory storage | 0 | 0 | 312 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/mejorar-mecanicas-del-proyecto-cwh8a3` | `8e50db8e7cd32c188410ae101012c54f54280f0f` | 2026-07-31T12:39:22+02:00 | Complete R-06 authorization contract | 0 | 0 | 280 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/mejorar-patron-de-desafio-reinos` | `1b0c63dbdd3d398b3f723d17988884581d473e13` | 2026-08-04T10:06:10+02:00 | test: ampliar detector de desafío obsoleto | 0 | 0 | 127 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/modificar-collectionregistry-para-estado-inmutable` | `6723e55954e050b3d5aabb96bf517a406e57d0b6` | 2026-08-01T13:23:00+02:00 | Make collection registry publication atomic | 0 | 0 | 226 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/modificar-gameengine-para-manejar-excepciones` | `bbf5144d969da34ec5fcd05d549e4ea2b9a46668` | 2026-07-31T18:08:22+02:00 | Restore pending replacement after replay failure | 0 | 0 | 270 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/modificar-logica-de-chequeo-de-version` | `bffaa1305e65ccd91b1fe3def7f911cbac2345b6` | 2026-08-01T13:47:55+02:00 | Fix source checkout version resolution | 0 | 0 | 218 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/modificar-logica-de-objetivos-y-habilidades` | `8ccc044fac86150294cb4df492222165f0c1d6d6` | 2026-08-02T12:06:42+02:00 | Fix divine targeting for transformed ability sources | 0 | 0 | 188 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/modificar-run_headless-y-ampliar-simulationreport` | `0d480ee39b0199d69903aca131c65480e096cf94` | 2026-07-31T19:31:41+02:00 | Separate simulation command limit from match status | 0 | 0 | 262 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/preparar-card-duel-engine-0.16.0` | `48de9bb6da52a3e6b949de6457aee1670208ede3` | 2026-07-23T12:06:50+02:00 | Prepare reproducible 0.16.0 release verification | 0 | 0 | 319 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/preparar-card-duel-engine-0.17.0` | `d3f62e76d2f785aaf8e4ec5a3814def3bee78275` | 2026-07-23T12:36:09+02:00 | Prepare card-duel-engine 0.17.0 | 0 | 0 | 317 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/preparar-entrega-0.12.0-de-card_duel` | `6cf2907c5fb389a0ea031cf0dec7d6abaa80153f` | 2026-07-23T10:38:25+02:00 | feat: preparar Card Duel Engine 0.12.0 | 0 | 0 | 327 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/preparar-version-0.14.0-y-pr` | `5b3a1ec86f175c883ddcfb6d0698999c569c1a9d` | 2026-07-23T11:16:44+02:00 | feat: preparar Card Duel Engine 0.14.0 | 0 | 0 | 323 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/preparar-version-0.15.0-en-rama-nueva` | `9aec67bf71a10528abff174cd0bd6d1e3b3ad790` | 2026-07-23T11:38:54+02:00 | Prepare release 0.15.0 | 0 | 0 | 321 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/preparate-para-la-version-0.13.0` | `096aa17e4bd28429d08de11c30c8af82f88bca41` | 2026-07-23T10:58:27+02:00 | feat: preparar Card Duel Engine 0.13.0 | 0 | 0 | 325 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/realizar-auditoria-de-ramas-remotas-codex` | `3f9af7ff265d37d77aaa2ce40eb27b7b530094a7` | 2026-08-27T13:17:09+02:00 | docs: audit remote Codex branches for 0.20.1 | 0 | 0 | 19 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/realizar-commit-y-abrir-pr-en-borrador` | `4b13e87889f20d88e19d9ee91b977b11271d6025` | 2026-08-01T14:18:38+02:00 | Completa atomicidad y rollback de creación de partidas | 0 | 0 | 214 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/realizar-mediciones-de-rendimiento-en-sha` | `ceca531177db630421d8736c62a2fca7fdb62562` | 2026-08-15T07:27:29+02:00 | benchmarks: validate targeting local cache | 0 | 0 | 41 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/realizar-operaciones-de-git-y-analisis` | `9e41ba726d3f3299fa64a440dac49153374eb8b9` | 2026-08-02T11:26:31+02:00 | docs: registrar diagnóstico previo de 0.20.1 | 0 | 0 | 194 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/realizar-proceso-de-commit-y-verificacion` | `10b0de1a446befc2152e8e1aefd6107806cc324e` | 2026-08-13T19:21:54+02:00 | docs: record resolver wheel reproducibility evidence | 0 | 0 | 69 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/realizar-prueba-de-rendimiento-post-optimizacion` | `3c2a1662bd178a0d5ca0312cd861f71513f114f5` | 2026-08-15T10:24:47+02:00 | benchmarks: capture post-targeting measurements | 0 | 0 | 37 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/realizar-pruebas-para-la-version-0.19.0` | `47eb25a8b126d3df401882445637af41d83a9d34` | 2026-08-03T13:51:54+02:00 | Add historical 0.19 lord ability replay | 0 | 0 | 167 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/refactorizar-action-option-resolver` | `a23edb924b99bec703e5f67054cc25024e946c2a` | 2026-08-13T13:11:02+02:00 | docs: diagnose action option resolver extraction | 0 | 0 | 83 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/refactorizar-actionoptionresolver` | `5e3b7b9af0907d997515676c733e8a76ac729ce4` | 2026-08-13T13:44:17+02:00 | refactor: extract action option resolution | 0 | 0 | 79 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/refactorizar-gameengine-para-replaycompatibility` | `f56f82cebe6689d5b76fb86755e013cd56c74168` | 2026-08-03T13:12:04+02:00 | Preserve legacy replay engine semantics | 0 | 0 | 169 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/refactorizar-gameengine-y-zonemanager` | `bafe68506515433ea90675a683b48e3d61141412` | 2026-07-31T19:11:07+02:00 | Complete R-07.2 zone manager parity | 0 | 0 | 266 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/refactorizar-generacion-de-worktree` | `518ff1a49a2d1ffb6b74d75ffccf1f31232cdbec` | 2026-08-04T08:44:50+02:00 | Use isolated worktrees for legacy replay generation | 0 | 0 | 133 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/refactorizar-legal_actions-para-enumerar-acciones` | `b9753f412127080abff72a240514178bebeaab50` | 2026-07-31T13:56:44+02:00 | Enumerate combat attacker subsets deterministically | 0 | 0 | 276 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/refactorizar-logica-de-dano-en-combate` | `c9f0f82ed1ffbc2c7d1416dc96a5d69ac2586eda` | 2026-07-31T13:39:15+02:00 | Preserve marked damage after combat | 0 | 0 | 278 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/refactorizar-new_match-en-game.py` | `c6e6dde95fcfddfd904e364e488d33ecc0a00b4b` | 2026-08-01T13:37:27+02:00 | Refactor new match setup atomically | 0 | 0 | 222 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/refactorizar-politica-de-barajas-miticas` | `150c4c7df5eb629a34064a0b9ff4f149a68eb91a` | 2026-08-03T14:03:15+02:00 | Harden mythic deck set classification | 0 | 0 | 165 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/refactorizar-script-de-construccion-de-wheels` | `039c805d306b160dd491cf4a6b1ef932f33346e4` | 2026-08-03T14:24:48+02:00 | Build reproducible wheels from detached worktree | 0 | 0 | 163 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/registrar-informacion-de-ramas-remotas` | `bafc1aeb5859c9a4611f30cadf43c406f0580ef8` | 2026-08-28T13:24:21+02:00 | docs: refresh remote branch audit | 0 | 0 | 7 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/registrar-resultados-de-rendimiento-y-benchmarks` | `301951e17f627c85c1021856565c663bc048bab8` | 2026-08-14T17:04:29+02:00 | docs: record action option benchmark results | 0 | 0 | 51 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/reorganizar-validacion-en-validate_invariants` | `e2b61e2aaec35adc9d2b75e86ece329e81c25cf4` | 2026-07-30T14:12:16+02:00 | Validate pending search players before zone lookup | 0 | 0 | 300 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/revisar-documentos-y-decidir-sobre-adaptador-http` | `fdd85539548f8f76ac071bcdb2c3dc68e2ba9707` | 2026-08-01T10:31:58+02:00 | docs: exclude network transports from roadmap | 0 | 0 | 252 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/revisar-reglas-de-fantasy-tokens` | `9c918b53df8143276f633d2f7d0a667bbf2536ae` | 2026-07-30T12:39:55+02:00 | Document multiplayer rules ambiguity | 0 | 0 | 306 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/revisar-y-ajustar-documentacion-de-refactorizacion` | `3c5f70f0288a453c824396c5fa050969a80c3041` | 2026-08-13T08:42:11+02:00 | docs: clarify final legal action refactor state | 0 | 0 | 103 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/revisar-y-auditar-proceso-de-construccion-de-wheels` | `ff7508f9a6a4d2a6810315632c93eb524ba86974` | 2026-08-02T12:39:38+02:00 | Audit and publish one reproducible wheel | 0 | 0 | 182 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/revisar-y-confirmar-cambios-antes-del-pr` | `2fa625fb90e709f06201e1d5c7c838e8e89bd1a7` | 2026-08-28T10:20:19+02:00 | docs: audit post-0.20.1 branch integrations | 0 | 0 | 9 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/validar-documento-migrado-en-manifest.py` | `ea16eef0234ab07386ef789d272fe230f6ae08bd` | 2026-07-30T14:53:24+02:00 | Harden collection manifest document validation | 0 | 0 | 294 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/validar-limites-en-deckconstructionpolicy` | `6a74b1e0ceaee31d26e499e04d1819cc7974a635` | 2026-08-02T11:51:05+02:00 | Harden deck construction policies | 0 | 0 | 190 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/verificar-arquitectura-y-restricciones-del-gameengine` | `e036426d57a8dcf46796cae8dc6e55b7754016bd` | 2026-08-14T06:09:05+02:00 | docs: audit final engine collaborator architecture | 0 | 0 | 65 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/verificar-cambios-antes-del-commit` | `78cd97acd0a567fae64d89c647a274d3a4eabf2d` | 2026-08-13T12:13:37+02:00 | audit: close phase manager parity evidence | 0 | 0 | 85 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/verificar-proceso-de-limpieza-de-ramas` | `4176f5be560da2fa784926c5ae4e42ad68411241` | 2026-08-28T15:55:07+02:00 | docs: record codex branch cleanup closure | 0 | 0 | 1 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `codex/verificar-y-registrar-version-de-lanzamiento` | `49b30c99bcd7a74cbfd5afab608529b7419fe3af` | 2026-08-04T13:51:53+02:00 | Validate formal release version selection | 0 | 0 | 121 | A — SAFE_TO_DELETE | KEEP — NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE |
| `main` | `16d2c09464d801662490b699b490f404e3f82a1e` | 2026-08-28T16:03:34+02:00 | Merge pull request #166 from Alphonsus411/codex/verificar-proceso-de-limpieza-de-ramas | — | — | — | BASE | KEEP — rama base |

## Eliminaciones

**Ramas eliminadas: 0.** Por ello no existen ramas eliminadas para enumerar. El único intento queda documentado con nombre, SHA, doble prueba de ancestralidad y resultado:

| Rama | SHA | Primera prueba | Tip remoto revalidado | `main` revalidado | Segunda prueba | Resultado |
|---|---|---:|---|---|---:|---|
| `codex/actualiza-allowed_content-y-mejora-validaciones` | `a5151b8947dab727e6d5773254a7cce1dde140dd` | exit `0` | coincidió: `a5151b8947dab727e6d5773254a7cce1dde140dd` | coincidió: `16d2c09464d801662490b699b490f404e3f82a1e` | exit `0` | **KEEP / DELETE_FAILED** — exit `128`: `fatal: could not read Username for 'https://github.com': No such device or address` |

## Ramas conservadas B/C/D/E

| Rama | SHA | Categoría | Motivo |
|---|---|---|---|
| `Bella-2.0` | `851bc963692c7c2e0e70d34c8e09b67781da1ac4` | **E** | Rama especial: exclusión expresa; UNTOUCHED / KEEP. |
| `codex/agregar-pruebas-para-targeting-local-cache` | `4aa6cccceeff6d7cb22a052422ab4080829d61a2` | **B** | Cambios equivalentes por parche, pero el tip no es ancestro; la equivalencia nunca autoriza borrado. |
| `codex/capturar-perfil-de-acciones-legales-con-cprofile` | `6f1f5e9a3e67005526b7522ab1b16f75599e9d8b` | **D** | Historia divergente o incierta con commits no equivalentes; conservación obligatoria. |
| `codex/corrige-errores-de-revision-de-codex` | `9c627ed6b94cebdc1408f5e6033e9b209d5d5fb0` | **D** | Historia divergente o incierta con commits no equivalentes; conservación obligatoria. |
| `codex/corrige-errores-en-la-prueba-de-paridad` | `20248530cbeaefc52b44d9adfbc8bb7d82cb7422` | **B** | Cambios equivalentes por parche, pero el tip no es ancestro; la equivalencia nunca autoriza borrado. |
| `codex/crear-rama-para-card-duel-engine-0.18.0` | `532cf10560d85b9754a1864a2d98ab7a999a95eb` | **D** | Historia divergente o incierta con commits no equivalentes; conservación obligatoria. |
| `codex/fix-issues-from-codex-review-#146` | `e706d3baee4ed3612485d7c47d2e209732f76d7f` | **D** | Historia divergente o incierta con commits no equivalentes; conservación obligatoria. |

### Salvaguardas adicionales

- `KEEP_OPEN_PR`: **0** ramas; no había PR abiertas.
- `DELETE_FAILED`: **1** rama, `codex/actualiza-allowed_content-y-mejora-validaciones`; se conserva con el mismo SHA.
- Las restantes ramas A se conservan como `NOT_ATTEMPTED_AFTER_GLOBAL_FAILURE`; no se confunden con B/C/D/E ni con eliminaciones.

## Garantía dedicada para Bella

Bella-2.0
UNTOUCHED
KEEP

## Estado final y aritmética

Tras el intento se ejecutó nuevamente `git fetch --prune origin` y se repitieron los conteos.

| Comprobación | Antes | Eliminado | Después | Aritmética |
|---|---:|---:|---:|---|
| Ramas remotas totales | 169 | 0 | 169 | `169 - 0 = 169` — PASS |
| Ramas `codex/*` | 167 | 0 | 167 | `167 - 0 = 167` — PASS |
| Categorías Codex | 167 | — | 161+2+0+4 | `161 + 2 + 0 + 4 = 167` — PASS |

- recuento eliminado: **0**.
- recuento restante total: **169**.
- `main before`: `16d2c09464d801662490b699b490f404e3f82a1e`.
- `main after`: `16d2c09464d801662490b699b490f404e3f82a1e`.
- `unchanged: yes`.

## Gobierno observable y recomendación

| Configuración | Estado observable |
|---|---|
| Protección de `main` | `protected: false` en el resumen público de la rama; reglas detalladas de force-push/eliminación: **NOT OBSERVABLE** sin autenticación. |
| `delete_branch_on_merge` | **NOT OBSERVABLE**: el recurso público del repositorio omitió el campo. |

La eventual configuración de protección de `main` y de eliminación automática de ramas debe tratarse en otra entrega, con autorización y evidencia propias. No se cambia ninguna de esas opciones aquí.

## Criterios de cierre

El encargo sólo puede recibir `GO` si las eliminaciones previstas se completan, las ramas protegidas se conservan, la aritmética cierra y `main` permanece inmutable. Aunque las invariantes y salvaguardas sí pasan, la limpieza operativa eliminó 0 ramas por un `DELETE_FAILED`; aplicando literalmente esos criterios corresponde `NO-GO`.

## Dictamen

NO-GO
