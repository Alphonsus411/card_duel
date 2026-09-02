from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .enums import (
    CardKind,
    CardRank,
    ControllerScope,
    CostComponent,
    CostMetric,
    EffectDuration,
    EffectKind,
    MatchStatus,
    LordDomain,
    Keyword,
    MoveReason,
    Phase,
    RevealExhaustionPolicy,
    TargetMode,
    TriggerKind,
    Zone,
)


@dataclass(frozen=True)
class CompositeCost:
    steps: int = 0
    wounds: int = 0
    discard_count: int = 0
    sacrifice_count: int = 0
    exhaust_source: bool = False
    strength: int = 0
    mill_count: int = 0

    def __post_init__(self) -> None:
        values = (
            self.steps,
            self.wounds,
            self.discard_count,
            self.sacrifice_count,
            self.strength,
            self.mill_count,
        )
        if any(value < 0 for value in values):
            raise ValueError("Los componentes de un coste no pueden ser negativos")


@dataclass(frozen=True)
class CostTerm:
    metric: CostMetric
    multiplier: int = 1


@dataclass(frozen=True)
class DynamicCostDefinition:
    component: CostComponent
    terms: tuple[CostTerm, ...]
    base: CompositeCost = CompositeCost()
    offset: int = 0
    minimum: int = 0
    maximum: int | None = None

    def __post_init__(self) -> None:
        if not self.terms:
            raise ValueError("Un coste dinámico necesita al menos un término")
        if self.minimum < 0:
            raise ValueError("El mínimo de un coste dinámico no puede ser negativo")
        if self.maximum is not None and self.maximum < self.minimum:
            raise ValueError("El intervalo del coste dinámico no es válido")


@dataclass(frozen=True)
class XCostDefinition:
    component: CostComponent
    base: CompositeCost = CompositeCost()
    multiplier: int = 1
    minimum: int = 0
    maximum: int = 20

    def __post_init__(self) -> None:
        if self.multiplier < 1:
            raise ValueError("El multiplicador de X debe ser positivo")
        if self.minimum < 0 or self.maximum < self.minimum:
            raise ValueError("El intervalo permitido para X no es válido")


@dataclass(frozen=True)
class EffectPatchDefinition:
    effect_index: int
    amount_delta: int = 0
    set_minimum_targets: int | None = None
    set_maximum_targets: int | None = None
    set_target: TargetMode | None = None
    ability_id: str | None = None
    legendary: bool = False

    def __post_init__(self) -> None:
        if self.effect_index < 0:
            raise ValueError("El índice de efecto no puede ser negativo")
        if self.ability_id is not None and self.legendary:
            raise ValueError("Un parche no puede apuntar a habilidad y leyenda a la vez")


@dataclass(frozen=True)
class TextPatchDefinition:
    grant_keywords: frozenset[str | Keyword] = frozenset()
    remove_keywords: frozenset[str | Keyword] = frozenset()
    grant_subtypes: frozenset[str] = frozenset()
    remove_subtypes: frozenset[str] = frozenset()
    add_abilities: tuple[AbilityDefinition, ...] = ()
    remove_ability_ids: frozenset[str] = frozenset()
    set_transmutable: bool | None = None
    effect_patches: tuple[EffectPatchDefinition, ...] = ()

    def __post_init__(self) -> None:
        if self.grant_keywords & self.remove_keywords:
            raise ValueError("Un parche no puede conceder y retirar la misma palabra clave")
        if self.grant_subtypes & self.remove_subtypes:
            raise ValueError("Un parche no puede conceder y retirar el mismo subtipo")
        ids = [ability.ability_id for ability in self.add_abilities]
        if len(ids) != len(set(ids)):
            raise ValueError("Un parche no puede añadir dos habilidades con el mismo id")


