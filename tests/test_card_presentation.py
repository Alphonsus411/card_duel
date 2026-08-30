import unittest

from card_duel_engine import CardPresentation, CardPresentationCatalog


def presentation(card_id: str = "set-001") -> CardPresentation:
    return CardPresentation(card_id, "token", "Nombre", "Texto libre", None)


class CardPresentationTests(unittest.TestCase):
    def test_validates_text_fields_and_art(self):
        for field in ("card_id", "token", "name"):
            values = vars(presentation()).copy()
            values[field] = ""
            with self.subTest(field=field), self.assertRaises(ValueError):
                CardPresentation(**values)

        for field in ("card_id", "token", "name", "rules_text", "art"):
            values = vars(presentation()).copy()
            values[field] = lambda: None
            with self.subTest(field=field), self.assertRaises(TypeError):
                CardPresentation(**values)

        self.assertEqual(CardPresentation("id", "t", "n", "", "art").rules_text, "")

    def test_catalog_rejects_duplicates_and_snapshot_is_defensive(self):
        catalog = CardPresentationCatalog()
        first = presentation("b")
        catalog.register(first)
        with self.assertRaisesRegex(ValueError, "duplicada"):
            catalog.register(first)

        snapshot = catalog.snapshot()
        catalog.register(presentation("a"))
        self.assertEqual(snapshot.get("b"), first)
        self.assertNotIn("a", snapshot)
        self.assertEqual(tuple(item.card_id for item in snapshot), ("b",))

    def test_snapshot_traversal_is_sorted_by_identifier(self):
        snapshot = CardPresentationCatalog(
            (presentation("z"), presentation("a"), presentation("m"))
        ).snapshot()
        self.assertEqual(
            tuple(item.card_id for item in snapshot.presentations()),
            ("a", "m", "z"),
        )
        with self.assertRaisesRegex(KeyError, "desconocida"):
            snapshot.get("missing")


if __name__ == "__main__":
    unittest.main()
