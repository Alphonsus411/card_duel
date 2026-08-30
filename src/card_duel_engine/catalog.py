"""Catálogo desacoplado para futuras colecciones."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping, Protocol

from .domain.models import CardDefinition


class CardCatalogReader(Protocol):
    """Lectura mecánica mínima requerida por consumidores desacoplados."""

    def get(self, card_id: str) -> CardDefinition: ...

    def definitions(self) -> tuple[CardDefinition, ...]: ...


class CardCatalogSnapshot:
    """Copia inmutable del conjunto de definiciones mecánicas."""

    def __init__(self, definitions: Mapping[str, CardDefinition]) -> None:
        self._cards = MappingProxyType(dict(definitions))

    def get(self, card_id: str) -> CardDefinition:
        try:
            return self._cards[card_id]
        except KeyError as exc:
            raise KeyError(f"Carta desconocida: {card_id}") from exc

    def definitions(self) -> tuple[CardDefinition, ...]:
        return tuple(self._cards[key] for key in sorted(self._cards))

    def __contains__(self, card_id: object) -> bool:
        return card_id in self._cards

    def __len__(self) -> int:
        return len(self._cards)


@dataclass
class CardCatalog:
    """Registro de definiciones; comienza vacío en producción."""

    _cards: dict[str, CardDefinition] = field(default_factory=dict)

    def register(self, card: CardDefinition) -> None:
        if card.card_id in self._cards:
            raise ValueError(f"Definición duplicada: {card.card_id}")
        self._cards[card.card_id] = card

    def get(self, card_id: str) -> CardDefinition:
        try:
            return self._cards[card_id]
        except KeyError as exc:
            raise KeyError(f"Carta desconocida: {card_id}") from exc

    def definitions(self) -> tuple[CardDefinition, ...]:
        return tuple(self._cards.values())

    def snapshot(self) -> CardCatalogSnapshot:
        """Congela el estado mecánico actual sin incorporar presentación."""

        return CardCatalogSnapshot(self._cards)

    def __contains__(self, card_id: str) -> bool:
        return card_id in self._cards

    def __len__(self) -> int:
        return len(self._cards)
