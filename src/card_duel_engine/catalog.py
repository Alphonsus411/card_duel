"""Catálogo desacoplado para futuras colecciones."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping, Protocol

from .domain.errors import InvalidDeckDefinition
from .domain.models import CardDefinition


class CardCatalogReader(Protocol):
    """Interfaz mínima de consulta compartida por catálogos y fotografías."""

    def get(self, card_id: str) -> CardDefinition: ...
    def definitions(self) -> tuple[CardDefinition, ...]: ...
    def __contains__(self, card_id: str) -> bool: ...
    def __len__(self) -> int: ...


@dataclass(frozen=True)
class CardCatalogSnapshot:
    """Fotografía inmutable de un catálogo, sin operaciones de escritura."""

    _cards: Mapping[str, CardDefinition]

    def __init__(self, cards: Mapping[str, CardDefinition]) -> None:
        object.__setattr__(self, "_cards", MappingProxyType(dict(cards)))

    def get(self, card_id: str) -> CardDefinition:
        try:
            return self._cards[card_id]
        except KeyError as exc:
            raise KeyError(f"Carta desconocida: {card_id}") from exc

    def definitions(self) -> tuple[CardDefinition, ...]:
        return tuple(self._cards.values())

    def __contains__(self, card_id: str) -> bool:
        return card_id in self._cards

    def __len__(self) -> int:
        return len(self._cards)


@dataclass
class CardCatalog:
    """Registro de definiciones; comienza vacío en producción."""

    _cards: dict[str, CardDefinition] = field(default_factory=dict)

    def register(self, card: CardDefinition) -> None:
        if card.card_id in self._cards:
            raise InvalidDeckDefinition(f"Definición duplicada: {card.card_id}")
        self._cards[card.card_id] = card

    def get(self, card_id: str) -> CardDefinition:
        try:
            return self._cards[card_id]
        except KeyError as exc:
            raise KeyError(f"Carta desconocida: {card_id}") from exc

    def definitions(self) -> tuple[CardDefinition, ...]:
        return tuple(self._cards.values())

    def __contains__(self, card_id: str) -> bool:
        return card_id in self._cards

    def __len__(self) -> int:
        return len(self._cards)

    def snapshot(self) -> CardCatalogSnapshot:
        """Copia el contenido actual en una fotografía de solo lectura."""
        return CardCatalogSnapshot(self._cards)
