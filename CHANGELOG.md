# Historial de versiones

## Sin publicar

## 0.20.0

- Integradas como fuentes primarias verificables tanto las reglas base como la
  actualización Mítica, con hashes, tamaño y doble paginación física/interna.
- Reorganizada la trazabilidad paginada en reglas universales, formatos de mazo,
  normalizaciones del motor, bloqueos y contenido de cartas.
- Formalizada la política de mazos mediante perfiles optativos Clásico/Mística,
  sin resolver las cifras contradictorias de `N-POINTS-01`.
- Documentadas las correcciones mecánicas ya realizadas: secuencia Legendaria,
  Divinos transmutables con inmunidad Mítica, Desafío, Señores, sustituciones,
  regeneración y consolidación de combate y zonas, sin atribuir cambios nuevos.
- Añadidas regresiones con artefactos 0.19.0 de esquemas v1/v2 que conservan
  huella final, historial, contadores, orden e identificadores.
- Conservada la compatibilidad persistente: esquemas v1/v2 y migración v1 → v2;
  no se introduce v3 ni se alteran condiciones terminales multijugador.
- Excluidos explícitamente del wheel ambos PDF, las dependencias runtime y todo
  catálogo de producción; el catálogo distribuido sigue vacío.
- Centralizada la versión vigente en `project.version`; paquete, `RuleSet`,
  scripts y workflow la resuelven dinámicamente.

- Añadida `docs/MYTHIC_RULES_AUDIT.md` con jerarquía de fuentes, doble paginación
  Mítica, categorías A–E y separación exacta entre reglas y cartas concretas.
- Registrados como bloqueos `N-POINTS-01` (200, 300, 300–400 y recomendación de
  unos 300 puntos) y la ambigüedad de «a modo de Eventos», que solo respalda la
  temporización de Fase Activa para habilidades de Señor.
- Corregidas las afirmaciones obsoletas sobre la ausencia del PDF Mítico o de su
  paginación; el inventario usa física 3 / interna 2 para Divinos y física 4 /
  interna 3 para Señores de los Reinos, Desafío y comienzo del corpus de cartas.
- Dividida R-03 en el inventario documental R-03A, ya completado, y la
  eventual decisión normativa R-03B, bloqueada hasta recibir aclaración oficial.
- Registrada la modificación base–Mítica de inmunidad y Transmutación de Divinos
  con referencias verificables y la precedencia documentada.
- Conservados sin cambios el motor y las expectativas reglamentarias de pruebas;
  el inventario no incorpora cartas ni resuelve nuevas ambigüedades.
- Decidido de forma uniforme que HTTP y cualquier otro transporte permanecen
  fuera de alcance, sin identificador de hoja de ruta ni consideración de
  pendiente implementable.
- Fijada `AuthenticatedMatchApplication` como frontera autoritativa también ante
  una eventual decisión futura: ningún transporte podrá aceptar `player_id`,
  exponer `GameEngine` o `GameState`, omitir `expected_version`/CAS ni
  reinterpretar comandos.
- Corregida la documentación de pendientes para reconocer como completadas la
  política de confianza de colecciones de R-04 y la frontera autenticada de
  aplicación de R-06.
- Aclarado que R-06 entrega una frontera agnóstica del transporte, no un
  adaptador HTTP ni otro servicio de red concreto, que continúa fuera de alcance.

- Cerrada R-07.2 con una única implementación de robo, movimientos y
  sustituciones en `ZoneManager`; `GameEngine` conserva solo adaptadores y los
  servicios transaccionales del coordinador.
- Añadida paridad exhaustiva de zonas con contexto mínimo independiente, curso
  reproducible, elecciones y contadores, además de atomicidad ante rechazo y
  excepción; no se modifican reglas ni ambigüedades normativas.

- Cerrada R-07.1 al trasladar a `CombatManager` la construcción determinista de
  atacantes, Desafíos, bloqueadores y `ResolveCombat`, conservando el límite de
  enumeración y la aceptación autoritativa de comandos válidos no enumerados.
- Ampliada la paridad de combate para comparar acceso público y gestor directo
  con dos y más jugadores, éxito, rechazo, excepción y huellas que incluyen
  estado, eventos, historial y contadores; R-07.2 queda habilitada.
