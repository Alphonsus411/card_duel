# Ejecución conservadora de limpieza de ramas — 2026-08-28

- **Fecha de ejecución UTC:** `2026-08-28T13:39:08Z`.
- **`BASE_MAIN_SHA`:** `5dcbe09da38ff48955779f329eaed54138e99b30`.
- **PR abiertas observadas:** `0`; no hubo candidatas reclasificadas como `KEEP_OPEN_PR`.
- **Candidatas A ordenadas antes de borrar:** `159`.
- **Eliminaciones completadas:** `0`.
- **Resultado:** la primera eliminación falló por falta de credenciales de escritura; se clasificó como `KEEP/DELETE_FAILED` y se detuvieron las restantes porque el mismo error de autenticación afecta a todas las operaciones de escritura.

## Secuencia aplicada

1. Se restauró `origin`, se refrescaron las ramas y se consultó directamente `refs/heads/main` con `git ls-remote --heads`.
2. Se fijó el SHA anterior como `BASE_MAIN_SHA` y se construyó, antes de cualquier intento de borrado, la lista A ordenada que aparece más abajo. Sólo entraron filas cuyo primer `git merge-base --is-ancestor <tip> <BASE_MAIN_SHA>` devolvió `0`.
3. La API REST pública de GitHub devolvió HTTP 200 y una lista vacía para las PR abiertas. Por tanto, ninguna rama fue excluida como `KEEP_OPEN_PR`.
4. Inmediatamente antes del único intento se consultaron directamente tanto el tip remoto de la candidata como el tip remoto de `main`; ambos coincidieron con el inventario y la base.
5. Se repitió `git merge-base --is-ancestor <tip-verificado> origin/main`, con resultado `0`.
6. Se ejecutó exactamente un `git push origin --delete <nombre-exacto>`. Falló con exit `128`; no se forzó ni se agrupó con otra eliminación.
7. Dado que el fallo fue la ausencia global de credenciales HTTPS, continuar no podía producir eliminaciones válidas. La rama quedó `KEEP/DELETE_FAILED` y no se intentó ninguna candidata restante.
8. No se tocó `Bella-2.0`, ninguna rama no ancestral (B/C/D), `main`, `KEEP_OPEN_PR` ni `DELETE_FAILED`.

## Registro exacto de la operación de eliminación

| Nombre | SHA inventariado | Primera ancestralidad | Tip verificado | Base reconfirmada | Segunda ancestralidad | Resultado | Exit push | Salida exacta del push |
|---|---|---:|---|---|---:|---|---:|---|
| `codex/actualiza-allowed_content-y-mejora-validaciones` | `a5151b8947dab727e6d5773254a7cce1dde140dd` | `0` | `a5151b8947dab727e6d5773254a7cce1dde140dd` | `5dcbe09da38ff48955779f329eaed54138e99b30` | `0` | **KEEP/DELETE_FAILED** | `128` | `fatal: could not read Username for 'https://github.com': No such device or address` |

La consulta posterior confirmó que la rama fallida continúa en el remoto con el mismo SHA; no hubo eliminación parcial.

## Lista A ordenada creada antes de borrar

