import json
import unittest
from dataclasses import FrozenInstanceError

from card_duel_engine.catalog import CardCatalog
from card_duel_engine.domain.enums import CardKind, CardRank, Keyword
from card_duel_engine.domain.models import CardDefinition
from card_duel_engine.presentation import CardPresentation, CardPresentationCatalog
from card_duel_engine.public_catalog import PublicCard, PublicCardCatalog
from json_contract_helpers import assert_json_contract


MECHANICAL_FIELDS = (
    "mechanical_name",
    "kind",
    "cost",
    "rank",
    "base_strength",
    "set_id",
    "revision",
    "keywords",
    "subtypes",
)


def synthetic_definition(
    card_id: str = "card-distinctive", *, name: str = "Nombre mecánico inmutable"
) -> CardDefinition:
    """Crea una definición cuyos campos públicos son fáciles de distinguir."""
    return CardDefinition(
        card_id=card_id,
        name=name,
        kind=CardKind.CREATURE,
        cost=7,
        rank=CardRank.LEGENDARY,
        base_strength=11,
        set_id="set-mecanico-42",
        revision=9,
        keywords=frozenset({"custom_keyword", Keyword.CAN_CHALLENGE}),
        subtypes=frozenset({"dragon", "scholar"}),
    )


def synthetic_presentation(
    card_id: str = "card-distinctive",
    *,
    token: str = "token-editorial-v1",
    name: str = "Nombre editorial visible",
    rules_text: str = "Texto editorial, no ejecutable.",
    art: str = "art/editorial-v1.webp",
) -> CardPresentation:
    return CardPresentation(card_id, token, name, rules_text, art)


def projected_mechanics(card: PublicCard) -> tuple[object, ...]:
    return tuple(getattr(card, field) for field in MECHANICAL_FIELDS)


def build_catalog(card_ids: tuple[str, ...]) -> PublicCardCatalog:
    mechanical = CardCatalog()
    editorial = CardPresentationCatalog()
    for card_id in card_ids:
        mechanical.register(synthetic_definition(card_id, name=f"Mecánica {card_id}"))
        editorial.register(
            synthetic_presentation(
                card_id,
                token=f"token-{card_id}",
                name=f"Editorial {card_id}",
                rules_text=f"Reglas {card_id}",
                art=f"art/{card_id}.webp",
            )
        )
    return PublicCardCatalog(mechanical, editorial)


class PublicCardProjectionTests(unittest.TestCase):
    def test_projects_each_field_from_its_authoritative_source(self):
        definition = synthetic_definition()
        presentation = synthetic_presentation()

        card = PublicCard.from_sources(definition, presentation)

        self.assertEqual(card.mechanical_name, definition.name)
        self.assertEqual(card.kind, definition.kind.name.lower())
        self.assertEqual(card.cost, definition.cost)
        self.assertEqual(card.rank, definition.rank.name.lower())
        self.assertEqual(card.base_strength, definition.base_strength)
        self.assertEqual(card.set_id, definition.set_id)
        self.assertEqual(card.revision, definition.revision)
        self.assertEqual(card.keywords, ("can_challenge", "custom_keyword"))
        self.assertEqual(card.subtypes, ("dragon", "scholar"))
        self.assertEqual(card.token, presentation.token)
        self.assertEqual(card.name, presentation.name)
        self.assertEqual(card.rules_text, presentation.rules_text)
        self.assertEqual(card.art, presentation.art)

    def test_editorial_name_can_differ_without_mutating_definition(self):
        definition = synthetic_definition()
        original_definition = definition

        card = PublicCard.from_sources(
            definition, synthetic_presentation(name="Un título editorial diferente")
        )

        self.assertNotEqual(card.name, card.mechanical_name)
        self.assertEqual(card.name, "Un título editorial diferente")
        self.assertEqual(card.mechanical_name, "Nombre mecánico inmutable")
        self.assertIs(definition, original_definition)
        self.assertEqual(definition.name, "Nombre mecánico inmutable")

    def test_each_editorial_variant_preserves_all_projected_mechanics(self):
        definition = synthetic_definition()
        baseline = PublicCard.from_sources(definition, synthetic_presentation())
        variants = (
            synthetic_presentation(rules_text="Otro texto únicamente"),
            synthetic_presentation(art="art/otra-imagen.png"),
            synthetic_presentation(token="token-alternativo"),
        )

        for variant in variants:
            with self.subTest(variant=variant):
                projected = PublicCard.from_sources(definition, variant)
                self.assertEqual(
                    projected_mechanics(projected), projected_mechanics(baseline)
                )

    def test_rejects_sources_with_different_card_ids(self):
        with self.assertRaisesRegex(ValueError, "mismo card_id"):
            PublicCard.from_sources(
                synthetic_definition("mechanical-id"),
                synthetic_presentation("editorial-id"),
            )

    def test_to_dict_is_deeply_json_safe_and_contains_no_domain_objects(self):
        payload = PublicCard.from_sources(
            synthetic_definition(), synthetic_presentation()
        ).to_dict()

        assert_json_contract(
            self, payload, forbidden_types=(CardDefinition, CardPresentation)
        )
        self.assertIsInstance(json.dumps(payload), str)

    def test_public_card_is_frozen_and_serialized_collections_are_detached(self):
        card = PublicCard.from_sources(
            synthetic_definition(), synthetic_presentation()
        )
        payload = card.to_dict()
        payload["keywords"].append("mutación externa")  # type: ignore[union-attr]
        payload["subtypes"].clear()  # type: ignore[union-attr]

        self.assertEqual(card.keywords, ("can_challenge", "custom_keyword"))
        self.assertEqual(card.subtypes, ("dragon", "scholar"))
        with self.assertRaises(FrozenInstanceError):
            card.name = "Mutación"  # type: ignore[misc]


class PublicCardCatalogTests(unittest.TestCase):
    def test_opposite_registration_orders_produce_equal_payloads(self):
        ids = ("z-card", "a-card", "m-card")

        forward = build_catalog(ids)
        reverse = build_catalog(tuple(reversed(ids)))

        self.assertEqual(forward.to_dict(), reverse.to_dict())

    def test_card_id_is_the_final_ordering_criterion(self):
        catalog = build_catalog(("card-20", "card-03", "card-11", "card-01"))

        self.assertEqual(
            tuple(card.card_id for card in catalog.cards),
            ("card-01", "card-03", "card-11", "card-20"),
        )
        self.assertEqual(
            [item["card_id"] for item in catalog.to_dict()["cards"]],  # type: ignore[index]
            ["card-01", "card-03", "card-11", "card-20"],
        )

    def test_to_dict_is_deeply_json_safe(self):
        payload = build_catalog(("second", "first")).to_dict()

        assert_json_contract(
            self, payload, forbidden_types=(CardDefinition, CardPresentation)
        )
        self.assertIsInstance(json.dumps(payload), str)

    def test_returned_collections_cannot_mutate_catalog_state(self):
        catalog = build_catalog(("b", "a"))
        payload = catalog.to_dict()
        payload["cards"].reverse()  # type: ignore[union-attr]
        payload["cards"].clear()  # type: ignore[union-attr]

        self.assertEqual(tuple(card.card_id for card in catalog.cards), ("a", "b"))
        self.assertEqual(len(catalog.to_dict()["cards"]), 2)  # type: ignore[arg-type]
        self.assertIsInstance(catalog.cards, tuple)
        with self.assertRaises(FrozenInstanceError):
            catalog.cards = ()  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