@dataclass(frozen=True)
class EffectDefinition:
    kind: EffectKind
    amount: int
    target: TargetMode = TargetMode.SELF
    duration: EffectDuration = EffectDuration.PERMANENT
    minimum_targets: int = 1
    maximum_targets: int = 1
    destination_zone: Zone | None = None
    phase: Phase | None = None
    distributed: bool = False
    allows_regeneration: bool = True
    selection_minimum: int = 1
    selection_maximum: int = 1
    search_filter: CardFilter | None = None
    shuffle_after_search: bool = True
    reveal_search_selection: bool = True
    transform_definition_id: str | None = None
    text_patch: TextPatchDefinition | None = None
    x_multiplier: int = 0
    failure_destination_zone: Zone | None = None
    exhaustion_policy: RevealExhaustionPolicy | None = None

    def __post_init__(self) -> None:
        if self.amount < 0 and self.kind is not EffectKind.MODIFY_STRENGTH:
            raise ValueError("La magnitud de un efecto no puede ser negativa")
        if self.x_multiplier < 0:
            raise ValueError("El multiplicador de X de un efecto no puede ser negativo")
        if self.minimum_targets < 0 or self.maximum_targets < self.minimum_targets:
            raise ValueError("El intervalo de objetivos no es válido")
        player_effects = {
            EffectKind.DEAL_WOUNDS,
            EffectKind.HEAL_WOUNDS,
            EffectKind.GAIN_STEPS,
            EffectKind.DRAW_CARDS,
            EffectKind.PREVENT_WOUNDS,
            EffectKind.SKIP_PHASE,
        }
        card_effects = {
            EffectKind.DEAL_DAMAGE,
            EffectKind.MODIFY_STRENGTH,
            EffectKind.TAP,
            EffectKind.UNTAP,
            EffectKind.DESTROY,
            EffectKind.PREVENT_DAMAGE,
            EffectKind.BECOME_CREATURE,
            EffectKind.ADD_REGENERATION,
            EffectKind.CHANGE_CONTROL,
            EffectKind.COPY_DEFINITION,
            EffectKind.TRANSFORM_DEFINITION,
            EffectKind.MODIFY_TEXT,
        }
        zone_effects = {EffectKind.MOVE_CARDS}
        zone_effects.update({EffectKind.SEARCH_ZONE, EffectKind.SHUFFLE_ZONE, EffectKind.REVEAL_UNTIL})
        if self.kind in player_effects and self.target not in {
            TargetMode.SELF,
            TargetMode.CHOSEN_PLAYER,
        }:
            raise ValueError("El tipo de efecto necesita un objetivo de jugador")
        if self.kind in card_effects and self.target not in {
            TargetMode.SOURCE,
            TargetMode.CHOSEN_PERMANENT,
        }:
            raise ValueError("El tipo de efecto necesita un objetivo de permanente")
        if self.kind in zone_effects and self.target is not TargetMode.CHOSEN_ZONE:
            raise ValueError("El tipo de efecto necesita una zona objetivo")
        if self.kind is EffectKind.DEAL_HARM and self.target is not TargetMode.CHOSEN_ENTITY:
            raise ValueError("El daño repartido necesita objetivos de entidad")
        if self.kind is EffectKind.DEAL_HARM and not self.distributed:
            raise ValueError("DEAL_HARM necesita un reparto explícito")
        if self.distributed and self.amount <= 0 and self.x_multiplier <= 0:
            raise ValueError("Un efecto repartido necesita una cantidad positiva")
        if self.kind is EffectKind.MOVE_CARDS and self.destination_zone is None:
            raise ValueError("Mover cartas necesita una zona de destino")
        if self.kind is EffectKind.MOVE_CARDS and self.amount <= 0:
            raise ValueError("Mover cartas necesita una cantidad positiva")
        if self.kind is EffectKind.SEARCH_ZONE:
            if self.destination_zone is None:
                raise ValueError("Buscar necesita una zona de destino")
            if self.selection_minimum < 0 or self.selection_maximum < self.selection_minimum:
                raise ValueError("El intervalo de selección de búsqueda no es válido")
        if self.kind is EffectKind.REVEAL_UNTIL:
            if self.search_filter is None:
                raise ValueError("Revelar hasta necesita un filtro mecánico")
            if self.destination_zone is None or self.failure_destination_zone is None:
                raise ValueError("Revelar hasta necesita destinos de acierto y fallo")
            if self.exhaustion_policy is None:
                raise ValueError("Revelar hasta necesita una política de agotamiento")
            if self.destination_zone is Zone.REVEAL or self.failure_destination_zone is Zone.REVEAL:
                raise ValueError("Revelar hasta necesita destinos finales")
        elif self.failure_destination_zone is not None or self.exhaustion_policy is not None:
            raise ValueError("Los campos de revelación sólo pertenecen a REVEAL_UNTIL")
        if (
            self.kind is EffectKind.TRANSFORM_DEFINITION
            and not self.transform_definition_id
        ):
            raise ValueError("Transformar necesita una definición de destino")
        if self.kind is EffectKind.MODIFY_TEXT and self.text_patch is None:
            raise ValueError("Modificar texto necesita un parche declarativo")
        if self.kind is not EffectKind.MODIFY_TEXT and self.text_patch is not None:
            raise ValueError("Solo MODIFY_TEXT puede contener un parche de texto")
        if self.kind is EffectKind.SKIP_PHASE and self.phase is None:
            raise ValueError("Omitir una fase necesita indicar cuál")
        if self.distributed and self.kind is not EffectKind.DEAL_HARM:
            raise ValueError("Solo DEAL_HARM admite reparto manual en la versión 0.10")


