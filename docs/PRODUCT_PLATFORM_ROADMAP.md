# Card Duel — Hoja de ruta de producto y plataforma competitiva

> **Estado: PROPUESTA DE PRODUCTO (no implementada).** Documento independiente de `docs/ROADMAP.md`, que gobierna el backend y sus bloqueos normativos. No autoriza modificar reglas de Fantasy Tokens, corpus, formatos, transporte ni contratos existentes. Requiere decisiones explícitas y pruebas antes de implementar.

## Visión

**«Los tramposos pierden. Los frikis ganan».** Juego de cartas gratuito, sin compras integradas ni ventajas competitivas de pago. La habilidad decide los campeones; la colección registra la historia. Publicidad contextual adecuada a la edad y sujeta a revisión de políticas y legislación, especialmente para menores.

## Principios acordados

1. **Gratuidad total:** sin venta de gemas, cartas, sobres, tiradas ni entradas competitivas por dinero real. La publicidad sostiene la operación, sin alterar la fuerza de los mazos.
2. **Progresión por habilidad:** victorias como fuente principal de gemas; se admiten regalos gratuitos y reciclaje de comunes como fuentes secundarias. Evitar bloquear a principiantes que pierdan.
3. **Reciclaje exclusivo de cartas COMUNES:** destrucción lógica irreversible de la instancia a cambio de gemas; nunca poco comunes, raras, épicas ni legendarias. Proteger favoritas, firmadas y estampadas. Historial conservado con minimización de datos.
4. **Coleccionismo persistente:** UUID por instancia, edición, propiedad, procedencia, historial de intercambios, firmas y sellos de campeones. Separar rareza/prestigio de potencia jugable.
5. **Ediciones vintage:** emisión limitada y cierre verificable de cada tirada; sobres sellados individualizados, con historial. Su precio en gemas puede variar por oferta y demanda, no por una revalorización garantizada. No reemitir unidades indistinguibles de una tirada cerrada.
6. **Regalos aleatorios gratuitos:** bienvenida, sobre semanal, ruleta y sorteos; probabilidades publicadas, límites razonables, resultados autoritativos del servidor, sin compra de oportunidades. Los premios vintage deben proceder de reservas emitidas previamente.
7. **Competición:** PvP, ranking K (Elo/Glicko-2 por evaluar), ligas, torneos, finales regionales/nacionales/internacionales, árbitros y recursos. Ninguna compra, publicidad o colección incrementa K.
8. **Títulos oficiales:** certificados expedidos por Card Duel tras resultados verificados y reclamaciones; firma criptográfica, revocación motivada y verificación pública respetuosa con la privacidad. Son títulos del ecosistema Card Duel, no reconocimiento federativo externo.
9. **Identidad portátil:** cuenta persistente por player ID, correo verificado, PIN local para desbloqueo y autenticación reforzada (passkey o equivalente) en dispositivos nuevos; recuperación, exportación firmada y sesiones revocables.
10. **Permanencia y justicia:** no eliminar por inactividad ni derrotas. Baja voluntaria conforme a derechos de protección de datos; sanciones con evidencia, proporcionalidad y apelación. Expulsión e inhabilitación no equivalen a borrar toda evidencia, cuya retención debe justificarse legalmente.
11. **Eventos externos:** tiendas pueden patrocinar premios, sujetos a condiciones, regulación y responsabilidades concretas. No asumir que Card Duel queda exento por ser tercero el organizador.

## Fases y dependencias

| Fase | Prioridad | Entrega propuesta | Criterio de aceptación |
| --- | --- | --- | --- |
| P0-A | Crítica | Especificación de producto, separación entre motor y plataforma | No se altera semántica, tests ni bloqueos del motor |
| P0-B | Crítica | Identidad, recuperación y autorización | Cuenta recuperable desde otro dispositivo; PIN insuficiente para alta de dispositivo |
| P0-C | Crítica | Registro de instancias y ledger de gemas | UUID único, emisión y transferencias atómicas, operaciones idempotentes |
| P0-D | Alta | Economía de gemas, burning de comunes, inventario y mazos | Nunca se queman rarezas superiores; sin dobles abonos ni saldo negativo |
| P0-E | Alta | Motor de duelos competitivos y rating | Resultado validado, anti-colusión, K independiente de colección |
| P1-A | Alta | Recompensas gratuitas, sobres, ruleta y sorteos | Probabilidades auditables, cuotas por cuenta, protección de menores |
| P1-B | Alta | Intercambio justo y ediciones limitadas/vintage | Propiedad y cantidades consistentes; cierre de emisión verificable |
| P1-C | Alta | Torneos, árbitros, resultados y apelaciones | Final homologada y decisiones auditadas |
| P2-A | Media | Certificados de campeón y pasaporte público | Firma Ed25519 verificable y estado de revocación consultable |
| P2-B | Media | Firmas de campeones, sellos y procedencia histórica | Certificado vinculado a instancia y campeón válido |
| P2-C | Media | Publicidad y eventos con tiendas | Evaluación de cumplimiento, privacidad y viabilidad económica |

