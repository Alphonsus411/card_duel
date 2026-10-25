# CAP-TAXONOMY-001 T5 — matriz de verificación

**Fecha:** 2026-10-25
**Estado:** T5 completada; sin ampliar la capability

## Matriz acreditada

| Eje | Evidencia | Resultado exigido |
| --- | --- | --- |
| Positivo de modelo | T2: `LORD + dominio` y `CREATURE + dominio`. | Ambas formas conservan su `CardKind` acreditado. |
| Filtro y proyección | T4: filtros por tipo y JSON público. | No se deduce tipo por dominio; no se expone el dominio. |
| Literalidad | T5: `Pixy` frente a `Pixie`. | No existe alias implícito. |
| Rechazo cerrado | T5: `LordDomain` futuro en el codec. | Se rechaza el enum desconocido, sin fallback. |
| Snapshot y replay actuales | T3: snapshot v5 y replay v4. | Conservan las dos formas acreditadas y su digest. |
| Legado | T5: golden snapshot v1 y replay v2 de 0.19.0. | Un `lord_domain` ausente sigue ausente tras la lectura; no se inventa un valor. |

## Determinismo y compatibilidad

Los recorridos actuales de snapshot y replay se verifican en T3 con las dos
formas de Señor. T5 añade los *golden artifacts* históricos para demostrar el
caso complementario: la ausencia documentada de dominio no se completa al
migrar. Las versiones originales, v1 para snapshot y v2 para replay, se fijan
en la prueba para evitar presentarlas como formatos taxonómicos nuevos.

El rechazo de un miembro futuro de `LordDomain` es deliberado: aceptar un
valor desconocido, convertirlo en `None` o asignarle un tipo implícito rompería
la separación de dimensiones y el requisito de rechazo cerrado.

## Salida de fase

T5 acredita la matriz técnica permitida. No cierra `CAP-TAXONOMY-001`: siguen
fuera de alcance Leyenda autónoma, tipos impresos múltiples, aliases y
procedencia de subtipos, selectores por dominio y exposición pública de ese
campo. La capability conserva estado `PARTIAL / READY` hasta la nota final T6.
