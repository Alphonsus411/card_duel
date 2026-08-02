# Backlog de ingeniería

Este registro contiene únicamente trabajo técnico pendiente. No autoriza ni
describe cartas, colecciones, mecánicas o cambios normativos. `docs/ROADMAP.md`
continúa siendo la fuente de decisiones normativas: R-02, R-03B y R-05
permanecen bloqueadas y ninguna entrada de este backlog las promociona ni las
desbloquea.

Las entradas requieren priorización y alcance propios antes de implementarse.

## Descomposición R-03B (no inmediata)

- **R-03B.1:** conservar y verificar fuentes, hashes y paginación.
- **R-03B.2:** mantener la matriz de reglas universales frente al motor y sus pruebas.
- **R-03B.3:** evolucionar las políticas optativas Clásico/Mística sin fijar puntos.
- **R-03B.4:** preparar manifiestos para un futuro corpus externo; **no** cargar ni
  transcribir ahora el catálogo completo.
- **N-POINTS-01 (bloqueado):** no elegir entre 200, 300, 300–400 o «unos 300»
  hasta recibir una aclaración normativa trazable.
- **M-LORD-EVENT-01 (bloqueado):** mantener la Fase Activa sin reclasificar como
  Eventos todas las habilidades de Señor hasta recibir aclaración normativa.

## Mantenimiento técnico

- Revisar en cada cambio mayor el puente `R-COMPAT-019-REPLAY`. Su alcance se
  limita a reproducir semánticamente los fixtures generados con el commit 0.19
  documentado: no es sólo deserialización v2, no se activa en juego nuevo y no
  es compatibilidad perpetua. Retirarlo únicamente mediante una decisión
  versionada con criterio de soporte y prueba explícitos.

- Revisar periódicamente las dependencias bloqueadas en `uv.lock`, aplicar las
  actualizaciones compatibles en cambios aislados y documentar cualquier
  incompatibilidad antes de adoptarla.
- Inventariar y retirar utilidades internas obsoletas sólo después de confirmar
  mediante búsqueda y pruebas que no tienen consumidores.

## CI y release

- Mantener la comprobación cerrada de deriva de versión (**AUD-01**) y el
  procedimiento ensayable de rollback (**AUD-03**) incorporados en 0.20.1.

### Recomendación operativa sobre ramas

- Activar en GitHub la eliminación automática de ramas después del merge.
- Eliminar manualmente ramas `codex/*` únicamente después de comprobar que
  están integradas.
- Revisar `Bella-2.0` en una tarea separada porque no comparte ancestro con
  `main`.
- No mezclar ni borrar `Bella-2.0` desde este trabajo.

## Seguridad

- Elaborar un modelo de amenazas para las fronteras de autenticación,
  persistencia y carga de manifiestos, sin ampliar sus contratos funcionales.
- Mantener las reglas versionadas de análisis estático y detección de secretos
  del checkout (**AUD-02**) y justificar cualquier excepción antes de añadirla.
- Añadir fuzzing de entradas serializadas y manifiestos no confiables para
  verificar rechazos acotados y ausencia de filtraciones de estado privado.

## Rendimiento

- Definir benchmarks reproducibles para enumeración de acciones, resolución de
  pila, persistencia CAS y registro de manifiestos.
- Medir tiempo, memoria y tamaño de instantáneas con cargas sintéticas antes de
  fijar presupuestos o realizar optimizaciones.
- Perfilar las rutas que excedan los presupuestos acordados y optimizarlas sólo
  con pruebas de regresión que preserven el comportamiento existente.

## Calidad

- Publicar cobertura de pruebas por módulo en CI y acordar umbrales basados en
  una línea base reproducible.
- Añadir pruebas de mutación en los límites de dominio y persistencia para
  localizar aserciones insuficientes.
- Unificar las comprobaciones locales y de CI en un único punto de entrada que
  mantenga los comandos individuales disponibles para diagnóstico.

## Deuda arquitectónica

### Identidad pública de alternativas legales para un transporte futuro

`PublicLegalAction.action` identifica el tipo general de una acción legal, pero
no distingue necesariamente alternativas simultáneas del mismo tipo. El DTO
actual es suficiente para la frontera autenticada en proceso y no constituye un
protocolo de selección remota.

Antes de autorizar una decisión futura de transporte que permita seleccionar
una alternativa legal, será necesario diseñar conjuntamente:

- identificadores opacos por alternativa;
- una representación pública que no revele estado privado;
- expiración de las alternativas vinculada a la versión CAS observada;
- resolución exclusivamente contra el conjunto de acciones emitido por el
  servidor;
- rechazo de comandos internos arbitrarios; y
- prohibición de exponer elecciones privadas.

Esta limitación futura es exclusivamente técnica y documental. No implementa
resolución remota, HTTP, HTTPS, REST, WebSocket ni ningún otro transporte;
tampoco modifica `PublicLegalAction`, su serialización ni la legalidad de los
comandos existentes.

### Separación de ensamblado y ejecución de la aplicación

- Evaluar una raíz de composición explícita para almacenes, políticas y
  servicios, evitando que los adaptadores futuros construyan dependencias de
  dominio por su cuenta.
- Definir puertos técnicos para telemetría y reloj sólo cuando exista un caso de
  uso probado, manteniéndolos fuera de las reglas del motor.
