# Frontera de enumeración de acciones legales — 0.20.1

## Alcance de esta iteración

`LegalActionEnumerator` enumera comandos, pero no valida ni ejecuta ninguno. Su
dependencia sobre el coordinador queda declarada estructuralmente mediante
`LegalActionContext`: cada acceso que realiza la enumeración tiene una firma
concreta y usa los tipos de dominio correspondientes.

La consulta `_legal_action_state` devuelve **la misma instancia autoritativa** de
`GameState` que conserva `GameEngine`. No se construye una copia, proyección ni
instantánea: así, la enumeración completa y los helpers a los que delega leen una
única fuente de verdad durante la llamada.

## Justificación del protocolo

| Miembro | Tipo / firma | Motivo de pertenencia |
|---|---|---|
| `_legal_action_state` | `GameState` (propiedad) | Lee fase, estado, prioridad, jugadores, zonas, pila y decisiones pendientes desde el objeto autoritativo. |
| `_legal_action_enumeration_limit` | `int` (propiedad) | Acota búsquedas, permutaciones y selecciones sin exponer el `RuleSet` completo. |
| `_legal_action_hand_limit` | `int` (propiedad) | Calcula el descarte obligatorio sin exponer configuración ajena a la enumeración. |
| `_definition` | `(card_id: str) -> CardDefinition` | Consulta naturaleza, coste y capacidades impresas del permanente recorrido. |
| `_replacement_definitions` | `(definition: CardDefinition) -> tuple[MoveReplacementDefinition, ...]` | Obtiene las sustituciones cuyo orden puede elegir el jugador. |
| `_trigger_target_commands` | `(player_id: str, item: StackItem) -> list[ChooseTriggeredTargets]` | Conserva en el motor la construcción y validación compartida de objetivos disparados. |
| `_legal_plays` | `(player_id: str) -> list[PlayCard]` | Delega la enumeración de jugadas que depende de costes, timing y objetivos. |
| `_legal_ability_activations` | `(player_id: str, source_card_id: str) -> list[ActivateAbility]` | Delega costes, disponibilidad y objetivos de habilidades activadas. |
| `_is_creature` | `(card_id: str) -> bool` | Filtra objetivos de equipamiento según las reglas efectivas del motor. |
| `_legacy_019` | `bool` (propiedad) | Mantiene la ventana histórica de drenaje y habilidades al reproducir semántica 0.19. |
| `_combat_action_enumerator` | `CombatActionEnumerator` (propiedad) | Integra los comandos de combate a través de su propia frontera mínima y tipada. |

## Frontera pendiente

Los helpers de **costes**, **objetivos**, **jugadas** y **habilidades** permanecen
temporalmente en `GameEngine`. Moverlos ahora duplicaría validaciones o podría
alterar reglas observables al separar cálculos que comparten estado y semántica.
Su extracción queda marcada como frontera pendiente para una iteración posterior,
que deberá incorporar pruebas de paridad antes de cambiar su propiedad.

En particular, esta decisión cubre `_card_cost_options`,
`_card_cost_for_option`, `_target_selections`, `_zone_target_selections`,
`_allocation_selections`, `_trigger_target_commands`, `_legal_plays` y
`_legal_ability_activations`, junto con las consultas auxiliares que usan para
timing y selección de objetivos.