| # | Nombre exacto | Tip observado | `merge-base --is-ancestor` |
|---:|---|---|---:|
| 1 | `codex/actualiza-allowed_content-y-mejora-validaciones` | `a5151b8947dab727e6d5773254a7cce1dde140dd` | `0` |
| 2 | `codex/actualizar-acciones-en-tests.yml` | `70194f7862c80eb73acea65a9c8277ca09249b3e` | `0` |
| 3 | `codex/actualizar-backend-a-version-0.11.0` | `190bf8e9591daff284a690eb96dc5ef27feb3ba4` | `0` |
| 4 | `codex/actualizar-documentacion-y-mantener-requerimientos` | `c8ddf2f73bf050c8bf4ec030cff52c120dbc5829` | `0` |
| 5 | `codex/actualizar-documentacion-y-restricciones-en-reglas` | `2599d9c1638c19a15a47374897fa3dd73592ea8f` | `0` |
| 6 | `codex/actualizar-documento-de-rollback-y-pruebas` | `00dd708cd27b57b35249d6f9580ba177f48e92c2` | `0` |
| 7 | `codex/actualizar-estado-de-r-04-en-readme.md` | `8dd6a0fd76d9d8ef510afbf1724a09ddf0e2d6bf` | `0` |
| 8 | `codex/actualizar-flujo-de-trabajo-tests.yml` | `d0237df9e4398396e1fb025ccbdd24dccac6cb4b` | `0` |
| 9 | `codex/actualizar-gestion-de-versiones-en-el-proyecto` | `2eb7930a21e91247663fb671374254ebacfc2741` | `0` |
| 10 | `codex/actualizar-historial-de-validacion-y-scripts` | `8369ee97482c4e18d3228960be44720fa6846f16` | `0` |
| 11 | `codex/actualizar-logica-de-acciones-legales-y-pruebas` | `eee04108308f89ba83ed6bce7f57d4b737441cf3` | `0` |
| 12 | `codex/actualizar-patrones-de-secretos-y-pruebas` | `d01d17d29e4f2367f831bcfaed785dd8db231e1d` | `0` |
| 13 | `codex/actualizar-patrones-de-seguridad-y-pruebas` | `2b0bd5a59551931ce221fadf6b8b599349141307` | `0` |
| 14 | `codex/actualizar-reconstruccion-de-fuentes-en-snapshot.py` | `386f6f626d0ea35d4642506f170bdfa33a4720f0` | `0` |
| 15 | `codex/actualizar-reglas-de-seguridad-y-pruebas` | `d1b4abdd49966a664fb8bd62bfea6f101f581dba` | `0` |
| 16 | `codex/actualizar-reglas-en-documentacion` | `80f0acce19fc167367248d4a2903b5bb3d7d0185` | `0` |
| 17 | `codex/actualizar-roadmap.md-y-documentacion-asociada` | `d20a094a457f3f65cc9e2a8f1960d6dc99cba716` | `0` |
| 18 | `codex/actualizar-script-de-benchmark-para-guardar-resultados` | `c39a5642fce2e03b314e79c9b4d83181dee8690c` | `0` |
| 19 | `codex/actualizar-version-a-0.20.0-en-pyproject.toml` | `261b46ae497fe9335bd9c2eadf81ace8d6160eef` | `0` |
| 20 | `codex/actualizar-version-y-regenerar-uv` | `ce2ba1af55ff3976e2b27afa4bd39cbf655634b6` | `0` |
| 21 | `codex/actualizar-version-y-sincronizar-archivos` | `98d0c23552ee5935568d80a632413dbf17c928f5` | `0` |
| 22 | `codex/add-engine-semantics-handling-in-replay` | `7624a27bd06e5e6e5758851427de4c916ea3fe27` | `0` |
| 23 | `codex/add-immutable-tuple-executable_command_types` | `4d3f4a84d071647524d09dade8150af02a7d19d9` | `0` |
| 24 | `codex/add-legacy-state-digest-extraction-and-comparison` | `f823dc4edd6a34e92b7524d2e8c47e900a2ffc5c` | `0` |
| 25 | `codex/add-r-06-specifications-to-architecture.md` | `3c1b50595e69418a5bc1237d9b806a7f85345a7d` | `0` |
| 26 | `codex/add-section-estado-posterior-de-la-decision` | `6e9f9f2aac61e7a415f7866ab52c86edbeeb308e` | `0` |
| 27 | `codex/amplia-la-validacion-de-match_id` | `0c811859ecfe9b3e960f54a07e607097b46f7cdb` | `0` |
| 28 | `codex/ampliar-documentacion-de-reglas-y-creacion-de-catalogo` | `7ec4495e9f65a739743e1000d5cd828cdc8dd3d8` | `0` |
| 29 | `codex/anadir-benchmarks-para-gameengine` | `15a30ab9446f7a51b4162380b1bf898bdc64f5f2` | `0` |
| 30 | `codex/anadir-capacidad-can_challenge-y-pruebas-asociadas` | `3b7654dccbf3f5be00b7862404a5a41218dc8e08` | `0` |
| 31 | `codex/anadir-casos-de-prueba-para-actionoptionresolver` | `96464ec9bf9f5099650ae223aa45fd9a75ebf907` | `0` |
| 32 | `codex/anadir-casos-de-prueba-para-ruleset` | `1bf4e15edeb4860bb2cc600ffb5c08a3f8399c44` | `0` |
| 33 | `codex/anadir-engine_semantics-a-snapshots` | `e73c2e82d303be1203a32587ffc411b40219ead0` | `0` |
| 34 | `codex/anadir-entrada-de-deuda-arquitectonica` | `5b59aacbe8913d46f81f64be9687885dbea47d0b` | `0` |
| 35 | `codex/anadir-matriz-diferencial-de-cierre-a-documentacion` | `e2931504c5ef883e1da6285fd23476a8bac4e31e` | `0` |
| 36 | `codex/anadir-prueba-e2e-para-reemplazo-diferido` | `f0e67995a98187e2314fe5b9a52fb8f4f61371d1` | `0` |
| 37 | `codex/anadir-pruebas-en-test_legal_action_enumerator_parity` | `c7e7539e1f2b21bc0c5303daad1b05f029a1e14c` | `0` |
| 38 | `codex/anadir-pruebas-en-tests/test_new_match_transaction.py` | `694e20c657065ba1a1109ffb3aa16b89977bdc69` | `0` |
| 39 | `codex/anadir-pruebas-y-paralelizar-verificaciones-legales` | `2c8a18789d742c242017a8df9afb209b94c1e0d4` | `0` |
| 40 | `codex/anadir-seccion-decision-en-phase_manager_diagnostic` | `b69c3ef6ed9b3c9b0235f1887b8f2a1b38e3c4cd` | `0` |
| 41 | `codex/auditar-artefactos-de-construccion-de-wheels` | `27c561a2e8bd576c7cec2def4a3ccd3f5744bf71` | `0` |
| 42 | `codex/auditar-y-corregir-logica-de-drenaje` | `7510bd5f5e4bc82630bb3efab7f02956dc04d32c` | `0` |
| 43 | `codex/auditar-y-crear-pruebas-para-motor-de-juego` | `2dfb02b4f528dc54b5d04499f6daf218ae4c8432` | `0` |
| 44 | `codex/automatiza-revision-y-creacion-de-pr` | `85753dc8a9313840fbef554c50119cfd9b6efe31` | `0` |
| 45 | `codex/avanza-en-la-hoja-de-ruta-del-proyecto` | `b1f1e88076a6982cad25c424a66df7370bcdc35b` | `0` |
| 46 | `codex/confirmar-y-auditar-implementacion-de-0.20.1` | `e996a20c65a3ebe6cb3b49603a80da9e31e0bad3` | `0` |
| 47 | `codex/confirmar-y-auditar-implementacion-de-0.20.1-6qor6d` | `431f6ae3d408c6034954e8ecf7c56d873eec6706` | `0` |
| 48 | `codex/conservar-historia-en-conformance-review` | `bdcf997d8bea5a5c954cc08eef5a542a296f7abf` | `0` |
| 49 | `codex/consulta-hilos-de-revision-de-prs` | `e6b51b795ae960a366e9eea56f29a0131a422ea8` | `0` |
| 50 | `codex/consultar-configuracion-de-repositorio-en-github` | `aa3447c819e3858ae6be0f9244b9c98bc5c66d72` | `0` |
| 51 | `codex/consultar-reglas-de-proteccion-y-estado-de-repositorio` | `c348734c39307132e6a31d7bb0295e03d8ec4251` | `0` |
| 52 | `codex/consultar-y-clasificar-pr-abiertas` | `1cbd45c1470f31cf284a23d5f75da78a55718e5d` | `0` |
| 53 | `codex/corrige-defectos-de-la-edicion-mitica` | `0edc513c974e296fabb579ee3096b89459c29be7` | `0` |
| 54 | `codex/corrige-la-hoja-de-ruta-y-documentacion` | `b6b61c93ca5ab018f750fbddde387f293646f520` | `0` |
| 55 | `codex/crear-actionoptioncontext-y-actionoptionresolver` | `d830d7282544f1156996d188ed931b74d12c15b4` | `0` |
| 56 | `codex/crear-archivo-mythic_rules_audit.md` | `d63f0eede006efd32c9bc9c03815c6810cae4a5b` | `0` |
| 57 | `codex/crear-benchmark-de-accion-con-cli-y-mediciones` | `4a6d932ab0e4a4d3e8f27fd5e03418e400167f1f` | `0` |
| 58 | `codex/crear-commit-y-actualizar-informe-de-evidencia` | `8d878c23dc0af0b8e8e509b6eede6c82bd3b03bd` | `0` |
| 59 | `codex/crear-documentacion-de-refactorizacion` | `6cbf6d7ccea106a33dde012af49530d607e29776` | `0` |
| 60 | `codex/crear-documentacion-de-rendimiento-y-comparacion` | `43b5060ee6761b7aa817904c3888568d7e13d613` | `0` |
| 61 | `codex/crear-documento-de-auditoria-de-integracion` | `8b5154fa73301c601342942ae6cc3ea5cb8a2c66` | `0` |
| 62 | `codex/crear-documento-de-benchmarks-de-rendimiento` | `2695c1aae83a64a1bca6ce176d76bb90bd186b90` | `0` |
| 63 | `codex/crear-documento-para-auditoria-de-integracion` | `b8b163310efd41e3d13258e8e5bdcb12a6d5abb1` | `0` |
| 64 | `codex/crear-engineering_backlog.md-y-documentar-requisitos` | `bd8a2f55a8bfd6d2157ba1efa26edc56e79bdab1` | `0` |
| 65 | `codex/crear-fixtures-de-benchmarks-con-constructores` | `cdf47c626e0c5b3c2d0e5edea0e2f03d0bd91c7a` | `0` |
| 66 | `codex/crear-informes-de-diagnostico-y-refactorizacion` | `0d28bb8cbb664f9a7353b512667e539e9d80ff1f` | `0` |
| 67 | `codex/crear-informes-de-diagnostico-y-refactorizacion-cayjbe` | `ff0895697e3925135f103c4cab3d562c97659001` | `0` |
| 68 | `codex/crear-legalactioncontext-y-legalactionenumerator` | `206cd759f9aebd7d4a4ec24e5bf0e340689261a3` | `0` |
| 69 | `codex/crear-modulo-de-tests-para-adaptador-r-06` | `8ddd4a2ac935c0a0e6863ad7016b543860c93875` | `0` |
| 70 | `codex/crear-rama-audit/phase-manager-parity-completion` | `6dc599f4df8aeede00eeae58d189bb1943a227a4` | `0` |
| 71 | `codex/crear-tests-para-action_option_resolver` | `f16c0cf662eaaee63b0d9ce026d9e31693cecdf4` | `0` |
| 72 | `codex/crear-tests-para-legalactionenumerator` | `deaacd79393fa54810a579974f027b9f68ebf988` | `0` |
| 73 | `codex/declarar-protocol-y-mantener-helpers-temporalmente` | `fd028d4068a18c296eb2c98d3ff5b7dd03e8fd52` | `0` |
| 74 | `codex/definir-clasificacion-de-errores-en-application.py` | `f8703cddb40e10994379168a2e9f21836b061cad` | `0` |
| 75 | `codex/definir-excepcion-invaliddeckdefinition-y-manejar-errores` | `f7747cf444794ec0eb47d2f51c45ce4e65b8f610` | `0` |
| 76 | `codex/definir-funciones-de-conjuntos-miticos` | `1fadd1cb2be29e28078536df6452bcec3226275d` | `0` |
| 77 | `codex/dividir-r-03-en-inventario-y-modificacion` | `c0b50a02e80a1a691109bcbfa5faf4af4722efa0` | `0` |
| 78 | `codex/documentar-operacion-get_match-y-restricciones-dto` | `c3a06d3e7aab7f18269742e8d10fcf8dd90ca9ca` | `0` |
| 79 | `codex/documentar-y-verificar-optimizacion-de-rendimiento` | `96f13b4bc05b6b7b56da8ded6e12c93d39c1047a` | `0` |
| 80 | `codex/ejecutar-pruebas-y-crear-documentacion` | `53e8ce7180d8b483c7cf6a4d1a216bee7fa7650d` | `0` |
| 81 | `codex/ejecutar-pruebas-y-crear-documentacion-de-resultados` | `e4da60c98925054f4edc337205c4e56ddbc7af14` | `0` |
| 82 | `codex/ejecutar-secuencia-de-comandos-y-validaciones` | `40d8e0080d68ed555d5e940458dd93346dbdebd5` | `0` |
| 83 | `codex/ejecutar-tareas-de-verificacion-y-documentacion` | `82fa8e7ca4144248f6f17514f6970555d171486c` | `0` |
| 84 | `codex/ejecutar-verificacion-de-release-y-documentar-resultados` | `5b139cc62f21bfd95c0f3b8fd48e9d03a34d8280` | `0` |
| 85 | `codex/ejecutar-verificacion-final-y-pruebas` | `c36f277c359edc4464ac5e12a1d2d7031bd0284b` | `0` |
| 86 | `codex/ejecutar-y-verificar-benchmarks-de-rendimiento` | `e672ccb328ebf533a7fbac3297ac497980502e8b` | `0` |
| 87 | `codex/ejecutar-y-verificar-proceso-de-benchmarks` | `a6f305d2ee7c1d64543c893593886b3cf3bdab28` | `0` |
| 88 | `codex/extender-pruebas-para-registro-de-colecciones` | `060c717683d86526ea07848377bf2a25e146b408` | `0` |
| 89 | `codex/extraer-autoridad-y-anadir-pruebas` | `25d097fcb654ea40dba3d2812640d85e50f8c273` | `0` |
| 90 | `codex/extraer-funcion-para-enumerar-bloqueadores` | `eecf32f7a5f8d338760fda067a8a00b86e8eaeda` | `0` |
| 91 | `codex/extraer-validacion-de-combate-a-combat.py` | `6771eed25d94e87adfe48cd033dd7bfa0c47a88e` | `0` |
| 92 | `codex/extraer-y-actualizar-logica-del-juego` | `c1bbfd9b4eafe190a4f268eb5f92257d3b8bcd95` | `0` |
| 93 | `codex/fortalecer-validez-de-externalidentity` | `d3458a5dc8f13eb6d2dc60e6489627f0b6f23282` | `0` |
| 94 | `codex/implementar-actionoption-en-gameengine` | `5354163c23845e411ab44c2358b72f5dcb757410` | `0` |
| 95 | `codex/implementar-cambios-y-abrir-pr-en-borrador` | `9b93f55f15e78e4f30b3a1986315677ef59b751d` | `0` |
| 96 | `codex/implementar-compatibilidad-con-replays-v2-en-0.19.0` | `b16e0384e06923ecce3df0800e54b9da111caf74` | `0` |
| 97 | `codex/implementar-contexto-privado-en-legal_actions` | `185962d2c135d0e1ac24d30aed8221f93263437c` | `0` |
| 98 | `codex/implementar-mejoras-en-abilitysourceprofile` | `78bc87c9e96e7549c72d048773885cdd2b234836` | `0` |
| 99 | `codex/implementar-mejoras-en-el-motor-de-duelo` | `4a98539cb7de32d1eb91d0bbde062f8404d57d57` | `0` |
| 100 | `codex/implementar-modelo-abilitysourceprofile-y-mejoras` | `c0c1ee153db4925f7588cec23cc793c0e5f50682` | `0` |
| 101 | `codex/implementar-politica-de-construccion-de-mazos` | `9714cdd7952d98ee9b7c651ef5e7e71fbeb154d7` | `0` |
| 102 | `codex/implementar-proceso-de-integracion-de-pdfs` | `a4942e6d8e9501578d9f9b3e192777ea3fd4056e` | `0` |
| 103 | `codex/implementar-pruebas-de-rendimiento-en-gameengine` | `9ce3278ee8babb30a31749479ab8cc922a9341eb` | `0` |
| 104 | `codex/implementar-rlock-y-pruebas-concurrentes` | `20ae3af91d18bc2c11ea4ee8a4f78d4092d38ba1` | `0` |
| 105 | `codex/implementar-validacion-de-version-en-dominio` | `3089e9bb8670a4c579e13c331474fd0878ed3b5b` | `0` |
| 106 | `codex/incorporar-gestion-de-ciclo-de-vida-en-sqlitematchstore` | `196e52f47d62d1d3be39e4b24156bcba62837b6e` | `0` |
| 107 | `codex/inspeccionar-secuencia-de-fases-y-documentar` | `497855b9b206065d559444de6728bbbec8235355` | `0` |
| 108 | `codex/inspeccionar-y-comparar-cambios-de-pr-#151` | `1ba7da1bfa7e84e95ba6ecbaf945a0bb69f9e1c5` | `0` |
| 109 | `codex/inspeccionar-y-comparar-cambios-del-pr` | `83e2daf525bae4fec0bc1daf3e2e0ff8a4854411` | `0` |
| 110 | `codex/inspeccionar-y-validar-el-pr` | `985bef1dbcb6ec9492477a66fd9824c63e74c90d` | `0` |
| 111 | `codex/inventariar-responsabilidades-de-combate` | `850b063599f0f22faf1ed98e8628bc915297f012` | `0` |
| 112 | `codex/localiza-y-reemplaza-prueba-de-metadata` | `079032e401432a1bd4f2168c977544c8d5f4d495` | `0` |
| 113 | `codex/localizar-y-actualizar-detector-de-afirmaciones` | `79d5928205780a0c56654a910b1a569548d59b4f` | `0` |
| 114 | `codex/localizar-y-validar-versionado-en-manifest.py` | `9abc5f7ad890e12c123ddea36ea7c4159d2d5e47` | `0` |
| 115 | `codex/medir-rendimiento-de-deepcopy-en-gamestate` | `5283cfe4e600c6cfe2ad2734b74528286f93a0d4` | `0` |
| 116 | `codex/mejorar-mecanicas-del-proyecto` | `8eacd77ecb7478f0e77e02939e94ea2df4bdb322` | `0` |
| 117 | `codex/mejorar-mecanicas-del-proyecto-cwh8a3` | `8e50db8e7cd32c188410ae101012c54f54280f0f` | `0` |
| 118 | `codex/mejorar-patron-de-desafio-reinos` | `1b0c63dbdd3d398b3f723d17988884581d473e13` | `0` |
| 119 | `codex/modificar-collectionregistry-para-estado-inmutable` | `6723e55954e050b3d5aabb96bf517a406e57d0b6` | `0` |
| 120 | `codex/modificar-gameengine-para-manejar-excepciones` | `bbf5144d969da34ec5fcd05d549e4ea2b9a46668` | `0` |
| 121 | `codex/modificar-logica-de-chequeo-de-version` | `bffaa1305e65ccd91b1fe3def7f911cbac2345b6` | `0` |
| 122 | `codex/modificar-logica-de-objetivos-y-habilidades` | `8ccc044fac86150294cb4df492222165f0c1d6d6` | `0` |
| 123 | `codex/modificar-run_headless-y-ampliar-simulationreport` | `0d480ee39b0199d69903aca131c65480e096cf94` | `0` |
| 124 | `codex/preparar-card-duel-engine-0.16.0` | `48de9bb6da52a3e6b949de6457aee1670208ede3` | `0` |
| 125 | `codex/preparar-card-duel-engine-0.17.0` | `d3f62e76d2f785aaf8e4ec5a3814def3bee78275` | `0` |
| 126 | `codex/preparar-entrega-0.12.0-de-card_duel` | `6cf2907c5fb389a0ea031cf0dec7d6abaa80153f` | `0` |
| 127 | `codex/preparar-version-0.14.0-y-pr` | `5b3a1ec86f175c883ddcfb6d0698999c569c1a9d` | `0` |
| 128 | `codex/preparar-version-0.15.0-en-rama-nueva` | `9aec67bf71a10528abff174cd0bd6d1e3b3ad790` | `0` |
| 129 | `codex/preparate-para-la-version-0.13.0` | `096aa17e4bd28429d08de11c30c8af82f88bca41` | `0` |
| 130 | `codex/realizar-auditoria-de-ramas-remotas-codex` | `3f9af7ff265d37d77aaa2ce40eb27b7b530094a7` | `0` |
| 131 | `codex/realizar-commit-y-abrir-pr-en-borrador` | `4b13e87889f20d88e19d9ee91b977b11271d6025` | `0` |
| 132 | `codex/realizar-mediciones-de-rendimiento-en-sha` | `ceca531177db630421d8736c62a2fca7fdb62562` | `0` |
| 133 | `codex/realizar-operaciones-de-git-y-analisis` | `9e41ba726d3f3299fa64a440dac49153374eb8b9` | `0` |
| 134 | `codex/realizar-proceso-de-commit-y-verificacion` | `10b0de1a446befc2152e8e1aefd6107806cc324e` | `0` |
| 135 | `codex/realizar-prueba-de-rendimiento-post-optimizacion` | `3c2a1662bd178a0d5ca0312cd861f71513f114f5` | `0` |
| 136 | `codex/realizar-pruebas-para-la-version-0.19.0` | `47eb25a8b126d3df401882445637af41d83a9d34` | `0` |
| 137 | `codex/refactorizar-action-option-resolver` | `a23edb924b99bec703e5f67054cc25024e946c2a` | `0` |
| 138 | `codex/refactorizar-actionoptionresolver` | `5e3b7b9af0907d997515676c733e8a76ac729ce4` | `0` |
| 139 | `codex/refactorizar-gameengine-para-replaycompatibility` | `f56f82cebe6689d5b76fb86755e013cd56c74168` | `0` |
| 140 | `codex/refactorizar-gameengine-y-zonemanager` | `bafe68506515433ea90675a683b48e3d61141412` | `0` |
| 141 | `codex/refactorizar-generacion-de-worktree` | `518ff1a49a2d1ffb6b74d75ffccf1f31232cdbec` | `0` |
| 142 | `codex/refactorizar-legal_actions-para-enumerar-acciones` | `b9753f412127080abff72a240514178bebeaab50` | `0` |
| 143 | `codex/refactorizar-logica-de-dano-en-combate` | `c9f0f82ed1ffbc2c7d1416dc96a5d69ac2586eda` | `0` |
| 144 | `codex/refactorizar-new_match-en-game.py` | `c6e6dde95fcfddfd904e364e488d33ecc0a00b4b` | `0` |
| 145 | `codex/refactorizar-politica-de-barajas-miticas` | `150c4c7df5eb629a34064a0b9ff4f149a68eb91a` | `0` |
| 146 | `codex/refactorizar-script-de-construccion-de-wheels` | `039c805d306b160dd491cf4a6b1ef932f33346e4` | `0` |
| 147 | `codex/registrar-informacion-de-ramas-remotas` | `bafc1aeb5859c9a4611f30cadf43c406f0580ef8` | `0` |
| 148 | `codex/registrar-resultados-de-rendimiento-y-benchmarks` | `301951e17f627c85c1021856565c663bc048bab8` | `0` |
| 149 | `codex/reorganizar-validacion-en-validate_invariants` | `e2b61e2aaec35adc9d2b75e86ece329e81c25cf4` | `0` |
| 150 | `codex/revisar-documentos-y-decidir-sobre-adaptador-http` | `fdd85539548f8f76ac071bcdb2c3dc68e2ba9707` | `0` |
| 151 | `codex/revisar-reglas-de-fantasy-tokens` | `9c918b53df8143276f633d2f7d0a667bbf2536ae` | `0` |
| 152 | `codex/revisar-y-ajustar-documentacion-de-refactorizacion` | `3c5f70f0288a453c824396c5fa050969a80c3041` | `0` |
| 153 | `codex/revisar-y-auditar-proceso-de-construccion-de-wheels` | `ff7508f9a6a4d2a6810315632c93eb524ba86974` | `0` |
| 154 | `codex/revisar-y-confirmar-cambios-antes-del-pr` | `2fa625fb90e709f06201e1d5c7c838e8e89bd1a7` | `0` |
| 155 | `codex/validar-documento-migrado-en-manifest.py` | `ea16eef0234ab07386ef789d272fe230f6ae08bd` | `0` |
| 156 | `codex/validar-limites-en-deckconstructionpolicy` | `6a74b1e0ceaee31d26e499e04d1819cc7974a635` | `0` |
| 157 | `codex/verificar-arquitectura-y-restricciones-del-gameengine` | `e036426d57a8dcf46796cae8dc6e55b7754016bd` | `0` |
| 158 | `codex/verificar-cambios-antes-del-commit` | `78cd97acd0a567fae64d89c647a274d3a4eabf2d` | `0` |
| 159 | `codex/verificar-y-registrar-version-de-lanzamiento` | `49b30c99bcd7a74cbfd5afab608529b7419fe3af` | `0` |

