"""Metadatos editoriales de cartas, separados de las reglas del motor.

``rules_text`` es deliberadamente un texto opaco: este módulo sólo lo almacena
y nunca intenta interpretarlo, analizarlo ni ejecutarlo.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


def _require_text(value: object, field_name: str, *, non_empty: bool) -> None:
    """Exige una cadena concreta y excluye subtipos potencialmente ejecutables."""

    if callable(value) or type(value) is not str:
        raise TypeError(f"{field_name} debe ser una cadena")
    if non_empty and not value:
        raise ValueError(f"{field_name} no puede estar vacío")


@dataclass(frozen=True)
class CardPresentation:
    """Contenido de presentación sin significado para las reglas de juego."""

    card_id: str
    token: str
    name: str
    rules_text: str
    art: str | None

    def __post_init__(self) -> None:
        _require_text(self.card_id, "card_id", non_empty=True)
        _require_text(self.token, "token", non_empty=True)
        _require_text(self.name, "name", non_empty=True)
        _require_text(self.rules_text, "rules_text", non_empty=False)
        if callable(self.art) or (self.art is not None and type(self.art) is not str):
            raise TypeError("art debe ser una cadena o None")


class CardPresentationSnapshot:
    """Copia inmutable de las presentaciones registradas."""

    def __init__(self, presentations: Mapping[str, CardPresentation]) -> None:
        # La copia evita que cambios posteriores en el registro afecten al snapshot.
        self._presentations = MappingProxyType(dict(presentations))

    def get(self, card_id: str) -> CardPresentation:
        """Consulta una presentación por el identificador autoritativo de carta."""

        try:
            return self._presentations[card_id]
        except KeyError as exc:
            raise KeyError(f"Presentación desconocida: {card_id}") from exc

    def presentations(self) -> tuple[CardPresentation, ...]:
        """Devuelve las presentaciones ordenadas de forma estable por ``card_id``."""

        return tuple(self._presentations[key] for key in sorted(self._presentations))

    def __iter__(self) -> Iterator[CardPresentation]:
        return iter(self.presentations())

    def __contains__(self, card_id: object) -> bool:
        return card_id in self._presentations

    def __len__(self) -> int:
        return len(self._presentations)


class CardPresentationCatalog:
    """Constructor mutable que registra presentaciones antes de congelarlas."""

    def __init__(self, presentations: Iterable[CardPresentation] = ()) -> None:
        self._presentations: dict[str, CardPresentation] = {}
        for presentation in presentations:
            self.register(presentation)

    def register(self, presentation: CardPresentation) -> None:
        """Registra una presentación y rechaza identificadores repetidos."""

        if not isinstance(presentation, CardPresentation):
            raise TypeError("Sólo se pueden registrar presentaciones de carta")
        if presentation.card_id in self._presentations:
            raise ValueError(f"Presentación duplicada: {presentation.card_id}")
        self._presentations[presentation.card_id] = presentation

    def snapshot(self) -> CardPresentationSnapshot:
        """Crea una vista inmutable y aislada del estado actual del registro."""

        return CardPresentationSnapshot(self._presentations)

