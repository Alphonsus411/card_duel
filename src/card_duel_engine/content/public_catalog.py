"""Proyección pública desacoplada de mecánicas y presentación."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from ..catalog import CardCatalogReader
from ..domain.models import CardDefinition
from .presentation import CardPresentation, CardPresentationSnapshot


@dataclass(frozen=True)
class PublicCard:
    """Datos públicos de una carta, sin referencias a objetos del motor."""

    card_id: str
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
    art: str | None

    @classmethod
    def from_sources(
        cls,
        definition: CardDefinition,
        presentation: CardPresentation,
    ) -> PublicCard:
        """Copia valores escalares; el nombre mecánico se ignora expresamente."""

        if definition.card_id != presentation.card_id:
            raise ValueError("La definición y la presentación no corresponden")
        return cls(
            card_id=definition.card_id,
            kind=definition.kind.name,
            cost=definition.cost,
            rank=definition.rank.name,
            base_strength=definition.base_strength,
            set_id=definition.set_id,
            revision=definition.revision,
            keywords=tuple(sorted(definition.keywords)),
            subtypes=tuple(sorted(definition.subtypes)),
            token=presentation.token,
            name=presentation.name,
            rules_text=presentation.rules_text,
            art=presentation.art,
        )

    def to_dict(self) -> dict[str, Any]:
        """Devuelve un árbol JSON-safe nuevo en cada llamada."""

        return {
            "card_id": self.card_id,
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


class PublicCardCatalog:
    """Snapshot público inmutable, indexado y ordenado por ``card_id``."""

    def __init__(self, cards: Mapping[str, PublicCard]) -> None:
        self._cards = MappingProxyType(dict(cards))
        self._ordered = tuple(self._cards[key] for key in sorted(self._cards))

    @classmethod
    def build(
        cls,
        catalog: CardCatalogReader,
        presentations: CardPresentationSnapshot,
        *,
        complete: bool = False,
    ) -> PublicCardCatalog:
        """Proyecta presentaciones válidas y, opcionalmente, exige cobertura total."""

        definitions = {item.card_id: item for item in catalog.definitions()}
        presentation_items = presentations.presentations()
        presentation_ids = {item.card_id for item in presentation_items}

        unknown = presentation_ids - definitions.keys()
        if unknown:
            identifiers = ", ".join(sorted(unknown))
            raise ValueError(f"Presentación sin definición mecánica: {identifiers}")

        if complete:
            missing = definitions.keys() - presentation_ids
            if missing:
                identifiers = ", ".join(sorted(missing))
                raise ValueError(f"Definición mecánica sin presentación: {identifiers}")

        cards = {
            presentation.card_id: PublicCard.from_sources(
                definitions[presentation.card_id], presentation
            )
            for presentation in presentation_items
        }
        return cls(cards)

    @classmethod
    def build_complete(
        cls,
        catalog: CardCatalogReader,
        presentations: CardPresentationSnapshot,
    ) -> PublicCardCatalog:
        """Proyecta exigiendo igualdad entre ambos conjuntos de identificadores."""

        return cls.build(catalog, presentations, complete=True)

    def get(self, card_id: str) -> PublicCard:
        try:
            return self._cards[card_id]
        except KeyError as exc:
            raise KeyError(f"Carta pública desconocida: {card_id}") from exc

    def cards(self) -> tuple[PublicCard, ...]:
        return self._ordered

    def to_dict(self) -> dict[str, list[dict[str, Any]]]:
        """Crea una estructura JSON-safe independiente del snapshot."""

        return {"cards": [card.to_dict() for card in self._ordered]}

    def __iter__(self) -> Iterator[PublicCard]:
        return iter(self._ordered)

    def __contains__(self, card_id: object) -> bool:
        return card_id in self._cards

    def __len__(self) -> int:
        return len(self._cards)
