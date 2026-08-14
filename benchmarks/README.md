# Benchmarks de enumeración legal

`benchmark_action_options.py` mide las consultas públicas y privadas existentes
desde fuera de `GameEngine`; no replica ni sustituye el `product(...)` del motor.

## Perfiles

```bash
python benchmarks/benchmark_action_options.py --profile quick
python benchmarks/benchmark_action_options.py --profile full
```

`quick` conserva los microcasos y usa sólo `SMALL` para poder ejecutarse de
forma interactiva. `full` añade `MEDIUM` y `STRESS_CONTROLLED`, más repeticiones
y los triggers ordenables. Ambos perfiles incluyen los cuatro límites (8, 32,
128 y 512) de `legal_actions`; cada caso reconstruye el mismo escenario con un
`RuleSet` válido que sólo cambia ese límite.

Los casos directos de `_legal_plays`, `_legal_ability_activations` y
`_trigger_target_commands` combinan objetivos de jugador, carta y zona con
repartos. Los dos primeros ejercitan además descartes y sacrificios mediante
costes sintéticos controlados. El perfil `full` mide también `deepcopy` para los
tres tamaños; el cronómetro rodea exclusivamente la llamada de copia.

Cada caso registra duración, memoria actual y pico con `tracemalloc`, conteo y
fingerprint SHA-256. Antes y después de cada repetición se comprueba que el
estado original es idéntico. Para `deepcopy` también se exige equivalencia de la
copia y una identidad de objeto distinta.

## Perfiles semánticos

Los escenarios de alto nivel se guardan por separado bajo `CURRENT` y
`LEGACY_019`; nombre y parámetros JSON identifican el perfil. La estabilidad se
exige dentro de cada caso, pero deliberadamente no se comparan fingerprints
entre perfiles. La compatibilidad 0.19 permite ventanas de activación distintas
para habilidades de Señor fuera de la fase de efectos, mientras `CURRENT` las
restringe. El fixture actual se ejecuta en fase de efectos y por ello no presenta
esa diferencia: en la referencia controlada ambos perfiles producen el mismo
conteo y fingerprint. Si un escenario futuro alcanza la ventana divergente, el
resultado separado documentará la diferencia sin convertirla en un NO-GO.

El perfil `full` mantiene casos finitos mediante el límite productivo y evita
una matriz cartesiana innecesaria; no está diseñado como prueba de carga sin
límite ni como ejecución de decenas de minutos.
