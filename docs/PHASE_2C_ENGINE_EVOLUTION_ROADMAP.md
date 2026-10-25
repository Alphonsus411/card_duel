Warning: truncated output (original token count: 21822)
Total output lines: 993

# Fase 2-C: roadmap maestro de evolución del motor

## Executive summary

Este documento prioriza las 64 capabilities de `ENGINE_CAPABILITY_MATRIX.csv` sin convertir frecuencia textual en una falsa medida de valor. El baseline permanece explícitamente congelado: **431/431 entradas auditadas** —Alpha **103**, Beta **147** y Mítica **181**—, correspondientes a **386 identidades** y **45 reimpresiones/variantes**. Sus estados son **2 `SUPPORTED`**, **245 `PARTIAL`**, **143 `MISSING`**, **41 `AMBIGUOUS`** y **0 `CONFLICT`**. Las variantes no se vuelven a contar como identidades ni un desbloqueo transversal se atribuye íntegramente a una sola capability.

La tabla es una herramienta de ordenación arquitectónica, no una promesa de que una capability cierre por sí sola todas las cartas que la mencionan. La auditoría canónica es [`FANTASY_TOKENS_BACKEND_GAP_AUDIT.md`](FANTASY_TOKENS_BACKEND_GAP_AUDIT.md); esta roadmap es exclusivamente **planificación derivada**, no implementación ni release. La evidencia declarativa de prerequisites y estados se distribuye entre `ENGINE_CAPABILITY_MATRIX.csv` y `ENGINE_CAPABILITY_DEPENDENCIES.md`; la evidencia de corpus sigue siendo `CARD_CORPUS_CONFORMANCE.md`; y una duda abierta sigue bajo `NORMATIVE_AMBIGUITIES.md`.

**Regla uniforme de estado técnico.** `MISSING` significa que no existe ningún subconjunto ejecutable demostrable; `PARTIAL`, que existe un subconjunto real pero todavía no el contrato completo; `SUPPORTED` exige el recorrido público, persistente, replayable y de servicio completo. Esta clasificación de capabilities no modifica los estados ni los totales de las 431 entradas auditadas.

## estado actual

**Phase 2C: `IN PROGRESS`. Phase 3: `PENDING`.** La creación o aprobación de esta roadmap no altera esos estados.

### Modelo ordinal explicable

No se suman columnas ni se calculan medias. Cada dimensión usa exclusivamente `LOW < MEDIUM < HIGH`:

1. **Centralidad de dependencias:** `HIGH` si sostiene tres o más dependientes directos o cruza contratos transversales de estado/efectos/catálogo; `MEDIUM` con uno o dos; `LOW` sin dependientes. Es topología, no popularidad.
2. **Desbloqueo de corpus y reglas:** `HIGH` cuando habilita directamente una primitiva transversal y además cadenas indirectas; `MEDIUM` cuando desbloquea una familia o un siguiente eslabón; `LOW` cuando consolida una hoja ya soportada. No significa “número de cartas arregladas”.
3. **Riesgo para determinismo/replay/persistencia/API:** `HIGH` reúne las severidades `CRITICAL` y `HIGH` de la matriz, porque ambas requieren diseño contractual antes del contenido; `MEDIUM` corresponde a divergencia local; `LOW`, a cambios sin contrato observable previsto.
4. **Claridad normativa:** `HIGH` cuando hay base suficiente para implementar; `LOW` cuando existe bloqueo normativo. `MEDIUM` queda reservado para aclaraciones editoriales acotadas que permitan un núcleo inequívoco, aunque el baseline actual no necesita usarlo.
5. **Coste de migración/reescritura futura:** `HIGH` si cambia modelos serializados, orden/atomicidad, proyección o composición; `MEDIUM` si añade semántica especializada; `LOW` si completa o verifica un contrato estable sin romperlo.

Los ordinales expresan clases argumentables, no precisión matemática. Ante empate se ordena por gate, después por centralidad, riesgo de hacerlo fuera de orden, desbloqueo y por último coste. La frecuencia sólo puede desempatar capabilities con el mismo gate y prerequisites cerrados.

## principios arquitectónicos

### Gates arquitectónicos y normativos

El campo **Gate** es vinculante:

- `CLOSED`: capability ya soportada; se preserva mediante regresión y no compite como nueva implementación.
- `READY`: prerequisites técnicos cerrados y autoridad normativa suficiente; puede entrar en planificación.
- `WAIT-PREREQ`: queda detrás del primer prerequisite no cerrado, aunque aparezca más veces en el corpus.
- `NORM-BLOCKED`: no se implementa ni se publica una interpretación hasta obtener autoridad normativa; prototipos, si existen, no alteran el contrato público.