- Cerrada R-06 al alinear la hoja de ruta con la frontera autenticada ya
  implementada y verificar por separado las capacidades de creación,
  observación, envío y administración sobre memoria y SQLite.
- Dividida la continuación de R-07 en extracciones consecutivas de combate y
  movimientos, sin promover deuda normativa ni mezclar cambios de reglas.
- Extraída únicamente la coordinación de creación y lotes de disparos a
  `StackManager`, ampliando `StackContext` con operaciones tipadas explícitas.
- Añadidos dobles mínimos, testigo estructural y paridad de éxito, acción ilegal,
  elección pendiente y excepción, incluidos estado, eventos, historial y próximos
  identificadores.
- Conservados en `GameEngine` transacción, fases, comandos, invariantes y replay
  de movimientos reemplazables. Esta extracción arquitectónica no modifica
  ninguna regla observable.

## 0.19.0

- Añadido un sobre de firma v1 separado que conserva el manifiesto v2 y su
  digest canónico sin cambios.
- Incorporada una política de confianza inyectable con resolución de claves,
  revocación, lista cerrada de algoritmos y verificación HMAC-SHA256.
- El registro verifica por completo firmas, dependencias y colisiones antes de
  modificar el catálogo o la procedencia; no carga ni ejecuta código externo.
- Documentadas integridad, autenticidad, compatibilidad y la finalización de
  R-04, sin alterar reglas ni añadir cartas.

## 0.18.3

- Las partidas de tres o más participantes dejan de declarar como ganadores a
  todos los no derrotados ante una concesión o el límite de Heridas: se bloquean
  con diagnóstico explícito hasta que exista una regla normativa.
- Añadida una hoja de ruta con tareas separadas y sin convertir deuda normativa
  en mecánicas nuevas.
- Marcada como completada la protección de condiciones terminales multijugador
  entregada en 0.18.3 y seleccionada R-04 como única tarea siguiente. R-02 y
  R-03 siguen bloqueadas por aclaraciones normativas, y R-05 por la ausencia de
  un esquema 3 definido.

## 0.18.2

- Documentada la autorización expresa del reglamento para enfrentarse a uno o
  más adversarios y compartir entre todos el límite acordado de Heridas.
- Registrada, sin inferir una mecánica, la ausencia de reglas multijugador para
  concesión, continuidad tras derrotas, simultaneidad y selección u orden de
  ganadores.

## 0.18.1

- La creación de partidas valida por completo las definiciones antes de mutar el
  catálogo y rechaza cartas ajenas a un registro de colecciones inyectado.
- `RuleSet` rechaza configuraciones que romperían el mínimo de participantes o la
  secuencia normativa de fases.
- `SQLiteMatchStore(":memory:")` conserva sus datos entre conexiones cortas y
  ofrece cierre explícito de la conexión de mantenimiento.

## 0.17.0

- Resolución extraída a `EffectManager`, con `EffectContext` tipado, registro
  cerrado de `EffectKind` y error de dominio para efectos no soportados.
- Perfiles `runtime` y `full`, JSON determinista y diagnóstico por etapa.
- Matriz runtime 3.11–3.13 y una única entrega full en 3.13.
- Trazabilidad de reglas y cobertura mínima elevada al 85%.

## 0.16.0

- Verificador integral y fail-fast para lockfile, tipado, compilación, cobertura,
  carga determinista, persistencia, wheel reproducible e instalación multiversión.
- Auditoría del wheel mediante manifiesto cerrado, orden ZIP canónico e integridad RECORD.
- Las rondas de persistencia ejecutan comandos reproducibles sin mutar el estado interno.
- CI unificada en el verificador común para Python 3.11–3.13.

## 0.15.0

- `mypy` refuerza igualdad, genéricos y definiciones incompletas en los 31 módulos.
- Validaciones multiplataforma para 300 simulaciones, 54.000 comandos, 84.000
  eventos y 30 pares snapshot/replay con huellas idénticas.
- Cobertura de ramas con umbral anti-regresión y dependencia solo de desarrollo.
- Auditoría integral y reproducible del wheel, con informe JSON y SHA-256.
- CI con acciones fijadas por SHA, permisos mínimos, límites y trabajos separados.