@dataclass(frozen=True)
class ZoneTarget:
    player_id: str
    zone: Zone


@dataclass(frozen=True)
class CardFilter:
    kinds: frozenset[CardKind] = frozenset()
    ranks: frozenset[CardRank] = frozenset()
    subtypes: frozenset[str] = frozenset()
    definition_ids: frozenset[str] = frozenset()

    def matches(self, definition: CardDefinition) -> bool:
        if self.kinds and definition.kind not in self.kinds:
            return False
        if self.ranks and definition.rank not in self.ranks:
            return False
        if self.subtypes and not (self.subtypes & definition.subtypes):
            return False
        if self.definition_ids and definition.card_id not in self.definition_ids:
            return False
        return True


@dataclass(frozen=True)
class TargetAllocation:
    target_id: str
    amount: int

    def __post_init__(self) -> None:
        if self.amount <= 0:
            raise ValueError("Una asignación debe ser positiva")


@dataclass(frozen=True)
class MoveReplacementDefinition:
    destination: Zone
    applies_to: frozenset[MoveReason] = frozenset(
        {
            MoveReason.RULE,
            MoveReason.DESTROY,
            MoveReason.STATE_BASED,
            MoveReason.TRANSMUTE,
            MoveReason.SACRIFICE,
        }
    )
    strength_delta: int = 0
    enters_exhausted: bool = False
    clear_damage: bool = True
    minimum_strength_after: int | None = None
    priority: int = 0

    def __post_init__(self) -> None:
        if self.destination in {Zone.RESOLUTION, Zone.REVEAL, Zone.VOID}:
            raise ValueError("La sustitución usa una zona de destino no admitida")


@dataclass(frozen=True)
class ContinuousEffectDefinition:
    strength_delta: int = 0
    grant_keywords: frozenset[str | Keyword] = frozenset()
    remove_keywords: frozenset[str | Keyword] = frozenset()
    controller_scope: ControllerScope = ControllerScope.SELF
    affected_kinds: frozenset[CardKind] = frozenset()
    affected_subtypes: frozenset[str] = frozenset()
    excludes_source: bool = False
    suppressed_phases: frozenset[Phase] = frozenset()

    def __post_init__(self) -> None:
        overlap = self.grant_keywords & self.remove_keywords
        if overlap:
            raise ValueError(
                "Un efecto continuo no puede conceder y retirar a la vez: "
                f"{sorted(overlap, key=str)}"
            )