Por tanto, ninguna puntuación de frecuencia puede adelantar un nodo `WAIT-PREREQ`, ni una valoración `HIGH` autoriza un nodo `NORM-BLOCKED`. Al cambiar un prerequisite o una fuente normativa se debe reevaluar la fila y sus descendientes, no conservar mecánicamente su orden anterior.

## capabilities

### Valoración de las 64 capabilities

Las columnas `Central.`, `Desbloq.`, `Riesgo`, `Claridad` y `Migración` corresponden, en ese orden, a las cinco dimensiones anteriores. La explicación concreta de cada valoración queda trazable en la última columna: estado, prerequisites y dependientes declarados.

| Capability | Estado | Gate | Central. | Desbloq. | Riesgo | Claridad | Migración | Explicación verificable |
|---|---|---|---|---|---|---|---|---|
| `CAP-ACTION-001` — Modelo tipado de acciones y comandos | `SUPPORTED` | `CLOSED` | HIGH | MEDIUM | MEDIUM | HIGH | LOW | Prerequisites: ninguno; dependientes: CAP-ACTION-002, CAP-TIME-003, CAP-EFFECT-001. |
| `CAP-ACTION-002` — Enumeración y revalidación de acciones legales | `SUPPORTED` | `CLOSED` | MEDIUM | MEDIUM | HIGH | HIGH | LOW | Prerequisites: CAP-ACTION-001; dependientes: CAP-TARGET-001, CAP-ACTION-004. |
| `CAP-ACTION-003` — Transacción, rollback y determinismo | `SUPPORTED` | `CLOSED` | HIGH | MEDIUM | HIGH | HIGH | LOW | Prerequisites: CAP-ACTION-001; dependientes: CAP-COST-002, CAP-ZONE-003, CAP-EFFECT-003. |
| `CAP-ACTION-004` — Decisión pendiente autorizada | `PARTIAL` | `READY` | HIGH | HIGH | HIGH | HIGH | HIGH | W1.3 acredita historia total tipada, replay v3, lifecycle interno reproducible `None → PENDING → CLOSED → None`, permanencia de `CLOSED` hasta consumo explícito, snapshot v4 y migraciones fail-closed, preservando CAS y privacidad `ELECTOR` de W1.2. Siguen pendientes apertura pública, bloqueo selectivo por familia, decisiones simultáneas y audiencias adicionales; no inicia W1.4, no declara `SUPPORTED` y no desbloquea `CAP-TIME-002`. Prerequisites: CAP-ACTION-002, CAP-PRIVACY-001; dependientes: CAP-SECRET-002, CAP-TIME-002; prioridad P0, riesgo CRITICAL, wave W1. |
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
| `CAP-PRIVACY-001` — Proyección pública por audiencia | `SUPPORTED` | `CLOSED` | MEDIUM | MEDIUM | HIGH | HIGH | LOW | Prerequisites: CAP-ZONE-002; dependientes: CAP-SECRET-001, CAP-SEARCH-001, CAP-ACTION-004. |
| `CAP-SECRET-001` — Mirar sin revelar | `MISSING` | `READY` | MEDIUM | MEDIUM | HIGH | HIGH | MEDIUM | Prerequisites: CAP-PRIVACY-001, CAP-ZONE-002; dependientes: CAP-SECRET-002, CAP-SEARCH-002. |
| `CAP-SECRET-002` — Elección secreta y compuesta | `PARTIAL` | `READY` | HIGH | HIGH | HIGH | HIGH | HIGH | Prerequisites: CAP-ACTION-004, CAP-COST-004, CAP-SECRET-001; dependientes: CAP-SEARCH-002, CAP-ZONE-004, CAP-EFFECT-003. |
| `CAP-TARGET-001` — Targets tipados y congelados | `SUPPORTED` | `CLOSED` | MEDIUM | MEDIUM | HIGH | HIGH | LOW | Prerequisites: CAP-ACTION-002; dependientes: CAP-TARGET-002, CAP-IMMUNITY-001. |
| `CAP-TARGET-002` — Selectores multidimensionales | `PARTIAL` | `WAIT-PREREQ` | MEDIUM | MEDIUM | HIGH | HIGH | HIGH | Prerequisites: CAP-TARGET-001, CAP-TAXONOMY-001; dependientes: CAP-SEARCH-001, CAP-EFFECT-002. |
| `CAP-TAXONOMY-001` — Dimensiones canónicas separadas | `PARTIAL` | `CLOSED` | MEDIUM | HIGH | HIGH | HIGH | HIGH | Incremento T0–T6 cerrado: fija dimensiones actuales, persistencia y consumidores sin inventar tipos, aliases ni defaults. La capability global sigue parcial por las brechas explícitas; prerequisites: ninguno; dependientes: CAP-TARGET-002, CAP-KEYWORD-001. |
| `CAP-TAXONOMY-002` — Leyenda y tipos impresos múltiples | `BLOCKED` | `NORM-BLOCKED` | MEDIUM | MEDIUM | HIGH | LOW | MEDIUM | Prerequisites: CAP-TAXONOMY-001; dependientes: CAP-TARGET-002. |
| `CAP-TAXONOMY-003` — Vocabulario, aliases y procedencia de subtipos | `PARTIAL` | `WAIT-PREREQ` | MEDIUM | MEDIUM | MEDIUM | HIGH | LOW | Prerequisites: CAP-TAXONOMY-001; dependientes: CAP-TARGET-002. |
| `CAP-TIME-001` — Preparación inicial | `PARTIAL` | `NORM-BLOCKED` | MEDIUM | MEDIUM | MEDIUM | LOW | LOW | Prerequisites: CAP-ZONE-002, CAP-PRIVACY-001; dependientes: CAP-TIME-002. |
| `CAP-TIME-002` — Mulligan decreciente | `PARTIAL` | `WAIT-PREREQ` | MEDIUM | MEDIUM | HIGH | HIGH | MEDIUM | Prerequisites: CAP-ACTION-004, CAP-TIME-005; dependientes: CAP-TIME-003. |
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
| `CAP-KEYWORD-001` — Keywords nominales de combate | `MISSING` | `WAIT-PREREQ` | MEDIUM | HIGH | HIGH | HIGH | HIGH | Prerequisite…13822 tokens truncated…rar campos autoritativos, discriminadores, canonicalización o digest. | **Cambio que requiere nueva versión de snapshot/replay/manifest.** | Golden por versión, decoder seleccionado por `schema_version`, round-trip estable y rechazo explícito de versiones desconocidas. |
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

