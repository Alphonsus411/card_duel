import unittest

from card_duel_engine import CardCatalog

from fixtures import test_deck


class CatalogTests(unittest.TestCase):
    def test_production_catalog_starts_empty(self):
        self.assertEqual(len(CardCatalog()), 0)

    def test_catalog_rejects_duplicate_definition(self):
        catalog = CardCatalog()
        card = test_deck("A", 1)[0]
        catalog.register(card)
        with self.assertRaisesRegex(ValueError, "duplicada"):
            catalog.register(card)
