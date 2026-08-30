"""Datos editoriales de cartas, independientes de las reglas del motor.

Una presentación puede carecer de texto de reglas o de arte; por ello esos dos
campos admiten la cadena vacía. Los identificadores y tokens se conservan
exactamente como se reciben: este módulo nunca los normaliza silenciosamente.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping, Protocol

from .catalog import CardCatalogReader


@dataclass(frozen=True)
class CardPresentation:
    """Representación editorial, sin ninguna dependencia del motor de juego."""

    card_id: str
    token: str
    name: str
    rules_text: str
    art: str

    def __post_init__(self) -> None:
        for field_name in ("card_id", "token", "name", "rules_text", "art"):
            if not isinstance(getattr(self, field_name), str):
                raise ValueError(f"{field_name} debe ser una cadena")

        for field_name in ("card_id", "token", "name"):
            if not getattr(self, field_name).strip():
                raise ValueError(f"{field_name} no puede estar vacío")


class CardPresentationCatalogReader(Protocol):
    """Contrato de lectura común al registro y a sus fotografías."""

    def get(self, card_id: str) -> CardPresentation: ...
    def presentations(self) -> tuple[CardPresentation, ...]: ...
    def __contains__(self, card_id: str) -> bool: ...
    def __len__(self) -> int: ...


def validate_card_presentations(
    card_catalog: CardCatalogReader,
    presentation_catalog: CardPresentationCatalogReader,
) -> None:
    """Comprueba la correspondencia por ``card_id`` y retorna ``None`` si es total.

    Las diferencias se comunican mediante ``ValueError`` y se separan por tipo.
    Los metadatos editoriales no participan en esta validación.
    """
    mechanical_ids = {definition.card_id for definition in card_catalog.definitions()}
    presentation_ids = {
        presentation.card_id for presentation in presentation_catalog.presentations()
    }

    errors: list[str] = []
    orphan_presentations = sorted(presentation_ids - mechanical_ids)
    if orphan_presentations:
        errors.append(
            "Presentaciones huérfanas: " + ", ".join(orphan_presentations)
        )

    missing_presentations = sorted(mechanical_ids - presentation_ids)
    if missing_presentations:
        errors.append(
            "Definiciones mecánicas sin presentación: "
            + ", ".join(missing_presentations)
        )

    if errors:
        raise ValueError("; ".join(errors))


@dataclass(frozen=True)
class CardPresentationSnapshot:
    """Copia inmutable y validada de las presentaciones de un catálogo."""

    _cards: Mapping[str, CardPresentation]
    _tokens: Mapping[str, str] = field(init=False, repr=False)

    def __init__(self, cards: Mapping[str, CardPresentation]) -> None:
        copied_cards: dict[str, CardPresentation] = {}
        copied_tokens: dict[str, str] = {}
        for key, presentation in cards.items():
            if not isinstance(presentation, CardPresentation):
                raise ValueError("El snapshot solo admite CardPresentation")
            if key != presentation.card_id:
                raise ValueError(
                    "La clave del snapshot debe coincidir con card_id: "
                    f"{key!r} != {presentation.card_id!r}"
                )
            if presentation.card_id in copied_cards:
                raise ValueError(f"card_id duplicado: {presentation.card_id}")
            if presentation.token in copied_tokens:
                raise ValueError(f"token duplicado: {presentation.token}")
            copied_cards[presentation.card_id] = presentation
            copied_tokens[presentation.token] = presentation.card_id

        object.__setattr__(self, "_cards", MappingProxyType(copied_cards))
        object.__setattr__(self, "_tokens", MappingProxyType(copied_tokens))

    def get(self, card_id: str) -> CardPresentation:
        try:
            return self._cards[card_id]
        except KeyError as exc:
            raise KeyError(f"Presentación desconocida: {card_id}") from exc

    def presentations(self) -> tuple[CardPresentation, ...]:
        return tuple(self._cards[card_id] for card_id in sorted(self._cards))

    def __contains__(self, card_id: str) -> bool:
        return card_id in self._cards

    def __len__(self) -> int:
        return len(self._cards)


@dataclass
class CardPresentationCatalog:
    """Registro mutable de datos editoriales, inicialmente vacío."""

    _cards: dict[str, CardPresentation] = field(default_factory=dict, init=False)
    _tokens: dict[str, str] = field(default_factory=dict, init=False, repr=False)

    def register(self, presentation: CardPresentation) -> None:
        """Registra una presentación sin reemplazar entradas existentes."""
        if not isinstance(presentation, CardPresentation):
            raise ValueError("El catálogo solo admite CardPresentation")
        if presentation.card_id in self._cards:
            raise ValueError(f"card_id duplicado: {presentation.card_id}")
        if presentation.token in self._tokens:
            raise ValueError(f"token duplicado: {presentation.token}")
        self._cards[presentation.card_id] = presentation
        self._tokens[presentation.token] = presentation.card_id

    def get(self, card_id: str) -> CardPresentation:
        try:
            return self._cards[card_id]
        except KeyError as exc:
            raise KeyError(f"Presentación desconocida: {card_id}") from exc

    def presentations(self) -> tuple[CardPresentation, ...]:
        return tuple(self._cards[card_id] for card_id in sorted(self._cards))

    def __contains__(self, card_id: str) -> bool:
        return card_id in self._cards

    def __len__(self) -> int:
        return len(self._cards)

    def snapshot(self) -> CardPresentationSnapshot:
        """Obtiene una copia de solo lectura del estado actual."""
        return CardPresentationSnapshot(self._cards)