## primer slice

### Readiness del primer slice candidato — `N-PHASE-02`

```yaml
slice_id: N-PHASE-02
capability_id: CAP-TIME-002
normative_rule_id: N-PHASE-02
authorization: BLOCKED
status: PARTIAL
gate: WAIT-PREREQ
prerequisites:
  - capability_id: CAP-ACTION-004
    status: PARTIAL
    gate: READY
  - capability_id: CAP-TIME-005
    status: MISSING
    gate: WAIT-PREREQ
blockers:
  - blocker_id: CAP-ACTION-004
    kind: technical
    status: OPEN
    gate: READY
  - blocker_id: CAP-TIME-005
    kind: technical
    status: OPEN
    gate: WAIT-PREREQ
  - blocker_id: N-MULLIGAN-01.OPEN-ORDER
    kind: normative
    status: OPEN
    gate: NORM-BLOCKED
  - blocker_id: N-MULLIGAN-01.OPEN-MODE
    kind: normative
    status: OPEN
    gate: NORM-BLOCKED
  - blocker_id: N-MULLIGAN-01.OPEN-REVEAL
    kind: normative
    status: OPEN
    gate: NORM-BLOCKED
  - blocker_id: N-MULLIGAN-01.OPEN-STARTER
    kind: normative
    status: OPEN
    gate: NORM-BLOCKED
verdict: N-PHASE-02 IMPLEMENTATION BLOCKED
```

Los dos primeros elementos de `blockers` son la lista exacta de prerequisites
no cerrados declarada para `CAP-TIME-002`: `CAP-ACTION-004` (decisión pendiente
autorizada, capability `PARTIAL` con recorrido público aún pendiente y gate `READY`) y `CAP-TIME-005` (lifecycle autoritativo de
setup, `MISSING` y `WAIT-PREREQ`). Los cuatro elementos
`N-MULLIGAN-01.OPEN-*` son blockers normativos granulares del protocolo, no
prerequisites técnicos. La dependencia directa de `CAP-SECRET-002` queda eliminada:
el mulligan sólo necesita opciones opacas y lifecycle universal, no candidatos
de cartas, cardinalidad, ordenación, selección compuesta, *simultaneous reveal*
ni semántica de búsquedas. Por ello, el resultado vigente de readiness es **`N-PHASE-02
IMPLEMENTATION BLOCKED`**. Mientras `authorization` sea `BLOCKED`, **no existe
autorización para modificar el runtime**, incluidos dominio, motor,
persistencia, aplicación, servicio o tests de implementación del mulligan. La
aprobación de esta roadmap o de estos informes documentales no cambia ese
resultado.

