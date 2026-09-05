# Fase 2-C: roadmap maestro de evolución del motor

## Propósito, baseline y límites

Este documento prioriza las 62 capabilities de `ENGINE_CAPABILITY_MATRIX.csv` sin convertir frecuencia textual en una falsa medida de valor. El baseline permanece explícitamente congelado: **431/431 entradas auditadas** —Alpha **103**, Beta **147** y Mítica **181**—, correspondientes a **386 identidades** y **45 reimpresiones/variantes**. Sus estados son **2 `SUPPORTED`**, **245 `PARTIAL`**, **143 `MISSING`**, **41 `AMBIGUOUS`** y **0 `CONFLICT`**. Las variantes no se vuelven a contar como identidades ni un desbloqueo transversal se atribuye íntegramente a una sola capability.

La tabla es una herramienta de ordenación arquitectónica, no una promesa de que una capability cierre por sí sola todas las cartas que la mencionan. La evidencia canónica de prerequisites y estados sigue siendo `ENGINE_CAPABILITY_DEPENDENCIES.md`; la evidencia de corpus sigue siendo `CARD_CORPUS_CONFORMANCE.md`; y una duda abierta sigue bajo `NORMATIVE_AMBIGUITIES.md`.

## Modelo ordinal explicable

No se suman columnas ni se calculan medias. Cada dimensión usa exclusivamente `LOW < MEDIUM < HIGH`:

1. **Centralidad de dependencias:** `HIGH` si sostiene tres o más dependientes directos o cruza contratos transversales de estado/efectos/catálogo; `MEDIUM` con uno o dos; `LOW` sin dependientes. Es topología, no popularidad.
2. **Desbloqueo de corpus y reglas:** `HIGH` cuando habilita directamente una primitiva transversal y además cadenas indirectas; `MEDIUM` cuando desbloquea una familia o un siguiente eslabón; `LOW` cuando consolida una hoja ya soportada. No significa “número de cartas arregladas”.
3. **Riesgo para determinismo/replay/persistencia/API:** `HIGH` reúne las severidades `CRITICAL` y `HIGH` de la matriz, porque ambas requieren diseño contractual antes del contenido; `MEDIUM` corresponde a divergencia local; `LOW`, a cambios sin contrato observable previsto.
4. **Claridad normativa:** `HIGH` cuando hay base suficiente para implementar; `LOW` cuando existe bloqueo normativo. `MEDIUM` queda reservado para aclaraciones editoriales acotadas que permitan un núcleo inequívoco, aunque el baseline actual no necesita usarlo.
5. **Coste de migración/reescritura futura:** `HIGH` si cambia modelos serializados, orden/atomicidad, proyección o composición; `MEDIUM` si añade semántica especializada; `LOW` si completa o verifica un contrato estable sin romperlo.

Los ordinales expresan clases argumentables, no precisión matemática. Ante empate se ordena por gate, después por centralidad, riesgo de hacerlo fuera de orden, desbloqueo y por último coste. La frecuencia sólo puede desempatar capabilities con el mismo gate y prerequisites cerrados.

## Gates arquitectónicos y normativos

El campo **Gate** es vinculante:

- `CLOSED`: capability ya soportada; se preserva mediante regresión y no compite como nueva implementación.
- `READY`: prerequisites técnicos cerrados y autoridad normativa suficiente; puede entrar en planificación.
- `WAIT-PREREQ`: queda detrás del primer prerequisite no cerrado, aunque aparezca más veces en el corpus.
- `NORM-BLOCKED`: no se implementa ni se publica una interpretación hasta obtener autoridad normativa; prototipos, si existen, no alteran el contrato público.

Por tanto, ninguna puntuación de frecuencia puede adelantar un nodo `WAIT-PREREQ`, ni una valoración `HIGH` autoriza un nodo `NORM-BLOCKED`. Al cambiar un prerequisite o una fuente normativa se debe reevaluar la fila y sus descendientes, no conservar mecánicamente su orden anterior.

## Fichas de contención por ambigüedad normativa activa

Las fichas siguientes cubren **cada fila** del registro activo de
`NORMATIVE_AMBIGUITIES.md`. Una interfaz preparada o un fixture técnico sólo
preserva opciones de diseño: no constituye evidencia, no cambia el gate y no
puede convertirse en una prueba del canon. `N-TRANSMUTATION-02` se explicita
además porque alimenta directamente `CAP-TRANSMUTE-002` y el carril normativo,
aunque el registro resumido la mantenga trazada desde el documento maestro.

### `N-POINTS-01`

| Capability bloqueada | Capability parcial permitida | Interfaz preparada | Default prohibido | Test normativo pendiente |
|---|---|---|---|---|
| Fijar un presupuesto Mítico canónico o interpretar como tal 200, 300 o 400. | Sumar `CardDefinition.cost`, conservar el mínimo Base y comparar presupuestos entre participantes; validar un límite sólo cuando la configuración lo proporcione expresamente. | Política de construcción con `point_budget: int \| None` y fábricas con `point_budget=None`; el consumidor puede inyectar un límite explícito sin elevarlo a canon. | Cualquier presupuesto implícito, especialmente 200, 300 o 400. | Queda pendiente toda prueba que proclame un presupuesto Mítico canónico; sólo son admisibles pruebas de `None`, suma, comparación e inyección explícita. |

### `N-LEGENDARY-06` / `M-LORD-EVENT-01`

| Capability bloqueada | Capability parcial permitida | Interfaz preparada | Default prohibido | Test normativo pendiente |
|---|---|---|---|---|
| Reclasificar una propiedad de Señor como Evento o derivar por ello inmunidades, targets especiales, interacción con Divinos, pila o semántica de respuesta. | Representar perfiles de fuente y ventanas tipadas; conservar únicamente la Fase Activa expresamente respaldada. | Perfil de fuente parametrizable y política de ventana inyectable, sin activar consecuencias por identidad o por el texto «a modo de Eventos». | `source_type=EVENT`, inmunidad, selector, target o ventana de respuesta inferidos automáticamente. | Quedan pendientes las pruebas canónicas de clasificación, inmunidad, targeting, apilado y respuesta; los tests de perfiles sólo pueden verificar parametrización neutral. |

### `N-COMBAT-03`

| Capability bloqueada | Capability parcial permitida | Interfaz preparada | Default prohibido | Test normativo pendiente |
|---|---|---|---|---|
| Proclamar un orden de bloqueadores como regla canónica o implementar un algoritmo normativo de reparto de daño entre múltiples bloqueadores. | Estructuras deterministas para capturar, serializar y reproducir orden y asignación suministrados explícitamente. | Secuencia ordenada y asignaciones tipadas, versionables y validadas, sin atribuir autoridad normativa al orden de normalización. | Orden por inserción, ID, fuerza o elección del atacante y reparto automático presentados como canon. | Pruebas canónicas de orden, simultaneidad, reparto y sobrante pendientes; fixtures técnicos de codec/replay se mantienen separados y rotulados como no normativos. |

### `N-COMBAT-06`

| Capability bloqueada | Capability parcial permitida | Interfaz preparada | Default prohibido | Test normativo pendiente |
|---|---|---|---|---|
| Determinar para 3+ ganador automático, empate, eliminación, continuidad o terminación global. | Modelos extensibles de resultado y eliminación, capaces de expresar `BLOCKED` y decisiones futuras sin perder participantes ni orden. | Resultado multijugador tipado con política explícita de terminación/eliminación y estado no resuelto. | Extrapolar a 3+ cualquier ganador, empate o fin global derivado de la lógica de exactamente dos jugadores. | Pruebas normativas de eliminación, supervivientes, concesión, empate, ganadores y fin global para 3+ pendientes; sólo se prueba por ahora la conservación determinista de un resultado no resuelto. |

### `N-PHASE-01`–`02`, `N-PHASE-04`–`05`, `N-PHASE-07`, `N-PHASE-09`–`10` — `BASE VIGENTE / MITICA SILENTE`

| Capability bloqueada | Capability parcial permitida | Interfaz preparada | Default prohibido | Test normativo pendiente |
|---|---|---|---|---|
| Añadir por silencio Mítico excepciones a preparación, mulligan, robo, mantenimiento, descarte, pila o enderezado. | Aplicar y probar la regla Base vigente, manteniendo separada su procedencia. | Políticas tipadas por formato/fuente para incorporar una futura extensión Mítica expresa. | Una variante Mítica implícita, tanto más permisiva como más restrictiva que Base. | Pendiente cualquier prueba que afirme una extensión Mítica; las pruebas Base continúan siendo canónicas sólo para la regla Base vigente. |

### `N-ZONE-01`–`03`, `N-COST-03`, `N-COMBAT-04` — `BASE VIGENTE / MITICA SILENTE`

