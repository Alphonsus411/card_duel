"""Políticas explícitas e inmutables para construir mazos.

Los perfiles de este módulo sólo interpretan los campos autoritativos de
``CardDefinition``.  En particular, no mantienen tablas paralelas de coste,
rango o colección.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import dataclass

from ..domain.enums import CardRank
from ..domain.models import CardDefinition

SetPredicate = Callable[[str], bool]


@dataclass(frozen=True, order=True)
class DeckValidationIssue:
    """Un incumplimiento estable, apto para mostrar o registrar."""

    code: str
    message: str
    card_id: str | None = None


@dataclass(frozen=True)
class DeckValidationResult:
    """Resultado determinista que conserva la única materialización realizada."""

    cards: tuple[CardDefinition, ...]
    issues: tuple[DeckValidationIssue, ...]

    @property
    def is_valid(self) -> bool:
        return not self.issues


class InvalidDeckConstruction(ValueError):
    """Excepción de dominio para un mazo rechazado por su formato."""

    def __init__(self, result: DeckValidationResult) -> None:
        self.result = result
        super().__init__("; ".join(issue.message for issue in result.issues))


@dataclass(frozen=True)
class DeckConstructionPolicy:
    """Restricciones declarativas de un formato de construcción.

    ``point_budget`` queda deliberadamente bajo control de la aplicación. Su
    ausencia representa la decisión abierta ``N-POINTS-01``.
    """

    min_cards: int | None = None
    max_cards: int | None = None
    max_standard_copies: int | None = None
    max_legendary_copies: int | None = None
    forbid_zero_cost: bool = False
    max_zero_cost_copies: int | None = None
    max_zero_cost_total: int | None = None
    allowed_set_ids: frozenset[str] | None = None
    set_predicate: SetPredicate | None = None
    mythic_set_ids: frozenset[str] = frozenset()
    mythic_set_predicate: SetPredicate | None = None
    mythic_min_cost: int | None = None
    mythic_max_cost: int | None = None
    point_budget: int | None = None

    def __post_init__(self) -> None:
        if self.allowed_set_ids is not None:
            object.__setattr__(self, "allowed_set_ids", frozenset(self.allowed_set_ids))
        object.__setattr__(self, "mythic_set_ids", frozenset(self.mythic_set_ids))
        nonnegative = (
            "min_cards", "max_cards", "max_standard_copies",
            "max_legendary_copies", "max_zero_cost_copies",
            "max_zero_cost_total", "mythic_min_cost", "mythic_max_cost",
            "point_budget",
        )
        if any(getattr(self, name) is not None and getattr(self, name) < 0 for name in nonnegative):
            raise ValueError("Los límites de construcción no pueden ser negativos")
        if self.min_cards is not None and self.max_cards is not None and self.min_cards > self.max_cards:
            raise ValueError("El mínimo de cartas no puede superar el máximo")
        if self.mythic_min_cost is not None and self.mythic_max_cost is not None and self.mythic_min_cost > self.mythic_max_cost:
            raise ValueError("El coste Mítico mínimo no puede superar el máximo")
        if self.allowed_set_ids is not None and self.set_predicate is not None:
            raise ValueError("Use conjuntos permitidos o un predicado, no ambos")

    def validate(self, cards: Iterable[CardDefinition]) -> DeckValidationResult:
        """Consume ``cards`` exactamente una vez y no modifica ningún argumento."""
        materialized = tuple(cards)
        issues: list[DeckValidationIssue] = []
        size = len(materialized)
        if self.min_cards is not None and size < self.min_cards:
            issues.append(DeckValidationIssue("deck.too_small", f"El mazo tiene {size} cartas; mínimo {self.min_cards}"))
        if self.max_cards is not None and size > self.max_cards:
            issues.append(DeckValidationIssue("deck.too_large", f"El mazo tiene {size} cartas; máximo {self.max_cards}"))

        by_id = Counter(card.card_id for card in materialized)
        definitions = {card.card_id: card for card in materialized}
        for card_id in sorted(by_id):
            card = definitions[card_id]
            limit = self.max_legendary_copies if card.rank is CardRank.LEGENDARY else self.max_standard_copies
            if limit is not None and by_id[card_id] > limit:
                issues.append(DeckValidationIssue("copies.exceeded", f"{card_id} tiene {by_id[card_id]} copias; máximo {limit}", card_id))

        illegal_sets = sorted({card.set_id for card in materialized if not self._set_allowed(card.set_id)})
        for set_id in illegal_sets:
            issues.append(DeckValidationIssue("set.not_allowed", f"Colección no permitida: {set_id}"))

        zero_cards = [card for card in materialized if card.cost == 0]
        if self.forbid_zero_cost and zero_cards:
            issues.append(DeckValidationIssue("cost.zero_forbidden", "El formato no permite cartas de coste cero"))
        if self.max_zero_cost_copies is not None:
            for card_id in sorted({card.card_id for card in zero_cards}):
                count = sum(card.card_id == card_id for card in zero_cards)
                if count > self.max_zero_cost_copies:
                    issues.append(DeckValidationIssue("cost.zero_copies", f"{card_id} tiene {count} copias de coste cero; máximo {self.max_zero_cost_copies}", card_id))
        if self.max_zero_cost_total is not None and len(zero_cards) > self.max_zero_cost_total:
            issues.append(DeckValidationIssue("cost.zero_total", f"El mazo tiene {len(zero_cards)} cartas de coste cero; máximo {self.max_zero_cost_total}"))

        for card_id in sorted(by_id):
            card = definitions[card_id]
            if self._is_mythic(card.set_id) and (
                (self.mythic_min_cost is not None and card.cost < self.mythic_min_cost)
                or (self.mythic_max_cost is not None and card.cost > self.mythic_max_cost)
            ):
                issues.append(DeckValidationIssue("mythic.cost_range", f"{card_id} tiene coste Mítico fuera del intervalo {self.mythic_min_cost}–{self.mythic_max_cost}", card_id))
        if self.point_budget is not None and sum(card.cost for card in materialized) > self.point_budget:
            issues.append(DeckValidationIssue("points.exceeded", f"El mazo supera el presupuesto de {self.point_budget} puntos"))
        return DeckValidationResult(materialized, tuple(issues))

    def require_valid(self, cards: Iterable[CardDefinition]) -> tuple[CardDefinition, ...]:
        result = self.validate(cards)
        if not result.is_valid:
            raise InvalidDeckConstruction(result)
        return result.cards

    def _set_allowed(self, set_id: str) -> bool:
        if self.allowed_set_ids is not None:
            return set_id in self.allowed_set_ids
        return self.set_predicate(set_id) if self.set_predicate is not None else True

    def _is_mythic(self, set_id: str) -> bool:
        return set_id in self.mythic_set_ids or (
            self.mythic_set_predicate(set_id) if self.mythic_set_predicate is not None else False
        )


def mythic_deck_policy(
    *, allowed_set_ids: frozenset[str] | None = None,
    set_predicate: SetPredicate | None = None,
    mythic_set_ids: frozenset[str] = frozenset(),
    mythic_set_predicate: SetPredicate | None = None,
    point_budget: int | None = None,
) -> DeckConstructionPolicy:
    return DeckConstructionPolicy(
        min_cards=40, max_cards=60, max_standard_copies=5,
        max_legendary_copies=4, forbid_zero_cost=True,
        allowed_set_ids=allowed_set_ids, set_predicate=set_predicate,
        mythic_set_ids=mythic_set_ids, mythic_set_predicate=mythic_set_predicate,
        mythic_min_cost=5, mythic_max_cost=50, point_budget=point_budget,
    )


def classic_deck_policy(
    *, allowed_set_ids: frozenset[str] | None = None,
    set_predicate: SetPredicate | None = None,
    max_standard_copies: int | None = None,
    max_legendary_copies: int | None = None,
    point_budget: int | None = None,
) -> DeckConstructionPolicy:
    return DeckConstructionPolicy(
        max_standard_copies=max_standard_copies,
        max_legendary_copies=max_legendary_copies,
        max_zero_cost_copies=1, max_zero_cost_total=6,
        allowed_set_ids=allowed_set_ids, set_predicate=set_predicate,
        point_budget=point_budget,
    )