Los siguientes slices son exclusivamente de planificación y deben ejecutarse
en este orden antes de volver a evaluar `N-PHASE-02`:

1. **Diseño de la abstracción mínima (`CAP-ACTION-004`):** cerrar su contrato universal persistible, revalidable y proyectable por audiencia sin incorporar las especializaciones de `CAP-SECRET-002`.
2. **Lifecycle autoritativo de setup (`CAP-TIME-005`):** demostrar creación, seguimiento y cierre de las decisiones obligatorias dentro de `SETUP`, sin conceder prioridad inicial ni anticipar `CAP-TIME-002`.

El alcance que sigue es una especificación condicionada para una futura
reevaluación. Sólo podrá convertirse en trabajo de runtime mediante una nueva
decisión documental que registre los dos prerequisites técnicos y los cuatro
blockers normativos como `CLOSED`, cambie el gate a `READY` y cambie
expresamente `authorization` a `AUTHORIZED`.

#### Alcance vinculante

1. El setup representa explícitamente el estado autoritativo del mulligan,
   incluidos los tamaños autorizados, cantidad de repeticiones, elecciones
   pendientes y condición de cierre. No representará un participante
   habilitado, orden o ronda de decisión hasta cerrar
   `N-MULLIGAN-01.OPEN-ORDER` y `N-MULLIGAN-01.OPEN-MODE`.
2. Existe un comando universal —no ligado a una carta ni a un formato por
   nombre— para que cada participante conserve su mano o solicite reemplazarla.
   La elección aceptada es persistible y queda disponible para snapshot,
   reconexión y replay sin pedirla de nuevo al cliente.
3. Cada repetición reduce de forma determinista el tamaño de la nueva mano
   conforme a la evidencia normativa vigente. El tamaño se deriva del estado
   persistido y de la regla versionada, nunca de un contador del proceso, del
   reloj ni de un default implícito.
4. Actor, estado de setup, orden de decisión sólo cuando quede autorizado,
   versión CAS, cardinalidad y vigencia de la elección se validan **antes de
   cualquier movimiento o barajado**. Un rechazo deja idénticos estado, zonas,
   RNG, versión y log de eventos.
5. Devolver la mano, barajar y robar la nueva mano atraviesa la autoridad única
   de movimientos de zona y la fuente de RNG reproducible. No se permiten
   mutaciones laterales de mazo o mano desde el handler del comando.
6. `N-MULLIGAN-01.OPEN-ORDER` y `N-MULLIGAN-01.OPEN-MODE` bloquean el tramo que
   necesite ordenar o coordinar decisiones. La implementación no elegirá orden,
   alternancia ni simultaneidad como default para rellenar esos vacíos.
7. `N-MULLIGAN-01.OPEN-REVEAL` bloquea cualquier publicación de una decisión.
   Una futura observación pública o por oponente mostrará sólo progreso,
   tamaños y decisiones cuya visibilidad haya sido autorizada; nunca identidades,
   orden ni contenido de las cartas de otra mano o mazo. Cada jugador recibe
   únicamente su proyección privada autorizada.
8. El setup termina una sola vez y de forma determinista cuando todas las
   elecciones exigidas han concluido. `N-MULLIGAN-01.OPEN-STARTER` bloquea toda
   conducta que conserve, cambie o vuelva a determinar el jugador inicial: no
   se escogerá ninguna como default técnico.

#### Superficies probablemente afectadas

El diseño y el diff deberán revisar, aunque sólo modificar cuando sea
necesario, `domain/models.py`, `engine/commands.py`, `engine/game.py` **o un
manager de setup dedicado**, `engine/actions.py`, `engine/zones.py`,
`persistence/codec.py`, `persistence/snapshot.py`, `persistence/replay.py`,
`application.py`, `service.py` y pruebas específicas de dominio, motor,
persistencia, aplicación y servicio. Cualquier nueva representación
autoritativa del setup seguirá la matriz W0: tendrá schema/perfil semántico
versionado y decoder explícito, en lugar de aparecer como campo opcional con
significado reglamentario.

#### Exclusiones explícitas