| Capability bloqueada | Capability parcial permitida | Interfaz preparada | Default prohibido | Test normativo pendiente |
|---|---|---|---|---|
| Inventar extensiones Míticas de reciclaje, zonas ocultas, Equipo, coste de equipar o aptitud de combate tras giro. | Mantener sin ampliación ni restricción las reglas Base vigentes y su trazabilidad. | Políticas de zona, coste y elegibilidad parametrizadas por fuente/formato, inicialmente alimentadas sólo con Base. | Sobrescribir Base o añadir una excepción Mítica a partir de ausencia textual. | Pendiente cualquier prueba de diferencia Mítica; fixtures técnicos pueden ejercitar parámetros no canónicos sin etiquetarlos como reglas Míticas. |

### `N-PHASE-03`, `N-COMBAT-05`

| Capability bloqueada | Capability parcial permitida | Interfaz preparada | Default prohibido | Test normativo pendiente |
|---|---|---|---|---|
| Inferir del silencio una secuencia Mítica distinta o condiciones terminales/alcance total para multijugador. | Conservar la secuencia Base y preparar partidas de 2+ con selección explícita de participantes/defensor, sin decidir su final global. | Secuencia y alcance parametrizados; resultado multijugador delega la terminación no resuelta a una política explícita. | Alteración automática de fases o terminación de 3+ por analogía con dos jugadores. | Pendientes las pruebas canónicas de una secuencia Mítica distinta y del alcance/fin 3+; siguen válidas las pruebas Base y los fixtures técnicos no normativos. |

### `N-TRANSMUTATION-02`

| Capability bloqueada | Capability parcial permitida | Interfaz preparada | Default prohibido | Test normativo pendiente |
|---|---|---|---|---|
| Publicar una tabla normativa de ventanas de Transmutación por tipo o rol mientras «fases correspondientes» carezca de definición suficiente. | Preservar la operación atómica común y aceptar una política explícita de timing por tipo para experimentación o futura configuración autorizada. | `TransmutationTimingPolicy` (o contrato equivalente) parametrizado por tipo, actor y ventana, sin tabla canónica incorporada. | Una ventana uniforme o una matriz criatura/Equipo/Evento presentada como interpretación normativa predeterminada. | Pruebas normativas por tipo y rol pendientes hasta disponer de evidencia; sólo se prueban neutralidad, inyección, rechazo seguro, codec y replay de la política explícita. |

## Valoración de las 62 capabilities

Las columnas `Central.`, `Desbloq.`, `Riesgo`, `Claridad` y `Migración` corresponden, en ese orden, a las cinco dimensiones anteriores. La explicación concreta de cada valoración queda trazable en la última columna: estado, prerequisites y dependientes declarados.

