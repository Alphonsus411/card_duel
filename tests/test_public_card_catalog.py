import json
import unittest
from collections.abc import Mapping
from dataclasses import fields, is_dataclass

from card_duel_engine import (
    CardCatalog,
    CardPresentation,
    CardPresentationCatalog,
    PublicCardCatalog,
)
from card_duel_engine.domain.models import (
    AbilityDefinition,
    CardDefinition,
    EffectDefinition,
    GameState,
)
from card_duel_engine.engine.commands import GameCommand
from card_duel_engine.engine.game import GameEngine

from fixtures import public_card_fixture


def presentation(
    card_id: str,
    *,
    token: str = "token-editorial",
    name: str = "Nombre editorial",
    rules_text: str = "Texto editorial opaco",
    art: str | None = "arte/editorial.png",
) -> CardPresentation:
    return CardPresentation(card_id, token, name, rules_text, art)


def catalog_with(*definitions: CardDefinition) -> CardCatalog:
    catalog = CardCatalog()
    for definition in definitions:
        catalog.register(definition)
    return catalog


def assert_json_tree(test: unittest.TestCase, value: object) -> None:
    """Comprueba recursivamente el subconjunto de tipos aceptado por JSON."""

    if value is None or type(value) in (str, int, float, bool):
        return
    if isinstance(value, list):
        for item in value:
            assert_json_tree(test, item)
        return
    test.assertIsInstance(value, dict)
    for key, item in value.items():
        test.assertIs(type(key), str)
        assert_json_tree(test, item)


def walk_dto(value: object):
    """Recorre DTO, dataclasses y contenedores sin entrar en valores escalares."""

    yield value
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            yield from walk_dto(getattr(value, field.name))
    elif isinstance(value, Mapping):
        for key, item in value.items():
            yield from walk_dto(key)
            yield from walk_dto(item)
    elif isinstance(value, (tuple, list, set, frozenset)):
        for item in value:
            yield from walk_dto(item)


