"""Políticas explícitas e inmutables para construir mazos.

Los perfiles de este módulo sólo interpretan los campos autoritativos de
``CardDefinition``.  En particular, no mantienen tablas paralelas de coste,
rango o colección.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from types import MappingProxyType

from ..domain.enums import CardRank
from ..domain.models import CardDefinition

SetPredicate = Callable[[str], bool]


def deck_points(cards: Iterable[CardDefinition]) -> int:
    """Devuelve los puntos del mazo usando únicamente el coste de cada carta."""
    materialized = tuple(cards)
    return sum(card.cost for card in materialized)


def _all_sets_are_mythic(_set_id: str) -> bool:
    """Clasifica cualquier colección como Mítica en el perfil aislado."""
    return True


def _no_sets_are_mythic(_set_id: str) -> bool:
    """Representa un clasificador Mítico explícitamente vacío."""
    return False


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


@dataclass(frozen=True)
class DeckGroupValidationResult:
    """Resultado de grupo reutilizable sin exponer contenido en los errores."""

    decks: Mapping[str, tuple[CardDefinition, ...]]
    issues: tuple[DeckValidationIssue, ...]

    @property
    def is_valid(self) -> bool:
        return not self.issues


def validate_deck_group(
    decks: Mapping[str, Iterable[CardDefinition]],
    *,
    require_equal_points: bool = False,
) -> DeckGroupValidationResult:
    """Materializa los mazos una vez y valida una relación opcional entre ellos.

    La incidencia deliberadamente no identifica jugadores, cartas ni totales, de
    modo que el resultado sea estable y seguro al cruzar fronteras de servicio.
    """
    if type(require_equal_points) is not bool:
        raise TypeError("require_equal_points debe ser bool")

    prepared = {
        player_id: tuple(deck)
        for player_id, deck in decks.items()
    }
    issues: tuple[DeckValidationIssue, ...] = ()
    if require_equal_points:
        totals = tuple(deck_points(deck) for deck in prepared.values())
        if totals and any(total != totals[0] for total in totals[1:]):
            issues = (
                DeckValidationIssue(
                    "decks.points_not_equal",
                    "Los mazos no tienen la misma cantidad de puntos",
                ),
            )
    return DeckGroupValidationResult(MappingProxyType(prepared), issues)


class InvalidDeckConstruction(ValueError):
    """Excepción de dominio para un mazo rechazado por su formato."""

    def __init__(self) -> None:
        # La excepción cruza fronteras de servicio: no conserva el mazo ni
        # detalles internos de la política. El resultado detallado sigue
        # disponible para quien invoque ``validate`` explícitamente.
        super().__init__("El mazo no cumple la política de construcción")


@dataclass(frozen=True)
class DeckConstructionPolicy:
    """Restricciones declarativas de un formato de construcción.

    Los puntos son la suma de ``CardDefinition.cost`` (Pasos); no existe una
    puntuación paralela por carta. ``min_points`` permite configurar un mínimo
    cuando el formato aplicable lo establezca.
    ``point_budget`` es solamente un máximo opcional bajo control de la
    aplicación: no tiene valor predeterminado porque ``N-POINTS-01`` bloquea
    las cifras Míticas 200, 300 y 400.

    La equivalencia de puntos es una relación entre las barajas participantes
    y, por tanto, no puede decidirla ``validate``, que recibe una sola baraja.
    """

    min_cards: int | None = None
    max_cards: int | None = None
    max_standard_copies: int | None = None
    max_legendary_copies: int | None = None
    forbid_zero_cost: bool = False
    max_zero_cost_copies: int | None = None
    max_zero_cost_total: int | None = None
    allowed_set_ids: Iterable[str] | None = None
    set_predicate: SetPredicate | None = None
    mythic_set_ids: Iterable[str] = frozenset()
    mythic_set_predicate: SetPredicate | None = None
    mythic_min_cost: int | None = None
    mythic_max_cost: int | None = None
    min_points: int | None = None
    point_budget: int | None = None

    def __post_init__(self) -> None:
        nonnegative = (
            "min_cards", "max_cards", "max_standard_copies",
            "max_legendary_copies", "max_zero_cost_copies",
            "max_zero_cost_total", "mythic_min_cost", "mythic_max_cost",
            "min_points", "point_budget",
        )
        for name in nonnegative:
            value = getattr(self, name)
            if value is not None and type(value) is not int:
                raise TypeError(f"{name} debe ser un entero o None")
        if type(self.forbid_zero_cost) is not bool:
            raise TypeError("forbid_zero_cost debe ser bool")
        if self.set_predicate is not None and not callable(self.set_predicate):
            raise TypeError("set_predicate debe ser invocable o None")
        if self.mythic_set_predicate is not None and not callable(self.mythic_set_predicate):
            raise TypeError("mythic_set_predicate debe ser invocable o None")

        allowed_set_ids = self._materialize_set_ids("allowed_set_ids", self.allowed_set_ids)
        mythic_set_ids = (
            self._materialize_set_ids("mythic_set_ids", self.mythic_set_ids)
            or frozenset()
        )
        object.__setattr__(self, "allowed_set_ids", allowed_set_ids)
        object.__setattr__(self, "mythic_set_ids", mythic_set_ids)

        if any(getattr(self, name) is not None and getattr(self, name) < 0 for name in nonnegative):
            raise ValueError("Los límites de construcción no pueden ser negativos")
        if self.min_cards is not None and self.max_cards is not None and self.min_cards > self.max_cards:
            raise ValueError("El mínimo de cartas no puede superar el máximo")
        if self.mythic_min_cost is not None and self.mythic_max_cost is not None and self.mythic_min_cost > self.mythic_max_cost:
            raise ValueError("El coste Mítico mínimo no puede superar el máximo")
        if self.min_points is not None and self.point_budget is not None and self.min_points > self.point_budget:
            raise ValueError("El mínimo de puntos no puede superar el presupuesto máximo")
        if self.allowed_set_ids is not None and self.set_predicate is not None:
            raise ValueError("Use conjuntos permitidos o un predicado, no ambos")
        if allowed_set_ids is not None and not mythic_set_ids.issubset(allowed_set_ids):
            raise ValueError("Las colecciones Míticas deben pertenecer a las colecciones permitidas")
        if self.set_predicate is not None and mythic_set_ids:
            try:
                mythic_sets_are_allowed = all(
                    self.set_predicate(set_id) for set_id in mythic_set_ids
                )
            except Exception:
                raise ValueError("La configuración de colecciones es incoherente") from None
            if not mythic_sets_are_allowed:
                raise ValueError("La configuración de colecciones es incoherente")
        has_mythic_limits = self.mythic_min_cost is not None or self.mythic_max_cost is not None
        if has_mythic_limits and not mythic_set_ids and self.mythic_set_predicate is None:
            raise ValueError("Los límites Míticos requieren un mecanismo de clasificación aplicable")

    @staticmethod
    def _materialize_set_ids(
        name: str, values: Iterable[str] | None
    ) -> frozenset[str] | None:
        if values is None:
            return None
        try:
            materialized = tuple(values)
        except TypeError:
            raise TypeError(f"{name} debe ser un iterable de cadenas") from None
        if any(type(value) is not str or not value for value in materialized):
            raise TypeError(f"Cada elemento de {name} debe ser una cadena no vacía")
        return frozenset(materialized)

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
        points = deck_points(materialized)
        if self.min_points is not None and points < self.min_points:
            issues.append(DeckValidationIssue("deck.points_below_minimum", f"El mazo tiene {points} puntos; mínimo {self.min_points}"))
        if self.point_budget is not None and points > self.point_budget:
            issues.append(DeckValidationIssue("deck.points_exceeded", f"El mazo supera el presupuesto de {self.point_budget} puntos"))
        return DeckValidationResult(materialized, tuple(issues))

    def require_valid(self, cards: Iterable[CardDefinition]) -> tuple[CardDefinition, ...]:
        result = self.validate(cards)
        if not result.is_valid:
            raise InvalidDeckConstruction from None
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
    *, allowed_set_ids: Iterable[str] | None = None,
    set_predicate: SetPredicate | None = None,
    mythic_set_ids: Iterable[str] | None = None,
    mythic_set_predicate: SetPredicate | None = None,
    point_budget: int | None = None,
) -> DeckConstructionPolicy:
    for name, predicate in (
        ("set_predicate", set_predicate),
        ("mythic_set_predicate", mythic_set_predicate),
    ):
        if predicate is not None and not callable(predicate):
            raise TypeError(f"{name} debe ser invocable o None")

    has_general_classifier = allowed_set_ids is not None or set_predicate is not None
    has_mythic_classifier = (
        mythic_set_ids is not None or mythic_set_predicate is not None
    )
    if has_general_classifier and not has_mythic_classifier:
        raise ValueError("La configuración de colecciones es incompleta")

    # El perfil aislado sigue siendo exclusivamente Mítico. En cuanto el
    # llamador abre el formato a colecciones explícitas, debe clasificarlas
    # también de forma explícita para que futuras ediciones no hereden 5–50.
    if not has_general_classifier and not has_mythic_classifier:
        mythic_set_predicate = _all_sets_are_mythic
    elif mythic_set_ids is not None and mythic_set_predicate is None:
        mythic_set_ids = frozenset(mythic_set_ids)
        if not mythic_set_ids:
            # El conjunto vacío es un clasificador explícito y se distingue del
            # perfil aislado, que clasifica todas las colecciones como Míticas.
            mythic_set_predicate = _no_sets_are_mythic
    return DeckConstructionPolicy(
        min_cards=40, max_cards=60, max_standard_copies=5,
        max_legendary_copies=4, forbid_zero_cost=True,
        allowed_set_ids=allowed_set_ids, set_predicate=set_predicate,
        mythic_set_ids=frozenset() if mythic_set_ids is None else mythic_set_ids,
        mythic_set_predicate=mythic_set_predicate,
        mythic_min_cost=5, mythic_max_cost=50, min_points=50,
        point_budget=point_budget,
    )


def classic_deck_policy(
    *, allowed_set_ids: Iterable[str] | None = None,
    set_predicate: SetPredicate | None = None,
    max_standard_copies: int | None = 5,
    max_legendary_copies: int | None = 4,
    point_budget: int | None = None,
) -> DeckConstructionPolicy:
    return DeckConstructionPolicy(
        min_cards=40, max_cards=60,
        max_standard_copies=max_standard_copies,
        max_legendary_copies=max_legendary_copies,
        max_zero_cost_copies=1, max_zero_cost_total=6,
        allowed_set_ids=allowed_set_ids, set_predicate=set_predicate,
        min_points=50, point_budget=point_budget,
    )