| Capability | Estado | Gate | Central. | Desbloq. | Riesgo | Claridad | Migración | Explicación verificable |
|---|---|---|---|---|---|---|---|---|
| `CAP-ACTION-001` — Modelo tipado de acciones y comandos | `SUPPORTED` | `CLOSED` | HIGH | MEDIUM | MEDIUM | HIGH | LOW | Prerequisites: ninguno; dependientes: CAP-ACTION-002, CAP-TIME-003, CAP-EFFECT-001. |
| `CAP-ACTION-002` — Enumeración y revalidación de acciones legales | `SUPPORTED` | `CLOSED` | MEDIUM | MEDIUM | HIGH | HIGH | LOW | Prerequisites: CAP-ACTION-001; dependientes: CAP-TARGET-001, CAP-SECRET-002. |
| `CAP-ACTION-003` — Transacción, rollback y determinismo | `SUPPORTED` | `CLOSED` | HIGH | MEDIUM | HIGH | HIGH | LOW | Prerequisites: CAP-ACTION-001; dependientes: CAP-COST-002, CAP-ZONE-003, CAP-EFFECT-003. |
| `CAP-COST-001` — Modelo declarativo de costes | `SUPPORTED` | `CLOSED` | HIGH | MEDIUM | MEDIUM | HIGH | LOW | Prerequisites: CAP-ACTION-001; dependientes: CAP-COST-002, CAP-COST-003, CAP-COST-004. |
| `CAP-COST-002` — Preflight, determinación y pago atómico | `SUPPORTED` | `CLOSED` | MEDIUM | MEDIUM | HIGH | HIGH | LOW | Prerequisites: CAP-COST-001, CAP-ACTION-003; dependientes: CAP-COST-003, CAP-STACK-001. |
| `CAP-COST-003` — Costes adicionales y compuestos | `SUPPORTED` | `CLOSED` | MEDIUM | MEDIUM | HIGH | HIGH | LOW | Prerequisites: CAP-COST-001, CAP-COST-002; dependientes: CAP-EFFECT-003. |
| `CAP-COST-004` — Costes alternativos | `SUPPORTED` | `CLOSED` | MEDIUM | MEDIUM | MEDIUM | HIGH | LOW | Prerequisites: CAP-COST-001, CAP-COST-002; dependientes: CAP-SECRET-002. |
| `CAP-COST-005` — Costes dinámicos | `SUPPORTED` | `CLOSED` | MEDIUM | MEDIUM | MEDIUM | HIGH | LOW | Prerequisites: CAP-COST-002; dependientes: CAP-COST-006, CAP-EFFECT-003. |
| `CAP-COST-006` — Costes y escala X | `SUPPORTED` | `CLOSED` | MEDIUM | MEDIUM | MEDIUM | HIGH | LOW | Prerequisites: CAP-COST-005; dependientes: CAP-EFFECT-003. |
| `CAP-ZONE-001` — Ownership y control | `SUPPORTED` | `CLOSED` | MEDIUM | MEDIUM | MEDIUM | HIGH | LOW | Prerequisites: CAP-ACTION-001; dependientes: CAP-ZONE-002, CAP-EFFECT-006. |
| `CAP-ZONE-002` — Zonas base y transiciones | `SUPPORTED` | `CLOSED` | HIGH | MEDIUM | MEDIUM | HIGH | LOW | Prerequisites: CAP-ZONE-001, CAP-ACTION-003; dependientes: CAP-ZONE-003, CAP-SEARCH-001, CAP-ATTACH-001. |
| `CAP-ZONE-003` — Puerta uniforme de cambio de zona | `PARTIAL` | `READY` | HIGH | HIGH | HIGH | HIGH | HIGH | Prerequisites: CAP-ZONE-002, CAP-ACTION-003; dependientes: CAP-ZONE-004, CAP-ZONE-005, CAP-ATTACH-001. |
| `CAP-ZONE-004` — Reemplazos de transición | `PARTIAL` | `WAIT-PREREQ` | MEDIUM | MEDIUM | HIGH | HIGH | MEDIUM | Prerequisites: CAP-ZONE-003, CAP-SECRET-002; dependientes: CAP-ZONE-005, CAP-TRANSMUTE-001. |
| `CAP-ZONE-005` — Triggers generales de salida | `MISSING` | `WAIT-PREREQ` | MEDIUM | MEDIUM | HIGH | HIGH | MEDIUM | Prerequisites: CAP-ZONE-003, CAP-STACK-001; dependientes: CAP-EFFECT-003. |
| `CAP-ZONE-006` — Last-known information | `MISSING` | `WAIT-PREREQ` | MEDIUM | MEDIUM | HIGH | HIGH | MEDIUM | Prerequisites: CAP-ZONE-003, CAP-PRIVACY-001; dependientes: CAP-ZONE-005, CAP-EFFECT-003. |
| `CAP-PRIVACY-001` — Proyección pública por audiencia | `SUPPORTED` | `CLOSED` | MEDIUM | MEDIUM | HIGH | HIGH | LOW | Prerequisites: CAP-ZONE-002; dependientes: CAP-SECRET-001, CAP-SEARCH-001. |
| `CAP-SECRET-001` — Mirar sin revelar | `MISSING` | `READY` | MEDIUM | MEDIUM | HIGH | HIGH | MEDIUM | Prerequisites: CAP-PRIVACY-001, CAP-ZONE-002; dependientes: CAP-SECRET-002, CAP-SEARCH-002. |
| `CAP-SECRET-002` — Elección secreta y compuesta | `PARTIAL` | `READY` | HIGH | HIGH | HIGH | HIGH | HIGH | Prerequisites: CAP-ACTION-002, CAP-PRIVACY-001; dependientes: CAP-SEARCH-002, CAP-ZONE-004, CAP-EFFECT-003. |
| `CAP-TARGET-001` — Targets tipados y congelados | `SUPPORTED` | `CLOSED` | MEDIUM | MEDIUM | HIGH | HIGH | LOW | Prerequisites: CAP-ACTION-002; dependientes: CAP-TARGET-002, CAP-IMMUNITY-001. |
| `CAP-TARGET-002` — Selectores multidimensionales | `PARTIAL` | `WAIT-PREREQ` | MEDIUM | MEDIUM | HIGH | HIGH | HIGH | Prerequisites: CAP-TARGET-001, CAP-TAXONOMY-001; dependientes: CAP-SEARCH-001, CAP-EFFECT-002. |
| `CAP-TAXONOMY-001` — Dimensiones canónicas separadas | `PARTIAL` | `READY` | MEDIUM | HIGH | HIGH | HIGH | HIGH | Prerequisites: ninguno; dependientes: CAP-TARGET-002, CAP-KEYWORD-001. |
| `CAP-TAXONOMY-002` — Leyenda y tipos impresos múltiples | `BLOCKED` | `NORM-BLOCKED` | MEDIUM | MEDIUM | HIGH | LOW | MEDIUM | Prerequisites: CAP-TAXONOMY-001; dependientes: CAP-TARGET-002. |
| `CAP-TAXONOMY-003` — Vocabulario, aliases y procedencia de subtipos | `PARTIAL` | `WAIT-PREREQ` | MEDIUM | MEDIUM | MEDIUM | HIGH | LOW | Prerequisites: CAP-TAXONOMY-001; dependientes: CAP-TARGET-002. |
| `CAP-TIME-001` — Preparación inicial | `PARTIAL` | `NORM-BLOCKED` | MEDIUM | MEDIUM | MEDIUM | LOW | LOW | Prerequisites: CAP-ZONE-002, CAP-PRIVACY-001; dependientes: CAP-TIME-002. |
| `CAP-TIME-002` — Mulligan decreciente | `MISSING` | `WAIT-PREREQ` | MEDIUM | MEDIUM | HIGH | HIGH | MEDIUM | Prerequisites: CAP-TIME-001, CAP-SECRET-002; dependientes: CAP-TIME-003. |
| `CAP-TIME-003` — Secuencia y transición de fases | `PARTIAL` | `NORM-BLOCKED` | MEDIUM | MEDIUM | HIGH | LOW | HIGH | Prerequisites: CAP-ACTION-002, CAP-STACK-001; dependientes: CAP-TIME-004, CAP-COMBAT-001. |
| `CAP-TIME-004` — Prioridad y ventanas de respuesta | `PARTIAL` | `NORM-BLOCKED` | MEDIUM | HIGH | HIGH | LOW | HIGH | Prerequisites: CAP-TIME-003, CAP-ACTION-002; dependientes: CAP-STACK-001, CAP-COMBAT-001. |
| `CAP-STACK-001` — Pila LIFO | `SUPPORTED` | `CLOSED` | MEDIUM | MEDIUM | HIGH | HIGH | LOW | Prerequisites: CAP-ACTION-003, CAP-TIME-004; dependientes: CAP-EFFECT-001, CAP-TRIGGER-001. |
| `CAP-TRIGGER-001` — Orden de triggers simultáneos | `PARTIAL` | `NORM-BLOCKED` | MEDIUM | HIGH | HIGH | LOW | HIGH | Prerequisites: CAP-STACK-001, CAP-SECRET-002; dependientes: CAP-ZONE-005, CAP-EFFECT-003. |
| `CAP-STATE-001` — Estado derivado y recálculo | `SUPPORTED` | `CLOSED` | HIGH | MEDIUM | MEDIUM | HIGH | LOW | Prerequisites: CAP-ACTION-001; dependientes: CAP-DAMAGE-001, CAP-COMBAT-001, CAP-EFFECT-002. |
| `CAP-STATE-002` — Duraciones y limpieza | `SUPPORTED` | `CLOSED` | MEDIUM | MEDIUM | MEDIUM | HIGH | LOW | Prerequisites: CAP-STATE-001, CAP-ZONE-002; dependientes: CAP-EFFECT-002, CAP-TRANSFORM-001. |
| `CAP-DAMAGE-001` — Daño y Heridas separados | `SUPPORTED` | `CLOSED` | MEDIUM | MEDIUM | HIGH | HIGH | LOW | Prerequisites: CAP-STATE-001; dependientes: CAP-DAMAGE-002, CAP-COMBAT-001. |
| `CAP-DAMAGE-002` — Prevención tipada por causa y duración | `PARTIAL` | `READY` | MEDIUM | MEDIUM | HIGH | HIGH | LOW | Prerequisites: CAP-DAMAGE-001, CAP-STATE-002; dependientes: CAP-COMBAT-001. |
| `CAP-DAMAGE-003` — Destrucción | `SUPPORTED` | `CLOSED` | MEDIUM | MEDIUM | MEDIUM | HIGH | LOW | Prerequisites: CAP-DAMAGE-001, CAP-ZONE-002; dependientes: CAP-DAMAGE-004, CAP-DAMAGE-005. |
| `CAP-DAMAGE-004` — Regeneración | `SUPPORTED` | `CLOSED` | MEDIUM | MEDIUM | MEDIUM | HIGH | LOW | Prerequisites: CAP-DAMAGE-003; dependientes: CAP-COMBAT-001. |
| `CAP-DAMAGE-005` — Indestructibilidad | `SUPPORTED` | `CLOSED` | MEDIUM | MEDIUM | MEDIUM | HIGH | LOW | Prerequisites: CAP-DAMAGE-003, CAP-STATE-001; dependientes: CAP-IMMUNITY-001. |
| `CAP-ATTACH-001` — Anexos y Equipo | `SUPPORTED` | `CLOSED` | MEDIUM | MEDIUM | MEDIUM | HIGH | LOW | Prerequisites: CAP-ZONE-002, CAP-COST-002; dependientes: CAP-EFFECT-002. |
| `CAP-TRANSFORM-001` — Convertirse en criatura | `SUPPORTED` | `CLOSED` | MEDIUM | MEDIUM | MEDIUM | HIGH | LOW | Prerequisites: CAP-STATE-001, CAP-STATE-002; dependientes: CAP-COMBAT-002. |
| `CAP-TRANSFORM-002` — Copiar/transformar definición y modificar texto | `SUPPORTED` | `CLOSED` | MEDIUM | MEDIUM | MEDIUM | HIGH | LOW | Prerequisites: CAP-STATE-002, CAP-TARGET-001; dependientes: CAP-EFFECT-003. |
| `CAP-SEARCH-001` — Búsqueda filtrada en zona | `PARTIAL` | `WAIT-PREREQ` | MEDIUM | MEDIUM | HIGH | HIGH | MEDIUM | Prerequisites: CAP-ZONE-002, CAP-TARGET-002, CAP-PRIVACY-001; dependientes: CAP-SEARCH-002. |
| `CAP-SEARCH-002` — Revelar hasta coincidencia | `SUPPORTED` | `CLOSED` | MEDIUM | MEDIUM | MEDIUM | HIGH | LOW | Prerequisites: CAP-SEARCH-001, CAP-ACTION-003; dependientes: CAP-EFFECT-003. |
| `CAP-SEARCH-003` — Top-N, fondo y reordenación | `MISSING` | `WAIT-PREREQ` | MEDIUM | MEDIUM | HIGH | HIGH | MEDIUM | Prerequisites: CAP-SECRET-001, CAP-SECRET-002, CAP-ZONE-003; dependientes: CAP-EFFECT-003. |
| `CAP-TRANSMUTE-001` — Operación atómica de Transmutación | `SUPPORTED` | `CLOSED` | MEDIUM | MEDIUM | HIGH | HIGH | LOW | Prerequisites: CAP-ZONE-004, CAP-ACTION-003; dependientes: CAP-TRANSMUTE-002. |
| `CAP-TRANSMUTE-002` — Ventanas por tipo de Transmutación | `BLOCKED` | `NORM-BLOCKED` | LOW | MEDIUM | HIGH | LOW | MEDIUM | Prerequisites: CAP-TRANSMUTE-001, CAP-TIME-004; dependientes: ninguno. |
| `CAP-COMBAT-001` — Combate ordinario | `SUPPORTED` | `CLOSED` | MEDIUM | MEDIUM | HIGH | HIGH | LOW | Prerequisites: CAP-TIME-004, CAP-DAMAGE-001, CAP-STATE-001; dependientes: CAP-COMBAT-002, CAP-COMBAT-003. |
| `CAP-COMBAT-002` — Multibloqueo y asignación ordenada | `BLOCKED` | `NORM-BLOCKED` | MEDIUM | MEDIUM | HIGH | LOW | MEDIUM | Prerequisites: CAP-COMBAT-001, CAP-SECRET-002; dependientes: CAP-KEYWORD-001. |
| `CAP-COMBAT-003` — Desafío | `SUPPORTED` | `CLOSED` | MEDIUM | MEDIUM | HIGH | HIGH | LOW | Prerequisites: CAP-COMBAT-001, CAP-TRANSFORM-001; dependientes: CAP-COMBAT-004. |
| `CAP-COMBAT-004` — Desafío iniciado por efecto/no-Señor | `MISSING` | `WAIT-PREREQ` | MEDIUM | MEDIUM | HIGH | HIGH | MEDIUM | Prerequisites: CAP-COMBAT-003, CAP-TRIGGER-001; dependientes: CAP-EFFECT-003. |
| `CAP-COMBAT-005` — Combate multijugador | `PARTIAL` | `NORM-BLOCKED` | MEDIUM | MEDIUM | HIGH | LOW | MEDIUM | Prerequisites: CAP-COMBAT-001, CAP-PRIVACY-001; dependientes: CAP-COMBAT-006. |
| `CAP-COMBAT-006` — Terminación multijugador | `BLOCKED` | `NORM-BLOCKED` | LOW | MEDIUM | HIGH | LOW | MEDIUM | Prerequisites: CAP-COMBAT-005; dependientes: ninguno. |
| `CAP-KEYWORD-001` — Keywords nominales de combate | `MISSING` | `WAIT-PREREQ` | MEDIUM | HIGH | HIGH | HIGH | HIGH | Prerequisites: CAP-TAXONOMY-001, CAP-COMBAT-001; dependientes: CAP-EFFECT-002. |
| `CAP-KEYWORD-002` — Keywords concedidas y retiradas | `PARTIAL` | `WAIT-PREREQ` | MEDIUM | MEDIUM | HIGH | HIGH | MEDIUM | Prerequisites: CAP-KEYWORD-001, CAP-STATE-002; dependientes: CAP-IMMUNITY-001. |
| `CAP-IMMUNITY-001` — Inmunidades tipadas | `PARTIAL` | `NORM-BLOCKED` | MEDIUM | HIGH | HIGH | LOW | HIGH | Prerequisites: CAP-TARGET-001, CAP-TAXONOMY-001, CAP-STACK-001; dependientes: CAP-EFFECT-001. |
| `CAP-EFFECT-001` — Primitivas declarativas de efecto | `PARTIAL` | `READY` | MEDIUM | HIGH | HIGH | HIGH | HIGH | Prerequisites: CAP-ACTION-001, CAP-STACK-001, CAP-TARGET-001; dependientes: CAP-EFFECT-002, CAP-EFFECT-003. |
| `CAP-EFFECT-002` — Efectos continuos y estado derivado | `PARTIAL` | `WAIT-PREREQ` | MEDIUM | HIGH | HIGH | HIGH | HIGH | Prerequisites: CAP-STATE-001, CAP-STATE-002, CAP-TARGET-002; dependientes: CAP-EFFECT-003. |
| `CAP-EFFECT-003` — Composición de efectos | `MISSING` | `WAIT-PREREQ` | MEDIUM | HIGH | HIGH | HIGH | HIGH | Prerequisites: CAP-EFFECT-001, CAP-SECRET-002, CAP-ZONE-003, CAP-COST-003; dependientes: CAP-CATALOG-001. |
| `CAP-EFFECT-004` — Creación de fichas/instancias | `PARTIAL` | `WAIT-PREREQ` | MEDIUM | MEDIUM | HIGH | HIGH | MEDIUM | Prerequisites: CAP-EFFECT-003, CAP-ZONE-003; dependientes: CAP-CATALOG-001. |
| `CAP-EFFECT-005` — Descarte forzado con elector | `MISSING` | `WAIT-PREREQ` | MEDIUM | MEDIUM | HIGH | HIGH | MEDIUM | Prerequisites: CAP-SECRET-002, CAP-ZONE-003; dependientes: CAP-EFFECT-003. |
| `CAP-EFFECT-006` — Cambio de ownership/control | `SUPPORTED` | `CLOSED` | MEDIUM | MEDIUM | MEDIUM | HIGH | LOW | Prerequisites: CAP-ZONE-001, CAP-STATE-002; dependientes: CAP-EFFECT-003. |
| `CAP-CATALOG-001` — Ingesta completa del corpus | `PARTIAL` | `WAIT-PREREQ` | LOW | HIGH | HIGH | HIGH | HIGH | Prerequisites: CAP-EFFECT-003, CAP-TAXONOMY-001; dependientes: ninguno. |
| `CAP-NORM-001` — Resolución de ambigüedades editoriales | `BLOCKED` | `NORM-BLOCKED` | HIGH | HIGH | HIGH | LOW | MEDIUM | Prerequisites: ninguno; dependientes: CAP-TIME-003, CAP-TIME-004, CAP-COMBAT-002, CAP-COMBAT-006, CAP-TRANSMUTE-002. |
| `CAP-NORM-002` — Presupuesto de puntos Mítico | `BLOCKED` | `NORM-BLOCKED` | MEDIUM | MEDIUM | HIGH | LOW | MEDIUM | Prerequisites: ninguno; dependientes: CAP-CATALOG-001. |