**Dependencias:** P0-B antes de operaciones de propiedad; P0-C antes de burning/intercambios; P0-E antes de torneos; P1-C antes de títulos oficiales; P1-B antes de vintage negociable. Cualquier adaptador de red requiere una decisión arquitectónica nueva y debe respetar `AuthenticatedMatchApplication` y CAS, según la hoja de ruta vigente.

## Arquitectura candidata (no prescriptiva)

- **Motor existente:** determinista, headless, fuente autoritativa de las reglas y resultados. No introducir gemas ni publicidad en `GameEngine`.
- **Player Identity:** player ID inmutable, correo, autenticación, sesiones, recuperación y controles de edad.
- **Card Registry:** `CardDefinition`, `CardInstance`, `Edition`, `SealedPackInstance`, `OwnershipEvent`.
- **Economy Ledger:** movimientos de gemas de doble entrada o invariantes equivalentes, idempotencia, políticas versionadas, burning.
- **Competitive:** resultados, clasificación, emparejamientos, detección de fraude y revisión.
- **Tournament & Titles:** actas, árbitros, apelaciones, certificados, firmas y revocaciones.
- **Rewards & Ads:** presupuestos de emisión, premios gratuitos, probabilidades, publicidad no personalizada cuando corresponda.

Persistencia candidata: PostgreSQL con transacciones y JSONB de auditoría; eventos encadenados mediante SHA-256, firma Ed25519 para certificados, AES-GCM para datos sensibles y puntos de control de integridad independientes. El cifrado por sí solo no evita trampas: son indispensables controles de servidor, autorización, transacciones y monitorización.

## Reglas de economía por validar mediante simulación

- **2 gemas por común quemada**, **100 gemas por sobre estándar**, **una tirada diaria** y **un sobre semanal** son únicamente hipótesis de balance.
- No garantizar incrementos de valor de sobres vintage ni permitir creación ilimitada de gemas por bucles de apertura/reciclaje.
- Modelar emisión, burning, inventario, distribución de gemas, retención, inflación, abandono y fraude con simulaciones Monte Carlo y pruebas de propiedades.
- Diseñar acceso competitivo a cartas funcionalmente equivalentes para que el prestigio vintage no sea pay-to-win.

## Seguridad, menores y cumplimiento

- Prohibir apuestas, compra de tiradas y retirada de gemas por dinero real.
- Revisar RGPD, normativa de menores, políticas de Google Play y SDK publicitario antes de publicar; anuncios adecuados a edad y consentimiento donde proceda.
- Definir proceso de reclamación, moderación, borrado/anonimización, retención mínima de evidencias y protección frente a sanciones arbitrarias.
- No confundir sanción deportiva con derecho de supresión de datos.

## Pruebas de aceptación transversales

1. Doble solicitud de burning de una misma instancia: como máximo un abono.
2. Intento de quemar una rara o legendaria: rechazo sin mutación.
3. Intercambios concurrentes: nunca doble propiedad ni duplicación.
4. Recompensa semanal concurrente: una sola concesión por periodo.
5. Apertura de sobre: el sobre sellado se consume una sola vez y las cartas emitidas quedan vinculadas a su origen.
6. Reingreso tras años: identidad, colección y títulos se recuperan; K activo se recalibra sin borrar récord histórico.
7. Título nacional: no se expide sin final verificada, acta y cierre de reclamaciones.
8. Expulsión: requiere resolución motivada y posibilidad de apelación; acceso suspendido sin borrar indebidamente la trazabilidad.
9. Cliente manipulado: no puede emitir gemas, alterar resultados ni atribuirse otro `player_id`.
10. Suite del motor y replays históricos: sin regresiones ni cambios normativos implícitos.

## Estado y próxima decisión

Todo lo anterior está **PENDIENTE DE IMPLEMENTACIÓN**. El primer paso autorizado por este documento es revisar interfaces y diseñar contratos, no modificar reglas. Antes de construir servicios de red, definir alcance y aprobación arquitectónica separada. El producto deberá conservar compatibilidad con las fuentes normativas y las restricciones de `docs/ROADMAP.md`.
