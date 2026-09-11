# CAP-ACTION-004 — alcance normativo W1.1

**Fecha:** 2026-09-11
**Estado:** alcance cerrado para W1.1

## Lifecycle acreditado

W1.1 acredita exclusivamente el lifecycle de **una decisión individual** en el
slot autoritativo `GameState.pending_decision`:

```text
None -> PENDING -> CLOSED
```

La apertura sólo acepta un slot `None`. Una decisión `PENDING` y una decisión
`CLOSED` ocupan por igual el slot y provocan `DecisionSlotOccupied`. El cierre
sólo acepta `PENDING`, conserva la identidad y los demás campos de la decisión y
cambia su estado a `CLOSED` con la opción seleccionada.

Por tanto, W1.1 **todavía no permite abrir una segunda decisión en el mismo
agregado**. En particular, no implementa `CLOSED -> None`, `CLOSED -> PENDING`
ni la sustitución silenciosa de `CLOSED` por una decisión nueva.

## Consumo expresamente aplazado

No existe en W1.1 una operación de consumo o retirada. Un slice posterior debe
definir antes, de forma conjunta:

1. el significado normativo de consumir;
2. cómo se conservan identidad e historia;
3. qué comando o evento reproducible expresa la operación; y
4. cómo interactúa con snapshots y compare-and-swap (CAS).

Hasta entonces, `CLOSED` permanece en el agregado como estado terminal
observable y bloquea cualquier nueva apertura.

## Riesgo conocido de replay e INV-10

Las transiciones W1.1 se realizan por ahora mediante API interna y no agregan un
comando al historial. Por ello, replay v2 conserva su formato histórico, pero no
puede reconstruir una apertura o un cierre efectuados por esa vía: la
verificación de la huella detecta la divergencia y debe rechazar el replay.

Este límite es deliberado. `CAP-ACTION-004-INV-10` **permanece abierto** y su
cierre corresponde a un slice futuro que incorpore un comando reproducible y su
contrato de compatibilidad. W1.1 no añade comandos de apertura/cierre, no amplía
el registro del codec y no introduce excepciones en los perfiles legacy 0.19 o
0.20 para ocultar la divergencia.

## Dos versiones con responsabilidades distintas

`PendingDecision.state_version` es el vínculo determinista que declara quien
abre la decisión. El motor valida y conserva ese valor, pero no lo incrementa,
no lo deriva de persistencia y no crea con él un contador de dominio paralelo.

En cambio, `expected_version` y `StoredMatch.version` pertenecen al protocolo
CAS de las capas de servicio y storage. La integración de ese CAS con dos
cierres concurrentes queda fuera de W1.1; este slice no equipara ambos espacios
de versión.

Si para conectar el cierre interno con la arquitectura real resultara necesario
equiparar `PendingDecision.state_version` y `StoredMatch.version`, la ampliación
debe detenerse y registrarse como decisión arquitectónica. W1.1 no autoriza a
improvisar esa equivalencia.
