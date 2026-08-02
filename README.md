# Card Duel Engine (nombre provisional)

Primera estructura del backend headless para el futuro juego de cartas. El
paquete implementa el armazón de las reglas universales de Fantasy Tokens sin
incluir ninguna carta, personaje ni colección antigua.

## Alcance de la versión 0.20.0

- Catálogo de cartas vacío y extensible.
- Contratos pequeños de gestores verificados por `mypy` y dobles mínimos independientes.
- Resolución mediante un registro cerrado en `EffectManager`, sin estado duplicado.
- Elecciones de sustitución reproducidas mediante una operación encapsulada de consumo.
- Definiciones e instancias de cartas separadas.
- Zonas privadas y públicas.
- Jugadores activo y pasivos.
- Preparación para dos o más participantes, autorizada expresamente por el
  reglamento fuente; sus condiciones terminales multijugador siguen sin estar
  definidas y no se presentan como mecánica normativa.
- Secuencia Robo, Mantenimiento, Efectos, Combate, Legendaria y Descarte.
- Mano inicial, mulligan decreciente y reciclaje del descarte.
- Reserva de Pasos y pago atómico.
- Transmutación básica de permanentes.
- Juego genérico desde la mano y pago atómico de costes.
- Prioridad alterna y pila de resolución LIFO.
- Efectos declarativos iniciales: Heridas, curación, Pasos y robo.
- Recursos Rápidos como respuesta en cualquier fase.
- Combate con atacantes, bloqueadores, daño y destrucción.
- Activación automática de efectos legendarios propios.
- Comandos validados y registro determinista de eventos.
- Controladores intercambiables para humanos, agentes y AGIX.
- Invariantes para detectar corrupción del estado.
- Costes compuestos y atómicos: Pasos, Heridas, descarte, sacrificio y agotamiento.
- Habilidades activadas y disparadas integradas en la pila.
- Objetivos de jugador y de permanente, con inmunidades por tipo de fuente.
- Daño a criaturas, prevención de daño y Heridas e indestructibilidad.
- Modificadores permanentes y hasta el final del turno.
- Equipos, anexos, bonificaciones y separación automática.
- Limpieza de fin de turno para daño, prevención y límites de activación.
- Drenaje universal una vez por turno activo: un Paso gratuito y hasta cuatro
  adicionales por tres Heridas cada uno.
- Objetivos múltiples con límites mínimos y máximos declarativos.
- Capas continuas de Fuerza y palabras clave filtradas por controlador, tipo y subtipo.
- Divinos inmunes a Eventos, Recursos Rápidos y habilidades, pero transmutables.
- Señores de Abismo, Elíseo, Magia y Reinos con Fuerza pagable y descarte al llegar a cero.
- Transformación temporal de Señores no criatura.
- Desafío como duelo cerrado que sustituye el combate normal del turno.
- Elección explícita del orden de resolución de disparos simultáneos.
- Zonas de jugador como objetivos sin revelar las cartas que contienen.
- Movimiento declarativo de cartas entre zonas.
- Reparto exacto de daño entre jugadores y permanentes.
- Elección de objetivos para habilidades disparadas y efectos legendarios.
- Sustituciones declarativas cuando un permanente fuera a ir al descarte.
- Escudos consumibles de regeneración y efectos que impiden regenerar.
- Supresión de la siguiente fase, hasta fin de turno o de forma continua.
- Límite configurable de enumeración para evitar explosiones combinatorias en AGIX.
- Búsquedas pausables en zonas ocultas, con filtros declarativos y selección privada.
- Revelado opcional del resultado de una búsqueda y barajado explícito reproducible.
- Costes alternativos completos con Pasos, Heridas, descarte, sacrificio y molienda.
- Varias sustituciones de movimiento por carta, resueltas por prioridad declarada.
- Cambio de control permanente o temporal, conservando propietario y zona correcta.
- Copia de una definición existente y transformación completa en otra definición.
- Restauración automática de control, copia y transformación al final del turno.
- Costes calculados desde Heridas, Pasos, mano, tapiz, descarte, exilio,
  permanentes rivales o número de turno, con límites declarativos.
- Fórmulas dinámicas para el coste normal, alternativas y habilidades activadas.
- Orden de sustituciones elegido por el controlador de un permanente.
- Parches parciales de texto para conceder o retirar palabras clave, subtipos,
  habilidades y Transmutación sin modificar el catálogo.
