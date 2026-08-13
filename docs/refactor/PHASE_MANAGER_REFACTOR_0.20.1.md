# Refactor conservador de `PhaseManager` — 0.20.1

## 1. Decisión

**GO.** La extracción se limita a coordinación de transiciones y conserva el
mismo `GameState` autoritativo. La decisión se apoya en la prueba diferencial
específica y en la validación integral, no en cambios de snapshots.

## 2. Objetivo

Separar del coordinador general las tres operaciones mecánicas diagnosticadas:
avanzar una fase, terminar/rotar el turno e iterar fases suprimidas. No se añade
ninguna regla del juego ni estado persistente.

## 3. Funciones realmente movidas

Los cuerpos de `GameEngine._advance_phase`, `GameEngine._finish_turn` y
`GameEngine._enter_phase_or_skip` se trasladaron respectivamente a
`PhaseManager.advance_phase`, `finish_turn` y `enter_phase_or_skip`. Los métodos
privados originales permanecen como fachadas compatibles.

## 4. Frontera que permanece en `GameEngine`

No se movieron `_phase_is_suppressed`, `_enter_phase`,
`_cleanup_end_of_turn`, `_draw` ni `_emit`. Tampoco se movieron mantenimiento,
efectos legendarios, stack, prioridad, combate, acciones basadas en estado,
terminalidad, codec, snapshot o replay.

## 5. Contrato mínimo

`PhaseContext` expone solamente estado en ejecución, secuencia, límite de mano,
cleanup, consulta de supresión, entrada y emisión. `PhaseManager` no recibe
`RuleSet`, catálogo, gestores de dominio ni una copia del estado.

## 6. Estado autoritativo

El gestor sólo almacena `_context`. Todas las lecturas y mutaciones se realizan
sobre la instancia de `GameState` devuelta por el motor. Una prueba explícita
protege que el gestor no adquiera estado independiente.

## 7. Secuencia configurable

El sucesor se calcula con `_phase_sequence`, proyección de
`rules.phase_sequence`; no existe una segunda tupla codificada en el gestor. El
orden configurado continúa siendo la única autoridad.

## 8. Puertas de avance

Se preservan literalmente las comprobaciones de jugador activo, pila vacía,
ventana de prioridad cerrada, combate resuelto y límite de mano en descarte, con
los mismos tipos y mensajes de error.

## 9. Transición intermedia

Para una fase distinta de descarte se busca el índice actual y se coordina la
entrada del elemento siguiente. No se modifica jugador, turno, serial ni ronda.
La prueba diferencial cubre `DRAW` y `EFFECTS` en ambos perfiles semánticos.

## 10. Fin de turno

El orden sigue siendo cleanup delegado, incremento de `turn_serial`, rotación de
`active_player_index` e incremento de `turn_number` sólo al volver al índice
cero. Después se coordina `DRAW` o su supresión para el nuevo jugador.

## 11. Supresiones

El gestor pregunta al motor si la candidata está suprimida; no inspecciona ni
consume `PhaseSuppression`. La caracterización cubre una supresión
`NEXT_OCCURRENCE`, su retirada, el salto a `EFFECTS` y el orden de eventos.

## 12. Límite de progreso

Se conserva la comparación estricta tras cada skip contra
`len(phase_sequence) * len(turn_order)`. Al excederla se mantiene la mutación a
`MatchStatus.BLOCKED` y la delegación de `ALL_PHASES_SUPPRESSED`.

## 13. Eventos

La emisión sigue delegada a `GameEngine._emit`. El gestor sólo coordina las dos
invocaciones preexistentes, `PHASE_SKIPPED` y `ALL_PHASES_SUPPRESSED`, con los
mismos argumentos; `PHASE_STARTED` continúa perteneciendo a `_enter_phase`.

## 14. Automatismos de entrada

Robo, enderezado, ganancia de pasos y cola legendaria permanecen detrás de
`_enter_phase`. Por ello el nuevo módulo no conoce zonas de mazo/descarte,
definiciones de cartas, efectos ni stack.

## 15. Compatibilidad de API

