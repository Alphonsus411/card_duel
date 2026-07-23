# Trazabilidad de reglas

Esta matriz enlaza grupos de `RULES_BASELINE.md` con implementación y pruebas.
No convierte normalizaciones ni pendientes en reglas nuevas.

| Grupo | Módulos autoritativos | Pruebas principales |
|---|---|---|
| Preparación, mano, robo, Reserva, fases y descarte | `engine/game.py`, `engine/zones.py`, `rules/config.py` | `test_setup_and_phases.py`, `test_resources_and_zones.py` |
| Pago atómico, habilidades, costes alternativos, dinámicos y X | `engine/game.py`, `rules/resolvers.py`, `domain/models.py` | `test_stack_and_priority.py`, `test_advanced_mechanics.py`, `test_dynamic_rules_v070.py`, `test_variable_rules_v080.py` |
| Prioridad, pila, objetivos, búsquedas y disparos | `engine/stack.py`, `engine/effects.py`, `engine/game.py` | `test_stack_and_priority.py`, `test_resolution_v050.py`, `test_extensibility_v060.py` |
| Efectos, prevención, daño, regeneración y estado | `engine/effects.py`, `engine/game.py`, `engine/zones.py` | `test_effect_manager_v0170.py`, `test_advanced_mechanics.py`, `test_resolution_v050.py` |
| Combate, Desafío, Divinos, Señores y Legendaria | `engine/combat.py`, `engine/game.py` | `test_combat_and_legendary.py`, `test_mythic_v040.py` |
| Zonas, barajado, sustituciones y control | `engine/zones.py`, `engine/stack.py`, `engine/effects.py` | `test_resolution_v050.py`, `test_extensibility_v060.py`, `test_variable_rules_v080.py` |
| Texto efectivo, copia y transformación | `rules/resolvers.py`, `engine/effects.py`, `engine/game.py` | `test_dynamic_rules_v070.py`, `test_extensibility_v060.py` |
| Documentos v2 y migraciones v1 | `persistence/`, `content/manifest.py` | `test_persistence_v090.py`, `test_hardening_v0100.py` |
| Persistencia CAS | `storage/`, `service.py` | `test_service_v0110.py`, `test_hardening_v0100.py` |

## Ambigüedades y deuda normativa conservadas

- Reparto entre bloqueadores en orden declarado, pendiente de aclaración.
- Regeneración como escudo consumible, sin inferir un procedimiento ausente.
- Precedencia Mítica para la inmunidad de Divinos.
- Firma de colecciones, esquemas 3+, red/autenticación y registro formal de
  contradicciones siguen siendo pendientes, no reglas.

## Trazabilidad 0.18.0

El registro de colecciones es infraestructura de contenido y no modifica reglas observables. Los manifiestos, snapshots y replays continúan en esquema v2 y las migraciones v1 a v2 permanecen vigentes. La igualdad exacta entre una definición del mazo y la registrada se comprueba antes de crear la partida.
