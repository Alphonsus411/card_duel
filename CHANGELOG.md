# Historial de versiones

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