@dataclass(frozen=True)
class AbilityDefinition:
    ability_id: str
    effects: tuple[EffectDefinition, ...]
    cost: CompositeCost = CompositeCost()
    dynamic_cost: DynamicCostDefinition | None = None
    x_cost: XCostDefinition | None = None
    trigger: TriggerKind | None = None
    allowed_phases: frozenset[Phase] = frozenset()
    once_per_turn: bool = False

    def __post_init__(self) -> None:
        if not self.ability_id:
            raise ValueError("Una habilidad necesita identificador")
        if self.trigger is not None and (
            self.cost != CompositeCost()
            or self.dynamic_cost is not None
            or self.x_cost is not None
        ):
            raise ValueError("Una habilidad disparada no puede tener coste de activación")
        if self.dynamic_cost is not None and self.cost != CompositeCost():
            raise ValueError("Una habilidad debe elegir entre coste fijo o dinámico")
        if self.x_cost is not None and (
            self.cost != CompositeCost() or self.dynamic_cost is not None
        ):
            raise ValueError("Una habilidad debe elegir un único modelo de coste")


@dataclass(frozen=True)
class CardDefinition:
    """Definición mecánica de una carta.

    ``cost`` está expresado en Pasos. Ese mismo valor, sin una puntuación
    paralela, se suma para obtener los puntos de construcción del mazo.
    """

    card_id: str
    name: str
    kind: CardKind
    cost: int
    rank: CardRank = CardRank.STANDARD
    base_strength: int | None = None
    permanent: bool = True
    transmutable: bool = True
    set_id: str = "test"
    revision: int = 1
    keywords: frozenset[str | Keyword] = frozenset()
    effects: tuple[EffectDefinition, ...] = ()
    legendary_effects: tuple[EffectDefinition, ...] = ()
    abilities: tuple[AbilityDefinition, ...] = ()
    equipment_strength_bonus: int = 0
    equipment_granted_keywords: frozenset[str | Keyword] = frozenset()
    subtypes: frozenset[str] = frozenset()
    lord_domain: LordDomain | None = None
    continuous_effects: tuple[ContinuousEffectDefinition, ...] = ()
    move_replacement: MoveReplacementDefinition | None = None
    move_replacements: tuple[MoveReplacementDefinition, ...] = ()
    alternative_costs: tuple[CompositeCost, ...] = ()
    dynamic_cost: DynamicCostDefinition | None = None
    dynamic_alternative_costs: tuple[DynamicCostDefinition, ...] = ()
    player_orders_replacements: bool = False
    deferred_replacement_choice: bool = False
    x_cost: XCostDefinition | None = None
    x_alternative_costs: tuple[XCostDefinition, ...] = ()

    def __post_init__(self) -> None:
        if self.cost < 0:
            raise ValueError("El coste no puede ser negativo")
        if (
            self.kind is CardKind.CREATURE
            and self.base_strength is None
            and self.lord_domain is None
        ):
            raise ValueError("Una criatura necesita Fuerza base")
        if self.kind is CardKind.LORD and self.lord_domain is None:
            raise ValueError("Un Señor necesita un dominio")
        if any(cost.strength or cost.exhaust_source for cost in self.alternative_costs):
            raise ValueError("Una carta en mano no puede pagar Fuerza ni agotarse")
        dynamic_costs = tuple(
            cost
            for cost in (self.dynamic_cost, *self.dynamic_alternative_costs)
            if cost is not None
        )
        if any(
            cost.base.strength
            or cost.base.exhaust_source
            or cost.component is CostComponent.STRENGTH
            for cost in dynamic_costs
        ):
            raise ValueError("Una carta en mano no puede pagar Fuerza ni agotarse")
        if self.player_orders_replacements and not (
            self.move_replacement or self.move_replacements
        ):
            raise ValueError("No puede ordenarse una lista de sustituciones vacía")
        if self.deferred_replacement_choice and self.player_orders_replacements:
            raise ValueError("La sustitución no puede ser previa y diferida a la vez")
        if self.deferred_replacement_choice and len(
            (*((self.move_replacement,) if self.move_replacement else ()), *self.move_replacements)
        ) < 2:
            raise ValueError("Una elección diferida necesita varias sustituciones")
        if self.x_cost is not None and self.dynamic_cost is not None:
            raise ValueError("Una carta debe elegir un único coste normal calculado")
        x_costs = tuple(
            cost for cost in (self.x_cost, *self.x_alternative_costs) if cost is not None
        )
        if any(
            cost.base.strength
            or cost.base.exhaust_source
            or cost.component is CostComponent.STRENGTH
            for cost in x_costs
        ):
            raise ValueError("Una carta en mano no puede pagar Fuerza ni agotarse")
        if sum(effect.distributed for effect in self.effects) > 1:
            raise ValueError("Una carta solo puede contener un efecto repartido en la versión 0.10")
        if sum(effect.distributed for effect in self.legendary_effects) > 1:
            raise ValueError(
                "Un disparo legendario solo puede contener un efecto repartido en la versión 0.10"
            )
        ability_ids = [ability.ability_id for ability in self.abilities]
        if len(ability_ids) != len(set(ability_ids)):
            raise ValueError("Una carta no puede repetir identificadores de habilidad")
        for ability in self.abilities:
            if sum(effect.distributed for effect in ability.effects) > 1:
                raise ValueError(
                    "Una habilidad solo puede contener un efecto repartido en la versión 0.10"
                )


