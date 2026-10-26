# CAP-EFFECT-001 / E5 — Matriz de guardas declarativas

Fecha: 2026-10-26
Estado: completada

## Objetivo

Convertir el segundo requisito del contrato E0 en una garantía ejecutable: una
definición de efecto malformada se rechaza al construirse y no puede llegar a la
pila ni a un handler.

## Cobertura añadida

`tests/test_effect_validation_e5.py` verifica las fronteras locales de
`EffectDefinition`:

| Frontera | Casos protegidos |
| --- | --- |
| Modo de objetivo | jugador, permanente, zona y reparto sólo aceptan su selector tipado |
| Payload específico | movimiento/búsqueda requieren destino; revelación requiere filtro, destinos finales y política; transformación, texto y omisión de fase requieren sus campos propios |
| Exclusividad | los campos de revelación y el parche de texto no se aceptan fuera de su primitiva propietaria |
| Rangos | cantidad, X y mínimo/máximo de objetivos se validan antes de apilar |
| Destino de revelación | `REVEAL_UNTIL` no puede conservar `REVEAL` como destino final |

La prueba también conserva una construcción válida de `SKIP_PHASE`, para
distinguir una guarda de una prohibición general de la primitiva.

## Límites preservados

- No se añade ningún `EffectKind`, campo persistido, versión o migración.
- No se modifica resolución, prioridad, pila, secreto, composición, triggers,
  audiencias ni reglas de zona.
- La validación local no sustituye el fizzle de resolución ni la revalidación de
  targets existentes: esas capas siguen cubiertas por las pruebas de motor y
  pertenecen a sus capabilities propietarias.

## Resultado

El registro cerrado queda protegido en los dos extremos declarativos: E3 prueba
que toda primitiva actual tiene una forma mínima válida; E5 prueba que las
formas incompatibles fallan antes de cruzar la frontera de pila. La capability
sigue `PARTIAL / READY`; no se promociona ni desbloquea dependientes.