## Catálogo estable de invariantes del motor

Los identificadores `INV-2C-NNN` son referencias contractuales estables: no se
renumeran, reutilizan ni cambian de significado cuando se inserten o retiren
entradas. Un invariante retirado conserva su identificador con estado
`DEPRECATED` y remite a su sustituto. La columna **Pruebas obligatorias** indica
las superficies mínimas que deben aportar evidencia; no limita pruebas
adicionales. Las abreviaturas son: **U** (unitarias), **P** (paridad
enumerador/ejecutor), **C** (codec round-trip), **S** (snapshots heredados),
**R** (replay heredado), **A** (autorización), **CAS** (concurrencia y comandos
obsoletos) e **I** (integración).

| ID estable | Invariante normativo | Pruebas obligatorias |
|---|---|---|
| `INV-2C-001` | El mismo estado inicial, comando, versión semántica y estado/semilla de RNG producen exactamente los mismos eventos, en el mismo orden, y el mismo estado final. | U, C, S, R, CAS, I |
| `INV-2C-002` | Toda fuente de nondeterminismo se captura mediante una semilla reproducible o una decisión persistida; reloj, iteración de colecciones, proceso y cliente no deciden implícitamente el resultado. | U, C, R, CAS, I |
| `INV-2C-003` | Replay reproduce eventos, elecciones, orden y digests compatibles con la versión semántica declarada. | C, S, R, I |
| `INV-2C-004` | Cada snapshot identifica schema y semántica; una versión anterior se migra de forma determinista o se rechaza explícitamente, nunca se interpreta por aproximación. | U, C, S, R, I |
| `INV-2C-005` | La definición inmutable de una carta y su instancia de partida permanecen separadas y poseen identidades distintas. | U, C, S, R, I |
| `INV-2C-006` | `owner_id` y `controller_id` representan relaciones distintas y nunca se fusionan, ni siquiera cuando sus valores coinciden. | U, C, S, R, A, I |
| `INV-2C-007` | Toda transición hacia una zona del propietario resuelve explícitamente el propietario de destino y el controlador resultante; ninguno se infiere del otro. | U, C, S, R, A, I |
| `INV-2C-008` | El estado efectivo se deriva de fuentes canónicas y no se persiste como segunda verdad cuando pueda recalcularse; snapshots y replay almacenan causas, no cachés autoritativas. | U, C, S, R, I |
| `INV-2C-009` | Heridas del jugador, daño marcado en permanentes, Fuerza base/efectiva y modificadores son magnitudes distintas, con tipos, ciclo de vida y limpieza propios. | U, C, S, R, I |
| `INV-2C-010` | La validación de legalidad y la determinación/congelación del coste preceden cualquier mutación de estado. | U, P, R, A, CAS, I |
| `INV-2C-011` | El pago de un coste es atómico: o se aplica completo una sola vez o no cambia el estado; no existe pago parcial ni rollback ambiguo. | U, P, C, R, CAS, I |
| `INV-2C-012` | Pago, activación o apilado y resolución son etapas distintas, observables y ordenadas; completar una no implica haber completado las siguientes. | U, P, C, R, CAS, I |
| `INV-2C-013` | Toda instancia de carta está en exactamente una ubicación coherente, incluida una única zona/contenedor o la ubicación transitoria tipada que corresponda. | U, C, S, R, CAS, I |
| `INV-2C-014` | Todo movimiento atraviesa una única autoridad de transición y aplica allí las políticas declaradas de limpieza y conservación, sin mutaciones laterales de zonas. | U, C, S, R, CAS, I |
| `INV-2C-015` | Observaciones, DTO, errores y opciones se proyectan por audiencia y no filtran identidad, contenido, candidatos ni metadatos ocultos. | U, P, C, S, R, A, I |
| `INV-2C-016` | Ningún comando confía en IDs, targets, elecciones u option tokens enviados por el cliente sin revalidar pertenencia, audiencia, vigencia, cardinalidad y legalidad. | U, P, A, CAS, I |
| `INV-2C-017` | El enumerador y el ejecutor aceptan el mismo conjunto semántico de acciones para el mismo estado, actor y versión; toda opción emitida es ejecutable mientras siga vigente y toda ejecución aceptada era enumerable. | U, P, A, CAS, I |
| `INV-2C-018` | El orden de targets, triggers, reemplazos y efectos es determinista y forma parte del contrato persistido cuando una elección normativa pueda alterarlo. | U, P, C, S, R, I |
| `INV-2C-019` | Ninguna regla se resuelve por nombre de carta, texto editorial o `card_id` concreto; la ejecución despacha únicamente primitivas, capacidades y datos mecánicos tipados. | U, P, C, S, R, I |
| `INV-2C-020` | Transmutación es una acción universal distinta del sacrificio y determina su pago a partir del `CardDefinition.cost` efectivo aplicable, sin duplicarlo en la instancia ni inferirlo del texto. | U, P, C, S, R, A, CAS, I |
| `INV-2C-021` | Implementar una capability no equivale a incorporar, promover ni publicar una carta; cada carta exige trazabilidad y conformidad propias. | U, C, S, R, A, I |
| `INV-2C-022` | Todo fallo de versionado, decodificación o migración es explícito, tipado y atómico: no entrega ni persiste un estado parcialmente cargado. | U, C, S, R, CAS, I |