@dataclass
class CardInstance:
    instance_id: str
    definition_id: str
    owner_id: str
    controller_id: str
    zone: Zone = Zone.DECK
    exhausted: bool = False
    damage: int = 0
    strength_modifier: int = 0
    counters: dict[str, int] = field(default_factory=dict)
    attached_to: str | None = None
    damage_prevention: int = 0
    activated_this_turn: set[str] = field(default_factory=set)
    transformed_as_creature: bool = False
    creature_form_expires_turn_serial: int | None = None
    regeneration_shields: int = 0
    regeneration_blocked_until_state_check: bool = False
    overridden_definition_id: str | None = None
    definition_override_expires_turn_serial: int | None = None
    replacement_order: tuple[int, ...] = ()


def empty_zones() -> dict[Zone, list[str]]:
    return {
        Zone.DECK: [],
        Zone.HAND: [],
        Zone.BATTLEFIELD: [],
        Zone.DISCARD: [],
        Zone.EXILE: [],
        Zone.REVEAL: [],
    }


@dataclass
class PlayerState:
    player_id: str
    wounds: int = 0
    steps: int = 0
    zones: dict[Zone, list[str]] = field(default_factory=empty_zones)
    mulligans_taken: int = 0
    discard_recycling_blocked: bool = False
    conceded: bool = False
    wound_prevention: int = 0
    drainage_used_turn_serial: int | None = None


@dataclass(frozen=True)
class GameEvent:
    sequence: int
    event_type: str
    player_id: str | None = None
    card_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AbilitySourceProfile:
    """Características congeladas de la fuente al apilar una habilidad.

    ``printed_kind`` conserva su nombre por compatibilidad con snapshots y replays,
    pero en los perfiles nuevos contiene el tipo *efectivo* de la fuente en ese
    instante (incluidas copias y transformaciones), no necesariamente el impreso.
    """

    source_card_id: str
    printed_kind: CardKind
    was_effective_creature: bool
    was_permanent: bool
    was_on_battlefield: bool
    nature_is_certain: bool = True

    @property
    def effective_kind(self) -> CardKind:
        """Alias no persistido que expresa la semántica actual de ``printed_kind``."""

        return self.printed_kind


