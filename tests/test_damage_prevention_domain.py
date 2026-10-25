from __future__ import annotations

import unittest

from card_duel_engine.domain import DamageCause, DamagePreventionReservation
from card_duel_engine.engine.damage_prevention import (
    reserve_damage_prevention,
    resolve_damage_prevention,
)


class DamagePreventionDomainTests(unittest.TestCase):
    def test_cause_set_is_closed_to_combat_in_this_increment(self) -> None:
        self.assertEqual(tuple(DamageCause), (DamageCause.COMBAT,))

    def test_reservation_requires_explicit_cause_and_positive_amount(self) -> None:
        reservation = reserve_damage_prevention(DamageCause.COMBAT, 3)

        self.assertEqual(reservation, DamagePreventionReservation(DamageCause.COMBAT, 3))
        with self.assertRaises(ValueError):
            DamagePreventionReservation("combat", 3)  # type: ignore[arg-type]
        for amount in (0, -1, True):
            with self.subTest(amount=amount):
                with self.assertRaises(ValueError):
                    reserve_damage_prevention(DamageCause.COMBAT, amount)

    def test_resolution_is_pure_and_reports_every_atomic_output(self) -> None:
        reservation = reserve_damage_prevention(DamageCause.COMBAT, 3)

        resolution = resolve_damage_prevention(reservation, DamageCause.COMBAT, 5)

        self.assertEqual(reservation, DamagePreventionReservation(DamageCause.COMBAT, 3))
        self.assertEqual(resolution.cause, DamageCause.COMBAT)
        self.assertEqual(resolution.prevented_amount, 3)
        self.assertEqual(resolution.remaining_damage, 2)
        self.assertEqual(resolution.remaining_reservation, 0)

    def test_zero_damage_preserves_the_reservation_and_invalid_inputs_fail_closed(self) -> None:
        reservation = reserve_damage_prevention(DamageCause.COMBAT, 3)

        resolution = resolve_damage_prevention(reservation, DamageCause.COMBAT, 0)

        self.assertEqual(resolution.prevented_amount, 0)
        self.assertEqual(resolution.remaining_damage, 0)
        self.assertEqual(resolution.remaining_reservation, 3)
        for invalid_damage in (-1, True):
            with self.subTest(invalid_damage=invalid_damage):
                with self.assertRaises(ValueError):
                    resolve_damage_prevention(
                        reservation, DamageCause.COMBAT, invalid_damage
                    )
        with self.assertRaises(ValueError):
            resolve_damage_prevention(
                reservation, "combat", 1  # type: ignore[arg-type]
            )


if __name__ == "__main__":
    unittest.main()
