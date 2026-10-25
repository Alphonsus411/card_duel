"""Operaciones puras para la prevención de daño tipada.

Este módulo no conoce ``GameState`` ni persistencia. P3 decidirá cómo guardar
el perfil heredado y la reserva nueva; P4 conectará estas operaciones a la
puerta común de combate.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..domain.enums import DamageCause
from ..domain.models import DamagePreventionReservation


@dataclass(frozen=True)
class DamagePreventionResolution:
    """Resultado completo de aplicar una reserva a un único importe de daño."""

    cause: DamageCause
    prevented_amount: int
    remaining_damage: int
    remaining_reservation: int

    def __post_init__(self) -> None:
        if not isinstance(self.cause, DamageCause):
            raise ValueError("La causa de resolución no es válida")
        values = (
            self.prevented_amount,
            self.remaining_damage,
            self.remaining_reservation,
        )
        if any(type(value) is not int or value < 0 for value in values):
            raise ValueError("Los importes de prevención deben ser enteros no negativos")


def reserve_damage_prevention(
    cause: DamageCause, amount: int
) -> DamagePreventionReservation:
    """Crea una reserva tipada; no existe una causa implícita."""

    return DamagePreventionReservation(cause, amount)


def resolve_damage_prevention(
    reservation: DamagePreventionReservation,
    cause: DamageCause,
    damage_amount: int,
) -> DamagePreventionResolution:
    """Calcula consumo y remanente sin mutar la reserva de entrada.

    El resultado contiene las tres cantidades que P4 deberá confirmar de forma
    atómica: protección consumida, daño restante y saldo de reserva.
    """

    if not isinstance(reservation, DamagePreventionReservation):
        raise ValueError("La reserva de prevención no es válida")
    if not isinstance(cause, DamageCause):
        raise ValueError("La causa de daño no es válida")
    if type(damage_amount) is not int or damage_amount < 0:
        raise ValueError("El daño debe ser un entero no negativo")

    prevented = (
        min(reservation.amount, damage_amount)
        if reservation.cause is cause
        else 0
    )
    return DamagePreventionResolution(
        cause=cause,
        prevented_amount=prevented,
        remaining_damage=damage_amount - prevented,
        remaining_reservation=reservation.amount - prevented,
    )
