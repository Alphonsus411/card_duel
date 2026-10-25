# CAP-DAMAGE-002 P5 — matriz de verificación

**Fecha:** 2026-10-25
**Estado:** completada con límite de replay explícito

## Cobertura confirmada

- Daño de combate a permanente: saldo insuficiente, consumo exacto y un único
  remanente aplicado.
- Herida de combate a jugador: la misma propiedad para combate sin bloqueador.
- Combate ordinario y Desafío: paridad entre ejecución directa y snapshot v5
  restaurado, incluyendo digest final.
- Rollback del comando público: una excepción posterior a la prevención revierte
  conjuntamente daño, reservas, eventos y estado de combate.
- Daño ajeno a combate, compatibilidad de snapshots/replays heredados, esquema
  y causa desconocidos: permanecen cubiertos por las pruebas P1–P4.

## Delimitación aprobada

No existe todavía un comando o efecto autorizado que cree una reserva tipada.
En consecuencia, un replay no puede reconstruir una reserva positiva sin
introducir una mutación de prueba no registrada o ampliar el contrato de juego.
P5 no hace ninguna de esas dos cosas: verifica replay para compatibilidad y
persistencia ya existentes, y deja la paridad positiva de replay para la fase
que autorice un productor reproducible.

Esto no añade causas, cartas, efectos, redirección, sustituciones ni reglas de
duración. `CAP-DAMAGE-002` continúa en `PARTIAL`.
