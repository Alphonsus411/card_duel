# Contrato de integración de UI 0.20.1

## Estado y alcance

- **Fase 1-A: COMPLETE**
- **Fase 1-B: COMPLETE**
- **Fase 1: IN PROGRESS**

Este contrato documenta únicamente el límite entre la definición mecánica de
una carta, sus metadatos de presentación y la proyección segura que puede
consumir una interfaz. La finalización de 1-A y 1-B no implica que la Fase 1
global esté completa.

## Separación conceptual

La separación normativa es literalmente:

`CardDefinition = mechanical truth`, `CardPresentation = editorial/display metadata` y `PublicCard = safe UI projection`.

- `CardDefinition` conserva los datos autoritativos que utiliza el motor para
  validar y resolver las reglas.
- `CardPresentation` aporta metadatos editoriales y de visualización vinculados
  mediante `card_id`, sin reemplazar ni modificar la definición mecánica.
- `PublicCard` combina ambos orígenes en una vista inmutable y segura para UI;
  no entrega objetos internos ni convierte metadatos editoriales en reglas.

## Contrato de `CardPresentation`

Cada presentación contiene:

| Campo | Significado |
| --- | --- |
| `card_id` | Identificador que enlaza la presentación con su definición mecánica. |
| `token` | Identificador editorial estable para representación o localización. |
| `name` | Nombre mostrado a las personas usuarias. |
| `rules_text` | Texto humano/editorial que describe la carta. |
| `art` | Referencia visual opcional. |

`rules_text` es exclusivamente humano/editorial y nunca interviene en la
resolución de reglas. El motor no lo interpreta, analiza ni ejecuta; cambiarlo
no puede cambiar el resultado mecánico de una partida.

## Contrato de `PublicCard`

La proyección pública expone los datos mecánicos necesarios para representar
la carta junto con `token`, `name`, `rules_text` y `art`. La construcción exige
correspondencia por `card_id`, rechaza presentaciones huérfanas o ausentes en
una proyección completa y produce un orden determinista por identificador.

La proyección es una frontera de lectura. La UI debe tratar `PublicCard` como
el modelo público de visualización y no como una fuente alternativa de verdad
mecánica.

## Garantías completadas

### Fase 1-A: COMPLETE

- Existe un modelo de presentación separado de las definiciones mecánicas.
- El catálogo de presentación valida campos, unicidad y snapshots defensivos.
- El contenido editorial queda desacoplado de la resolución del motor.

### Fase 1-B: COMPLETE

- Existe una proyección pública inmutable para el consumo de UI.
- La unión entre mecánica y presentación se realiza mediante `card_id`.
- La proyección completa detecta datos ausentes, huérfanos y duplicados.
- Variar metadatos editoriales no altera la verdad mecánica.

Estas garantías completan solamente 1-A y 1-B. **Fase 1: IN PROGRESS**.
