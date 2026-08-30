import unittest
from dataclasses import dataclass

from card_duel_engine.presentation import (
    CardPresentation,
    CardPresentationCatalog,
    CardPresentationSnapshot,
    validate_card_presentations,
)


def presentation(card_id: str, token: str) -> CardPresentation:
    return CardPresentation(card_id, token, f"Nombre {card_id}", "", "")


@dataclass(frozen=True)
class MechanicalCardStub:
    card_id: str


class MechanicalCatalogStub:
    def __init__(self, *card_ids: str) -> None:
        self._definitions = tuple(MechanicalCardStub(card_id) for card_id in card_ids)

    def definitions(self) -> tuple[MechanicalCardStub, ...]:
        return self._definitions


class CardPresentationTests(unittest.TestCase):
    def test_requires_strings_and_non_blank_identity_fields(self):
        with self.assertRaisesRegex(ValueError, "rules_text debe ser una cadena"):
            CardPresentation("a", "token", "Nombre", None, "")  # type: ignore[arg-type]
        for field_name, values in (
            ("card_id", (" ", "token", "Nombre", "", "")),
            ("token", ("a", "\t", "Nombre", "", "")),
            ("name", ("a", "token", "\n", "", "")),
        ):
            with self.subTest(field_name=field_name):
                with self.assertRaisesRegex(ValueError, field_name):
                    CardPresentation(*values)

    def test_allows_empty_optional_content_without_normalizing_identifiers(self):
        card = CardPresentation(" card ", " token ", " Nombre ", "", "")
        self.assertEqual(card.card_id, " card ")
        self.assertEqual(card.token, " token ")


class CardPresentationCatalogTests(unittest.TestCase):
    def test_indexes_by_card_id_and_orders_independently_of_registration(self):
        catalog = CardPresentationCatalog()
        second = presentation("b", "token-b")
        first = presentation("a", "token-a")
        catalog.register(second)
        catalog.register(first)
        self.assertIs(catalog.get("a"), first)
        self.assertEqual(catalog.presentations(), (first, second))
        self.assertIn("a", catalog)
        self.assertNotIn("token-a", catalog)

    def test_rejects_duplicate_card_ids_and_global_tokens(self):
        catalog = CardPresentationCatalog()
        catalog.register(presentation("a", "token"))
        with self.assertRaisesRegex(ValueError, "card_id duplicado"):
            catalog.register(presentation("a", "other"))
        with self.assertRaisesRegex(ValueError, "token duplicado"):
            catalog.register(presentation("b", "token"))

    def test_snapshot_is_defensive_sorted_and_unchanged_after_registration(self):
        source = {"b": presentation("b", "token-b")}
        snapshot = CardPresentationSnapshot(source)
        source["a"] = presentation("a", "token-a")
        self.assertEqual([card.card_id for card in snapshot.presentations()], ["b"])

        catalog = CardPresentationCatalog()
        catalog.register(presentation("b", "catalog-b"))
        catalog_snapshot = catalog.snapshot()
        catalog.register(presentation("a", "catalog-a"))
        self.assertEqual([card.card_id for card in catalog_snapshot.presentations()], ["b"])
        self.assertEqual([card.card_id for card in catalog.presentations()], ["a", "b"])

    def test_direct_snapshot_construction_revalidates_ids_and_tokens(self):
        with self.assertRaisesRegex(ValueError, "clave.*card_id"):
            CardPresentationSnapshot({"wrong": presentation("a", "token-a")})
        with self.assertRaisesRegex(ValueError, "token duplicado"):
            CardPresentationSnapshot(
                {"a": presentation("a", "token"), "b": presentation("b", "token")}
            )


class CardPresentationValidationTests(unittest.TestCase):
    def test_returns_none_when_card_ids_match_without_comparing_names(self):
        mechanical = MechanicalCatalogStub("a")
        editorial = CardPresentationCatalog()
        editorial.register(CardPresentation("a", "token", "Nombre distinto", "", ""))

        self.assertIsNone(validate_card_presentations(mechanical, editorial))  # type: ignore[arg-type]

    def test_reports_both_mismatch_types_with_sorted_ids(self):
        mechanical = MechanicalCatalogStub("missing-z", "shared", "missing-a")
        editorial = CardPresentationCatalog()
        editorial.register(presentation("orphan-z", "token-z"))
        editorial.register(presentation("shared", "token-shared"))
        editorial.register(presentation("orphan-a", "token-a"))

        with self.assertRaisesRegex(
            ValueError,
            "Presentaciones huérfanas: orphan-a, orphan-z; "
            "Definiciones mecánicas sin presentación: missing-a, missing-z",
        ):
            validate_card_presentations(mechanical, editorial)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