### Regla de trazabilidad y aceptación

Cada cambio de W0–W7 debe citar los IDs afectados en su diseño, migración y
plan de pruebas. Para cada ID citado se ejecutan todas sus superficies
obligatorias o se documenta un bloqueo de entorno; una prueba en una superficie
no sustituye otra. Los fixtures heredados son inmutables y versionados: **S**
parte del snapshot anterior y verifica migración o rechazo, mientras **R** parte
del log anterior y verifica eventos, decisiones, orden, digest y estado final.
Las pruebas **CAS** deben demostrar tanto rechazo sin mutación del comando
obsoleto como éxito único del comando ganador. Las pruebas **A** se ejercitan
con audiencias autorizadas y no autorizadas. Una capability no puede pasar a
`SUPPORTED` si incumple un invariante aplicable, aunque sus escenarios felices
de integración sean correctos.

## Orden de ejecución por gates

### 1. Fundaciones antes que volumen superficial

La primera ola debe cerrar contratos transversales que ya estén `READY`, empezando por taxonomía canónica y siguiendo la puerta uniforme de zonas, elecciones secretas, targets/selectores, tiempo/prioridad, triggers, keywords/inmunidades y primitivas/composición de efectos **sólo cuando sus prerequisites pasen a `CLOSED`**. `CAP-CATALOG-001` queda al final de esa cadena: ingerir antes el corpus convertiría excepciones por `card_id` en API accidental y obligaría a reescribir snapshots y replay.

Una infraestructura transversal puede preceder legítimamente a una familia con más apariciones superficiales porque una sola decisión de identidad, transición de zona o elección persistible fija invariantes compartidos por muchas familias. Implementar primero la familia visible duplicaría selectores, orden de eventos y codecs; luego habría que migrar esos datos cuando llegue la abstracción común. La aparición textual mide demanda, pero la centralidad mide cuántos contratos pueden quedar incoherentes. Por eso el gate domina a la frecuencia.

### 2. Familias especializadas después de sus bases

Búsqueda top-N, desafío por efecto, creación de fichas, descarte forzado y otras hojas especializadas se planifican después de cerrar zona/secretos/targets/triggers/composición que les correspondan. Cada entrega debe demostrar legal-action parity, snapshot/codec round-trip y replay determinista antes de promover filas de corpus.

### 3. Carril normativo independiente

`CAP-NORM-001` y `CAP-NORM-002` no son tareas de programación: producen decisiones autoritativas y trazables. `CAP-TAXONOMY-002`, `CAP-TRANSMUTE-002`, `CAP-COMBAT-002` y `CAP-COMBAT-006`, además de cualquier tramo abierto de inmunidades o multijugador, permanecen `NORM-BLOCKED`. Una aclaración puede abrir el gate, pero nunca cuenta como implementación ni como soporte de corpus.

## Waves propuestas, sujetas a validación del grafo

Las waves son **fronteras de integración**, no sprints, fechas ni permiso para
ignorar un gate. Antes de iniciar cada capability se reconstruirá el grafo desde
`ENGINE_CAPABILITY_DEPENDENCIES.md`: todos sus prerequisites deberán estar
`CLOSED`, o bien capability y prerequisite deberán entrar juntos en un mismo
componente fuertemente conexo (SCC) con contrato y pruebas de integración
comunes. Un nodo `NORM-BLOCKED` permanece fuera aunque figure en una wave.

La tabla declarativa contiene referencias cruzadas que forman al menos el SCC
`CAP-TIME-003 ↔ CAP-TIME-004 ↔ CAP-STACK-001`: la pila ya existente se
reutiliza como baseline, pero no se usa su estado `SUPPORTED` para fingir que el
canon de fases y prioridad está resuelto. También existen dependencias cuya
implementación actual precede a un prerequisite parcial (por ejemplo,
Transmutación frente a reemplazos de zona). Son deuda a revalidar, no una razón
para invertir aristas. El orden W0–W7 se ajustará topológicamente dentro de cada
wave y, si una arista cruza hacia una wave posterior, el nodo dependiente se
aplazará; **nunca se adelantará el prerequisite sólo para conservar el número de
wave**.

### W0 — Contractos, versionado e invariantes

- **Objetivo:** congelar un baseline compatible y verificable antes de cambiar
  semántica observable.
- **Capabilities:** infraestructura transversal de schema version, comandos y
  eventos; snapshots, replay, serialización, CAS, migraciones y los invariantes
  ya cerrados de `CAP-ACTION-001/003`. W0 no reclasifica por sí sola ninguna
  capability mecánica.
- **Dependencias de entrada:** baseline 0.20.1 reproducible; inventario de todos
  los discriminadores y payloads persistidos; fixtures legacy y autoridad sobre
  la política de compatibilidad.
- **Exclusiones:** nuevas reglas, nuevas cartas, cambios editoriales y una
  migración destructiva sin decoder legado.
- **Normativa relacionada:** versionado de reglas y de fuentes, estabilidad de
  identificadores y las ambigüedades registradas; W0 registra la duda, no la
  decide.
- **Desbloqueo directo/indirecto del corpus:** directo, ninguno; indirecto,
  permite evolucionar todas las familias sin invalidar partidas guardadas ni
  atribuir soporte falso.
- **Superficies técnicas:** `domain/models.py`, `engine/commands.py`,
  `persistence/`, `storage/`, `application.py`, `service.py`, artefactos golden y
  metadatos de release.
- **Riesgos:** versión parcial, eventos reordenados, migración no idempotente,
  ABA/CAS, divergencia snapshot–replay o exposición de campos privados.
- **Criterios de salida:** matriz de versiones escrita; lectura del baseline y
  rechazo determinista de versiones desconocidas; migraciones idempotentes;
  IDs y orden estables; round-trip y replay equivalentes; conflictos CAS sin
  mutación parcial.
- **Categorías de tests:** contract/schema, golden y legacy replay, snapshot y
  codec round-trip, property/migration, determinismo, concurrencia CAS,
  compatibilidad de API y redacción de privacidad.

#### Matriz de impacto y compatibilidad de W0

Esta matriz es obligatoria antes de aprobar cualquier cambio de W1–W7. Cada
fila describe una unidad de cambio prevista y le asigna **una clasificación
principal**. Si una propuesta mezcla filas o clasificaciones, se divide antes
de implementarla; no se rebaja un cambio semántico a «campo opcional». En
particular, un *default exclusivamente técnico* sólo puede reconstruir una
representación cuya semántica anterior sea inequívoca: nunca elige reglas,
targets, orden de combate, audiencia ni decisiones de un jugador.