## 0.14.0

- Tipado estricto de los 31 módulos del paquete y validación del runner sin partida.
- Dependencias de desarrollo reproducibles con `uv sync --locked --extra dev`.
- Wheels deterministas mediante `SOURCE_DATE_EPOCH`, con verificación doble.
- CI matricial en Python 3.11–3.13 y trabajo único de empaquetado.

## 0.13.0

- Verificación estática con `mypy` de motor, servicio, almacenamiento y persistencia.
- `GameEngine` se comprueba estructuralmente contra los tres protocolos independientes.
- Estado de reproducción de sustituciones encapsulado tras una operación de consumo.
- Dobles mínimos de prueba para combate, pila y zonas sin construir un motor completo.
- CI endurecida en Python 3.11–3.13, con compilación, pruebas y construcción del wheel.

## 0.12.0

- Contratos `Protocol` específicos para combate, pila y zonas, inyectados por el coordinador.
- Eliminada la delegación dinámica y las copias de `_EngineComponent`, sin duplicar `GameState`.
- Pruebas directas de gestores, atomicidad y paridad de `MatchService` entre memoria y SQLite.
- Validación continua en Python 3.11, 3.12 y 3.13, incluida compilación, pruebas y wheel.
- Compatibilidad conservada con API 0.11.0, documentos v2 y migraciones v1.

## 0.11.0

- Combate, pila y zonas extraídos a componentes especializados.
- `GameEngine` sigue coordinando y `GameState` conserva la autoridad.
- `MatchService` crea, recupera, observa y ejecuta comandos con CAS.
- Contratos `MatchStore` y `CommandSource` desacoplados de AGIX.
- Compatibilidad con documentos v2 y migraciones desde v1.

## 0.10.0

- Extracción de costes y parches de texto a resolutores puros sin estado mutable.
- Reducción de responsabilidades directas del coordinador `GameEngine`.
- Esquema 2 para instantáneas con huella interna independiente del estado.
- Esquema 2 para reproducciones con recuento verificado de comandos.
- Esquema 2 para manifiestos con metadatos y dependencias.
- Registro explícito de migraciones `v1 → v2` y rechazo de rutas desconocidas.
- `InMemoryMatchStore` con aislamiento por instantánea y compare-and-swap.
- `SQLiteMatchStore` con WAL, `BEGIN IMMEDIATE` y versiones optimistas.
- Conflictos diferenciados de partidas inexistentes y versiones obsoletas.
- Pruebas generativas deterministas para fórmulas y máquinas de estados.
- Carrera concurrente de ocho escritores validada sobre SQLite.

## 0.9.0

- Codec JSON seguro basado en una lista cerrada de dataclasses y enumeraciones.
- Conservación de tuplas, conjuntos, claves enum y orden de mapeos relevantes.
- Comprobación estricta de tipos al reconstruir objetos del dominio.
- Instantáneas con reglas, catálogo, estado, decisiones pendientes y contadores.
- Huella SHA-256 y validación de invariantes después de restaurar.
- Historial automático de comandos aceptados y mulligans de preparación.
- Registro de reproducción con semilla, orden de jugadores y mazos originales.
- Reconstrucción de partidas y comparación de la huella final esperada.
- Manifiestos de colección con versión mínima de motor y revisión propia.
- Rechazo de cartas duplicadas, colecciones incoherentes y tipos desconocidos.
- Registro de una colección completo o nulo ante conflictos de catálogo.

## 0.8.0

- Costes `X` con componente, multiplicador e intervalo declarativos.
- Costes `X` normales, alternativos y de habilidades activadas.
- Valor de `X` almacenado en la pieza de pila y registrado en eventos.
- Magnitudes de efectos calculadas como base más múltiplo de `X`.
- Reparto de daño validado contra la magnitud variable definitiva.
- Parches sobre efectos principales, legendarios o de una habilidad concreta.
- Cambio declarativo de magnitud, modo y límites de objetivos.
- Comando `ResolveMoveReplacement` para elecciones en el instante del movimiento.
- Reversión y reejecución transaccional de acciones interrumpidas.
- Soporte para varias elecciones de sustitución dentro de una misma acción.
- Ocultación de alternativas al controlador que no debe elegir.

