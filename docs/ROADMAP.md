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

### R-04 — Política de confianza para colecciones

- **Entrega 0.19.0:** sobre de firma v1 separado del manifiesto v2, bytes
  canónicos únicos, resolución inyectada de claves y política estricta o
  permisiva elegida por la aplicación.
- **Garantía:** la autenticación de un lote completo se resuelve antes de
  modificar catálogo o procedencia, sin cargar módulos ni ejecutar contenido.

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

- **Decisiones aprobadas:** HTTPS/JSON REST versionado, OAuth 2.0 Bearer con JWT
  validado según OpenID Connect, identidad estable (`iss`, `sub`) y asociación
  externa por partida, jugador y capacidad. El detalle normativo está en
  `ARCHITECTURE.md`; estas son decisiones de infraestructura, no reglas del juego.
- **Criterios de salida:**
  1. existe una capa de aplicación fuera de `GameEngine`, los modelos de dominio
     y `MatchService`, sin red, tokens ni sesiones en esos componentes;
  2. ninguna operación de observación o comando permite al cliente escoger el
     `player_id`: se deriva de identidad autenticada, partida y capacidad;
  3. creación, observación, comandos y administración se autorizan por separado;
  4. toda escritura exige `expected_version` y mantiene la semántica CAS idéntica
     en memoria y SQLite;
  5. los rechazos públicos de partida ausente, versión obsoleta y acción ilegal
     no filtran instantáneas, observaciones privadas ni detalles internos;
  6. pruebas del adaptador cubren identidad ausente o inválida, cruces de jugador
     y partida, atribución falsa, versión obsoleta y ausencia de mutación, y se
     conservan las pruebas directas de `MatchService` y la paridad de almacenes.
- **Fuera de alcance:** estas decisiones no alteran prioridad, legalidad de
  comandos, información visible, fases, victoria ni ninguna otra regla del juego.

### R-07 — Continuar separando el coordinador

- Extraer responsabilidades restantes de pila, combate y movimientos hacia
  resolutores especializados sin duplicar `GameState`.
- Exigir paridad observable, tipado estricto y pruebas de atomicidad en cada paso.
