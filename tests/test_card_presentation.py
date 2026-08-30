"""Contrato de presentaciones usando exclusivamente cartas sintéticas."""

from dataclasses import FrozenInstanceError

import pytest

from card_duel_engine.catalog import CardCatalog
from card_duel_engine.domain.enums import CardKind
from card_duel_engine.domain.models import CardDefinition
from card_duel_engine.presentation import (
    CardPresentation,
    CardPresentationCatalog,
    CardPresentationSnapshot,
    validate_card_presentations,
)


def synthetic_definition(card_id: str) -> CardDefinition:
    """Crea una definición mínima sin depender de ninguna colección publicada."""
    return CardDefinition(
        card_id=card_id,
        name=f"Definición {card_id}",
        kind=CardKind.CREATURE,
        cost=1,
        base_strength=1,
        set_id="synthetic-presentations",
    )


def synthetic_presentation(card_id: str, token: str) -> CardPresentation:
    return CardPresentation(
        card_id=card_id,
        token=token,
        name=f"Presentación {card_id}",
        rules_text="Texto sintético",
        art="synthetic://art",
    )


def definition_catalog(*card_ids: str) -> CardCatalog:
    catalog = CardCatalog()
    for card_id in card_ids:
        catalog.register(synthetic_definition(card_id))
    return catalog


def presentation_catalog(*card_ids: str) -> CardPresentationCatalog:
    catalog = CardPresentationCatalog()
    for card_id in card_ids:
        catalog.register(synthetic_presentation(card_id, f"token-{card_id}"))
    return catalog


def test_registers_and_recovers_a_valid_presentation_by_card_id() -> None:
    catalog = CardPresentationCatalog()
    card = synthetic_presentation("synthetic-a", "token-a")

    catalog.register(card)

    assert catalog.get("synthetic-a") is card


def test_rejects_duplicate_card_id_even_when_token_changes() -> None:
    catalog = CardPresentationCatalog()
    catalog.register(synthetic_presentation("synthetic-a", "token-a"))

    with pytest.raises(ValueError, match=r"^card_id duplicado: synthetic-a$"):
        catalog.register(synthetic_presentation("synthetic-a", "token-other"))


def test_rejects_duplicate_token_even_when_card_id_changes() -> None:
    catalog = CardPresentationCatalog()
    catalog.register(synthetic_presentation("synthetic-a", "shared-token"))

    with pytest.raises(ValueError, match=r"^token duplicado: shared-token$"):
        catalog.register(synthetic_presentation("synthetic-b", "shared-token"))


@pytest.mark.parametrize("field", ["card_id", "token", "name"])
@pytest.mark.parametrize("invalid", ["", "  \t\n"])
def test_rejects_empty_or_whitespace_only_required_strings(
    field: str, invalid: str
) -> None:
    values = {
        "card_id": "synthetic-a",
        "token": "token-a",
        "name": "Nombre",
        "rules_text": "",
        "art": "",
    }
    values[field] = invalid

    with pytest.raises(ValueError, match=rf"^{field} no puede estar vacío$"):
        CardPresentation(**values)


@pytest.mark.parametrize(
    ("field", "invalid"),
    [
        ("card_id", 1),
        ("token", None),
        ("name", ["Nombre"]),
        ("rules_text", {"texto": "inválido"}),
        ("art", b"arte"),
    ],
)
def test_rejects_structurally_invalid_field_types(field: str, invalid: object) -> None:
    values: dict[str, object] = {
        "card_id": "synthetic-a",
        "token": "token-a",
        "name": "Nombre",
        "rules_text": "",
        "art": "",
    }
    values[field] = invalid

    with pytest.raises(ValueError, match=rf"^{field} debe ser una cadena$"):
        CardPresentation(**values)  # type: ignore[arg-type]


def test_catalog_rejects_structurally_invalid_entries() -> None:
    with pytest.raises(ValueError, match="solo admite CardPresentation"):
        CardPresentationCatalog().register(object())  # type: ignore[arg-type]


def test_card_presentation_is_frozen() -> None:
    card = synthetic_presentation("synthetic-a", "token-a")

    with pytest.raises(FrozenInstanceError):
        card.name = "Nombre modificado"  # type: ignore[misc]


def test_snapshot_does_not_change_after_later_catalog_registrations() -> None:
    catalog = presentation_catalog("synthetic-b")
    snapshot = catalog.snapshot()

    catalog.register(synthetic_presentation("synthetic-a", "token-a"))

    assert [card.card_id for card in snapshot.presentations()] == ["synthetic-b"]
    assert [card.card_id for card in catalog.presentations()] == [
        "synthetic-a",
        "synthetic-b",
    ]


def test_snapshot_internal_mapping_cannot_be_modified() -> None:
    snapshot = presentation_catalog("synthetic-a").snapshot()

    with pytest.raises(TypeError):
        snapshot._cards["synthetic-b"] = synthetic_presentation(  # type: ignore[index]
            "synthetic-b", "token-b"
        )


def test_presentations_have_stable_card_id_order() -> None:
    catalog = CardPresentationCatalog()
    for card_id in ("synthetic-c", "synthetic-a", "synthetic-b"):
        catalog.register(synthetic_presentation(card_id, f"token-{card_id}"))

    expected = ["synthetic-a", "synthetic-b", "synthetic-c"]
    assert [card.card_id for card in catalog.presentations()] == expected
    assert [card.card_id for card in catalog.presentations()] == expected
    assert [card.card_id for card in catalog.snapshot().presentations()] == expected


def test_orphan_presentation_has_clear_deterministic_diagnostic() -> None:
    mechanical = definition_catalog("shared")
    editorial = presentation_catalog("orphan-z", "shared", "orphan-a")

    with pytest.raises(ValueError) as error:
        validate_card_presentations(mechanical, editorial)

    assert str(error.value) == "Presentaciones huérfanas: orphan-a, orphan-z"


def test_definition_without_presentation_has_clear_deterministic_diagnostic() -> None:
    mechanical = definition_catalog("missing-z", "shared", "missing-a")
    editorial = presentation_catalog("shared")

    with pytest.raises(ValueError) as error:
        validate_card_presentations(mechanical, editorial)

    assert str(error.value) == (
        "Definiciones mecánicas sin presentación: missing-a, missing-z"
    )


def test_reports_both_mismatch_types_simultaneously() -> None:
    mechanical = definition_catalog("missing-z", "shared", "missing-a")
    editorial = presentation_catalog("orphan-z", "shared", "orphan-a")

    with pytest.raises(ValueError) as error:
        validate_card_presentations(mechanical, editorial)

    assert str(error.value) == (
        "Presentaciones huérfanas: orphan-a, orphan-z; "
        "Definiciones mecánicas sin presentación: missing-a, missing-z"
    )


def test_complete_synthetic_catalogs_validate() -> None:
    mechanical = definition_catalog("synthetic-b", "synthetic-a")
    editorial = presentation_catalog("synthetic-a", "synthetic-b")

    assert validate_card_presentations(mechanical, editorial) is None


def test_direct_snapshot_construction_cannot_bypass_token_uniqueness() -> None:
    cards = {
        "synthetic-a": synthetic_presentation("synthetic-a", "shared-token"),
        "synthetic-b": synthetic_presentation("synthetic-b", "shared-token"),
    }

    with pytest.raises(ValueError, match=r"^token duplicado: shared-token$"):
        CardPresentationSnapshot(cards)