@dataclass(frozen=True)
class StackItem:
    item_id: str
    controller_id: str
    source_card_id: str
    effects: tuple[EffectDefinition, ...]
    chosen_player_ids: tuple[str, ...] = ()
    chosen_card_ids: tuple[str, ...] = ()
    destination_on_resolve: Zone | None = None
    ability_id: str | None = None
    chosen_zone_targets: tuple[ZoneTarget, ...] = ()
    allocations: tuple[TargetAllocation, ...] = ()
    targets_locked: bool = True
    x_value: int = 0
    ability_source_profile: AbilitySourceProfile | None = None


@dataclass(frozen=True)
class TimedModifier:
    modifier_id: str
    target_card_id: str
    strength_delta: int
    expires_at_turn_serial: int


@dataclass
class PhaseSuppression:
    player_id: str
    phase: Phase
    expires_at_turn_serial: int | None = None
    remaining_occurrences: int | None = 1


@dataclass
class ControlChange:
    card_id: str
    previous_controller_id: str
    expires_at_turn_serial: int


@dataclass(frozen=True)
class AppliedTextPatch:
    patch_id: str
    target_card_id: str
    patch: TextPatchDefinition
    expires_at_turn_serial: int | None = None


@dataclass
class PendingSearch:
    stack_item: StackItem
    next_effect_index: int
    chooser_id: str
    zone_target: ZoneTarget
    eligible_card_ids: tuple[str, ...]
    minimum: int
    maximum: int
    destination_zone: Zone
    shuffle_after: bool
    reveal_selection: bool


@dataclass
class PendingMoveReplacement:
    original_command: Any
    chooser_id: str
    card_id: str
    reason: MoveReason
    candidate_indices: tuple[int, ...]
    candidate_destinations: tuple[Zone, ...]
    resume_priority_player_id: str
    replay_choices: tuple[int, ...] = ()


@dataclass
class CombatState:
    attacking_player_id: str
    defending_player_id: str
    attackers: tuple[str, ...]
    blockers: dict[str, tuple[str, ...]] = field(default_factory=dict)
    blockers_declared: bool = False
    resolved: bool = False
    is_challenge: bool = False


@dataclass
class GameState:
    ruleset_id: str
    ruleset_version: str
    players: dict[str, PlayerState]
    turn_order: tuple[str, ...]
    cards: dict[str, CardInstance]
    active_player_index: int = 0
    phase: Phase = Phase.DRAW
    turn_number: int = 1
    priority_player_id: str | None = None
    consecutive_passes: int = 0
    resolution: list[str] = field(default_factory=list)
    void: list[str] = field(default_factory=list)
    stack: list[StackItem] = field(default_factory=list)
    pending_triggers: list[StackItem] = field(default_factory=list)
    combat: CombatState | None = None
    phase_priority_complete: bool = False
    turn_serial: int = 1
    timed_modifiers: list[TimedModifier] = field(default_factory=list)
    phase_suppressions: list[PhaseSuppression] = field(default_factory=list)
    control_changes: list[ControlChange] = field(default_factory=list)
    pending_search: PendingSearch | None = None
    pending_move_replacement: PendingMoveReplacement | None = None
    text_patches: list[AppliedTextPatch] = field(default_factory=list)
    status: MatchStatus = MatchStatus.SETUP
    winner_ids: tuple[str, ...] = ()
    event_log: list[GameEvent] = field(default_factory=list)
    random_seed: int = 0
    initial_decks: dict[str, tuple[str, ...]] = field(default_factory=dict)
    command_history: list[Any] = field(default_factory=list)
    setup_mulligans: list[str] = field(default_factory=list)

    @property
    def active_player_id(self) -> str:
        return self.turn_order[self.active_player_index]