`AdvancePhase` sigue despachándose a `GameEngine._advance_phase`; llamadas
internas y consumidores existentes conservan los nombres privados anteriores.
No cambian comandos, modelos, eventos ni exportaciones públicas.

## 16. Compatibilidad persistente

No se añade ningún campo a `GameState`, snapshot o replay. La prueba compara el
estado completo mediante `encode_value`, incluida la secuencia ordenada del log
de eventos, después del cuerpo anterior y del gestor extraído.

## 17. Compatibilidad `CURRENT` y `LEGACY_019`

La coordinación no consulta ni infiere semántica. La prueba parametrizada
repite transiciones intermedias y de descarte con `EngineSemantics.CURRENT` y
`LEGACY_019`, y exige igualdad completa del observable codificado.

## 18. Interfaz de pruebas

`pytest` se declara en el extra `dev` y queda fijado en `uv.lock`, de modo que el
comando solicitado `uv run pytest -q tests/test_phase_manager_parity.py` es una
interfaz reproducible del proyecto. `unittest discover` continúa siendo parte
de la validación integral.

## 19. Evidencia de release y seguridad

Los perfiles runtime/full, mypy, compileall, unittest y construcción
reproducible finalizaron correctamente. Los dos PDF normativos conservaron los
SHA-256 registrados; no se editaron ni se incluyeron en el wheel.

## 20. Conclusión y trabajo excluido

La frontera mínima queda extraída con decisión **GO**. Una extracción futura de
supresiones, entrada, cleanup, prioridad o automatismos requeriría una tarea y
caracterización propias; este cambio no la presupone ni amplía su alcance.

## Matriz diferencial de cierre

La batería ampliada se ejecutó con
`uv run pytest -q tests/test_phase_manager_parity.py` y terminó con **26 pruebas
aprobadas**. `igual` significa que el cuerpo anterior y `PhaseManager`
produjeron el mismo observable; `✓` señala una comprobación ejecutada y
aprobada. La igualdad del estado completo se obtuvo con su representación
persistible, que incluye el log ordenado de eventos. Las celdas de perfil no
extrapolan resultados: cuando el caso no se ejecutó expresamente bajo una
semántica, se indica literalmente `NO EJECUTADO`.

| Escenario | Igualdad `Previous vs PhaseManager` | Estado completo | Eventos | `CURRENT` | `LEGACY_019` |
|---|---|---|---|---|---|
| Transición normal (`DRAW`, `EFFECTS` y `DISCARD`) | igual | ✓ | ✓ | ✓ | ✓ |
| `NEXT_OCCURRENCE` apilada | igual | ✓ | ✓ | ✓ | NO EJECUTADO |
| Continua más almacenada | igual | ✓ | ✓ | ✓ | NO EJECUTADO |
| `END_OF_TURN` | igual | ✓ | ✓ | ✓ | NO EJECUTADO |
| Tres jugadores (`A → B → C → A`) | igual | ✓ | ✓ | ✓ | NO EJECUTADO |
| Draw fallido por mazo y descarte vacíos | igual | ✓ | ✓ | ✓ | NO EJECUTADO |
| Reciclaje de descarte | igual | ✓ | ✓ | ✓ | NO EJECUTADO |
| Cleanup de modificador expirable | igual | ✓ | ✓ | ✓ | NO EJECUTADO |
| `BLOCKED` por todas las fases suprimidas | igual | ✓ | ✓ | ✓ | NO EJECUTADO |
| `FINISHED` en las tres fronteras | igual | ✓ | ✓ | ✓ | NO EJECUTADO |
| Combate pendiente | igual | ✓ | ✓ | ✓ | NO EJECUTADO |
| Stack no vacío | igual | ✓ | ✓ | ✓ | NO EJECUTADO |
| Prioridad abierta y frontera cerrada | igual | ✓ | ✓ | ✓ | NO EJECUTADO |
| Acciones legales ordenadas antes y después | igual | ✓ | ✓ | ✓ | NO EJECUTADO |
| Supresión simple `NEXT_OCCURRENCE` | igual | ✓ | ✓ | ✓ | NO EJECUTADO |
| Escenario legacy adicional: supresión de `DRAW` al cambiar turno | igual | ✓ | ✓ | NO EJECUTADO | ✓ |
