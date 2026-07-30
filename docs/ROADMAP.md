# Hoja de ruta del backend

Esta hoja de ruta convierte únicamente trabajo ya documentado en tareas
separadas. No completa ambigüedades del reglamento ni añade cartas o mecánicas.
La fuente normativa continúa siendo `Fantasy Tokens.pdf`, interpretada mediante
`RULES_BASELINE.md` y su matriz `RULES_TRACEABILITY.md`.

## Entregas completadas

### R-01 — Proteger las condiciones terminales multijugador

- **Evidencia:** el reglamento permite uno o más adversarios, pero no define la
  continuidad, la concesión ni los ganadores para tres o más participantes.
- **Entrega 0.18.3:** ante una concesión o el límite de Heridas, una partida con
  más de dos participantes pasa a `BLOCKED`, no declara ganadores y publica la
  causa y los participantes afectados.
- **Criterio de salida:** sustituir este bloqueo solo cuando exista una
  aclaración normativa trazable.

## Siguiente tarea

### R-04 — Política de confianza para colecciones

- Diseñar firmas y confianza fuera del digest de integridad existente.
- Mantener la política inyectable y evitar ejecutar código de manifiestos.

## Pendientes normativos bloqueados

### R-02 — Revisar el reparto de daño entre bloqueadores

- Contrastar el orden actualmente normalizado con una aclaración oficial.
- No cambiar el algoritmo hasta disponer de esa aclaración.

### R-03 — Formalizar contradicciones entre reglamento base y Mítica

- Registrar cada contradicción, las páginas fuente y la precedencia aplicada.
- Mantener mientras tanto la precedencia Mítica ya declarada para Divinos.

## Pendientes técnicos bloqueados

### R-05 — Evolución de formatos persistentes

- Añadir migraciones únicamente cuando exista un esquema 3 o posterior definido.
- Rechazar rutas desconocidas sin completar datos mediante suposiciones.

## Pendientes técnicos

### R-06 — Frontera de red del servicio

- Incorporar red, autenticación y autorización sobre `MatchService` y el almacén.
- Conservar comandos validados, observaciones privadas y persistencia CAS como
  frontera autoritativa.

### R-07 — Continuar separando el coordinador

- Extraer responsabilidades restantes de pila, combate y movimientos hacia
  resolutores especializados sin duplicar `GameState`.
- Exigir paridad observable, tipado estricto y pruebas de atomicidad en cada paso.
