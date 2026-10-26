# CAP-SECRET-001 / S4 — Revisión de cierre incremental

Fecha: 2026-10-26
Estado: cierre de la línea incremental; sin cambio de runtime
Capability: `MISSING / READY`

## Evidencia revisada

| Subfase | Evidencia | Resultado |
| --- | --- | --- |
| S0 | contrato de audiencia, sólo lectura, vida efímera y rechazo estable | fija la frontera que una mirada debe respetar |
| S1 | inventario de motor, servicio, aplicación y DTO | confirma que no existe ruta genérica autorizada ni se debe promover una especialización pendiente |
| S2 | modelo de grant interno, originado y no serializable | descarta persistencia, tokens reutilizables y parámetros remotos de jugador/zona |
| S3 | prueba de no interferencia de orden oculto rival | un cambio que altera el digest interno no altera observación, acciones ni DTO del no destinatario |

Las pruebas de autenticación ya caracterizan que `AuthenticatedMatchApplication`
resuelve el jugador desde `ExternalIdentity` y no acepta `player_id` público.
Las de búsqueda y reemplazo preservan sus datos privados sólo para el elector,
sin que ello los convierta en una mirada general.

## Decisión de integración

No se añade una clase `PrivateLookGrant`, una operación `look`, un comando, un
campo en `GameState` ni una ruta de aplicación. Aunque S2 define la forma que
deberá adoptar un grant, no hay hoy una capability especializada cerrada que
pueda emitirlo con un `origin` y `scope` legítimos. Un tipo o endpoint sin tal
emisor sólo trasladaría al transporte la capacidad de elegir contenido oculto.

Esta ausencia es intencionalmente fail-closed: el motor continúa exponiendo
únicamente observación propia y superficies públicas ya existentes.

## Matriz de requisitos

| Requisito S0 | Estado | Base |
| --- | --- | --- |
| Identidad no elegible por el transporte | acreditado para la vista existente | `AuthenticatedMatchApplication.view` y sus pruebas R-06 |
| Audiencia y no filtración al rival | acreditado para las proyecciones existentes | S3 y pruebas de búsqueda/reemplazo |
| Sólo lectura y sin evento | no aplicable sin operación de mirada | no se ha introducido runtime |
| No persistencia ni replay/digest | acreditado por ausencia de nuevo estado | S2 y revisión de cambios S0–S3 |
| Revalidación de origin/scope | pendiente de una capability originadora | no se puede simular sin inventar semántica |
| Rechazo estable anti-oráculo | pendiente de una capability originadora | la frontera actual rechaza identidad no autorizada, pero no existe operación de mirada que rechazar |

## Estado y siguiente desbloqueo legítimo

`CAP-SECRET-001` permanece `MISSING / READY`: la línea S0–S4 reduce el riesgo
de integración, pero no aporta una regla de juego que autorice contenido oculto
adicional. No declara `SUPPORTED`, no actualiza snapshots/replay/esquemas y no
desbloquea `CAP-SECRET-002`, `CAP-SEARCH-002` ni `CAP-SEARCH-003`.

La reanudación correcta requiere que una capability propietaria cierre primero
su semántica de mirada y emita internamente el grant de S2. Su primera entrega
de runtime deberá añadir las pruebas de revalidación y rechazo estable que la
matriz marca como pendientes, además de conservar la no interferencia S3.
