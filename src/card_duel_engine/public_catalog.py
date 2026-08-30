"""Proyección pública de los catálogos mecánico y editorial."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypeAlias

from .catalog import CardCatalogReader
from .domain.models import CardDefinition
from .presentation import (
    CardPresentation,
    CardPresentationCatalogReader,
    validate_card_presentations,
)

JsonValue: TypeAlias = str | int | None | list["JsonValue"] | dict[str, "JsonValue"]


def _enum_string(value: Enum) -> str:
    """Devuelve la representación pública estable de un enum mecánico."""
    return value.name.lower()


@dataclass(frozen=True)
class PublicCard:
    """Datos seguros y autocontenidos que pueden entregarse a un cliente."""

    card_id: str
    mechanical_name: str
    kind: str
    cost: int
    rank: str
    base_strength: int | None
    set_id: str
    revision: int
    keywords: tuple[str, ...]
    subtypes: tuple[str, ...]
    token: str
    name: str
    rules_text: str
    art: str

    @classmethod
    def from_sources(
        cls, definition: CardDefinition, presentation: CardPresentation
    ) -> PublicCard:
        """Copia los campos públicos de dos fuentes correspondientes."""
        if definition.card_id != presentation.card_id:
            raise ValueError(
                "definition y presentation deben tener el mismo card_id: "
                f"{definition.card_id!r} != {presentation.card_id!r}"
            )

        keywords = tuple(
            sorted(
                _enum_string(keyword) if isinstance(keyword, Enum) else keyword
                for keyword in definition.keywords
            )
        )
        return cls(
            card_id=definition.card_id,
            mechanical_name=definition.name,
            kind=_enum_string(definition.kind),
            cost=definition.cost,
            rank=_enum_string(definition.rank),
            base_strength=definition.base_strength,
            set_id=definition.set_id,
            revision=definition.revision,
            keywords=keywords,
            subtypes=tuple(sorted(definition.subtypes)),
            token=presentation.token,
            name=presentation.name,
            rules_text=presentation.rules_text,
            art=presentation.art,
        )

    def to_dict(self) -> dict[str, JsonValue]:
        """Serializa la carta usando exclusivamente tipos compatibles con JSON."""
        return {
            "card_id": self.card_id,
            "mechanical_name": self.mechanical_name,
            "kind": self.kind,
            "cost": self.cost,
            "rank": self.rank,
            "base_strength": self.base_strength,
            "set_id": self.set_id,
            "revision": self.revision,
            "keywords": list(self.keywords),
            "subtypes": list(self.subtypes),
            "token": self.token,
            "name": self.name,
            "rules_text": self.rules_text,
            "art": self.art,
        }


@dataclass(frozen=True, init=False)
class PublicCardCatalog:
    """Instantánea pública inmutable, sin referencias a sus catálogos fuente."""

    cards: tuple[PublicCard, ...]

    def __init__(
        self,
        card_catalog: CardCatalogReader,
        presentation_catalog: CardPresentationCatalogReader,
    ) -> None:
        validate_card_presentations(card_catalog, presentation_catalog)
        presentations = {
            presentation.card_id: presentation
            for presentation in presentation_catalog.presentations()
        }
        cards = tuple(
            PublicCard.from_sources(definition, presentations[definition.card_id])
            for definition in sorted(
                card_catalog.definitions(), key=lambda definition: definition.card_id
            )
        )
        object.__setattr__(self, "cards", cards)

    def to_dict(self) -> dict[str, JsonValue]:
        """Serializa todo el catálogo como una lista de cartas JSON-safe."""
        return {"cards": [card.to_dict() for card in self.cards]}
