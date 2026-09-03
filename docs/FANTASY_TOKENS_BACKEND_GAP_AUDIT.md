# Auditoría de cobertura fuente de Fantasy Tokens

Fecha de la auditoría: 2026-09-03.

## Alcance y resultado

Esta auditoría es un inventario **de fuente**, no una interpretación ni una propuesta de implementación. El inventario fila a fila está en [`FANTASY_TOKENS_SOURCE_INVENTORY.csv`](FANTASY_TOKENS_SOURCE_INVENTORY.csv). No se modificaron el motor, las pruebas, los enums, los modelos, el contenido ejecutable, la versión ni el lockfile.

La revisión cubrió físicamente, en orden, las **31/31 páginas** de *Fantasy Tokens* y las **18/18 páginas** de *Fantasy Tokens Edición Mítica*: **49/49 páginas (100 %)**. Incluye portadas, índices, introitos, reglas, ejemplos/listas de mazos promocionales, notas editoriales y todo el corpus de cartas.

## Paso 1 — verificación previa a la extracción

Antes de extraer texto se compararon SHA-256, tamaño en bytes y cantidad de páginas con `docs/RULES_SOURCES.json`. Para el recuento previo se inspeccionaron los objetos `/Type /Page` de cada PDF; después de esa comprobación, el lector de PDF volvió a confirmar los mismos totales al abrir los documentos.

| Fuente | SHA-256 manifestado / observado | Bytes manifestados / observados | Páginas manifestadas / observadas | Discrepancia |
|---|---:|---:|---:|---|
| `Fantasy Tokens.pdf` | `1c51dabe2023626ad532368e2567d2084c47ec137c7a738bd8c0e0b707f86b21` / igual | `1283314` / `1283314` | `31` / `31` | Ninguna |
| `Fantasy Tokens Edicion Mitica.pdf` | `61243b30d219dd12d8897a206ed664d95a5e3c38b6670a818933f6d90904af36` / igual | `4129473` / `4129473` | `18` / `18` | Ninguna |

No se sustituyó ningún dato del manifiesto. Si una comprobación hubiera discrepado, se habría conservado el valor manifestado y registrado por separado el observado.

## Paso 2 — método de recorrido y transcripción

1. Se recorrieron secuencialmente todas las páginas físicas, sin omitir portada ni páginas que empezaban con la continuación de una entrada anterior.
2. Se usó únicamente la capa textual incorporada en los PDF. **No se aplicó OCR** ni se reconstruyó texto dudoso por conjetura.
3. Cada página tiene una fila `PAGE` en el CSV; estas 49 filas son el control explícito de recorrido.
4. Además, cada unidad normativa/editorial/formato identificada tiene su propia fila, y cada definición de carta/token tiene una fila independiente.
5. Los extractos son breves y conservan la grafía de la fuente (incluidos errores tipográficos de origen); solo se colapsaron espacios y saltos de línea para que el CSV sea manejable.

## Paso 3 — esquema y clasificación del inventario

Cada fila registra:

- `pdf`;
- `pagina_fisica` (la portada es siempre la página física 1);
- `pagina_logica` impresa por el documento;
- `seccion`;
- `numero_carta_token` (`PAGE`, identificador normativo/editorial, o identificador de colección);
- `clase_contenido`;
- `extracto_fuente_breve`.

Las clases distinguen explícitamente **reglas generales**, **reglas de formato**, **texto de cartas**, **ejemplos**, **material editorial** y **políticas de torneo**. Cuando una página contiene más de una clase, la fila de recorrido las enumera separadas por `/`; las filas detalladas mantienen la clase específica.

`UNKNOWN` se reserva para datos que no pueden leerse con seguridad. Las dos portadas no imprimen número lógico, por lo que sus filas consignan `pagina_logica=UNKNOWN`. No se detectó otra página o porción inventariada cuyo texto exigiera una reconstrucción insegura.

## Paso 4 — denominadores de cobertura conservados

| Unidad de cobertura | Base | Mítica | Total procesado / denominador |
|---|---:|---:|---:|
| Páginas físicas | 31 | 18 | **49/49** |
| Filas de sección normativa, de formato, editorial o ejemplo | 42 | 18 | **60/60** |
| Cartas/tokens definidos | 250 (Alpha 103 + Beta 147) | 181 | **431/431** |
| Filas de control de página | 31 | 18 | **49/49** |
| Filas de datos del inventario | 323 | 217 | **540** |

El denominador de cartas se deriva de las entradas realmente publicadas, no del número más alto aislado. En la edición base, Alpha es continua de 1 a 103 y Beta de 1 a 147. En Mítica aparecen 181 entradas: identificadores 1–90 y 100–189, con el nº 176 impreso dos veces para cartas distintas.

## Discrepancias y anomalías de la fuente (sin corrección silenciosa)

- **No hay discrepancias de integridad** entre los dos archivos y `docs/RULES_SOURCES.json`.
- La numeración de Mítica salta del nº 090 al nº 100: los números **091–099 no aparecen** en el corpus extraído. Además, **el nº 176 se imprime dos veces**, para «Nirvana» y «Tambor Chamánico». El inventario conserva tanto el salto como la duplicación; no crea cartas ficticias ni renumera las existentes. Los dos identificadores 176 añaden el nombre para que cada fila siga siendo inequívoca.
- La fuente usa puntuación/espaciado irregular en algunos identificadores (por ejemplo, nº 106 usa coma antes de «Edición Mítica», y nº 164 contiene doble espacio). El CSV conserva un identificador normalizado de inventario, pero el extracto breve mantiene la forma fuente.
- Las listas de los cinco mazos promocionales se clasifican como **ejemplos** de construcción y tienen una fila de sección por mazo. Sus líneas repiten cartas ya inventariadas en Alpha/Beta y, por tanto, no inflan el denominador de cartas definidas.

## Uso para la auditoría de brechas backend

Este documento establece el denominador verificable contra el que puede medirse cualquier cobertura backend posterior. No afirma que una regla o carta esté implementada: una fila significa solamente que el elemento fuente fue localizado, clasificado y trazado a su página. Cualquier análisis de implementación debe enlazar sus hallazgos con el identificador estable de `numero_carta_token` del CSV y mantener separados los hechos de fuente de las inferencias técnicas.
