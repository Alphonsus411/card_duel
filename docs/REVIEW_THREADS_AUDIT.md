# Auditoría de hilos de revisión de los PR #78–#89

Fecha de consulta: **2026-08-04**.

## Criterio de cierre

Una corrección integrada no basta para declarar un hilo `corregido`: su prueba
específica debe pasar en un job de CI del SHA final de este PR. Hasta disponer de
esos checks, el hilo permanece `todavía abierto` y no debe resolverse en GitHub.
`superado por cambios posteriores` queda reservado para código o contratos que ya
no existan, no para correcciones ordinarias.

El último SHA integrado al iniciar la auditoría fue
`a04d64b84a183e0f8351dd7d65f4ed8d169a5eb2`. Sus cuatro jobs fallaron porque el
checkout superficial no contenía `006534e`, requerido por la prueba de procedencia
histórica. Este PR configura `fetch-depth: 0` en ambos perfiles y prueba esa
precondición.

## Inventario

| Hilo | Defecto | Archivo y símbolo corregido | Prueba específica | CI del SHA final | Estado |
|---|---|---|---|---|---|
| [#78 r3703322230](https://github.com/Alphonsus411/card_duel/pull/78#discussion_r3703322230) | Digest incompatible en replays 0.20.x en vuelo. | `persistence/replay.py`: `_legacy_state_digest`, `replay_from_log` | `Legacy020AbilitySourceProfileReplayTests.test_authentic_historical_digests_are_accepted_without_losing_profile` | `runtime (3.11/3.12/3.13)`, `full`: pendiente | `todavía abierto` |
| [#78 r3703322238](https://github.com/Alphonsus411/card_duel/pull/78#discussion_r3703322238) | Perfil con tipo original en vez del efectivo. | `engine/game.py`: `_ability_source_profile`; `domain/models.py`: `AbilitySourceProfile` | `StackAndPriorityTests.test_source_profile_freezes_copied_and_transformed_effective_definition` | mismos jobs: pendiente | `todavía abierto` |
| [#78 r3703322246](https://github.com/Alphonsus411/card_duel/pull/78#discussion_r3703322246) | `legal_actions()` anunciaba activaciones rechazadas. | `engine/game.py`: `_legal_ability_activations`, `_ability_source_definition` | `StackAndPriorityTests.test_every_announced_ability_activation_executes_from_independent_snapshot` | mismos jobs: pendiente | `todavía abierto` |
| [#79 r3703399104](https://github.com/Alphonsus411/card_duel/pull/79#discussion_r3703399104) | Snapshot perdía `LEGACY_019`. | `persistence/snapshot.py`: `dump_snapshot`, `load_snapshot` | `PersistenceV090Tests.test_snapshot_restores_legacy_019_semantics` | mismos jobs: pendiente | `todavía abierto` |
| [#79 r3703399112](https://github.com/Alphonsus411/card_duel/pull/79#discussion_r3703399112) | Motor CURRENT 0.19 reaparecía como legado. | `persistence/replay.py`: `dump_replay`, `replay_from_log` | `Legacy019ReplayTests.test_manual_019_rules_do_not_enable_historical_semantics` | mismos jobs: pendiente | `todavía abierto` |
| [#80 r3703641750](https://github.com/Alphonsus411/card_duel/pull/80#discussion_r3703641750) | Borrado forzoso de worktree compartido. | `generate_legacy_019_replays.py`: `legacy_checkout` | `Legacy019ReplayGeneratorTests.test_parallel_runs_use_distinct_paths_and_preserve_preexisting_path` | mismos jobs: pendiente | `todavía abierto` |
| [#81 r3703717533](https://github.com/Alphonsus411/card_duel/pull/81#discussion_r3703717533) | Lambda rompía igualdad, hash y pickle. | `rules/deck.py`: `mythic_deck_policy`, `_never_mythic_set` | `DeckConstructionPolicyTests.test_equivalent_mythic_policies_have_equal_hashes_and_pickle_roundtrip` | mismos jobs: pendiente | `todavía abierto` |
| [#82 r3703845056](https://github.com/Alphonsus411/card_duel/pull/82#discussion_r3703845056) | Refactor retiró constantes de metadatos. | `verify_reproducible_wheel.py`: `policy_for` | `ReleaseMetadataTests.test_all_release_version_consumers_read_current_project_version` | mismos jobs: pendiente | `todavía abierto` |
| [#83 r3703906593](https://github.com/Alphonsus411/card_duel/pull/83#discussion_r3703906593) | Runtime construía wheels durante discovery. | `test_release_metadata.py`: prueba de wheel; `verify_reproducible_wheel.py`: auditoría sintética | `ReleaseVerifierTests.test_runtime_never_invokes_build_or_wheel_auditor` | mismos jobs: pendiente | `todavía abierto` |
| [#85 r3704427263](https://github.com/Alphonsus411/card_duel/pull/85#discussion_r3704427263) | Límite de token aceptaba `_` final. | `config/security-rules.json`: `github_fine_grained_token` | `RepositorySecretPatternTests.test_github_pat_token_with_underscore_suffix_is_accepted_whole` | mismos jobs: pendiente | `todavía abierto` |
| [#86 r3704803184](https://github.com/Alphonsus411/card_duel/pull/86#discussion_r3704803184) | Detector omitía “Desafío exige Reinos”. | `test_mythic_documentation.py`: `OBSOLETE_PATTERNS` | `MythicDocumentationTests.test_detector_recognizes_each_obsolete_claim` | mismos jobs: pendiente | `todavía abierto` |
| [#88 r3705117209](https://github.com/Alphonsus411/card_duel/pull/88#discussion_r3705117209) | Cierre conservaba solo la fecha inicial. | `CONFORMANCE_REVIEW_0.20.1.md`: fechas inicial/final | `ReleaseMetadataTests.test_current_documents_agree_on_completed_roadmap_deliveries` | mismos jobs: pendiente | `todavía abierto` |
| [#89 r3706082083](https://github.com/Alphonsus411/card_duel/pull/89#discussion_r3706082083) | 0.20.1 sobrescribía evidencia 0.20.0. | `release-results/{0.20.0,0.20.1}`; `verify_release.py`: `release_result_path` | `ReleaseMetadataTests.test_0200_results_are_the_exact_bytes_from_the_last_matching_commit` | mismos jobs: pendiente | `todavía abierto` |

Las rutas Python de la tabla son relativas a `src/card_duel_engine/`, salvo que se
indique otro directorio.

## Riesgos restantes

1. **Checks finales pendientes.** Ningún hilo puede ascender a `corregido` hasta que
   los cuatro jobs del SHA final terminen en verde.
2. **Estado remoto.** La API pública permitió consultar comentarios y checks, pero
   no mutar `isResolved`; todos deben permanecer abiertos hasta aplicar el criterio.
3. **Historia Git requerida.** La prueba de bytes de 0.20.0 necesita `006534e`; el
   workflow ahora obtiene historia completa y una prueba protege la configuración.

Tras CI se sustituirá “pendiente” por cada enlace exacto y solo entonces se resolverá
el hilo respaldado. Cualquier fallo conservará `todavía abierto` y este riesgo.