| Superficie | Cambio previsto | Clasificación principal | Condición y frontera exigidas |
|---|---|---|---|
| `MatchState` / `GameState` | Añadir metadatos no semánticos de procedencia o diagnóstico que puedan reconstruirse inequívocamente. | **Adición compatible mediante campo opcional y default exclusivamente técnico.** | El default no altera legalidad, orden, RNG, resultado ni observación; si afecta a replay pasa a la fila versionada. |
| `MatchState` / `GameState` | Añadir estado autoritativo que cambie fases, prioridad, combate, zonas, elecciones o resolución. | **Cambio que requiere nueva versión de snapshot/replay/manifest.** | El nuevo schema congela su semántica y conserva decoder del formato soportado anterior; no se infiere desde el estado actual. |
| `PlayerState` | Añadir contadores o marcas persistentes con efecto reglamentario. | **Cambio que requiere nueva versión de snapshot/replay/manifest.** | Se serializan de forma determinista y se proyectan por audiencia; ausencia sólo admite default si reproduce exactamente la regla histórica. |
| `PlayerState` | Añadir cachés, índices o marcas transitorias recalculables. | **Detalle interno que no debe entrar en el JSON público.** | No forman identidad persistente ni observable; deben invalidarse o reconstruirse sin modificar el resultado. |
| `CardDefinition` | Añadir metadatos editoriales no normativos y opcionales. | **Adición compatible mediante campo opcional y default exclusivamente técnico.** | El default significa «metadato ausente», no activa una capability ni inventa taxonomía o reglas. |
| `CardDefinition` | Cambiar significado, discriminadores, taxonomía o estructura ejecutable de una definición ya publicada. | **Ruptura deliberada y documentada.** | Nueva versión de manifiesto, nota de ruptura y migrador/diagnóstico cuando proceda; nunca reinterpretación silenciosa por el catálogo nuevo. |
| `CardInstance` | Incorporar identidad o estado por instancia que sobreviva movimientos, snapshot o replay. | **Cambio que requiere nueva versión de snapshot/replay/manifest.** | Se fijan identidad, ciclo de vida y orden; no se reconstruye a partir de una `CardDefinition` mutable. |
| `CardInstance` | Incorporar memoización o valores derivados recalculables. | **Detalle interno que no debe entrar en el JSON público.** | No entra en snapshot/replay salvo que se demuestre que es autoritativo; tampoco aparece en observaciones. |
| Comandos | Añadir un parámetro opcional puramente protocolario. | **Adición compatible mediante campo opcional y default exclusivamente técnico.** | El comando omitido conserva exactamente validación y efecto anteriores; una nueva elección reglamentaria exige comando/schema versionado. |
| Comandos | Cambiar el significado, orden, autorización o precondiciones de un comando existente. | **Ruptura deliberada y documentada.** | Se introduce discriminador/versionado explícito; el decoder antiguo conserva la interpretación antigua y CAS sigue siendo obligatorio. |
| Eventos | Añadir contexto opcional que no cambia causalidad, orden ni consumidores existentes. | **Adición compatible mediante campo opcional y default exclusivamente técnico.** | El payload antiguo sigue siendo suficiente; si el dato gobierna reproducción o proyección, se versiona. |
| Eventos | Cambiar tipo, causalidad, orden o payload necesario para reconstruir la partida. | **Cambio que requiere nueva versión de snapshot/replay/manifest.** | Los eventos históricos se decodifican con su tabla de tipos y semántica, sin normalizarlos al modelo vigente. |
| Reducers / managers | Extraer, cachear o reorganizar código manteniendo la misma transición autoritativa. | **Detalle interno que no debe entrar en el JSON público.** | Paridad diferencial de estado, eventos, errores, contadores, RNG y rollback; no se filtran nombres o estructuras internas. |
| Reducers / managers | Sustituir dos semánticas de combate por una única interpretación nueva. | **Ruptura deliberada y documentada.** | Sólo es aceptable al retirar de forma versionada un formato; mientras ambos sean soportados, se seleccionan por versión y nunca se mezclan. |
| Stores | Añadir metadatos internos de indexación, locking u observabilidad. | **Detalle interno que no debe entrar en el JSON público.** | No cambia CAS, DTO ni bytes canónicos; cualquier dato persistido se revisa además contra la fila SQLite. |
| SQLite | Añadir o transformar tablas, columnas, constraints, índices con efecto en los datos almacenados o en su versión. | **Migración explícita de SQLite.** | Migración identificada, transaccional, idempotente y probada desde cada versión soportada; W0 no diseña todavía el SQL. |
| Snapshots | Alterar campos autoritativos, discriminadores, canonicalización o digest. | **Cambio que requiere nueva versión de snapshot/replay/manifest.** | Golden por versión, decoder seleccionado por `schema_version`, round-trip estable y rechazo explícito de versiones desconocidas. |
| Replay logs | Alterar comandos/eventos registrados o cualquier regla necesaria para reproducirlos. | **Cambio que requiere nueva versión de snapshot/replay/manifest.** | El perfil semántico queda fijado en el documento y la reproducción histórica no se reinterpreta con reglas nuevas. |
| JSON público | Añadir un dato público no sensible que no cambia el significado de los existentes. | **Adición compatible mediante campo opcional y default exclusivamente técnico.** | Respuesta aditiva, documentada y con golden por audiencia; la ausencia mantiene el contrato anterior. |
| JSON público | Renombrar, eliminar o cambiar tipo/semántica de un campo o error publicado. | **Ruptura deliberada y documentada.** | Requiere versión de API/contrato, ventana de retirada y error explícito; nunca se expone el modelo interno como compatibilidad. |
| Fronteras de aplicación | Añadir una operación o DTO seguro sin debilitar identidad, capacidades o CAS. | **Adición compatible mediante campo opcional y default exclusivamente técnico.** | Sigue pasando por `AuthenticatedMatchApplication`; ningún default selecciona jugador, audiencia o autoridad. |
| Fronteras de aplicación | Exponer engine/state, aceptar identidad declarada por cliente, omitir CAS o devolver detalles internos. | **Ruptura deliberada y documentada.** | No es una evolución compatible y queda prohibida por defecto; cualquier sustitución futura exige decisión arquitectónica y versión pública. |

#### Política de decodificación y replay histórico

El discriminador `schema_version` se lee antes de decodificar el cuerpo y
selecciona un decoder registrado para esa versión. No se prueba sucesivamente
el decoder actual hasta que «funcione», no se completa una versión desconocida
con defaults y no se confunde `engine_version`, versión de reglas o versión de
manifiesto con la versión estructural. Toda versión desconocida o retirada falla
de forma controlada, estable y sin mutación parcial.

Decodificar estructura y ejecutar semántica son decisiones separadas. Cada
replay soportado selecciona también el perfil de reglas que quedó fijado al
crearlo: **la semántica histórica de replay no se reinterpreta con reglas
nuevas**, aunque el modelo actual pueda representar sus datos. Una migración
estructural conserva ese perfil; cambiarlo exige una conversión deliberada,
versionada y verificable, nunca una normalización implícita.

Los corpus inmutables bajo `tests/artifacts/0.19.0/` y
`tests/artifacts/0.20.x-pre-source-profile/` se conservan como **gates de
compatibilidad**: no se regeneran con el motor actual para hacerlos pasar. Su
lectura, replay, observables, digest y round-trip deben permanecer cubiertos
mientras sus versiones figuren como soportadas. Retirar ese soporte requiere
una ruptura deliberada, documentada y probada mediante rechazo controlado.

#### Presupuesto de compatibilidad

La compatibilidad razonable y exigida comprende: leer todos los formatos que la
política declare soportados; mantener respuestas públicas aditivas; conservar
identificadores y orden cuando sean contractuales; y devolver errores explícitos
para versiones, migraciones o comandos no admitidos, sin datos inventados ni
mutación parcial.

No se asume, en cambio, el coste indefinido de sostener estados internos
experimentales, caches o prototipos nunca publicados. Tampoco se mantienen dos
semánticas de combate dentro de un mismo schema/perfil, ni se simula
compatibilidad reinterpretando replays antiguos con reglas nuevas. Cuando el
coste de un puente deje de ser razonable se retira en una versión anunciada, con
diagnóstico o migración cuando sea posible y rechazo controlado en los demás
casos.

#### Gates de prueba para cualquier cambio de contrato

Antes de cerrar W0 y en cada evolución posterior afectada son obligatorios:

1. *golden files* independientes para snapshot, replay y JSON público, incluido
   un golden por audiencia cuando exista información privada;
2. round-trips `decode(encode(x))` y `encode(decode(golden))` acordes con la
   canonicalización declarada, más replay repetido con observables y digest
   deterministas;
3. migración SQLite idempotente, transaccional y ejercitada dos veces desde cada
   versión soportada, sin diseñar aquí tablas ni sentencias SQL;
4. rechazo controlado de versiones de schema, replay y manifiesto desconocidas,
   sin fallback, traceback interno ni mutación parcial; y
5. comparación por lista permitida de las observaciones/errores públicos para
   demostrar que ningún campo interno nuevo aparece en JSON, logs o DTO.

Este apartado es exclusivamente de roadmap y contrato. **No diseña todavía
SQL ni autoriza modificar `src/card_duel_engine/persistence/` o
`src/card_duel_engine/storage/`.** Esas implementaciones sólo se abrirán en una
entrega posterior con schema, migración y rollback aprobados.

### W1 — Acciones y costes atómicos

- **Objetivo:** convertir toda intención en una acción legal cuyo coste se
  determina, congela y paga atómicamente antes de activarla/apilarla, para luego
  resolverla y producir efectos derivados.
- **Capabilities:** `CAP-ACTION-001/002/003`, `CAP-COST-001`–`006`, el tramo
  basal de `CAP-EFFECT-001` y la frontera de entrada de `CAP-STACK-001`.
- **Dependencias de entrada:** contratos W0 cerrados y RNG/rollback
  deterministas.
- **Exclusiones:** nuevas ventanas de prioridad, elecciones ocultas generales,
  selectores editoriales completos y handlers por `card_id`.
- **Normativa relacionada:** diferencia entre validar, determinar, pagar,
  activar/apilar y resolver; costes adicionales, alternativos, dinámicos y X;
  qué pagos son reversibles ante ilegalidad.
- **Desbloqueo directo/indirecto del corpus:** directo, familias expresables con
  acciones y costes ya tipados; indirecto, recursos activables, composición de
  efectos y ventanas futuras sin pagos parciales.
- **Superficies técnicas:** `engine/actions.py`, `engine/options.py`,
  `engine/commands.py`, `engine/game.py`, `engine/stack.py`,
  `engine/effects.py`, modelos y persistencia.
- **Riesgos:** opciones obsoletas aceptadas, coste pagado dos veces, respuesta
  antes del pago, rollback incompleto o distinto resultado tras replay.
- **Criterios de salida:** enumeración y ejecución tienen paridad; toda acción
  hace preflight y revalidación; un fallo no cambia estado; coste y valores
  congelados sobreviven snapshot/replay; efectos derivados conservan causa.