## Ramas no ancestrales conservadas

| Nombre exacto | Tip observado | `merge-base --is-ancestor` | Disposición |
|---|---|---:|---|
| `codex/agregar-pruebas-para-targeting-local-cache` | `4aa6cccceeff6d7cb22a052422ab4080829d61a2` | `1` | **KEEP** |
| `codex/capturar-perfil-de-acciones-legales-con-cprofile` | `6f1f5e9a3e67005526b7522ab1b16f75599e9d8b` | `1` | **KEEP** |
| `codex/corrige-errores-de-revision-de-codex` | `9c627ed6b94cebdc1408f5e6033e9b209d5d5fb0` | `1` | **KEEP** |
| `codex/corrige-errores-en-la-prueba-de-paridad` | `20248530cbeaefc52b44d9adfbc8bb7d82cb7422` | `1` | **KEEP** |
| `codex/crear-rama-para-card-duel-engine-0.18.0` | `532cf10560d85b9754a1864a2d98ab7a999a95eb` | `1` | **KEEP** |
| `codex/fix-issues-from-codex-review-#146` | `e706d3baee4ed3612485d7c47d2e209732f76d7f` | `1` | **KEEP** |

Además, `Bella-2.0` se mantuvo como categoría E especial y `main` se mantuvo como rama base. Ninguna de ellas formó parte de la lista A.
