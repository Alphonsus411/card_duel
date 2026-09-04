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

## Orden de ejecución por gates

### 1. Fundaciones antes que volumen superficial

La primera ola debe cerrar contratos transversales que ya estén `READY`, empezando por taxonomía canónica y siguiendo la puerta uniforme de zonas, elecciones secretas, targets/selectores, tiempo/prioridad, triggers, keywords/inmunidades y primitivas/composición de efectos **sólo cuando sus prerequisites pasen a `CLOSED`**. `CAP-CATALOG-001` queda al final de esa cadena: ingerir antes el corpus convertiría excepciones por `card_id` en API accidental y obligaría a reescribir snapshots y replay.

Una infraestructura transversal puede preceder legítimamente a una familia con más apariciones superficiales porque una sola decisión de identidad, transición de zona o elección persistible fija invariantes compartidos por muchas familias. Implementar primero la familia visible duplicaría selectores, orden de eventos y codecs; luego habría que migrar esos datos cuando llegue la abstracción común. La aparición textual mide demanda, pero la centralidad mide cuántos contratos pueden quedar incoherentes. Por eso el gate domina a la frecuencia.

### 2. Familias especializadas después de sus bases

Búsqueda top-N, desafío por efecto, creación de fichas, descarte forzado y otras hojas especializadas se planifican después de cerrar zona/secretos/targets/triggers/composición que les correspondan. Cada entrega debe demostrar legal-action parity, snapshot/codec round-trip y replay determinista antes de promover filas de corpus.

### 3. Carril normativo independiente

`CAP-NORM-001` y `CAP-NORM-002` no son tareas de programación: producen decisiones autoritativas y trazables. `CAP-TAXONOMY-002`, `CAP-TRANSMUTE-002`, `CAP-COMBAT-002` y `CAP-COMBAT-006`, además de cualquier tramo abierto de inmunidades o multijugador, permanecen `NORM-BLOCKED`. Una aclaración puede abrir el gate, pero nunca cuenta como implementación ni como soporte de corpus.

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
