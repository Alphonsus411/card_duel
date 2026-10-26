# CAP-EFFECT-001 / E6 — Matriz de fizzle en runtime

Fecha: 2026-10-26
Estado: completada

## Objetivo

Demostrar el cuarto requisito del contrato E0 para el vocabulario cerrado: un
target que ya no es válido en resolución produce el fizzle diagnóstico previsto
y no deja mutaciones parciales del estado de partida.

## Cobertura añadida

`tests/test_effect_fizzle_e6.py` construye una forma declarativa válida de cada
uno de los 23 `EffectKind` y la invoca con un target de runtime inválido. Para
todas las familias —jugador, permanente, zona y reparto— exige:

1. un único evento `EFFECT_FIZZLED` con razón `invalid_target`;
2. identidad del resto de `GameState` antes y después, una vez aislado ese
   evento de diagnóstico;
3. ausencia de movimiento, daño, cambio de control, modificación, prevención,
   revelación o continuación creados parcialmente.

Esta matriz complementa, pero no sustituye, la revalidación de inmunidad basada
en el perfil de fuente ni los rollbacks transaccionales ya caracterizados en las
pruebas de resolución y revelación.

## Límites preservados

- No se cambia la semántica de ningún handler ni se añade recuperación nueva.
- No se generaliza una continuación para búsquedas ni se implementa composición,
  secreto, triggers, LKI, audiencias o estado continuo.
- No cambian `EffectKind`, `EffectDefinition`, el esquema ni los replays.

## Resultado

E3, E5 y E6 cubren ahora el registro cerrado, la validación previa y el fallo
seguro al resolver. `CAP-EFFECT-001` continúa `PARTIAL / READY`: las pruebas no
prueban textos compuestos ni desbloquean ninguna capability dependiente.
