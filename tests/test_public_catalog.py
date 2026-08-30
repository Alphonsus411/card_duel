import json
import unittest
from dataclasses import FrozenInstanceError

from card_duel_engine import (
    CardCatalog,
    CardPresentation,
    CardPresentationCatalog,
    PublicCard,
    PublicCardCatalog,
)
from card_duel_engine.domain.enums import CardKind, CardRank, Keyword
from card_duel_engine.domain.models import CardDefinition


def definition(card_id: str, name: str = "Nombre mecánico") -> CardDefinition:
    return CardDefinition(
        card_id=card_id,
        name=name,
        kind=CardKind.CREATURE,
        cost=3,
        rank=CardRank.LEGENDARY,
        base_strength=4,
        set_id="alpha",
        revision=2,
        keywords=frozenset({"flying", Keyword.CAN_CHALLENGE}),
        subtypes=frozenset({"warrior", "human"}),
    )


def presentation(card_id: str, name: str = "Nombre editorial") -> CardPresentation:
    return CardPresentation(card_id, f"token-{card_id}", name, "Texto", "art.png")


class PublicCardTests(unittest.TestCase):
    def test_from_sources_copies_safe_fields_and_serializes_json_values(self):
        card = PublicCard.from_sources(definition("a"), presentation("a"))

        self.assertEqual(card.mechanical_name, "Nombre mecánico")
        self.assertEqual(card.name, "Nombre editorial")
        self.assertEqual(card.kind, "creature")
        self.assertEqual(card.rank, "legendary")
        self.assertEqual(card.keywords, ("can_challenge", "flying"))
        self.assertEqual(card.subtypes, ("human", "warrior"))
        self.assertIsInstance(json.dumps(card.to_dict()), str)
        self.assertIsInstance(card.to_dict()["keywords"], list)

    def test_from_sources_rejects_different_ids(self):
        with self.assertRaisesRegex(ValueError, "mismo card_id"):
            PublicCard.from_sources(definition("a"), presentation("b"))

    def test_is_frozen(self):
        card = PublicCard.from_sources(definition("a"), presentation("a"))
        with self.assertRaises(FrozenInstanceError):
            card.name = "Cambio"  # type: ignore[misc]


class PublicCardCatalogTests(unittest.TestCase):
    def test_validates_full_correspondence_before_projection(self):
        mechanical = CardCatalog()
        mechanical.register(definition("a"))
        editorial = CardPresentationCatalog()
        with self.assertRaisesRegex(ValueError, "sin presentación: a"):
            PublicCardCatalog(mechanical, editorial)

    def test_sorts_cards_detaches_sources_and_serializes(self):
        mechanical = CardCatalog()
        editorial = CardPresentationCatalog()
        for card_id in ("b", "a"):
            mechanical.register(definition(card_id))
            editorial.register(presentation(card_id))

        catalog = PublicCardCatalog(mechanical, editorial)
        mechanical.register(definition("c"))
        editorial.register(presentation("c"))

        self.assertEqual(tuple(card.card_id for card in catalog.cards), ("a", "b"))
        self.assertIsInstance(catalog.cards, tuple)
        self.assertEqual([card["card_id"] for card in catalog.to_dict()["cards"]], ["a", "b"])  # type: ignore[index]
        self.assertIsInstance(json.dumps(catalog.to_dict()), str)
        with self.assertRaises(FrozenInstanceError):
            catalog.cards = ()  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