Quedan fuera del slice `N-MULLIGAN-01.OPEN-3PLUS`: el slice se limita a dos
participantes sin establecer que esa limitación sea una regla del juego ni
definir conducta alguna para tres o más. También quedan fuera la prioridad
general —incluida la primera prioridad—, la entrada en `DRAW`, el protocolo de
pases y cualquier transición a `RUNNING` si el slice termina antes de ese
estado, además de Recursos Rápidos, cartas nuevas,
combate, keywords, taxonomías, frontend y cambios de presupuesto. También se
excluye resolver, asumir o anticipar cualquier ambigüedad sobre Legendaria o
el resto del multijugador. Cada cuestión abierta de `N-MULLIGAN-01` queda así
registrada como blocker o exclusión explícita. El slice no modifica otras
reglas, no amplía el corpus y no usa defaults normativos para hacer ejecutable
una fuente incompleta.

#### Pruebas obligatorias y compatibilidad

La promoción requiere evidencia automatizada de todos estos casos:

- tamaños de mano decrecientes en repeticiones sucesivas, incluidos límites y
  terminación, con secuencia de eventos estable;
- rechazo de conservar o reemplazar fuera del estado de setup y, sólo después
  de cerrar los blockers protocolarios, fuera del orden que resulte autorizado;
  demostración de **no mutación** de estado, zonas, RNG, versión
  y eventos después de cada validación fallida;
- mismo resultado, movimientos, barajado, eventos y digest al repetir con la
  misma semilla, y divergencia únicamente donde la semilla forme parte del
  contrato;
- privacidad por jugador y no interferencia de observaciones, opciones,
  errores y DTO, sin revelar cartas ni orden oculto;
- paridad entre las acciones legales enumeradas y el ejecutor para conservar y
  reemplazar, incluidas autorización, vigencia y comandos obsoletos;
- snapshot tomado en mitad del mulligan, restauración y continuación idéntica
  sin repetir ni perder una elección;
- replay completo desde el inicio hasta la finalización del setup, con las
  mismas decisiones, eventos, observaciones autorizadas, digest y estado final;
- round-trip del codec para comando, elección, estado y eventos del mulligan,
  además de golden/versiones soportadas y rechazo controlado de versiones
  desconocidas;
- CAS con rechazo sin mutación del perdedor y aplicación exactamente una vez
  del comando ganador; y
- compatibilidad con partidas y artefactos históricos que ya comenzaron
  **después del setup**: se cargan y continúan con su semántica anterior sin
  fabricar estado de mulligan, reabrir el setup ni reinterpretar su replay.

Estas pruebas cubren como mínimo `INV-2C-001`–`004`, `INV-2C-010`,
`INV-2C-013`–`018` y `INV-2C-022`, con todas las superficies obligatorias que
les asigna el catálogo. Los fixtures históricos permanecen inmutables.

#### Criterio de aceptación del slice

`N-PHASE-02` se acepta sólo cuando `CAP-TIME-002` pueda pasar de `PARTIAL` a
`SUPPORTED` en **todo el recorrido técnico** —modelo, comando, enumeración,
validación, transición autoritativa, observación, codec, snapshot, replay,
aplicación, servicio y CAS— y todas las pruebas anteriores estén verdes. La
promoción no es válida si exige modificar otra regla, resolver una exclusión o
introducir un default normativo; en cualquiera de esos casos el slice permanece
incompleto o bloqueado en el punto exacto para el que falte evidencia.

## Definition of Done de Phase 2C

### Criterio de salida y re-priorización

Una capability sólo cambia a `SUPPORTED` cuando: (1) todos sus prerequisites están `CLOSED`; (2) no existe interpretación normativa abierta; (3) los contratos de dominio, ejecución, persistencia/replay y servicio están probados; (4) las filas del corpus se reauditan individualmente; y (5) los totales globales vuelven a sumar exactamente 431 sin mezclar las 386 identidades con las 45 variantes. Cerrar infraestructura no promueve cartas de forma masiva: habilita su reevaluación.

## condiciones para abrir Phase 3

Phase 3 sólo puede abrirse mediante una decisión documental posterior cuando se cumpla íntegramente la Definition of Done anterior, la auditoría canónica mantenga trazabilidad 39/39 y 431/431, no queden gates técnicos de Phase 2C abiertos y cada bloqueo normativo pendiente esté resuelto por autoridad o expresamente excluido del alcance. Hasta entonces, **Phase 2C permanece `IN PROGRESS` y Phase 3 permanece `PENDING`**; ninguna wave, capability o primer slice de este plan constituye implementación, incorporación de cartas ni release.

La priorización se revisa cuando se cierre un gate, cambie una fuente normativa o aparezca evidencia reproducible del corpus. No se revisa sólo porque una palabra sea frecuente. El registro debe conservar el valor anterior, la evidencia nueva y la razón ordinal del cambio.