- Parches permanentes o hasta el final del turno, eliminados al abandonar el tapiz.
- Costes con valor `X` en cartas, alternativas y habilidades activadas.
- Congelación de `X` en la pila y uso declarativo en magnitudes y daño repartido.
- Parches de efectos para cambiar magnitud, modo y cantidad de objetivos.
- Elecciones de sustitución diferidas hasta el movimiento exacto.
- Reejecución transaccional de la acción original, incluso con varias elecciones.
- Observaciones y acciones específicas para controladores humanos, IA y AGIX.
- Instantáneas JSON restaurables con catálogo, reglas, estado y contadores.
- Huellas SHA-256 para detectar corrupción o alteraciones accidentales.
- Historial autoritativo de comandos y mulligans dentro de la partida.
- Reproducción determinista desde semilla, mazos y comandos.
- Verificación automática de la huella final de una reproducción.
- Manifiestos externos versionados para incorporar colecciones nuevas.
- Lista cerrada de tipos persistibles y validación estricta de campos.
- Registro atómico de colecciones, sin cargas parciales ante una colisión.
- Resolutores puros de costes dinámicos, costes `X` y parches de texto.
- Migraciones encadenadas de instantáneas, reproducciones y manifiestos `v1 → v2`.
- Metadatos y dependencias declarativas en manifiestos de colección.
- Almacén en memoria aislado para pruebas y procesos locales.
- Almacén SQLite multiproceso con modo WAL y transacciones atómicas.
- Control optimista de versiones para impedir actualizaciones perdidas.
- Pruebas generativas deterministas de fórmulas y secuencias de comandos.
- Componentes aislados para combate, pila y movimiento entre zonas.
- `MatchService` headless con persistencia CAS y contrato futuro para AGIX.
- Preparación atómica de mazos y aplicación estricta del registro autoritativo.
- SQLite en memoria funcional entre las conexiones cortas del servicio.
- Ciclo de vida explícito para SQLite: `close()` es idempotente y, también al
  salir de un bloque `with`, el almacén rechaza cualquier operación posterior.
- Bloqueo explícito de finales multijugador no definidos, sin inferir ganadores
  ante una concesión o al alcanzar el límite de Heridas.
- Hoja de ruta con R-04 (confianza de colecciones), R-06 (frontera autenticada),
  R-07.1 (combate, incluida su enumeración) y R-07.2 (movimientos y
  sustituciones) completadas. También se completó R-03A como inventario
  exclusivamente documental de la contradicción verificable sobre Divinos, sin
  cartas ni cambios de reglas. R-03B se divide ahora en fuente verificable,
  reglas universales, formatos de mazo y futuro corpus, y permanece abierta
  hasta alinear código, documentación y pruebas; R-02, los extremos normativos
  de R-03B y R-05 permanecen bloqueados. La
  frontera de R-06 es agnóstica del transporte; un adaptador HTTP
  u otro servicio de red concreto continúa fuera de alcance, no tiene entrega de
  hoja de ruta asignada y no es un pendiente implementable. Cualquier decisión
  futura deberá conservar `AuthenticatedMatchApplication` como frontera
  autoritativa: el transporte no podrá aceptar `player_id`, exponer `GameEngine`
  o `GameState`, omitir `expected_version`/CAS ni reinterpretar comandos.

Las únicas cartas utilizadas están en `tests/fixtures.py` y sirven para probar
el motor. El catálogo de producción comienza vacío.

Los reglamentos primarios son `Fantasy Tokens.pdf` y `Fantasy Tokens Edicion Mitica.pdf`. Se conservan en el repositorio para trazabilidad, pero **ninguno de los dos PDF se empaqueta en el wheel**. El catálogo distribuido continúa vacío: no se ha incorporado ninguna carta de producción.

## Desarrollo reproducible

`uv` 0.7.22 y `uv.lock` constituyen la única estrategia para resolver las
dependencias de desarrollo y CI. La instalación de usuario continúa siendo un
wheel estándar sin dependencias de ejecución.

```bash
uv sync --locked --extra dev
uv run python -m mypy
uv run python -m compileall -q src tests
uv run python -m unittest discover -s tests -v
uv run python scripts/verify_release.py --profile runtime
uv run python scripts/verify_release.py --profile full --json release-verification.json
uv run python scripts/verify_reproducible_wheel.py
```

El verificador obtiene `SOURCE_DATE_EPOCH` de la fecha del commit `HEAD`, construye
dos veces en directorios temporales limpios y compara nombre, bytes, SHA-256 y
metadatos.

## Ejecutar las pruebas

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

## Principio arquitectónico

La interfaz nunca modifica el estado directamente. Un controlador solicita una
acción, el motor valida un comando, aplica las reglas y publica eventos. Una
interfaz gráfica, un cliente remoto y AGIX utilizarán exactamente el mismo
contrato.

Consulta `docs/ARCHITECTURE.md` y `docs/RULES_BASELINE.md` para conocer las
decisiones de esta primera versión. El trabajo técnico pendiente se registra
por separado en `docs/ENGINEERING_BACKLOG.md`.

### Registro autoritativo de colecciones

`CollectionRegistry` permite cargar manifiestos v2 individualmente o por lotes atómicos, resuelve dependencias de forma determinista y conserva revisión, dependencias y digest canónico. El sobre de firma v1 es independiente, y `CollectionTrustPolicy` recibe de la aplicación las claves confiables y su revocación. SHA-256 aporta integridad; una firma aceptada por la política aporta autenticidad. Manifiestos y sobres son datos y nunca código ejecutable.
