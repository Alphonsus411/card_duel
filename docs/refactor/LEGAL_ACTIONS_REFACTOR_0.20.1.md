# Informe posterior: refactor de acciones legales — 0.20.1

## 1. Resultado ejecutivo

La enumeración quedó extraída sin cambiar la API pública: `GameEngine` conserva
`legal_actions(player_id) -> tuple[GameCommand, ...]` y delega su trabajo.

## 2. Base realmente utilizada

La comparación usa `952b1759371eb9c591c7601d906547de4f508449` porque la
comprobación de ancestro terminó con código 0. El HEAD examinado antes de crear
estos informes fue `0d28bb8cbb664f9a7353b512667e539e9d80ff1f`.

## 3. Delegación resultante

La dirección de dependencias implantada es, literalmente:

```text
GameEngine -> LegalActionEnumerator -> consultas del contexto
```

`GameEngine.legal_actions` invoca a su enumerador; éste sólo conoce el protocolo
`LegalActionContext`, y las consultas vuelven al estado y helpers autoritativos
del motor.

## 4. Nuevo enumerador

`LegalActionEnumerator` contiene el flujo de construcción de la tupla: atiende
decisiones, prioridad, combate, jugadas, habilidades, equipamiento, descarte y
concesión, preservando los cortes por límite en sus posiciones originales.

## 5. Contrato del contexto

`LegalActionContext` es un `Protocol` interno y estructural. Expone solamente las
consultas requeridas por la enumeración y evita tipar el colaborador contra todo
`GameEngine`.

## 6. Estado autoritativo

`_legal_action_state` devuelve la misma instancia de `GameState` mantenida por
el motor. No crea copia, proyección ni snapshot; todos los helpers leen la misma
fuente de verdad durante la llamada.

## 7. Consultas escalares

`_legal_action_enumeration_limit` y `_legal_action_hand_limit` proyectan sólo los
dos valores de `RuleSet` necesarios. `_legacy_019` conserva la bifurcación
semántica histórica sin entregar al enumerador el coordinador completo.

## 8. Consultas de dominio

`_definition`, `_replacement_definitions` e `_is_creature` mantienen en el motor
el acceso al catálogo, sustituciones y clasificación efectiva de cartas.

## 9. Consultas de comandos complejos

`_trigger_target_commands`, `_legal_plays` y `_legal_ability_activations`
continúan construyendo alternativas que comparten lógica de costes, timing,
objetivos y validación con el motor.

## 10. Combate

La propiedad `_combat_action_enumerator` entrega la frontera existente de
combate. El enumerador general integra su resultado, pero no duplica su
algoritmo ni conoce la implementación de `CombatManager`.

## 11. API y encapsulación

La fachada pública no cambió. El enumerador y su contexto residen en la capa
`engine`; no importan servicio, aplicación, controladores ni simulación. Las
consultas añadidas son privadas por convención.

## 12. Paridad y no mutación

La prueba de caracterización conserva el cuerpo anterior y compara, desde
estados independientes, resultado/estado del algoritmo previo, enumerador
directo, fachada y llamada repetida. También verifica la excepción previa al
inicio.

## 13. Cobertura de escenarios

Las regresiones cubren decisiones y objetivos, prioridad, fases de combate,
equipamiento, descarte, concesión, estados terminales, límites 1/2/3, perfiles
de mano, legacy 0.19, consumo por servicio y serialización pública.

## 14. Privacidad y arquitectura

Las pruebas comprueban que no se filtran cartas privadas del rival en acciones
públicas, que sólo se exponen nombres públicos y que el módulo extraído permanece
dentro del motor sin dependencias hacia capas exteriores.

## 15. Frontera pendiente

Los helpers `_card_cost_options`, `_card_cost_for_option`,
`_target_selections`, `_zone_target_selections`, `_allocation_selections`,
`_trigger_target_commands`, `_legal_plays` y `_legal_ability_activations`
permanecen temporalmente en `GameEngine`. Extraerlos ahora duplicaría reglas o
separaría cálculos que comparten estado; requerirá otra iteración con paridad
propia.

## 16. Conclusión posterior

La responsabilidad quedó separada con una frontera mínima, tipada y comprobada.
Los resultados recién ejecutados, incluidos intentos fallidos y comprobaciones
no realizadas, se registran exclusivamente en
`results/LEGAL_ACTIONS_REFACTOR_RESULTS_0.20.1.md`.