- **Categorías de tests:** unitarios por coste, legal-action parity, option-token
  authorization, stale command/CAS, transacción y rollback, stack integration,
  replay determinista y fuzz/property de combinaciones de costes.

### W2 — Tiempo de juego

- **Objetivo:** hacer explícitos mulligan decreciente, fases, ventanas, prioridad
  y protocolo de pases, reutilizando la pila LIFO existente.
- **Capabilities:** `CAP-TIME-001`–`004`, `CAP-STACK-001` y
  `CAP-TRIGGER-001` en el SCC validado; sólo los tramos liberados por
  `CAP-NORM-001`.
- **Dependencias de entrada:** W1 cerrada; elección persistible/autorizada de W3
  disponible para el mulligan o, por la arista real, aplazamiento de
  `CAP-TIME-002`; resoluciones normativas de primera prioridad, ventanas y pases.
- **Exclusiones:** inventar timing para textos ambiguos, reescribir la pila desde
  cero, multibloqueo y Desafío ampliado.
- **Normativa relacionada:** preparación y jugador inicial, tamaño decreciente de
  mano, secuencia/omisión de fases, Recursos Rápidos, primera prioridad,
  cantidad de pases y orden de triggers simultáneos.
- **Desbloqueo directo/indirecto del corpus:** directo, cartas cuya legalidad
  depende sólo de una ventana inequívoca; indirecto, triggers, respuestas,
  combate y Transmutación por ventana.
- **Superficies técnicas:** `engine/phases.py`, `engine/stack.py`,
  `engine/actions.py`, `engine/game.py`, enums/modelos, replay, servicio y
  observación.
- **Riesgos:** el ciclo tiempo–pila, prioridad muerta, pases insuficientes,
  resolución fuera de ventana, diferencias tras reconexión y codificar una
  respuesta a una ambigüedad.
- **Criterios de salida:** SCC integrado sin aristas pendientes; tabla normativa
  fase×acción ejecutable; mulligan decreciente privado y reproducible; pases
  terminan/resuelven exactamente una vez; reconexión conserva turno, ventana,
  prioridad y pila.
- **Categorías de tests:** tablas de fases/ventanas, state-machine/property,
  mulligan y privacidad, protocolos de pase, triggers simultáneos, snapshot en
  cada frontera, reconexión y replay end-to-end.

### W3 — Zonas, movimientos y privacidad

- **Objetivo:** hacer que cada transición cruce una puerta autoritativa y lleve
  causa, audiencia y LKI sin filtrar información.
- **Capabilities:** `CAP-ZONE-001`–`006`, `CAP-PRIVACY-001`,
  `CAP-SECRET-001/002` y las bases de `CAP-SEARCH-001/003`.
- **Dependencias de entrada:** W0–W1; acciones autorizadas; stack/trigger de W2
  para `CAP-ZONE-005`; cuando W2 necesite secretos para mulligan, ambos tramos
  forman un paquete de integración, no una excepción al grafo.
- **Exclusiones:** filtros taxonómicos completos, reglas particulares por carta,
  efectos compuestos que sólo simulen movimientos y revelar información como
  atajo de implementación.
- **Normativa relacionada:** owner frente a controller, destinos, mirar/revelar,
  barajar, reemplazos, triggers de entrada/salida, orden de eventos y elector de
  decisiones ocultas.
- **Desbloqueo directo/indirecto del corpus:** directo, mover, buscar o elegir en
  zonas con filtros ya representables; indirecto, anexos, retorno, exilio,
  descarte, sacrificio, fichas y composición segura.
- **Superficies técnicas:** `engine/zones.py`, `engine/game.py`,
  `engine/stack.py`, modelos, `observe`, aplicación/servicio y todos los codecs.
- **Riesgos:** rutas laterales, doble trigger, LKI mutable, reemplazo no atómico,
  confundir owner/controller y fuga por payload, error, opciones o replay.
- **Criterios de salida:** ninguna ruta muta zona fuera de la puerta; cada evento
  incluye causa/origen/destino/lote/audiencia/LKI definidos; reemplazos y
  triggers se ordenan una vez; matrices por audiencia no filtran secretos;
  elecciones sobreviven reconexión.
- **Categorías de tests:** transition matrix, invariantes owner/controller,
  reemplazo/trigger ordering, LKI, batch atomicity, non-interference y redacción
  por audiencia, elecciones ocultas, persistencia y replay.

### W4 — Taxonomía, targeting y selectores

- **Objetivo:** separar identidad mecánica, vocabulario editorial y selección
  autorizada mediante dimensiones tipadas y componibles.
- **Capabilities:** `CAP-TAXONOMY-001/003` (y `002` sólo si se desbloquea),
  `CAP-TARGET-001/002`, elector/cardinalidad/autorización de
  `CAP-SECRET-002`, y `CAP-SEARCH-001` sobre esos selectores.
- **Dependencias de entrada:** W0 para versionar discriminadores; W1 para
  legalidad/revalidación; W3 para zona, visibilidad y elector.
- **Exclusiones:** inferir raza/subtipo desde nombre o ilustración, usar
  `definition_id` como dispatch mecánico, resolver aliases por heurística y
  declarar soporte sólo porque una carta pueda seleccionarse.
- **Normativa relacionada:** tipo, rango, dominio, raza/subtipo, Leyenda, tipos
  impresos múltiples, grafía/alias/procedencia, naturaleza de fuente, quién
  elige y cardinalidad exacta.
- **Desbloqueo directo/indirecto del corpus:** directo, efectos de raza/subtipo,
  fuente, zona o controlador con cardinalidad inequívoca; indirecto, efectos
  continuos, keywords, inmunidades, búsquedas y composición general.
- **Superficies técnicas:** `domain/enums.py`, `domain/models.py`,
  `engine/options.py`, `engine/actions.py`, `engine/game.py`, presentación,
  catálogo y codecs.
- **Riesgos:** mezclar taxonomía editorial con predicados de runtime, targets
  que cambian tras apilar, selección visible pero no autorizada, aliases
  incompatibles y migraciones ambiguas.
- **Criterios de salida:** registro canónico versionado; selector AND/OR tipado
  para todas las dimensiones autorizadas; targets congelados y revalidados;
  elector y cardinalidad en dominio; ningún handler por identidad; bloqueos
  editoriales permanecen sin interpretación.
- **Categorías de tests:** matriz de taxonomía, schema/migration, algebra de
  selectores, cardinalidades y elector, autorización/visibilidad, target freeze
  y revalidation, mutation/property y pruebas negativas de `card_id` dispatch.

### W5 — Estado derivado y permanentes

- **Objetivo:** disponer de una sola evaluación reproducible de Fuerza efectiva,
  condición de criatura y demás estado derivado de permanentes.
- **Capabilities:** `CAP-STATE-001/002`, `CAP-EFFECT-002`,
  `CAP-ATTACH-001`, `CAP-TRANSFORM-001/002` y el daño marcado/limpieza de
  `CAP-DAMAGE-001`.
- **Dependencias de entrada:** W3 para movimientos/limpieza y W4 para selectores
  y taxonomía; composición basal de W1.
- **Exclusiones:** persistir la Fuerza efectiva como segunda verdad, semántica
  completa de keywords, reparto avanzado de combate y excepciones por carta.
- **Normativa relacionada:** base frente a modificadores, orden/layers,
  duraciones, anexar/desanexar, transformación/copia, elegibilidad, Heridas,
  daño marcado y momentos de limpieza.
- **Desbloqueo directo/indirecto del corpus:** directo, buffs/debuffs,
  transformaciones y anexos expresables; indirecto, letalidad, keywords
  concedidas/retiradas, inmunidad y combate avanzado coherente.
- **Superficies técnicas:** modelos, `engine/effects.py`, `engine/zones.py`,
  `engine/game.py`, `engine/combat.py`, presentación de observación y
  persistencia de fuentes, no de caché derivada.
- **Riesgos:** caché obsoleta, ciclos de efectos continuos, orden no
  determinista, anexos huérfanos, transformación que pierde identidad y limpieza
  anticipada o tardía.
- **Criterios de salida:** algoritmo de layers/precedencia documentado; recálculo
  puro y determinista; invalidación completa; duraciones y limpieza exactas;
  anexos/transformaciones respetan transiciones; snapshot guarda causas y
  reconstruye el mismo derivado.
- **Categorías de tests:** unitarios de layers, metamórficos de orden, ciclos y
  terminación, duraciones/cleanup, anexos y transformación, daño marcado,
  snapshot/replay y escenarios combinatorios.

### W6 — Combate y habilidades universales

- **Objetivo:** componer combate y habilidades repetibles sobre estado derivado,
  timing, targeting y transiciones ya cerrados.
- **Capabilities:** `CAP-DAMAGE-002`–`005`, `CAP-COMBAT-001`–`006`,
  `CAP-KEYWORD-001/002`, `CAP-IMMUNITY-001`, Desafío ampliado
  (`CAP-COMBAT-004`) y `CAP-EFFECT-003`; cada nodo bloqueado conserva su gate.
