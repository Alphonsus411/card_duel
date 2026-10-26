# CAP-EFFECT-001 — E1: inventario de rutas declarativas

**Fecha:** 2026-10-26
**Estado de la fase:** completada; inventario estático sin cambio de runtime
**Capability:** `CAP-EFFECT-001` permanece `PARTIAL / READY`.

## Recorrido autorizado actual

| Etapa | Superficie | Evidencia y responsabilidad | Límite observado |
| --- | --- | --- | --- |
| Declaración | `CardDefinition.effects`, `legendary_effects` y `AbilityDefinition.effects` | reciben tuplas de `EffectDefinition`; sus validaciones fijan forma local, objetivos y campos propios del discriminador | no son catálogo completo ni autorizan despacho por identidad de carta |
| Transformación de definición | `rules/resolvers.py` | los parches reconstruyen la definición y sus tuplas de efectos, preservando el tipo declarativo | no implementa layers ni composición general (`CAP-EFFECT-002/003`) |
| Entrada ordinaria | `GameEngine._play_card` | paga/revalida y crea `StackItem` con efectos y objetivos congelados; la carta pasa a `RESOLUTION` | el pago y la legalidad pertenecen a sus capabilities de acción/coste |
| Entrada activada | `GameEngine._activate_ability` | crea `StackItem` con `ability_id`, objetivos y `AbilitySourceProfile` congelado | el perfil no convierte la habilidad en una nueva fuente de reglas |
| Entrada disparada o legendaria | `StackManager._queue_triggered_abilities` y `_queue_legendary_effects` | construyen ítems desde las definiciones existentes y los entregan a la política actual de pila | orden general de triggers sigue siendo `CAP-TRIGGER-001` |
| Resolución | `StackManager._continue_stack_resolution` → `GameEngine._apply_effect` → `EffectManager.apply` | selecciona los targets congelados por modo, delega la ejecución y termina con acciones basadas en estado | la secuencia de varios efectos aún no acredita composición general |
| Pausa de búsqueda | `StackManager._continue_stack_resolution` / `_resolve_search_choice` | `SEARCH_ZONE` crea `PendingSearch`, bloquea comandos ajenos y reanuda desde el índice siguiente tras revalidar la selección | es una especialización existente; no es `PendingChoice` universal ni secreto compuesto |
| Persistencia | `persistence/codec.py`, `snapshot.py` y `PendingSearch` | el codec codifica enums/dataclasses anidados; snapshot alcanza efectos incluidos en `StackItem` y el estado pendiente | una evolución de campos o significado exige versión, migración y goldens; no basta el decoder genérico |

## Cobertura por familia y pruebas actuales

| Familia | Resolución final | Evidencia principal |
| --- | --- | --- |
| Jugador y permanente | `EffectManager` delega a los métodos autoritativos de `GameEngine` después de validar target o inmunidad | `test_effect_manager_v0170.py`, `test_resolution_v050.py` |
| Zona y revelación | movimientos por `ZoneManager`; `REVEAL_UNTIL` recorre la zona y emite sus eventos; búsqueda se pausa en la pila | `test_effect_manager_v0170.py`, `test_reveal_until.py`, `test_extensibility_v060.py` |
| Objetivos y reparto | `StackItem` conserva listas o `TargetAllocation`; la resolución vuelve a comprobar existencia, campo de batalla e inmunidad | `test_targeting_local_cache_parity.py`, `test_legal_action_enumerator_parity.py` |
| Snapshot y legado | codec de dataclasses y fixtures de búsqueda pendiente/efectos anidados | `test_persistence_v090.py` y fixtures de replay históricos |

El test de registro cerrado acredita que los 23 miembros actuales de `EffectKind`
tienen handler. No demuestra que todos los textos de carta, todas las secuencias
de efectos o cada interacción de privacidad estén resueltos.

## Fronteras de compatibilidad detectadas

1. `EffectDefinition` viaja anidado en definiciones, `StackItem` y
   `PendingSearch`; modificar nombres de enum, campos o significado afecta
   snapshots y reanudaciones en curso.
2. El codec tolera únicamente la ausencia histórica de
   `failure_destination_zone` y `exhaustion_policy`. Esa excepción es de legado
   conocido, no una política para añadir defaults nuevos.
3. Los objetivos son congelados al apilar, pero se revalidan al resolver. E1 no
   permite sustituir esa revalidación por la lectura de una definición o de una
   carta que ya abandonó su zona.
4. Las rutas de zona, control, daño y prevención llaman a autoridades externas.
   Su presencia en una primitiva no cierra `CAP-ZONE-003`, `CAP-DAMAGE-002`,
   `CAP-IMMUNITY-001` ni sus dependientes.

## Salida de E1

E2 podrá diseñar un modelo mínimo de extensión sólo para huecos atómicos
demostrados por el inventario. Antes de tocar `EffectKind`, `EffectDefinition`,
codec, snapshot, replay o eventos tendrá que declarar su estrategia de
versionado y comprobar que no adelanta `CAP-EFFECT-002`, `CAP-EFFECT-003`,
secretos, triggers o corpus.
