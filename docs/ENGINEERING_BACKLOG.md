# Deuda de ingeniería

Este registro documenta decisiones técnicas pendientes sin convertirlas por sí
solo en entregas autorizadas. Cada entrada requiere una decisión de alcance
independiente antes de implementarse.

## AD-01 — Identidad pública de alternativas legales para un transporte futuro

### Problema

`PublicLegalAction.action` identifica el tipo general de una acción legal, pero
no distingue necesariamente alternativas simultáneas del mismo tipo. El DTO
actual es suficiente para la frontera autenticada en proceso y no constituye un
protocolo de selección remota.

### Condiciones para una decisión futura

Antes de autorizar cualquier decisión de transporte que permita seleccionar una
alternativa legal, deberá definir conjuntamente:

- identificadores opacos por alternativa;
- una representación pública que no revele estado privado;
- expiración de las alternativas vinculada a la versión CAS observada;
- resolución exclusivamente contra el conjunto de acciones emitido por el servidor;
- rechazo de comandos internos arbitrarios; y
- prohibición de exponer elecciones privadas.

Estas condiciones pretenden conservar al servidor como autoridad y evitar que
un identificador, sus campos o sus errores se conviertan en un canal lateral de
información privada.

### Alcance de esta entrada

Esta deuda es exclusivamente documental. No implementa resolución remota,
HTTP, HTTPS, REST, WebSocket ni ningún otro transporte. Tampoco modifica
`PublicLegalAction`, la serialización existente ni la legalidad de comandos.