- **Dependencias de entrada:** W2–W5 cerradas y decisiones normativas para
  multibloqueo, inmunidad, Desafío por efecto y multijugador cuando apliquen.
- **Exclusiones:** keywords nominales sin conducta, inmunidad como ocultación de
  target, prevención sin causa/duración, reglas ad hoc por combatiente o carta y
  asumir reglas de 3+ jugadores.
- **Normativa relacionada:** causa/fuente/duración de prevención, destrucción,
  regeneración, indestructibilidad, keywords, inmunidad, asignación de daño,
  Desafío y terminación multijugador.
- **Desbloqueo directo/indirecto del corpus:** directo, familias de combate y
  keywords completamente parametrizables; indirecto, efectos compuestos que
  crean combate, conceden capacidades o reaccionan a su resultado.
- **Superficies técnicas:** `engine/combat.py`, `engine/effects.py`,
  `engine/stack.py`, `engine/actions.py`, `engine/game.py`, enums/modelos,
  opciones, observación y persistencia.
- **Riesgos:** orden incorrecto prevenir–destruir–regenerar, doble aplicación,
  inmunidad divergente entre legalidad y resolución, keywords no componibles y
  resultado distinto por orden de colección.
- **Criterios de salida:** pipeline causal único; legalidad y resolución comparten
  predicados; cada keyword tiene semántica tipada y composición; Desafío usa el
  combate común; casos normativamente bloqueados siguen rechazados; replay
  reproduce asignación, prevención y resultado.
- **Categorías de tests:** tablas de combate, causal prevention, destrucción/
  regeneración/indestructibilidad, keywords e inmunidad, composición y
  conmutatividad, Desafío, multijugador autorizado, fuzz/property y replay.

### W7 — Conformidad masiva del corpus

- **Objetivo:** incorporar por familias sólo cartas cuya semántica completa sea
  representable mediante capacidades generales cerradas.
- **Capabilities:** `CAP-CATALOG-001`, `CAP-EFFECT-004/005` cuando sus
  prerequisites estén cerrados, y paquetes declarativos de contenido; W7 no
  inventa capacidades para completar una familia.
- **Dependencias de entrada:** W0–W6 según el subgrafo de cada familia,
  `CAP-EFFECT-003` y `CAP-TAXONOMY-001` cerradas, procedencia normativa completa
  y `CAP-NORM-002` resuelta cuando el formato requiera presupuesto Mítico.
- **Exclusiones:** lógica específica por carta, clasificar `PARTIAL` como
  soportada, rellenar ambigüedades, contabilizar variantes como identidades y
  publicar automáticamente definiciones.
- **Normativa relacionada:** fuente y revisión de cada texto, procedencia de
  taxonomía, presupuesto/formato, ambigüedades y criterio `SUPPORTED` por carta
  completa.
- **Desbloqueo directo/indirecto del corpus:** directo, promociones individuales
  auditadas dentro de familias enteramente representables; indirecto, evidencia
  de huecos generales para volver al grafo, sin convertir frecuencia en
  prioridad.
- **Superficies técnicas:** catálogos mecánico y de presentación, manifiestos,
  validadores, corpus/conformance, fixtures, codecs, servicio y tooling de
  auditoría.
- **Riesgos:** soporte por parecido, semántica oculta en datos, handler por ID,
  deriva mecánica/presentación, totales inflados y confundir incorporación
  interna con disponibilidad pública.
- **Criterios de salida:** cada familia tiene trazabilidad carta→norma→capability
  y pruebas end-to-end; cero dispatch por identidad; toda promoción se reaudita;
  los totales siguen sumando 431 entradas/386 identidades/45 variantes; el gate
  de publicación continúa separado.
- **Categorías de tests:** conformance parametrizada, schema/catalog, unicidad y
  join presentación–mecánica, golden card scenarios, corpus totals, replay,
  regresión por familia y pruebas arquitectónicas contra handlers por ID.

**Límite de fase y publicación.** W7 pertenece a la **Fase 2-C**: no abre la
Fase 3, no es un release gate y no autoriza publicar cartas. La publicación
requiere una decisión separada, sus controles de release, procedencia,
presentación y seguridad, incluso cuando una carta ya sea mecánicamente
`SUPPORTED`.

## Diferencias justificadas respecto a la hipótesis inicial

1. **W0 reduce el riesgo de migraciones improvisadas.** El schema, replay,
   snapshots, eventos, serialización y CAS son observables duraderos; fijar antes
   su estrategia evita crear un decoder distinto por wave y permite revertir
   fallos sin corromper partidas.
2. **Acciones y costes preceden al crecimiento de ventanas activables.** Una
   ventana adicional multiplica las oportunidades de ejecutar una acción; sin
   preflight, pago atómico y rollback también multiplica estados parciales y
   respuestas a acciones ilegales.
3. **La privacidad acompaña a toda transición.** No es una capa de UI posterior:
   origen, destino, candidatos, LKI, eventos y errores necesitan audiencia en el
   momento en que nacen. Redactarlos después no deshace una fuga en replay o API.
4. **Targeting se separa de taxonomía editorial.** La taxonomía define qué es
   un objeto y conserva vocabulario/procedencia; targeting decide qué objetos
   puede elegir un elector autorizado y con qué cardinalidad. Comparten tipos,
   pero ni una errata editorial debe cambiar autorización ni un selector debe
   convertirse en fuente editorial.
5. **El estado derivado precede a keywords y combate avanzado.** Fuerza efectiva,
   criatura efectiva, duraciones, anexos, transformación y limpieza determinan
   elegibilidad, letalidad y conducta; implementar keywords antes duplicaría
   cálculos y produciría resultados obsoletos.
6. **El contenido masivo queda después de cerrar capacidades generales.** Así el
   corpus valida primitivas comunes en lugar de convertir similitudes de texto
   en excepciones por carta. Una capability cerrada habilita reauditoría, no una
   promoción ni una publicación automáticas.

## Quick wins sin ruptura de contratos

Son candidatos pequeños y reversibles, siempre acompañados por tests y sin modificar discriminadores serializados ni semántica pública:

- completar casos tipados de `CAP-DAMAGE-002`, actualmente `READY`, que estén inequívocamente cubiertos por causa y duración actuales;
- ampliar tests y fixtures de vocabulario/procedencia para `CAP-TAXONOMY-003`, sin alterar el modelo ni promover la capability hasta que `CAP-TAXONOMY-001` cierre su gate;
- reforzar pruebas, trazabilidad y métricas de las capabilities `CLOSED`, incluida la paridad de acciones y round-trips, sin reclasificar cartas automáticamente;
- preparar migradores, golden replays y notas de versión de las fundaciones sin activar todavía su nuevo contrato.

Un quick win deja intactos schema version, comandos, eventos, snapshots y respuestas del servicio. Si durante el diseño exige cambiar cualquiera de ellos, sale de este carril y pasa a cambio fundacional versionado.

## Foundational changes que exigen versionado

Requieren versión explícita del schema/evento/API afectado, decoder de legado o migración, golden replays de antes y después y nota de compatibilidad:

- `CAP-ZONE-003` y `CAP-ZONE-006`: identidad y evento uniforme de transición, incluida last-known information;
- `CAP-SECRET-002`: elecciones persistibles y proyección por audiencia;
- `CAP-TAXONOMY-001`, `CAP-TARGET-002`, `CAP-KEYWORD-001` y `CAP-IMMUNITY-001`: discriminadores tipados y selectores canónicos;
- `CAP-TIME-003`, `CAP-TIME-004` y `CAP-TRIGGER-001`: orden observable de fases, prioridad y triggers;
- `CAP-EFFECT-001`–`003`: AST/composición, captura de valores, atomicidad y visibilidad por paso;
- `CAP-CATALOG-001`: publicación final de definiciones y procedencia, únicamente tras cerrar sus gates.

El versionado no permite saltarse prerequisites: sólo hace compatible una modificación ya autorizada. Cada cambio debe definir versión escrita, lectura de legado, comportamiento ante versión desconocida, estabilidad de IDs y orden de eventos, y equivalencia de replay/persistencia/API.

## Criterio de salida y re-priorización

Una capability sólo cambia a `SUPPORTED` cuando: (1) todos sus prerequisites están `CLOSED`; (2) no existe interpretación normativa abierta; (3) los contratos de dominio, ejecución, persistencia/replay y servicio están probados; (4) las filas del corpus se reauditan individualmente; y (5) los totales globales vuelven a sumar exactamente 431 sin mezclar las 386 identidades con las 45 variantes. Cerrar infraestructura no promueve cartas de forma masiva: habilita su reevaluación.

La priorización se revisa cuando se cierre un gate, cambie una fuente normativa o aparezca evidencia reproducible del corpus. No se revisa sólo porque una palabra sea frecuente. El registro debe conservar el valor anterior, la evidencia nueva y la razón ordinal del cambio.