## 0.7.0

- Fórmulas de coste compuestas por métricas del estado, multiplicadores,
  desplazamiento y límites mínimo y máximo.
- Costes dinámicos en cartas, alternativas y habilidades activadas.
- Registro del coste concreto pagado para reproducción y auditoría.
- Comando `SetReplacementOrder` y observación del orden vigente.
- Sustituciones elegibles ordenadas por su controlador, con prioridad automática
  como alternativa cuando la carta no exige elección.
- Modificación parcial del texto efectivo mediante capas inmutables.
- Concesión y retirada de palabras clave, subtipos y habilidades.
- Activación o desactivación declarativa de Transmutación.
- Expiración de parches al final del turno o al abandonar el tapiz.
- Invariantes nuevas para parches y preferencias de sustitución.

## 0.6.0

- Búsquedas interactivas en mazo u otras zonas mediante filtros de tipo, rango,
  subtipo o identificador de definición.
- Pausa y reanudación de la pila mientras el controlador elige cartas ocultas.
- Visibilidad privada de candidatos y revelado configurable del resultado.
- Barajado explícito y determinista, separado del movimiento de cartas.
- Costes alternativos atómicos, incluida la molienda del mazo propio.
- Múltiples sustituciones de movimiento con precedencia declarativa estable.
- Cambio de control permanente o hasta el final del turno.
- Copia de permanentes y transformación completa sin mutar la definición impresa.
- Restauración de identidades y control durante la limpieza del turno.
- Nuevas invariantes para control, búsquedas pendientes y definiciones sustitutas.

## 0.5.0

- Objetivos de zona y movimiento de cartas sin filtrar información oculta.
- Daño repartido con validación exacta de cantidades y objetivos mixtos.
- Selección diferida de objetivos para disparos automáticos.
- Sustituciones de movimientos al descarte por mano, mazo, exilio o campo.
- Retornos al campo con pérdida de Fuerza, agotamiento y umbral final.
- Regeneración consumible integrada antes de las sustituciones de movimiento.
- Daño y destrucción que pueden prohibir regeneración.
- Supresiones de fase temporales, de próxima ocurrencia y continuas.
- Enumeración acotada de acciones combinatorias sin relajar la validación.

## 0.4.0

- Drenaje universal conforme a la actualización Mítica.
- Objetivos múltiples declarativos.
- Efectos continuos por controlador, tipo y subtipo.
- Inmunidad automática de Tokens Divinos.
- Dominios de Señor y costes pagados con Fuerza.
- Forma de criatura permanente o hasta el final del turno.
- Regla universal de Desafío integrada en la Fase de Combate.
- Orden elegido para disparos simultáneos.
- Observaciones públicas de pila y disparos para controladores humanos o AGIX.

## 0.3.0

- Costes compuestos con validación previa y pago atómico.
- Habilidades activadas, límites por turno y restricciones de fase.
- Disparos al entrar en el campo y al transmutarse.
- Objetivos de permanentes e inmunidades a Eventos, Rápidos y habilidades.
- Daño, prevención, destrucción e indestructibilidad.
- Modificadores de Fuerza permanentes y temporales.
- Equipos con coste de anexión, bonificación y separación segura.
- Acciones basadas en estado y limpieza del final del turno.

## 0.2.0

- Juego de cartas genéricas desde la mano.
- Pago atómico de Pasos.
- Prioridad alterna y respuestas.
- Pila LIFO reproducible.
- Primer conjunto de efectos declarativos.
- Combate básico completo.
- Disparos de Fase Legendaria.
- Agente de simulación orientado a completar fases.

## 0.1.0

- Dominio, zonas, fases, Transmutación, preparación y simulación inicial.

## 0.18.0

- Añadido registro transaccional de colecciones con dependencias deterministas, revisiones y procedencia SHA-256.
- Añadida política externa opcional de confianza e inyección del registro en motor y servicio.
- El perfil runtime ya no prepara ni audita wheels; la auditoría usa fixtures ZIP sintéticos.
- Cobertura de ramas mínima elevada al 86%, sin alterar los esquemas persistentes v2.
