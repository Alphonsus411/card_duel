import json
import unittest

from card_duel_engine import (
    CardCatalog,
    CardPresentation,
    CardPresentationCatalog,
    PublicCardCatalog,
)
from card_duel_engine.domain.enums import CardKind, CardRank
from card_duel_engine.domain.models import CardDefinition


def definition(card_id: str, *, historical_name: str = "Nombre antiguo") -> CardDefinition:
    return CardDefinition(
        card_id=card_id,
        name=historical_name,
        kind=CardKind.CREATURE,
        cost=3,
        rank=CardRank.LEGENDARY,
        base_strength=4,
        set_id="alpha",
        revision=2,
        keywords=frozenset({"volar", "aura"}),
        subtypes=frozenset({"mago", "humano"}),
    )


def presentation(card_id: str, *, name: str = "Nombre editorial") -> CardPresentation:
    return CardPresentation(card_id, "token-x", name, "Texto libre", "art.png")


class PublicCardCatalogTests(unittest.TestCase):
    def test_projects_only_public_copied_values_in_stable_order(self):
        mechanics = CardCatalog()
        mechanics.register(definition("b"))
        mechanics.register(definition("a"))
        presentations = CardPresentationCatalog(
            (presentation("b"), presentation("a"))
        )

        projected = PublicCardCatalog.build_complete(
            mechanics.snapshot(), presentations.snapshot()
        )
        card = projected.get("a")

        self.assertEqual(tuple(item.card_id for item in projected), ("a", "b"))
        self.assertEqual(card.name, "Nombre editorial")
        self.assertEqual(card.kind, "CREATURE")
        self.assertEqual(card.rank, "LEGENDARY")
        self.assertEqual(card.keywords, ("aura", "volar"))
        self.assertEqual(card.subtypes, ("humano", "mago"))
        payload = card.to_dict()
        self.assertEqual(payload["keywords"], ["aura", "volar"])
        self.assertEqual(
            set(payload),
            {
                "card_id", "kind", "cost", "rank", "base_strength", "set_id",
                "revision", "keywords", "subtypes", "token", "name",
                "rules_text", "art",
            },
        )
        json.dumps(projected.to_dict())

    def test_rejects_orphans_on_either_side_as_required(self):
        mechanics = CardCatalog()
        mechanics.register(definition("mechanical"))

        with self.assertRaisesRegex(ValueError, "sin definición"):
            PublicCardCatalog.build(
                mechanics, CardPresentationCatalog((presentation("editorial"),)).snapshot()
            )

        with self.assertRaisesRegex(ValueError, "sin presentación"):
            PublicCardCatalog.build_complete(
                mechanics, CardPresentationCatalog().snapshot()
            )

    def test_projection_isolated_from_sources_and_serialized_results(self):
        mechanics = CardCatalog()
        mechanics.register(definition("a"))
        presentations = CardPresentationCatalog((presentation("a"),))
        projected = PublicCardCatalog.build(mechanics, presentations.snapshot())

        mechanics.register(definition("b"))
        presentations.register(presentation("b"))
        first_payload = projected.to_dict()
        first_payload["cards"][0]["keywords"].append("mutación")

        self.assertEqual(len(projected), 1)
        self.assertNotIn("b", projected)
        self.assertEqual(projected.get("a").keywords, ("aura", "volar"))
        self.assertNotEqual(projected.to_dict(), first_payload)


if __name__ == "__main__":
    unittest.main()
