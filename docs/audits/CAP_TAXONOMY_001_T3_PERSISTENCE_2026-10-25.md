# CAP-TAXONOMY-001 T3 — persistencia compatible

**Fecha:** 2026-10-25
**Estado:** T3 completada; no habilita un cambio de esquema
**Decisión:** se conservan los schemas actuales: snapshot v5 y replay v4.

## Alcance verificado

T2 no añadió ni reinterpretó ningún campo de `CardDefinition`. Por ello no hay
migración taxonómica autorizada ni motivo para incrementar versiones de
snapshot o replay. El catálogo completo se persiste por `encode_value` y se
restaura por `decode_value`; ambos discriminan `CardKind` y `LordDomain` como
enums independientes y reconstruyen los campos de `CardDefinition` por nombre.

La prueba T3 fija el recorrido de extremo a extremo para las dos formas de
Señor acreditadas:

- `CardKind.LORD + LordDomain.REALMS`;
- `CardKind.CREATURE + LordDomain.ABYSS`.

Tras `dump_snapshot`/`load_snapshot` y tras `dump_replay`/`replay_from_log`,
ambas retienen exactamente su tipo y su dominio. La prueba también afirma que
el documento emitido sigue declarando snapshot v5 y replay v4.

## Compatibilidad y rechazo

La compatibilidad de los documentos anteriores sigue bajo los migradores ya
existentes. No se inserta un default taxonómico para datos ausentes: el decoder
continúa rechazando campos desconocidos, campos obligatorios ausentes y enums
no autorizados. En particular, T3 no deduce `lord_domain` desde `CardKind`, ni
deduce `CardKind` desde dominio, nombre o identidad.

No se crea una versión nueva sólo para volver a codificar las mismas
dimensiones. Si una fase posterior añade un discriminador, cambia el
significado de los campos o resuelve los tipos múltiples de
`CAP-TAXONOMY-002`, deberá versionar snapshot/replay, definir lectura de legado
y aportar golden replays propios.

## Límites mantenidos

- No se migran ni reclasifican cartas del corpus.
- No se introducen aliases, procedencia de subtipo ni vocabulario nuevo.
- No se proyecta `lord_domain` en la API pública.
- `CAP-TAXONOMY-001` permanece `PARTIAL / READY`.