class PublicCardCatalogTests(unittest.TestCase):
    def test_links_presentation_to_fixture_definition(self):
        definition = public_card_fixture("linked")
        projected = PublicCardCatalog.build_complete(
            catalog_with(definition).snapshot(),
            CardPresentationCatalog((presentation("linked"),)).snapshot(),
        )

        self.assertEqual(projected.get("linked").card_id, definition.card_id)

    def test_rejects_orphan_presentation_explicitly(self):
        with self.assertRaisesRegex(ValueError, "Presentación sin definición mecánica: orphan"):
            PublicCardCatalog.build(
                catalog_with().snapshot(),
                CardPresentationCatalog((presentation("orphan"),)).snapshot(),
            )

    def test_rejects_duplicate_presentations(self):
        with self.assertRaisesRegex(ValueError, "Presentación duplicada: duplicate"):
            CardPresentationCatalog(
                (presentation("duplicate"), presentation("duplicate", name="Alternativa"))
            )

    def test_complete_projection_requires_every_presentation(self):
        mechanics = catalog_with(public_card_fixture("present"), public_card_fixture("missing"))

        with self.assertRaisesRegex(ValueError, "sin presentación: missing"):
            PublicCardCatalog.build_complete(
                mechanics.snapshot(),
                CardPresentationCatalog((presentation("present"),)).snapshot(),
            )

    def test_copies_every_mechanical_value_from_definition(self):
        definition = public_card_fixture("mechanics")
        card = PublicCardCatalog.build_complete(
            catalog_with(definition).snapshot(),
            CardPresentationCatalog((presentation("mechanics"),)).snapshot(),
        ).get("mechanics")

        self.assertEqual(
            (
                card.kind,
                card.cost,
                card.rank,
                card.base_strength,
                card.set_id,
                card.revision,
                card.keywords,
                card.subtypes,
            ),
            (
                definition.kind.name,
                definition.cost,
                definition.rank.name,
                definition.base_strength,
                definition.set_id,
                definition.revision,
                ("alfa", "zeta"),
                ("arcano", "sabio"),
            ),
        )

    def test_editorial_values_come_only_from_presentation(self):
        definition = public_card_fixture("editorial")
        metadata = presentation(
            "editorial",
            token="token-presentado",
            name="Nombre presentado distinto",
            rules_text="Reglas presentadas",
            art="arte-presentado.webp",
        )
        card = PublicCardCatalog.build_complete(
            catalog_with(definition).snapshot(),
            CardPresentationCatalog((metadata,)).snapshot(),
        ).get("editorial")

        self.assertNotEqual(definition.name, metadata.name)
        self.assertEqual(
            (card.token, card.name, card.rules_text, card.art),
            (metadata.token, metadata.name, metadata.rules_text, metadata.art),
        )
        self.assertNotEqual(card.name, definition.name)

    def test_alternative_presentations_never_change_mechanics(self):
        definition = public_card_fixture("alternative")
        mechanics = catalog_with(definition).snapshot()
        first = PublicCardCatalog.build_complete(
            mechanics,
            CardPresentationCatalog((presentation("alternative"),)).snapshot(),
        ).get("alternative")
        second = PublicCardCatalog.build_complete(
            mechanics,
            CardPresentationCatalog((presentation(
                "alternative", token="otro", name="Otro", rules_text="Otro texto", art=None
            ),)).snapshot(),
        ).get("alternative")

        mechanical_fields = (
            "card_id", "kind", "cost", "rank", "base_strength", "set_id",
            "revision", "keywords", "subtypes",
        )
        self.assertEqual(
            tuple(getattr(first, field) for field in mechanical_fields),
            tuple(getattr(second, field) for field in mechanical_fields),
        )
        self.assertNotEqual(first, second)

    def test_catalog_and_serialization_are_sorted_by_card_id(self):
        mechanics = catalog_with(public_card_fixture("z-card"), public_card_fixture("a-card"))
        metadata = CardPresentationCatalog((presentation("z-card"), presentation("a-card")))
        projected = PublicCardCatalog.build_complete(mechanics.snapshot(), metadata.snapshot())

        self.assertEqual(tuple(card.card_id for card in projected), ("a-card", "z-card"))
        self.assertEqual(
            [card["card_id"] for card in projected.to_dict()["cards"]],
            ["a-card", "z-card"],
        )

    def test_to_dict_contains_only_json_tree_types(self):
        projected = PublicCardCatalog.build_complete(
            catalog_with(public_card_fixture()).snapshot(),
            CardPresentationCatalog((presentation("TEST-PUBLIC-CARD"),)).snapshot(),
        )

        assert_json_tree(self, projected.to_dict())

    def test_keywords_and_subtypes_serialize_sorted(self):
        card = PublicCardCatalog.build_complete(
            catalog_with(public_card_fixture("ordered")).snapshot(),
            CardPresentationCatalog((presentation("ordered"),)).snapshot(),
        ).get("ordered")

        self.assertEqual(card.to_dict()["keywords"], ["alfa", "zeta"])
        self.assertEqual(card.to_dict()["subtypes"], ["arcano", "sabio"])

    def test_dtos_do_not_retain_engine_or_domain_definitions(self):
        projected = PublicCardCatalog.build_complete(
            catalog_with(public_card_fixture()).snapshot(),
            CardPresentationCatalog((presentation("TEST-PUBLIC-CARD"),)).snapshot(),
        )
        forbidden = (
            CardDefinition, AbilityDefinition, EffectDefinition, GameEngine, GameState, GameCommand
        )

        for value in walk_dto(projected.cards()):
            self.assertNotIsInstance(value, forbidden)

    def test_projection_isolated_from_mutable_source_catalogs(self):
        mechanics = catalog_with(public_card_fixture("stable"))
        metadata = CardPresentationCatalog((presentation("stable"),))
        projected = PublicCardCatalog.build_complete(mechanics, metadata.snapshot())
        before = projected.to_dict()

        mechanics.register(public_card_fixture("late"))
        metadata.register(presentation("late"))

        self.assertEqual(projected.to_dict(), before)
        self.assertNotIn("late", projected)

    def test_equivalent_inputs_have_identical_canonical_json(self):
        first = PublicCardCatalog.build_complete(
            catalog_with(public_card_fixture("b"), public_card_fixture("a")).snapshot(),
            CardPresentationCatalog((presentation("a"), presentation("b"))).snapshot(),
        )
        second = PublicCardCatalog.build_complete(
            catalog_with(public_card_fixture("a"), public_card_fixture("b")).snapshot(),
            CardPresentationCatalog((presentation("b"), presentation("a"))).snapshot(),
        )

        self.assertEqual(
            json.dumps(first.to_dict(), sort_keys=True),
            json.dumps(second.to_dict(), sort_keys=True),
        )

    def test_rejects_invalid_and_executable_editorial_fields(self):
        valid = {
            "card_id": "valid-id",
            "token": "valid-token",
            "name": "Valid name",
            "rules_text": "Valid text",
            "art": "valid.png",
        }
        invalid_values = (7, object(), lambda: "ejecutable")

        for field_name in valid:
            for invalid in invalid_values:
                values = valid | {field_name: invalid}
                with self.subTest(field=field_name, invalid=type(invalid).__name__):
                    with self.assertRaisesRegex(TypeError, field_name):
                        CardPresentation(**values)


if __name__ == "__main__":
    unittest.main()
