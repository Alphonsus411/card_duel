from __future__ import annotations

import random
from copy import deepcopy
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import replace
from itertools import combinations, islice, permutations, product

from ..catalog import CardCatalog
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..content.registry import CollectionRegistry
from ..controllers.base import PlayerObservation
from ..domain.enums import (
    CardKind,
    CardRank,
    ControllerScope,
    EffectDuration,
    EffectKind,
    MatchStatus,
    MoveReason,
    Phase,
    TargetMode,
    TriggerKind,
    Zone,
)
from ..domain.errors import IllegalAction, InvariantViolation, PaymentError
from ..domain.models import (
    AppliedTextPatch,
    CardDefinition,
    CardInstance,
    CombatState,
    CompositeCost,
    ControlChange,
    ContinuousEffectDefinition,
    EffectDefinition,
    DynamicCostDefinition,
    MoveReplacementDefinition,
    PendingMoveReplacement,
    GameEvent,
    GameState,
    PlayerState,
    PhaseSuppression,
    PendingSearch,
    StackItem,
    TimedModifier,
    TargetAllocation,
    TextPatchDefinition,
    ZoneTarget,
    XCostDefinition,
)
from ..rules.config import RuleSet
from ..rules.resolvers import apply_text_patch, resolve_dynamic_cost, resolve_x_cost
from .combat import CombatContext, CombatManager
from .effects import EffectContext, EffectManager
from .stack import StackContext, StackManager
from .zones import MoveReplacementChoiceRequired, ZoneContext, ZoneManager
from .commands import (
    AdvancePhase,
    ActivateAbility,
    ChooseTriggeredTargets,
    Concede,
    DeclareAttackers,
    DeclareChallenge,
    DeclareBlockers,
    DiscardCards,
    DrainSteps,
    EquipCard,
    GameCommand,
    PassPriority,
    OrderTriggeredAbilities,
    PlayCard,
    ResolveCombat,
    ResolveSearchChoice,
    ResolveMoveReplacement,
    SetReplacementOrder,
    TransmutePermanent,
)


class GameEngine:
    """Autoridad única sobre una partida; ninguna interfaz modifica el estado."""

    def __init__(self, rules: RuleSet | None = None, catalog: CardCatalog | CollectionRegistry | None = None):
        self.rules = rules or RuleSet()
        self.registry: CollectionRegistry | None = (
            catalog if catalog is not None and not isinstance(catalog, CardCatalog) else None
        )
        self.catalog: CardCatalog = (
            self.registry.catalog
            if self.registry is not None
            else catalog if isinstance(catalog, CardCatalog) else CardCatalog()
        )
        self.state: GameState | None = None
        self._next_instance = 1
        self._next_stack_item = 1
        self._replacement_replay_choices: tuple[int, ...] = ()
        self._replacement_replay_cursor = 0
        self._combat = CombatManager(self)
        self._stack = StackManager(self)
        self._zones = ZoneManager(self)
        self._effects = EffectManager(self)

    def _consume_replacement_replay_choice(self) -> int | None:
        """Consume una elección grabada sin exponer el cursor al gestor de zonas."""
        if self._replacement_replay_cursor >= len(self._replacement_replay_choices):
            return None
        choice = self._replacement_replay_choices[self._replacement_replay_cursor]
        self._replacement_replay_cursor += 1
        return choice

    def new_match(
        self,
        decks: Mapping[str, Iterable[CardDefinition]],
        *,
        seed: int = 0,
        auto_start: bool = True,
    ) -> GameState:
        if len(decks) < self.rules.minimum_players:
            raise ValueError(f"Se necesitan al menos {self.rules.minimum_players} jugadores")

        self._next_instance = 1
        self._next_stack_item = 1
        self._replacement_replay_choices = ()
        self._replacement_replay_cursor = 0
        rng = random.Random(seed)
        players = {player_id: PlayerState(player_id) for player_id in decks}
        cards: dict[str, CardInstance] = {}
        initial_decks: dict[str, tuple[str, ...]] = {}

        for player_id, definitions in decks.items():
            definition_ids: list[str] = []
            for definition in definitions:
                definition_ids.append(definition.card_id)
                if definition.card_id not in self.catalog:
                    if self.registry is not None:
                        raise ValueError(
                            f"La definición {definition.card_id} no está registrada en el catálogo"
                        )
                    self.catalog.register(definition)
                elif self.catalog.get(definition.card_id) != definition:
                    raise ValueError(
                        f"La definición {definition.card_id} no coincide con el catálogo"
                    )
                instance_id = f"card-{self._next_instance:06d}"
                self._next_instance += 1
                cards[instance_id] = CardInstance(
                    instance_id=instance_id,
                    definition_id=definition.card_id,
                    owner_id=player_id,
                    controller_id=player_id,
                )
                players[player_id].zones[Zone.DECK].append(instance_id)
            initial_decks[player_id] = tuple(definition_ids)
            rng.shuffle(players[player_id].zones[Zone.DECK])

        self.state = GameState(
            ruleset_id=self.rules.ruleset_id,
            ruleset_version=self.rules.version,
            players=players,
            turn_order=tuple(decks),
            cards=cards,
            priority_player_id=tuple(decks)[0],
            random_seed=seed,
            initial_decks=initial_decks,
            status=MatchStatus.SETUP,
        )
        for player_id in self.state.turn_order:
            self._draw(player_id, self.rules.initial_hand_size)
        if auto_start:
            self.start_match()
        self.validate_invariants()
        return self.state

    def start_match(self) -> None:
        state = self._require_state()
        if state.status is not MatchStatus.SETUP:
            raise IllegalAction("La partida ya ha comenzado")
        state.status = MatchStatus.RUNNING
        self._emit("MATCH_STARTED", payload={"seed": state.random_seed})
        self._enter_phase_or_skip(Phase.DRAW)

    def mulligan(self, player_id: str) -> None:
        state = self._require_state()
        if state.status is not MatchStatus.SETUP:
            raise IllegalAction("El mulligan solo puede realizarse durante la preparación")
        player = state.players[player_id]
        new_size = self.rules.initial_hand_size - player.mulligans_taken - 1
        if new_size < 1:
            raise IllegalAction("No se permiten más mulligans")
        for card_id in tuple(player.zones[Zone.HAND]):
            self._move_card(card_id, Zone.DECK, player_id)
        random.Random(state.random_seed + player.mulligans_taken + 1).shuffle(
            player.zones[Zone.DECK]
        )
        player.mulligans_taken += 1
        state.setup_mulligans.append(player_id)
        self._draw(player_id, new_size)
        self._emit("MULLIGAN", player_id, payload={"new_hand_size": new_size})

    def execute(self, command: GameCommand) -> None:
        if isinstance(command, ResolveMoveReplacement):
            self._resolve_move_replacement(command)
            self._require_state().command_history.append(command)
            return
        self._execute_transaction(command, ())
        self._require_state().command_history.append(command)

    def _execute_transaction(
        self, command: GameCommand, replay_choices: tuple[int, ...]
    ) -> None:
        state = self._require_running_state()
        transactional = bool(replay_choices) or any(
            definition.deferred_replacement_choice
            for definition in self.catalog.definitions()
        )
        snapshot = deepcopy(state) if transactional else None
        next_stack_item = self._next_stack_item
        self._replacement_replay_choices = replay_choices
        self._replacement_replay_cursor = 0
        try:
            self._execute_command(command)
            if self._replacement_replay_cursor != len(replay_choices):
                raise InvariantViolation("La reproducción dejó elecciones sin consumir")
        except MoveReplacementChoiceRequired as request:
            if snapshot is None:
                raise InvariantViolation(
                    "Se solicitó una sustitución sin respaldo transaccional"
                )
            self.state = snapshot
            self._next_stack_item = next_stack_item
            assert snapshot.priority_player_id is not None
            self.state.pending_move_replacement = PendingMoveReplacement(
                original_command=command,
                chooser_id=request.chooser_id,
                card_id=request.card_id,
                reason=request.reason,
                candidate_indices=request.candidate_indices,
                candidate_destinations=request.candidate_destinations,
                resume_priority_player_id=snapshot.priority_player_id,
                replay_choices=replay_choices,
            )
            self.state.priority_player_id = request.chooser_id
            self._emit(
                "MOVE_REPLACEMENT_CHOICE_REQUESTED",
                request.chooser_id,
                request.card_id,
                {
                    "reason": request.reason.name,
                    "candidate_indices": request.candidate_indices,
                    "destinations": tuple(
                        zone.name for zone in request.candidate_destinations
                    ),
                },
            )
            self.validate_invariants()
        except Exception:
            if snapshot is not None:
                self.state = snapshot
                self._next_stack_item = next_stack_item
            raise
        finally:
            self._replacement_replay_choices = ()
            self._replacement_replay_cursor = 0

    def _execute_command(self, command: GameCommand) -> None:
        state = self._require_running_state()
        if command.player_id not in state.players:
            raise IllegalAction("Jugador desconocido")
        if state.pending_move_replacement and not isinstance(command, Concede):
            raise IllegalAction("Debe elegirse primero una sustitución de movimiento")
        if state.pending_triggers and not isinstance(
            command, (ChooseTriggeredTargets, OrderTriggeredAbilities, Concede)
        ):
            raise IllegalAction("Deben ordenarse primero los disparos simultáneos")
        if state.pending_search and not isinstance(command, (ResolveSearchChoice, Concede)):
            raise IllegalAction("Debe completarse primero la búsqueda pendiente")

        if isinstance(command, AdvancePhase):
            self._advance_phase(command.player_id)
        elif isinstance(command, DiscardCards):
            self._discard_cards(command)
        elif isinstance(command, TransmutePermanent):
            self._transmute(command)
        elif isinstance(command, PlayCard):
            self._play_card(command)
        elif isinstance(command, ActivateAbility):
            self._activate_ability(command)
        elif isinstance(command, EquipCard):
            self._equip_card(command)
        elif isinstance(command, DrainSteps):
            self._drain_steps(command)
        elif isinstance(command, DeclareChallenge):
            self._declare_challenge(command)
        elif isinstance(command, OrderTriggeredAbilities):
            self._order_triggered_abilities(command)
        elif isinstance(command, ChooseTriggeredTargets):
            self._choose_triggered_targets(command)
        elif isinstance(command, ResolveSearchChoice):
            self._resolve_search_choice(command)
        elif isinstance(command, SetReplacementOrder):
            self._set_replacement_order(command)
        elif isinstance(command, PassPriority):
            self._pass_priority(command.player_id)
        elif isinstance(command, DeclareAttackers):
            self._declare_attackers(command)
        elif isinstance(command, DeclareBlockers):
            self._declare_blockers(command)
        elif isinstance(command, ResolveCombat):
            self._resolve_combat(command.player_id)
        elif isinstance(command, Concede):
            self._concede(command.player_id)
        else:
            raise TypeError(f"Comando no soportado: {type(command).__name__}")

        if state.status is MatchStatus.RUNNING:
            self._check_wound_limits()
        self.validate_invariants()

    def _resolve_move_replacement(self, command: ResolveMoveReplacement) -> None:
        state = self._require_running_state()
        pending = state.pending_move_replacement
        if pending is None or pending.chooser_id != command.player_id:
            raise IllegalAction("No existe una elección de sustitución propia pendiente")
        if command.replacement_index not in pending.candidate_indices:
            raise IllegalAction("La sustitución elegida no está disponible")
        original_command = pending.original_command
        replay_choices = (*pending.replay_choices, command.replacement_index)
        state.pending_move_replacement = None
        state.priority_player_id = pending.resume_priority_player_id
        self._emit(
            "MOVE_REPLACEMENT_CHOSEN",
            command.player_id,
            pending.card_id,
            {"replacement_index": command.replacement_index},
        )
        self._execute_transaction(original_command, replay_choices)

    def observe(self, player_id: str) -> PlayerObservation:
        state = self._require_state()
        if player_id not in state.players:
            raise KeyError(f"Jugador desconocido: {player_id}")
        player = state.players[player_id]
        return PlayerObservation(
            player_id=player_id,
            active_player_id=state.active_player_id,
            phase=state.phase,
            own_hand=tuple(player.zones[Zone.HAND]),
            own_steps=player.steps,
            own_wounds=player.wounds,
            opponent_hand_sizes={
                other_id: len(other.zones[Zone.HAND])
                for other_id, other in state.players.items()
                if other_id != player_id
            },
            public_event_count=len(state.event_log),
            own_battlefield=tuple(player.zones[Zone.BATTLEFIELD]),
            opponent_battlefields={
                other_id: tuple(other.zones[Zone.BATTLEFIELD])
                for other_id, other in state.players.items()
                if other_id != player_id
            },
            stack_size=len(state.stack) + len(state.pending_triggers),
            stack_items=tuple(
                (item.item_id, item.ability_id, item.source_card_id)
                for item in reversed(state.stack)
            ),
            pending_triggers=tuple(
                (
                    item.item_id,
                    item.ability_id,
                    item.source_card_id,
                    item.targets_locked,
                )
                for item in state.pending_triggers
            ),
            suppressed_phases=tuple(
                (suppression.player_id, suppression.phase)
                for suppression in state.phase_suppressions
            ),
            pending_search_item_id=(
                state.pending_search.stack_item.item_id
                if state.pending_search is not None
                else None
            ),
            searchable_card_ids=(
                state.pending_search.eligible_card_ids
                if state.pending_search is not None
                and state.pending_search.chooser_id == player_id
                else ()
            ),
            replacement_orders=tuple(
                (card_id, state.cards[card_id].replacement_order)
                for card_id in player.zones[Zone.BATTLEFIELD]
                if state.cards[card_id].replacement_order
            ),
            pending_replacement_card_id=(
                state.pending_move_replacement.card_id
                if state.pending_move_replacement is not None
                else None
            ),
            replacement_destinations=(
                tuple(
                    (index, destination.name)
                    for index, destination in zip(
                        state.pending_move_replacement.candidate_indices,
                        state.pending_move_replacement.candidate_destinations,
                        strict=True,
                    )
                )
                if state.pending_move_replacement is not None
                and state.pending_move_replacement.chooser_id == player_id
                else ()
            ),
        )

    def legal_actions(self, player_id: str) -> tuple[GameCommand, ...]:
        state = self._require_running_state()
        if player_id not in state.players:
            return ()
        actions: list[GameCommand] = []
        player = state.players[player_id]

        if state.pending_move_replacement:
            pending = state.pending_move_replacement
            if player_id != pending.chooser_id:
                return (Concede(player_id),)
            return tuple(
                ResolveMoveReplacement(player_id, index)
                for index in pending.candidate_indices
            ) + (Concede(player_id),)

        if state.pending_search:
            search = state.pending_search
            if player_id != search.chooser_id:
                return (Concede(player_id),)
            actions.extend(
                ResolveSearchChoice(player_id, tuple(selection))
                for count in range(search.minimum, search.maximum + 1)
                for selection in islice(
                    combinations(search.eligible_card_ids, count),
                    self.rules.legal_action_enumeration_limit,
                )
            )
            actions.append(Concede(player_id))
            return tuple(actions[: self.rules.legal_action_enumeration_limit + 1])

        if state.pending_triggers:
            if player_id != state.priority_player_id:
                return (Concede(player_id),)
            unlocked = next(
                (item for item in state.pending_triggers if not item.targets_locked),
                None,
            )
            if unlocked is not None:
                actions.extend(self._trigger_target_commands(player_id, unlocked))
                actions.append(Concede(player_id))
                return tuple(actions)
            item_ids = tuple(item.item_id for item in state.pending_triggers)
            actions.extend(
                OrderTriggeredAbilities(player_id, tuple(order))
                for order in islice(
                    permutations(item_ids),
                    self.rules.legal_action_enumeration_limit,
                )
            )
            actions.append(Concede(player_id))
            return tuple(actions)

        if state.phase is Phase.COMBAT and state.combat is not None:
            combat = state.combat
            if player_id == combat.defending_player_id and not combat.blockers_declared:
                actions.append(DeclareBlockers(player_id))
            if (
                player_id == combat.attacking_player_id
                and combat.blockers_declared
                and not combat.resolved
                and not state.stack
                and state.phase_priority_complete
            ):
                actions.append(ResolveCombat(player_id))

        if player_id == state.priority_player_id:
            actions.extend(self._legal_plays(player_id))
            if (
                player_id == state.active_player_id
                and player.drainage_used_turn_serial != state.turn_serial
            ):
                actions.extend(DrainSteps(player_id, amount) for amount in range(1, 6))
            for card_id in player.zones[Zone.BATTLEFIELD]:
                definition = self._definition(card_id)
                replacements = self._replacement_definitions(definition)
                if definition.player_orders_replacements and len(replacements) > 1:
                    actions.extend(
                        SetReplacementOrder(player_id, card_id, tuple(order))
                        for order in islice(
                            permutations(range(len(replacements))),
                            self.rules.legal_action_enumeration_limit,
                        )
                        if tuple(order) != state.cards[card_id].replacement_order
                    )
                if definition.transmutable:
                    actions.append(TransmutePermanent(player_id, card_id))
                actions.extend(self._legal_ability_activations(player_id, card_id))
                if definition.kind is CardKind.EQUIPMENT:
                    for creature_id in player.zones[Zone.BATTLEFIELD]:
                        if self._is_creature(creature_id):
                            if player.steps >= definition.cost:
                                actions.append(EquipCard(player_id, card_id, creature_id))
            actions.append(PassPriority(player_id))

        if (
            player_id == state.active_player_id
            and state.phase_priority_complete
            and not state.stack
        ):
            if state.phase is Phase.COMBAT and state.combat is None:
                ready = tuple(
                    card_id
                    for card_id in player.zones[Zone.BATTLEFIELD]
                    if self._is_ready_creature(card_id)
                )
                if ready:
                    for defender in state.turn_order:
                        if defender != player_id:
                            actions.append(DeclareAttackers(player_id, ready, defender))
                    for challenger_id in ready:
                        if self._is_lord_creature(challenger_id):
                            for defender_id in state.turn_order:
                                if defender_id == player_id:
                                    continue
                                for challenged_id in state.players[defender_id].zones[
                                    Zone.BATTLEFIELD
                                ]:
                                    if self._is_creature(challenged_id):
                                        actions.append(
                                            DeclareChallenge(
                                                player_id,
                                                challenger_id,
                                                challenged_id,
                                                defender_id,
                                            )
                                        )
            if state.phase is Phase.DISCARD:
                excess = max(0, len(player.zones[Zone.HAND]) - self.rules.hand_limit)
                if excess:
                    actions.extend(
                        DiscardCards(player_id, tuple(card_ids))
                        for card_ids in combinations(player.zones[Zone.HAND], excess)
                    )
                else:
                    actions.append(AdvancePhase(player_id))
            elif not (state.phase is Phase.COMBAT and state.combat and not state.combat.resolved):
                actions.append(AdvancePhase(player_id))

        actions.append(Concede(player_id))
        command_order = {
            DiscardCards: 0,
            DeclareBlockers: 0,
            ResolveCombat: 0,
            DeclareAttackers: 1,
            DeclareChallenge: 1,
            AdvancePhase: 2,
            PlayCard: 10,
            ActivateAbility: 11,
            DrainSteps: 11,
            EquipCard: 12,
            TransmutePermanent: 20,
            PassPriority: 90,
            SetReplacementOrder: 95,
            Concede: 100,
        }
        return tuple(sorted(actions, key=lambda action: command_order[type(action)]))

    def _trigger_target_commands(
        self, player_id: str, item: StackItem
    ) -> list[ChooseTriggeredTargets]:
        state = self._require_running_state()
        definition = self._definition(item.source_card_id)
        player_targets = self._target_selections(
            item.effects, TargetMode.CHOSEN_PLAYER, state.turn_order
        )
        eligible_cards = tuple(
            card_id
            for player in state.players.values()
            for card_id in player.zones[Zone.BATTLEFIELD]
            if self._card_can_be_targeted(
                definition, card_id, item.ability_id is not None
            )
        )
        card_targets = self._target_selections(
            item.effects, TargetMode.CHOSEN_PERMANENT, eligible_cards
        )
        zone_targets = self._zone_target_selections(item.effects)
        allocations = self._allocation_selections(
            item.effects,
            definition,
            from_ability=item.ability_id is not None,
        )
        return [
            ChooseTriggeredTargets(
                player_id,
                item.item_id,
                selected_players,
                selected_cards,
                selected_zones,
                selected_allocations,
            )
            for (
                selected_players,
                selected_cards,
                selected_zones,
                selected_allocations,
            ) in islice(
                product(player_targets, card_targets, zone_targets, allocations),
                self.rules.legal_action_enumeration_limit,
            )
        ]

    def add_wounds(self, player_id: str, amount: int) -> None:
        if amount < 0:
            raise ValueError("Usa heal_wounds para curar")
        self._deal_wounds(player_id, amount)
        self._check_wound_limits()

    def heal_wounds(self, player_id: str, amount: int) -> None:
        if amount < 0:
            raise ValueError("La curación debe ser positiva")
        player = self._require_running_state().players[player_id]
        actual = min(player.wounds, amount)
        player.wounds -= actual
        self._emit("WOUNDS_HEALED", player_id, payload={"amount": actual})

    def _resolve_dynamic_cost(
        self, definition: DynamicCostDefinition, player_id: str
    ) -> CompositeCost:
        return resolve_dynamic_cost(
            definition, self._require_running_state(), player_id
        )

    @staticmethod
    def _resolve_x_cost(definition: XCostDefinition, x_value: int) -> CompositeCost:
        try:
            return resolve_x_cost(definition, x_value)
        except ValueError as exc:
            raise PaymentError(str(exc)) from exc

    def _card_cost_options(
        self, definition: CardDefinition, player_id: str
    ) -> tuple[tuple[int | None, int | None, CompositeCost], ...]:
        result: list[tuple[int | None, int | None, CompositeCost]] = []
        if definition.x_cost is not None:
            result.extend(
                (None, x_value, self._resolve_x_cost(definition.x_cost, x_value))
                for x_value in islice(
                    range(definition.x_cost.minimum, definition.x_cost.maximum + 1),
                    self.rules.legal_action_enumeration_limit,
                )
            )
        else:
            normal = (
                self._resolve_dynamic_cost(definition.dynamic_cost, player_id)
                if definition.dynamic_cost is not None
                else CompositeCost(steps=definition.cost)
            )
            result.append((None, None, normal))
        alternatives: list[CompositeCost] = [*definition.alternative_costs]
        alternatives.extend(
            self._resolve_dynamic_cost(item, player_id)
            for item in definition.dynamic_alternative_costs
        )
        result.extend((index, None, cost) for index, cost in enumerate(alternatives))
        first_x_index = len(alternatives)
        for offset, x_cost in enumerate(definition.x_alternative_costs):
            result.extend(
                (
                    first_x_index + offset,
                    x_value,
                    self._resolve_x_cost(x_cost, x_value),
                )
                for x_value in islice(
                    range(x_cost.minimum, x_cost.maximum + 1),
                    self.rules.legal_action_enumeration_limit,
                )
            )
        return tuple(result)

    def _card_cost_for_option(
        self,
        definition: CardDefinition,
        player_id: str,
        option: int | None,
        x_value: int | None,
    ) -> CompositeCost:
        if option is None:
            if definition.x_cost is not None:
                if x_value is None:
                    raise PaymentError("La carta necesita declarar un valor de X")
                return self._resolve_x_cost(definition.x_cost, x_value)
            if x_value is not None:
                raise PaymentError("El coste normal de la carta no utiliza X")
            return (
                self._resolve_dynamic_cost(definition.dynamic_cost, player_id)
                if definition.dynamic_cost is not None
                else CompositeCost(steps=definition.cost)
            )
        fixed_count = len(definition.alternative_costs)
        dynamic_count = len(definition.dynamic_alternative_costs)
        if 0 <= option < fixed_count:
            if x_value is not None:
                raise PaymentError("La alternativa elegida no utiliza X")
            return definition.alternative_costs[option]
        if fixed_count <= option < fixed_count + dynamic_count:
            if x_value is not None:
                raise PaymentError("La alternativa elegida no utiliza X")
            return self._resolve_dynamic_cost(
                definition.dynamic_alternative_costs[option - fixed_count], player_id
            )
        x_index = option - fixed_count - dynamic_count
        if 0 <= x_index < len(definition.x_alternative_costs):
            if x_value is None:
                raise PaymentError("La alternativa necesita declarar un valor de X")
            return self._resolve_x_cost(
                definition.x_alternative_costs[x_index], x_value
            )
        raise PaymentError("La opción de coste alternativo no existe")

    def _legal_plays(self, player_id: str) -> list[PlayCard]:
        state = self._require_running_state()
        player = state.players[player_id]
        result: list[PlayCard] = []
        for card_id in player.zones[Zone.HAND]:
            definition = self._definition(card_id)
            if not self._timing_allows_play(player_id, definition):
                continue
            player_targets = self._target_selections(
                definition.effects, TargetMode.CHOSEN_PLAYER, state.turn_order
            )
            eligible_cards = tuple(
                permanent_id
                for owner in state.players.values()
                for permanent_id in owner.zones[Zone.BATTLEFIELD]
                if self._card_can_be_targeted(definition, permanent_id)
            )
            card_targets = self._target_selections(
                definition.effects, TargetMode.CHOSEN_PERMANENT, eligible_cards
            )
            zone_targets = self._zone_target_selections(definition.effects)
            costs = self._card_cost_options(definition, player_id)
            for cost_index, x_value, cost in costs:
                allocation_targets = self._allocation_selections(
                    definition.effects, definition, x_value=x_value or 0
                )
                hand_pool = tuple(
                    candidate
                    for candidate in player.zones[Zone.HAND]
                    if candidate != card_id
                )
                if (
                    player.steps < cost.steps
                    or len(hand_pool) < cost.discard_count
                    or len(player.zones[Zone.BATTLEFIELD]) < cost.sacrifice_count
                    or len(player.zones[Zone.DECK]) < cost.mill_count
                ):
                    continue
                discard_choices = combinations(hand_pool, cost.discard_count)
                sacrifice_choices = combinations(
                    player.zones[Zone.BATTLEFIELD], cost.sacrifice_count
                )
                for (
                    selected_players,
                    selected_cards,
                    selected_zones,
                    allocations,
                    discarded,
                    sacrificed,
                ) in islice(
                    product(
                        player_targets,
                        card_targets,
                        zone_targets,
                        allocation_targets,
                        discard_choices,
                        sacrifice_choices,
                    ),
                    self.rules.legal_action_enumeration_limit,
                ):
                    result.append(
                        PlayCard(
                            player_id,
                            card_id,
                            selected_players,
                            selected_cards,
                            selected_zones,
                            allocations,
                            cost_index,
                            tuple(discarded),
                            tuple(sacrificed),
                            x_value,
                        )
                    )
        return result

    def _zone_target_selections(
        self, effects: tuple[EffectDefinition, ...]
    ) -> tuple[tuple[ZoneTarget, ...], ...]:
        state = self._require_state()
        candidates = tuple(
            ZoneTarget(player_id, zone)
            for player_id, player in state.players.items()
            for zone in player.zones
        )
        targeted = tuple(
            effect for effect in effects if effect.target is TargetMode.CHOSEN_ZONE
        )
        if not targeted:
            return ((),)
        minimum = max(effect.minimum_targets for effect in targeted)
        maximum = min(effect.maximum_targets for effect in targeted)
        return tuple(
            islice(
                (
                    tuple(selection)
                    for count in range(minimum, min(maximum, len(candidates)) + 1)
                    for selection in combinations(candidates, count)
                ),
                self.rules.legal_action_enumeration_limit,
            )
        )

    def _allocation_selections(
        self,
        effects: tuple[EffectDefinition, ...],
        source_definition: CardDefinition,
        *,
        from_ability: bool = False,
        x_value: int = 0,
    ) -> tuple[tuple[TargetAllocation, ...], ...]:
        state = self._require_state()
        effect = next((item for item in effects if item.distributed), None)
        if effect is None:
            return ((),)
        candidates = [*state.turn_order]
        candidates.extend(
            card_id
            for player in state.players.values()
            for card_id in player.zones[Zone.BATTLEFIELD]
            if self._card_can_be_targeted(source_definition, card_id, from_ability)
        )
        results: list[tuple[TargetAllocation, ...]] = []
        for count in range(effect.minimum_targets, min(effect.maximum_targets, len(candidates)) + 1):
            for selected in combinations(candidates, count):
                for amounts in self._positive_compositions(
                    self._effect_amount(effect, x_value), count
                ):
                    results.append(
                        tuple(
                            TargetAllocation(target_id, amount)
                            for target_id, amount in zip(selected, amounts, strict=True)
                        )
                    )
                    if len(results) >= self.rules.legal_action_enumeration_limit:
                        return tuple(results)
        return tuple(results)

    def _positive_compositions(
        self, total: int, parts: int
    ) -> Iterator[tuple[int, ...]]:
        if parts == 1:
            if total >= 1:
                yield (total,)
            return
        for first in range(1, total - parts + 2):
            for rest in self._positive_compositions(total - first, parts - 1):
                yield (first, *rest)

    @staticmethod
    def _effect_amount(effect: EffectDefinition, x_value: int) -> int:
        amount = effect.amount + effect.x_multiplier * x_value
        if effect.kind is not EffectKind.MODIFY_STRENGTH and amount < 0:
            raise IllegalAction("La magnitud calculada del efecto no puede ser negativa")
        return amount

    def _target_selections(
        self,
        effects: tuple[EffectDefinition, ...],
        mode: TargetMode,
        candidates: Iterable[str],
    ) -> tuple[tuple[str, ...], ...]:
        targeted = tuple(effect for effect in effects if effect.target is mode)
        if not targeted:
            return ((),)
        minimum = max(effect.minimum_targets for effect in targeted)
        maximum = min(effect.maximum_targets for effect in targeted)
        pool = tuple(candidates)
        maximum = min(maximum, len(pool))
        return tuple(
            islice(
                (
                    tuple(selection)
                    for count in range(minimum, maximum + 1)
                    for selection in combinations(pool, count)
                ),
                self.rules.legal_action_enumeration_limit,
            )
        )

    def _play_card(self, command: PlayCard) -> None:
        state = self._require_running_state()
        if command.player_id != state.priority_player_id:
            raise IllegalAction("El jugador no posee prioridad")
        player = state.players[command.player_id]
        if command.card_id not in player.zones[Zone.HAND]:
            raise IllegalAction("La carta debe encontrarse en la mano propia")
        instance = state.cards[command.card_id]
        definition = self._definition(command.card_id)
        if not self._timing_allows_play(command.player_id, definition):
            raise IllegalAction("La carta no puede jugarse en esta fase")
        self._validate_effect_targets(
            definition.effects,
            command.chosen_player_ids,
            command.chosen_card_ids,
            command.chosen_zone_targets,
            command.allocations,
            definition,
            x_value=command.x_value or 0,
        )
        cost = self._card_cost_for_option(
            definition,
            command.player_id,
            command.cost_option_index,
            command.x_value,
        )
        self._validate_card_play_cost(command, cost)
        player.steps -= cost.steps
        player.wounds += cost.wounds
        for discarded_id in command.discard_card_ids:
            self._move_card(
                discarded_id,
                Zone.DISCARD,
                state.cards[discarded_id].owner_id,
                reason=MoveReason.DISCARD,
            )
        for sacrificed_id in command.sacrifice_card_ids:
            self._move_card(
                sacrificed_id,
                Zone.DISCARD,
                state.cards[sacrificed_id].owner_id,
                reason=MoveReason.SACRIFICE,
            )
        for milled_id in tuple(player.zones[Zone.DECK][-cost.mill_count :]) if cost.mill_count else ():
            self._move_card(
                milled_id,
                Zone.DISCARD,
                command.player_id,
                reason=MoveReason.DISCARD,
            )
        self._move_card(command.card_id, Zone.RESOLUTION, command.player_id)
        destination = Zone.BATTLEFIELD if definition.permanent else Zone.DISCARD
        state.stack.append(
            StackItem(
                item_id=f"stack-{self._next_stack_item:06d}",
                controller_id=command.player_id,
                source_card_id=command.card_id,
                effects=definition.effects,
                chosen_player_ids=command.chosen_player_ids,
                chosen_card_ids=command.chosen_card_ids,
                chosen_zone_targets=command.chosen_zone_targets,
                allocations=command.allocations,
                x_value=command.x_value or 0,
                destination_on_resolve=destination,
            )
        )
        self._next_stack_item += 1
        state.phase_priority_complete = False
        state.consecutive_passes = 0
        state.priority_player_id = self._next_player(command.player_id)
        self._emit(
            "CARD_PLAYED",
            command.player_id,
            command.card_id,
            {
                "printed_cost": definition.cost,
                "paid_cost": {
                    "steps": cost.steps,
                    "wounds": cost.wounds,
                    "discard_count": cost.discard_count,
                    "sacrifice_count": cost.sacrifice_count,
                    "mill_count": cost.mill_count,
                },
                "cost_option_index": command.cost_option_index,
                "x_value": command.x_value,
                "stack_size": len(state.stack),
                "player_targets": command.chosen_player_ids,
                "card_targets": command.chosen_card_ids,
                "zone_targets": tuple(
                    (target.player_id, target.zone.name)
                    for target in command.chosen_zone_targets
                ),
                "allocations": tuple(
                    (allocation.target_id, allocation.amount)
                    for allocation in command.allocations
                ),
            },
        )

    def _validate_card_play_cost(
        self, command: PlayCard, cost: CompositeCost
    ) -> None:
        state = self._require_running_state()
        player = state.players[command.player_id]
        if player.steps < cost.steps:
            raise PaymentError("La Reserva no permite pagar el coste completo")
        if cost.strength or cost.exhaust_source:
            raise PaymentError("El coste de una carta en mano no puede usar la fuente")
        if len(command.discard_card_ids) != cost.discard_count or len(
            set(command.discard_card_ids)
        ) != len(command.discard_card_ids):
            raise PaymentError("El coste de descarte no coincide")
        if command.card_id in command.discard_card_ids or any(
            card_id not in player.zones[Zone.HAND]
            for card_id in command.discard_card_ids
        ):
            raise PaymentError("El coste solo puede descartar otras cartas de la mano")
        if len(command.sacrifice_card_ids) != cost.sacrifice_count or len(
            set(command.sacrifice_card_ids)
        ) != len(command.sacrifice_card_ids):
            raise PaymentError("El coste de sacrificio no coincide")
        if any(
            card_id not in player.zones[Zone.BATTLEFIELD]
            for card_id in command.sacrifice_card_ids
        ):
            raise PaymentError("El coste solo puede sacrificar permanentes propios")
        if len(player.zones[Zone.DECK]) < cost.mill_count:
            raise PaymentError("El mazo no contiene suficientes cartas para el coste")

    def _timing_allows_play(self, player_id: str, definition: CardDefinition) -> bool:
        state = self._require_running_state()
        if definition.kind is CardKind.QUICK_RESOURCE:
            return True
        return player_id == state.active_player_id and state.phase is Phase.EFFECTS

    def _validate_effect_targets(
        self,
        effects: tuple[EffectDefinition, ...],
        chosen_player_ids: tuple[str, ...],
        chosen_card_ids: tuple[str, ...],
        chosen_zone_targets: tuple[ZoneTarget, ...],
        allocations: tuple[TargetAllocation, ...],
        source_definition: CardDefinition,
        *,
        from_ability: bool = False,
        x_value: int = 0,
    ) -> None:
        state = self._require_running_state()
        player_effects = tuple(
            effect for effect in effects if effect.target is TargetMode.CHOSEN_PLAYER
        )
        if player_effects and not all(
            effect.minimum_targets <= len(chosen_player_ids) <= effect.maximum_targets
            for effect in player_effects
        ):
            raise IllegalAction("El número de jugadores objetivo no es válido")
        if not player_effects and chosen_player_ids:
            raise IllegalAction("La carta no requiere jugador objetivo")
        if len(chosen_player_ids) != len(set(chosen_player_ids)):
            raise IllegalAction("Un jugador objetivo no puede repetirse")
        if any(player_id not in state.players for player_id in chosen_player_ids):
            raise IllegalAction("Jugador objetivo inexistente")
        card_effects = tuple(
            effect for effect in effects if effect.target is TargetMode.CHOSEN_PERMANENT
        )
        if card_effects and not all(
            effect.minimum_targets <= len(chosen_card_ids) <= effect.maximum_targets
            for effect in card_effects
        ):
            raise IllegalAction("El número de permanentes objetivo no es válido")
        if not card_effects and chosen_card_ids:
            raise IllegalAction("El efecto no requiere permanente objetivo")
        if len(chosen_card_ids) != len(set(chosen_card_ids)):
            raise IllegalAction("Un permanente objetivo no puede repetirse")
        for card_id in chosen_card_ids:
            if card_id not in state.cards or state.cards[card_id].zone is not Zone.BATTLEFIELD:
                raise IllegalAction("Permanente objetivo inexistente")
            if not self._card_can_be_targeted(source_definition, card_id, from_ability):
                raise IllegalAction("El permanente es inmune a esta fuente")
        zone_effects = tuple(
            effect for effect in effects if effect.target is TargetMode.CHOSEN_ZONE
        )
        if zone_effects and not all(
            effect.minimum_targets <= len(chosen_zone_targets) <= effect.maximum_targets
            for effect in zone_effects
        ):
            raise IllegalAction("El número de zonas objetivo no es válido")
        if not zone_effects and chosen_zone_targets:
            raise IllegalAction("El efecto no requiere una zona objetivo")
        if len(chosen_zone_targets) != len(set(chosen_zone_targets)):
            raise IllegalAction("Una zona objetivo no puede repetirse")
        if any(
            target.player_id not in state.players
            or target.zone not in state.players[target.player_id].zones
            for target in chosen_zone_targets
        ):
            raise IllegalAction("Zona objetivo inexistente")
        distributed = tuple(effect for effect in effects if effect.distributed)
        if not distributed and allocations:
            raise IllegalAction("El efecto no requiere reparto")
        if distributed:
            effect = distributed[0]
            target_ids = tuple(allocation.target_id for allocation in allocations)
            if len(target_ids) != len(set(target_ids)):
                raise IllegalAction("Un objetivo de reparto no puede repetirse")
            if not effect.minimum_targets <= len(allocations) <= effect.maximum_targets:
                raise IllegalAction("El número de objetivos del reparto no es válido")
            if sum(allocation.amount for allocation in allocations) != self._effect_amount(
                effect, x_value
            ):
                raise IllegalAction("La suma del reparto no coincide con el efecto")
            for target_id in target_ids:
                if target_id in state.players:
                    continue
                if target_id not in state.cards or state.cards[target_id].zone is not Zone.BATTLEFIELD:
                    raise IllegalAction("Objetivo de reparto inexistente")
                if not self._card_can_be_targeted(source_definition, target_id, from_ability):
                    raise IllegalAction("Un objetivo del reparto es inmune a esta fuente")

    def _card_can_be_targeted(
        self,
        source: CardDefinition,
        target_card_id: str,
        from_ability: bool = False,
    ) -> bool:
        state = self._require_state()
        target = self._definition(target_card_id)
        keywords = self._effective_keywords(target_card_id)
        if target.rank is CardRank.DIVINE and (
            from_ability or source.kind in {CardKind.EVENT, CardKind.QUICK_RESOURCE}
        ):
            return False
        if "IMMUNE_ABILITIES" in keywords and from_ability:
            return False
        if "IMMUNE_QUICK" in keywords and source.kind is CardKind.QUICK_RESOURCE:
            return False
        if "IMMUNE_EVENT" in keywords and source.kind is CardKind.EVENT:
            return False
        return True

    def _legal_ability_activations(
        self, player_id: str, source_card_id: str
    ) -> list[ActivateAbility]:
        state = self._require_running_state()
        player = state.players[player_id]
        source = state.cards[source_card_id]
        definition = self._definition(source_card_id)
        result: list[ActivateAbility] = []
        for ability in definition.abilities:
            if ability.trigger is not None:
                continue
            if ability.allowed_phases and state.phase not in ability.allowed_phases:
                continue
            if ability.once_per_turn and ability.ability_id in source.activated_this_turn:
                continue
            cost_options = (
                tuple(
                    (x, self._resolve_x_cost(ability.x_cost, x))
                    for x in islice(
                        range(ability.x_cost.minimum, ability.x_cost.maximum + 1),
                        self.rules.legal_action_enumeration_limit,
                    )
                )
                if ability.x_cost is not None
                else ((
                    None,
                    self._resolve_dynamic_cost(ability.dynamic_cost, player_id)
                    if ability.dynamic_cost is not None
                    else ability.cost,
                ),)
            )
            for x_value, cost in cost_options:
                if (
                    cost.steps > player.steps
                    or cost.strength > self._current_strength(source_card_id)
                    or cost.mill_count > len(player.zones[Zone.DECK])
                    or (cost.exhaust_source and source.exhausted)
                ):
                    continue
                hand_choices = tuple(
                    combinations(player.zones[Zone.HAND], cost.discard_count)
                )
                sacrifice_pool = tuple(
                    card_id
                    for card_id in player.zones[Zone.BATTLEFIELD]
                    if not (cost.exhaust_source and card_id == source_card_id)
                )
                sacrifice_choices = tuple(
                    combinations(sacrifice_pool, cost.sacrifice_count)
                )
                player_targets = self._target_selections(
                    ability.effects, TargetMode.CHOSEN_PLAYER, state.turn_order
                )
                eligible_cards = tuple(
                    card_id
                    for owner in state.players.values()
                    for card_id in owner.zones[Zone.BATTLEFIELD]
                    if self._card_can_be_targeted(definition, card_id, True)
                )
                card_targets = self._target_selections(
                    ability.effects, TargetMode.CHOSEN_PERMANENT, eligible_cards
                )
                zone_targets = self._zone_target_selections(ability.effects)
                allocation_targets = self._allocation_selections(
                    ability.effects,
                    definition,
                    from_ability=True,
                    x_value=x_value or 0,
                )
                for (
                    discarded,
                    sacrificed,
                    selected_players,
                    selected_cards,
                    selected_zones,
                    allocations,
                ) in islice(
                    product(
                        hand_choices,
                        sacrifice_choices,
                        player_targets,
                        card_targets,
                        zone_targets,
                        allocation_targets,
                    ),
                    self.rules.legal_action_enumeration_limit,
                ):
                    result.append(
                        ActivateAbility(
                            player_id,
                            source_card_id,
                            ability.ability_id,
                            selected_players,
                            selected_cards,
                            tuple(discarded),
                            tuple(sacrificed),
                            selected_zones,
                            allocations,
                            x_value,
                        )
                    )
        return result

    def _activate_ability(self, command: ActivateAbility) -> None:
        state = self._require_running_state()
        if command.player_id != state.priority_player_id:
            raise IllegalAction("El jugador no posee prioridad")
        player = state.players[command.player_id]
        if command.source_card_id not in player.zones[Zone.BATTLEFIELD]:
            raise IllegalAction("La fuente debe ser un permanente bajo control propio")
        source = state.cards[command.source_card_id]
        definition = self._definition(command.source_card_id)
        ability = next(
            (item for item in definition.abilities if item.ability_id == command.ability_id),
            None,
        )
        if ability is None or ability.trigger is not None:
            raise IllegalAction("Habilidad activada inexistente")
        if ability.allowed_phases and state.phase not in ability.allowed_phases:
            raise IllegalAction("La habilidad no puede activarse en esta fase")
        if ability.once_per_turn and ability.ability_id in source.activated_this_turn:
            raise IllegalAction("La habilidad ya se activó este turno")
        self._validate_effect_targets(
            ability.effects,
            command.chosen_player_ids,
            command.chosen_card_ids,
            command.chosen_zone_targets,
            command.allocations,
            definition,
            from_ability=True,
            x_value=command.x_value or 0,
        )
        if ability.x_cost is not None:
            if command.x_value is None:
                raise PaymentError("La habilidad necesita declarar un valor de X")
            cost = self._resolve_x_cost(ability.x_cost, command.x_value)
        else:
            if command.x_value is not None:
                raise PaymentError("La habilidad no posee un coste X")
            cost = (
                self._resolve_dynamic_cost(ability.dynamic_cost, command.player_id)
                if ability.dynamic_cost is not None
                else ability.cost
            )
        if player.steps < cost.steps:
            raise PaymentError("La Reserva no permite pagar el coste completo")
        if cost.strength > self._current_strength(command.source_card_id):
            raise PaymentError("La fuente no posee Fuerza suficiente")
        if cost.exhaust_source and source.exhausted:
            raise PaymentError("La fuente ya está agotada")
        if len(player.zones[Zone.DECK]) < cost.mill_count:
            raise PaymentError("El mazo no contiene suficientes cartas para el coste")
        if len(command.discard_card_ids) != cost.discard_count or len(
            set(command.discard_card_ids)
        ) != len(command.discard_card_ids):
            raise PaymentError("El coste de descarte no coincide")
        if any(card_id not in player.zones[Zone.HAND] for card_id in command.discard_card_ids):
            raise PaymentError("Solo pueden descartarse cartas de la mano propia")
        if len(command.sacrifice_card_ids) != cost.sacrifice_count or len(
            set(command.sacrifice_card_ids)
        ) != len(command.sacrifice_card_ids):
            raise PaymentError("El coste de sacrificio no coincide")
        if any(
            card_id not in player.zones[Zone.BATTLEFIELD]
            for card_id in command.sacrifice_card_ids
        ):
            raise PaymentError("Solo pueden sacrificarse permanentes propios")
        if cost.exhaust_source and command.source_card_id in command.sacrifice_card_ids:
            raise PaymentError("La fuente no puede agotarse y sacrificarse a la vez")

        player.steps -= cost.steps
        player.wounds += cost.wounds
        source.strength_modifier -= cost.strength
        if cost.exhaust_source:
            source.exhausted = True
        for card_id in command.discard_card_ids:
            self._move_card(
                card_id,
                Zone.DISCARD,
                state.cards[card_id].owner_id,
                reason=MoveReason.DISCARD,
            )
        for card_id in command.sacrifice_card_ids:
            self._move_card(
                card_id,
                Zone.DISCARD,
                state.cards[card_id].owner_id,
                reason=MoveReason.SACRIFICE,
            )
        for card_id in tuple(player.zones[Zone.DECK][-cost.mill_count :]) if cost.mill_count else ():
            self._move_card(
                card_id,
                Zone.DISCARD,
                command.player_id,
                reason=MoveReason.DISCARD,
            )
        if ability.once_per_turn:
            source.activated_this_turn.add(ability.ability_id)
        state.stack.append(
            StackItem(
                item_id=f"stack-{self._next_stack_item:06d}",
                controller_id=command.player_id,
                source_card_id=command.source_card_id,
                effects=ability.effects,
                chosen_player_ids=command.chosen_player_ids,
                chosen_card_ids=command.chosen_card_ids,
                chosen_zone_targets=command.chosen_zone_targets,
                allocations=command.allocations,
                ability_id=ability.ability_id,
                x_value=command.x_value or 0,
            )
        )
        self._next_stack_item += 1
        state.phase_priority_complete = False
        state.consecutive_passes = 0
        state.priority_player_id = self._next_player(command.player_id)
        self._emit(
            "ABILITY_ACTIVATED",
            command.player_id,
            command.source_card_id,
            {
                "ability_id": ability.ability_id,
                "x_value": command.x_value,
                "paid_cost": {
                    "steps": cost.steps,
                    "wounds": cost.wounds,
                    "discard_count": cost.discard_count,
                    "sacrifice_count": cost.sacrifice_count,
                    "strength": cost.strength,
                    "mill_count": cost.mill_count,
                },
                "player_targets": command.chosen_player_ids,
                "card_targets": command.chosen_card_ids,
                "zone_targets": tuple(
                    (target.player_id, target.zone.name)
                    for target in command.chosen_zone_targets
                ),
                "allocations": tuple(
                    (allocation.target_id, allocation.amount)
                    for allocation in command.allocations
                ),
            },
        )
        self._run_state_based_actions()

    def _equip_card(self, command: EquipCard) -> None:
        state = self._require_running_state()
        if command.player_id != state.priority_player_id:
            raise IllegalAction("El jugador no posee prioridad")
        if command.player_id != state.active_player_id or state.phase is not Phase.EFFECTS:
            raise IllegalAction("Equipar solo está permitido en la Fase de Efectos propia")
        if state.stack:
            raise IllegalAction("La pila debe estar vacía para equipar")
        player = state.players[command.player_id]
        if (
            command.equipment_id not in player.zones[Zone.BATTLEFIELD]
            or command.creature_id not in player.zones[Zone.BATTLEFIELD]
        ):
            raise IllegalAction("Equipo y criatura deben estar en el campo propio")
        equipment = state.cards[command.equipment_id]
        equipment_definition = self._definition(command.equipment_id)
        if equipment_definition.kind is not CardKind.EQUIPMENT or not self._is_creature(
            command.creature_id
        ):
            raise IllegalAction("La asignación de Equipo no es válida")
        if player.steps < equipment_definition.cost:
            raise PaymentError("La Reserva no permite pagar el coste de equipar")
        player.steps -= equipment_definition.cost
        equipment.attached_to = command.creature_id
        state.phase_priority_complete = False
        state.consecutive_passes = 0
        state.priority_player_id = self._next_player(command.player_id)
        self._emit("EQUIPMENT_ATTACHED", command.player_id, command.equipment_id,
                   {"creature_id": command.creature_id, "cost": equipment_definition.cost})

    def _drain_steps(self, command: DrainSteps) -> None:
        state = self._require_running_state()
        if command.player_id != state.priority_player_id:
            raise IllegalAction("El jugador no posee prioridad")
        if command.player_id != state.active_player_id:
            raise IllegalAction("Drenaje solo puede usarse durante la Fase Activa propia")
        player = state.players[command.player_id]
        if player.drainage_used_turn_serial == state.turn_serial:
            raise IllegalAction("Drenaje ya se utilizó este turno")
        if not 1 <= command.amount <= 5:
            raise IllegalAction("Drenaje permite recuperar entre uno y cinco Pasos")
        wounds = (command.amount - 1) * 3
        player.steps += command.amount
        player.wounds += wounds
        player.drainage_used_turn_serial = state.turn_serial
        state.phase_priority_complete = False
        state.consecutive_passes = 0
        state.priority_player_id = self._next_player(command.player_id)
        self._emit(
            "DRAINAGE_USED",
            command.player_id,
            payload={"steps_gained": command.amount, "wounds_paid": wounds},
        )

    def _order_triggered_abilities(self, command: OrderTriggeredAbilities) -> None:
        state = self._require_running_state()
        if command.player_id != state.priority_player_id or not state.pending_triggers:
            raise IllegalAction("No hay disparos propios pendientes de ordenar")
        if any(not item.targets_locked for item in state.pending_triggers):
            raise IllegalAction("Todos los disparos deben tener objetivos antes de ordenarse")
        pending_ids = tuple(item.item_id for item in state.pending_triggers)
        if len(command.resolution_order) != len(set(command.resolution_order)) or set(
            command.resolution_order
        ) != set(pending_ids):
            raise IllegalAction("El orden debe contener cada disparo exactamente una vez")
        by_id = {item.item_id: item for item in state.pending_triggers}
        for item_id in reversed(command.resolution_order):
            state.stack.append(by_id[item_id])
        state.pending_triggers.clear()
        state.consecutive_passes = 0
        state.phase_priority_complete = False
        state.priority_player_id = self._next_player(command.player_id)
        self._emit(
            "TRIGGERS_ORDERED",
            command.player_id,
            payload={"resolution_order": command.resolution_order},
        )

    def _choose_triggered_targets(self, command: ChooseTriggeredTargets) -> None:
        state = self._require_running_state()
        if command.player_id != state.priority_player_id:
            raise IllegalAction("El jugador no controla los disparos pendientes")
        index = next(
            (
                position
                for position, item in enumerate(state.pending_triggers)
                if item.item_id == command.item_id
            ),
            None,
        )
        if index is None or state.pending_triggers[index].targets_locked:
            raise IllegalAction("El disparo no necesita elegir objetivos")
        item = state.pending_triggers[index]
        definition = self._definition(item.source_card_id)
        self._validate_effect_targets(
            item.effects,
            command.chosen_player_ids,
            command.chosen_card_ids,
            command.chosen_zone_targets,
            command.allocations,
            definition,
            from_ability=item.ability_id is not None,
        )
        state.pending_triggers[index] = replace(
            item,
            chosen_player_ids=command.chosen_player_ids,
            chosen_card_ids=command.chosen_card_ids,
            chosen_zone_targets=command.chosen_zone_targets,
            allocations=command.allocations,
            targets_locked=True,
        )
        self._emit(
            "TRIGGER_TARGETS_CHOSEN",
            command.player_id,
            item.source_card_id,
            {
                "item_id": item.item_id,
                "player_targets": command.chosen_player_ids,
                "card_targets": command.chosen_card_ids,
                "zone_targets": tuple(
                    (target.player_id, target.zone.name)
                    for target in command.chosen_zone_targets
                ),
                "allocations": tuple(
                    (allocation.target_id, allocation.amount)
                    for allocation in command.allocations
                ),
            },
        )

    def _pass_priority(self, player_id: str) -> None:
        return self._stack._pass_priority(player_id)

    def _resolve_top_stack(self) -> None:
        return self._stack._resolve_top_stack()

    def _continue_stack_resolution(self, item: StackItem, start_index: int) -> None:
        return self._stack._continue_stack_resolution(item, start_index)

    def _resolve_search_choice(self, command: ResolveSearchChoice) -> None:
        return self._stack._resolve_search_choice(command)

    def _shuffle_zone(self, target: ZoneTarget) -> None:
        return self._stack._shuffle_zone(target)

    def _apply_effect(
        self,
        effect: EffectDefinition,
        item: StackItem,
        selected_target_id: str | ZoneTarget | TargetAllocation | None = None,
    ) -> None:
        return self._effects.apply(effect, item, selected_target_id)
    def _deal_wounds(self, player_id: str, amount: int, source_card_id: str | None = None) -> None:
        player = self._require_running_state().players[player_id]
        prevented = min(player.wound_prevention, amount)
        player.wound_prevention -= prevented
        dealt = amount - prevented
        player.wounds += dealt
        if prevented:
            self._emit("WOUNDS_PREVENTED", player_id, source_card_id, {"amount": prevented})
        if dealt:
            self._emit("WOUNDS_ADDED", player_id, source_card_id, {"amount": dealt})

    def _deal_damage(
        self,
        card_id: str,
        amount: int,
        source_card_id: str | None = None,
        *,
        allows_regeneration: bool = True,
    ) -> None:
        instance = self._require_running_state().cards[card_id]
        prevented = min(instance.damage_prevention, amount)
        instance.damage_prevention -= prevented
        dealt = amount - prevented
        instance.damage += dealt
        if dealt and not allows_regeneration:
            instance.regeneration_blocked_until_state_check = True
        if prevented:
            self._emit("DAMAGE_PREVENTED", card_id=card_id, payload={"amount": prevented})
        if dealt:
            self._emit("DAMAGE_DEALT", card_id=card_id,
                       payload={"amount": dealt, "source": source_card_id})

    def _destroy_permanent(
        self,
        card_id: str,
        reason: MoveReason,
        *,
        allows_regeneration: bool = True,
    ) -> bool:
        state = self._require_running_state()
        instance = state.cards[card_id]
        if "INDESTRUCTIBLE" in self._effective_keywords(card_id):
            self._emit("DESTRUCTION_PREVENTED", card_id=card_id)
            return False
        if allows_regeneration and instance.regeneration_shields > 0:
            instance.regeneration_shields -= 1
            instance.damage = 0
            instance.exhausted = True
            self._emit("PERMANENT_REGENERATED", card_id=card_id)
            return False
        destination = self._move_card(
            card_id,
            Zone.DISCARD,
            instance.owner_id,
            reason=reason,
        )
        if destination is Zone.DISCARD:
            self._emit("PERMANENT_DESTROYED", card_id=card_id)
            return True
        self._emit(
            "DESTRUCTION_REPLACED",
            card_id=card_id,
            payload={"destination": destination.name},
        )
        return False

    def _advance_phase(self, player_id: str) -> None:
        state = self._require_running_state()
        if player_id != state.active_player_id:
            raise IllegalAction("Solo el jugador activo puede avanzar la fase")
        if state.stack or not state.phase_priority_complete:
            raise IllegalAction("La ventana de prioridad debe estar cerrada")
        if state.phase is Phase.COMBAT and state.combat and not state.combat.resolved:
            raise IllegalAction("El combate declarado debe resolverse")
        if state.phase is Phase.DISCARD:
            if len(state.players[player_id].zones[Zone.HAND]) > self.rules.hand_limit:
                raise IllegalAction("Debe descartarse hasta el límite de mano")
            self._finish_turn()
            self._enter_phase_or_skip(Phase.DRAW)
            return
        index = self.rules.phase_sequence.index(state.phase)
        self._enter_phase_or_skip(self.rules.phase_sequence[index + 1])

    def _finish_turn(self) -> None:
        state = self._require_running_state()
        self._cleanup_end_of_turn()
        state.turn_serial += 1
        state.active_player_index = (state.active_player_index + 1) % len(
            state.turn_order
        )
        if state.active_player_index == 0:
            state.turn_number += 1

    def _enter_phase_or_skip(self, phase: Phase) -> None:
        state = self._require_running_state()
        skipped = 0
        while self._phase_is_suppressed(state.active_player_id, phase):
            self._emit(
                "PHASE_SKIPPED",
                state.active_player_id,
                payload={"phase": phase.name},
            )
            skipped += 1
            if skipped > len(self.rules.phase_sequence) * len(state.turn_order):
                state.status = MatchStatus.BLOCKED
                self._emit("ALL_PHASES_SUPPRESSED")
                return
            if phase is Phase.DISCARD:
                self._finish_turn()
                phase = Phase.DRAW
            else:
                index = self.rules.phase_sequence.index(phase)
                phase = self.rules.phase_sequence[index + 1]
        self._enter_phase(phase)

    def _phase_is_suppressed(self, player_id: str, phase: Phase) -> bool:
        state = self._require_running_state()
        continuous = False
        for source in state.cards.values():
            if source.zone is not Zone.BATTLEFIELD:
                continue
            definition = self._definition(source.instance_id)
            for effect in definition.continuous_effects:
                if phase not in effect.suppressed_phases:
                    continue
                if (
                    effect.controller_scope is ControllerScope.SELF
                    and player_id != source.controller_id
                ):
                    continue
                if (
                    effect.controller_scope is ControllerScope.OPPONENTS
                    and player_id == source.controller_id
                ):
                    continue
                continuous = True
        matching = [
            suppression
            for suppression in state.phase_suppressions
            if suppression.player_id == player_id and suppression.phase is phase
        ]
        for suppression in matching:
            if suppression.remaining_occurrences is not None:
                suppression.remaining_occurrences -= 1
        state.phase_suppressions = [
            suppression
            for suppression in state.phase_suppressions
            if suppression.remaining_occurrences != 0
        ]
        return continuous or bool(matching)

    def _enter_phase(self, phase: Phase) -> None:
        state = self._require_state()
        state.phase = phase
        state.priority_player_id = state.active_player_id
        state.consecutive_passes = 0
        state.phase_priority_complete = False
        state.combat = None
        self._emit("PHASE_STARTED", state.active_player_id, payload={"phase": phase.name})
        if phase is Phase.DRAW:
            self._draw(state.active_player_id, 1)
        elif phase is Phase.MAINTENANCE:
            player = state.players[state.active_player_id]
            for card_id in player.zones[Zone.BATTLEFIELD]:
                state.cards[card_id].exhausted = False
            player.steps += self.rules.steps_per_maintenance
            self._emit(
                "STEPS_GAINED",
                state.active_player_id,
                payload={"amount": self.rules.steps_per_maintenance},
            )
        elif phase is Phase.LEGENDARY:
            self._queue_legendary_effects()

    def _cleanup_end_of_turn(self) -> None:
        state = self._require_running_state()
        state.timed_modifiers = [
            modifier
            for modifier in state.timed_modifiers
            if modifier.expires_at_turn_serial > state.turn_serial
        ]
        state.phase_suppressions = [
            suppression
            for suppression in state.phase_suppressions
            if suppression.expires_at_turn_serial is None
            or suppression.expires_at_turn_serial > state.turn_serial
        ]
        expiring_control = tuple(
            change
            for change in state.control_changes
            if change.expires_at_turn_serial <= state.turn_serial
        )
        for change in reversed(expiring_control):
            if state.cards[change.card_id].zone is Zone.BATTLEFIELD:
                self._set_controller(change.card_id, change.previous_controller_id)
                self._emit(
                    "CONTROL_RESTORED",
                    change.previous_controller_id,
                    change.card_id,
                )
        state.control_changes = [
            change
            for change in state.control_changes
            if change.expires_at_turn_serial > state.turn_serial
        ]
        state.text_patches = [
            patch
            for patch in state.text_patches
            if patch.expires_at_turn_serial is None
            or patch.expires_at_turn_serial > state.turn_serial
        ]
        for player in state.players.values():
            player.wound_prevention = 0
        for instance in state.cards.values():
            instance.damage_prevention = 0
            instance.damage = 0
            instance.activated_this_turn.clear()
            if instance.creature_form_expires_turn_serial == state.turn_serial:
                instance.transformed_as_creature = False
                instance.creature_form_expires_turn_serial = None
            if instance.definition_override_expires_turn_serial == state.turn_serial:
                instance.overridden_definition_id = None
                instance.definition_override_expires_turn_serial = None
        self._emit("END_OF_TURN_CLEANUP", state.active_player_id)

    def _set_controller(self, card_id: str, controller_id: str) -> None:
        state = self._require_running_state()
        if controller_id not in state.players:
            raise IllegalAction("Controlador inexistente")
        instance = state.cards[card_id]
        if instance.zone is not Zone.BATTLEFIELD:
            raise IllegalAction("Solo puede cambiarse el control de un permanente")
        for player in state.players.values():
            if card_id in player.zones[Zone.BATTLEFIELD]:
                player.zones[Zone.BATTLEFIELD].remove(card_id)
                break
        state.players[controller_id].zones[Zone.BATTLEFIELD].append(card_id)
        instance.controller_id = controller_id

    def _queue_legendary_effects(self) -> None:
        state = self._require_running_state()
        player = state.players[state.active_player_id]
        items: list[StackItem] = []
        for card_id in player.zones[Zone.BATTLEFIELD]:
            definition = self._definition(card_id)
            if definition.rank is CardRank.LEGENDARY and definition.legendary_effects:
                items.append(
                    StackItem(
                        item_id=f"stack-{self._next_stack_item:06d}",
                        controller_id=state.active_player_id,
                        source_card_id=card_id,
                        effects=definition.legendary_effects,
                        targets_locked=not self._effects_need_choices(
                            definition.legendary_effects
                        ),
                    )
                )
                self._next_stack_item += 1
                self._emit("LEGENDARY_EFFECT_QUEUED", state.active_player_id, card_id)
        self._queue_trigger_batch(items, state.active_player_id)

    def _queue_triggered_abilities(self, source_card_id: str, trigger: TriggerKind) -> None:
        state = self._require_running_state()
        instance = state.cards[source_card_id]
        definition = self._definition(source_card_id)
        items: list[StackItem] = []
        for ability in definition.abilities:
            if ability.trigger is not trigger:
                continue
            items.append(
                StackItem(
                    item_id=f"stack-{self._next_stack_item:06d}",
                    controller_id=instance.controller_id,
                    source_card_id=source_card_id,
                    effects=ability.effects,
                    ability_id=ability.ability_id,
                    targets_locked=not self._effects_need_choices(ability.effects),
                )
            )
            self._next_stack_item += 1
            self._emit(
                "TRIGGERED_ABILITY_QUEUED",
                instance.controller_id,
                source_card_id,
                {"ability_id": ability.ability_id, "trigger": trigger.name},
            )
        self._queue_trigger_batch(items, instance.controller_id)

    def _queue_trigger_batch(self, items: list[StackItem], controller_id: str) -> None:
        state = self._require_running_state()
        viable: list[StackItem] = []
        for item in items:
            if item.targets_locked or self._trigger_target_commands(controller_id, item):
                viable.append(item)
            else:
                self._emit(
                    "TRIGGER_FIZZLED",
                    controller_id,
                    item.source_card_id,
                    {"item_id": item.item_id, "reason": "no_legal_targets"},
                )
        if not viable:
            return
        if len(viable) == 1 and viable[0].targets_locked:
            state.stack.append(viable[0])
            return
        if state.pending_triggers:
            raise InvariantViolation("Ya existe otro lote de disparos pendiente")
        state.pending_triggers.extend(viable)
        state.priority_player_id = controller_id
        state.phase_priority_complete = False
        state.consecutive_passes = 0
        self._emit(
            "SIMULTANEOUS_TRIGGERS_AWAITING_ORDER",
            controller_id,
            payload={"item_ids": tuple(item.item_id for item in viable)},
        )

    def _effects_need_choices(self, effects: tuple[EffectDefinition, ...]) -> bool:
        return any(
            effect.target
            in {
                TargetMode.CHOSEN_PLAYER,
                TargetMode.CHOSEN_PERMANENT,
                TargetMode.CHOSEN_ZONE,
                TargetMode.CHOSEN_ENTITY,
            }
            for effect in effects
        )

    def _discard_cards(self, command: DiscardCards) -> None:
        state = self._require_running_state()
        if command.player_id != state.active_player_id or state.phase is not Phase.DISCARD:
            raise IllegalAction("El descarte de ajuste solo se realiza en la Fase de Descarte")
        player = state.players[command.player_id]
        if len(set(command.card_ids)) != len(command.card_ids):
            raise IllegalAction("Una carta no puede descartarse dos veces")
        if any(card_id not in player.zones[Zone.HAND] for card_id in command.card_ids):
            raise IllegalAction("Solo pueden descartarse cartas de la mano propia")
        required = max(0, len(player.zones[Zone.HAND]) - self.rules.hand_limit)
        if len(command.card_ids) != required:
            raise IllegalAction(f"Deben descartarse exactamente {required} cartas")
        for card_id in command.card_ids:
            self._move_card(
                card_id,
                Zone.DISCARD,
                command.player_id,
                reason=MoveReason.DISCARD,
            )
        self._emit("HAND_ADJUSTED", command.player_id, payload={"count": required})

    def _transmute(self, command: TransmutePermanent) -> None:
        state = self._require_running_state()
        if command.player_id != state.priority_player_id:
            raise IllegalAction("El jugador no posee prioridad")
        player = state.players[command.player_id]
        if command.card_id not in player.zones[Zone.BATTLEFIELD]:
            raise IllegalAction("Solo puede transmutarse un permanente bajo control propio")
        definition = self._definition(command.card_id)
        if not definition.transmutable:
            raise IllegalAction("Este permanente no puede ser transmutado")
        controller_id = state.cards[command.card_id].controller_id
        self._move_card(
            command.card_id,
            Zone.DISCARD,
            state.cards[command.card_id].owner_id,
            reason=MoveReason.TRANSMUTE,
        )
        player.steps += definition.cost
        state.phase_priority_complete = False
        self._emit(
            "CARD_TRANSMUTED",
            command.player_id,
            command.card_id,
            {"steps_gained": definition.cost},
        )
        state.cards[command.card_id].controller_id = controller_id
        self._queue_triggered_abilities(command.card_id, TriggerKind.ON_TRANSMUTED)
        state.cards[command.card_id].controller_id = state.cards[command.card_id].owner_id

    def _declare_challenge(self, command: DeclareChallenge) -> None:
        return self._combat._declare_challenge(command)

    def _declare_attackers(self, command: DeclareAttackers) -> None:
        return self._combat._declare_attackers(command)

    def _declare_blockers(self, command: DeclareBlockers) -> None:
        return self._combat._declare_blockers(command)

    def _resolve_combat(self, player_id: str) -> None:
        return self._combat._resolve_combat(player_id)

    def _is_ready_creature(self, card_id: str) -> bool:
        state = self._require_state()
        instance = state.cards[card_id]
        return (
            instance.zone is Zone.BATTLEFIELD
            and self._is_creature(card_id)
            and not instance.exhausted
        )

    def _is_creature(self, card_id: str) -> bool:
        state = self._require_state()
        instance = state.cards[card_id]
        definition = self._definition(card_id)
        return definition.kind is CardKind.CREATURE or instance.transformed_as_creature

    def _is_lord_creature(self, card_id: str) -> bool:
        state = self._require_state()
        definition = self._definition(card_id)
        return definition.lord_domain is not None and self._is_creature(card_id)

    def _current_strength(self, card_id: str) -> int:
        state = self._require_state()
        instance = state.cards[card_id]
        definition = self._definition(card_id)
        base_strength = (
            definition.base_strength
            if definition.base_strength is not None
            else definition.cost if definition.lord_domain is not None else 0
        )
        continuous = sum(
            effect.strength_delta
            for source_id, effect in self._continuous_effects_for(card_id)
        )
        timed = sum(
            modifier.strength_delta
            for modifier in state.timed_modifiers
            if modifier.target_card_id == card_id
        )
        equipment = sum(
            self._definition(other.instance_id).equipment_strength_bonus
            for other in state.cards.values()
            if other.zone is Zone.BATTLEFIELD and other.attached_to == card_id
        )
        return max(
            0,
            base_strength
            + instance.strength_modifier
            + continuous
            + timed
            + equipment,
        )

    def _continuous_effects_for(
        self, target_card_id: str
    ) -> Iterator[tuple[str, ContinuousEffectDefinition]]:
        state = self._require_state()
        target = state.cards[target_card_id]
        target_definition = self._definition(target_card_id)
        for source_id, source in state.cards.items():
            if source.zone is not Zone.BATTLEFIELD:
                continue
            source_definition = self._definition(source_id)
            for effect in source_definition.continuous_effects:
                if effect.excludes_source and source_id == target_card_id:
                    continue
                if (
                    effect.controller_scope is ControllerScope.SELF
                    and target.controller_id != source.controller_id
                ):
                    continue
                if (
                    effect.controller_scope is ControllerScope.OPPONENTS
                    and target.controller_id == source.controller_id
                ):
                    continue
                if effect.affected_kinds:
                    kind_matches = target_definition.kind in effect.affected_kinds
                    if CardKind.CREATURE in effect.affected_kinds and self._is_creature(
                        target_card_id
                    ):
                        kind_matches = True
                    if not kind_matches:
                        continue
                if effect.affected_subtypes and not (
                    effect.affected_subtypes & target_definition.subtypes
                ):
                    continue
                yield source_id, effect

    def _effective_keywords(self, card_id: str) -> frozenset[str]:
        state = self._require_state()
        instance = state.cards[card_id]
        definition = self._definition(card_id)
        keywords = set(definition.keywords)
        for _, effect in self._continuous_effects_for(card_id):
            keywords.update(effect.grant_keywords)
            keywords.difference_update(effect.remove_keywords)
        for equipment in state.cards.values():
            if equipment.zone is Zone.BATTLEFIELD and equipment.attached_to == card_id:
                keywords.update(
                    self._definition(equipment.instance_id).equipment_granted_keywords
                )
        return frozenset(keywords)

    def _run_state_based_actions(self) -> None:
        state = self._require_running_state()
        while True:
            destroyed: list[str] = []
            for card_id, instance in state.cards.items():
                if instance.zone is not Zone.BATTLEFIELD:
                    continue
                definition = self._definition(card_id)
                strength = self._current_strength(card_id)
                lord_depleted = definition.lord_domain is not None and strength <= 0
                if lord_depleted:
                    destroyed.append(card_id)
                    continue
                if not self._is_creature(card_id):
                    continue
                if (
                    "INDESTRUCTIBLE" not in self._effective_keywords(card_id)
                    and (strength <= 0 or instance.damage >= strength)
                ):
                    destroyed.append(card_id)
            if not destroyed:
                for instance in state.cards.values():
                    instance.regeneration_blocked_until_state_check = False
                return
            for card_id in destroyed:
                definition = self._definition(card_id)
                if definition.lord_domain is not None:
                    self._move_card(
                        card_id,
                        Zone.DISCARD,
                        state.cards[card_id].owner_id,
                        reason=MoveReason.STATE_BASED,
                        allow_replacement=False,
                    )
                    self._emit(
                        "LORD_DEPLETED",
                        card_id=card_id,
                        payload={"reason": "state_based_action"},
                    )
                else:
                    self._destroy_permanent(
                        card_id,
                        MoveReason.STATE_BASED,
                        allows_regeneration=not state.cards[
                            card_id
                        ].regeneration_blocked_until_state_check,
                    )
                    if state.cards[card_id].zone is Zone.BATTLEFIELD:
                        state.cards[
                            card_id
                        ].regeneration_blocked_until_state_check = False

    def _concede(self, player_id: str) -> None:
        state = self._require_running_state()
        state.players[player_id].conceded = True
        winners = tuple(pid for pid in state.turn_order if pid != player_id)
        state.winner_ids = winners
        state.status = MatchStatus.FINISHED
        self._emit("PLAYER_CONCEDED", player_id, payload={"winners": winners})

    def _draw(self, player_id: str, amount: int) -> None:
        return self._zones._draw(player_id, amount)

    @staticmethod
    def _replacement_definitions(
        definition: CardDefinition,
    ) -> tuple[MoveReplacementDefinition, ...]:
        return ZoneManager._replacement_definitions(definition)

    def _set_replacement_order(self, command: SetReplacementOrder) -> None:
        return self._zones._set_replacement_order(command)

    def _ordered_replacements(
        self, card_id: str, definition: CardDefinition
    ) -> tuple[MoveReplacementDefinition, ...]:
        return self._zones._ordered_replacements(card_id, definition)

    def _move_card(
        self,
        card_id: str,
        destination: Zone,
        destination_player: str,
        *,
        reason: MoveReason = MoveReason.RULE,
        allow_replacement: bool = True,
    ) -> Zone:
        return self._zones._move_card(
            card_id, destination, destination_player,
            reason=reason, allow_replacement=allow_replacement,
        )

    @staticmethod
    def _apply_text_patch_to_definition(
        definition: CardDefinition, patch: TextPatchDefinition
    ) -> CardDefinition:
        return apply_text_patch(definition, patch)

    def _definition(self, card_id: str) -> CardDefinition:
        state = self._require_state()
        instance = state.cards[card_id]
        definition = self.catalog.get(
            instance.overridden_definition_id or instance.definition_id
        )
        for applied in state.text_patches:
            if applied.target_card_id == card_id:
                definition = self._apply_text_patch_to_definition(
                    definition, applied.patch
                )
        return definition

    def _check_wound_limits(self) -> None:
        state = self._require_running_state()
        defeated = tuple(
            player_id
            for player_id, player in state.players.items()
            if player.wounds >= self.rules.wound_limit or player.conceded
        )
        if not defeated:
            return
        winners = tuple(player_id for player_id in state.turn_order if player_id not in defeated)
        state.winner_ids = winners
        state.status = MatchStatus.FINISHED
        self._emit("MATCH_FINISHED", payload={"defeated": defeated, "winners": winners})

    def validate_invariants(self) -> None:
        state = self._require_state()
        if (
            state.ruleset_id != self.rules.ruleset_id
            or state.ruleset_version != self.rules.version
        ):
            raise InvariantViolation("El estado y su conjunto de reglas no coinciden")
        if state.initial_decks and set(state.initial_decks) != set(state.players):
            raise InvariantViolation("Los mazos iniciales no coinciden con los jugadores")
        if any(player_id not in state.players for player_id in state.setup_mulligans):
            raise InvariantViolation("El historial de mulligan contiene un jugador inválido")
        if any(not isinstance(command, GameCommand) for command in state.command_history):
            raise InvariantViolation("El historial contiene un comando inválido")
        locations: dict[str, int] = {card_id: 0 for card_id in state.cards}
        for player in state.players.values():
            for zone, card_ids in player.zones.items():
                if len(card_ids) != len(set(card_ids)):
                    raise InvariantViolation(f"Duplicado en {player.player_id}/{zone.name}")
                for card_id in card_ids:
                    if card_id not in state.cards:
                        raise InvariantViolation(f"Instancia desconocida: {card_id}")
                    locations[card_id] += 1
                    if state.cards[card_id].zone is not zone:
                        raise InvariantViolation(f"Zona incoherente para {card_id}")
                    if (
                        zone is Zone.BATTLEFIELD
                        and state.cards[card_id].controller_id != player.player_id
                    ):
                        raise InvariantViolation(
                            f"Control y tapiz incoherentes para {card_id}"
                        )
        for card_id in state.resolution:
            locations[card_id] += 1
            if state.cards[card_id].zone is not Zone.RESOLUTION:
                raise InvariantViolation(f"Resolución incoherente para {card_id}")
        for card_id in state.void:
            locations[card_id] += 1
            if state.cards[card_id].zone is not Zone.VOID:
                raise InvariantViolation(f"Vacío incoherente para {card_id}")
        invalid = [card_id for card_id, count in locations.items() if count != 1]
        if invalid:
            raise InvariantViolation(f"Cartas sin ubicación única: {invalid}")
        stack_sources = {item.source_card_id for item in state.stack if item.destination_on_resolve}
        if (
            state.pending_search is not None
            and state.pending_search.stack_item.destination_on_resolve is not None
        ):
            stack_sources.add(state.pending_search.stack_item.source_card_id)
        if stack_sources != set(state.resolution):
            raise InvariantViolation("La pila y la zona de resolución no coinciden")
        pending_ids = [item.item_id for item in state.pending_triggers]
        if len(pending_ids) != len(set(pending_ids)):
            raise InvariantViolation("Disparos pendientes duplicados")
        if state.pending_triggers and any(
            item.controller_id != state.priority_player_id for item in state.pending_triggers
        ):
            raise InvariantViolation("La prioridad no corresponde a los disparos pendientes")
        if state.active_player_id not in state.players:
            raise InvariantViolation("Jugador activo inexistente")
        if any(player.steps < 0 or player.wounds < 0 for player in state.players.values()):
            raise InvariantViolation("Pasos y Heridas no pueden ser negativos")
        if any(
            instance.regeneration_shields < 0 for instance in state.cards.values()
        ):
            raise InvariantViolation("Los escudos de regeneración no pueden ser negativos")
        if any(
            suppression.player_id not in state.players
            for suppression in state.phase_suppressions
        ):
            raise InvariantViolation("Supresión de fase con jugador inexistente")
        if any(
            instance.overridden_definition_id is not None
            and instance.overridden_definition_id not in self.catalog
            for instance in state.cards.values()
        ):
            raise InvariantViolation("Transformación con definición inexistente")
        if any(
            change.card_id not in state.cards
            or state.cards[change.card_id].zone is not Zone.BATTLEFIELD
            or change.previous_controller_id not in state.players
            for change in state.control_changes
        ):
            raise InvariantViolation("Cambio de control temporal incoherente")
        if state.pending_search is not None:
            search = state.pending_search
            source_zone = state.players[search.zone_target.player_id].zones[
                search.zone_target.zone
            ]
            if search.chooser_id not in state.players:
                raise InvariantViolation("Búsqueda asignada a un jugador inexistente")
            if len(search.eligible_card_ids) != len(set(search.eligible_card_ids)):
                raise InvariantViolation("Búsqueda con candidatos duplicados")
            if any(card_id not in source_zone for card_id in search.eligible_card_ids):
                raise InvariantViolation("Búsqueda con candidatos fuera de su zona")
        if state.pending_move_replacement is not None:
            pending = state.pending_move_replacement
            if (
                pending.chooser_id not in state.players
                or pending.card_id not in state.cards
                or pending.chooser_id != state.priority_player_id
            ):
                raise InvariantViolation("Elección de sustitución pendiente incoherente")
            if (
                not pending.candidate_indices
                or len(pending.candidate_indices)
                != len(pending.candidate_destinations)
                or len(pending.candidate_indices)
                != len(set(pending.candidate_indices))
            ):
                raise InvariantViolation("Candidatos de sustitución incoherentes")
        for card_id, instance in state.cards.items():
            if instance.attached_to is None:
                continue
            target = state.cards.get(instance.attached_to)
            if instance.zone is not Zone.BATTLEFIELD or target is None or target.zone is not Zone.BATTLEFIELD:
                raise InvariantViolation(f"Anexo incoherente para {card_id}")
            if not self._is_creature(instance.attached_to):
                raise InvariantViolation(f"Equipo unido a un objetivo no criatura: {card_id}")
        if any(
            modifier.target_card_id not in state.cards
            or state.cards[modifier.target_card_id].zone is not Zone.BATTLEFIELD
            for modifier in state.timed_modifiers
        ):
            raise InvariantViolation("Modificador temporal sin permanente válido")
        if any(
            patch.target_card_id not in state.cards
            or state.cards[patch.target_card_id].zone is not Zone.BATTLEFIELD
            for patch in state.text_patches
        ):
            raise InvariantViolation("Parche de texto sin permanente válido")
        for card_id, instance in state.cards.items():
            if not instance.replacement_order:
                continue
            replacements = self._replacement_definitions(self._definition(card_id))
            if instance.zone is not Zone.BATTLEFIELD or set(
                instance.replacement_order
            ) != set(range(len(replacements))):
                raise InvariantViolation(f"Orden de sustitución incoherente para {card_id}")

    def _next_player(self, player_id: str) -> str:
        state = self._require_state()
        index = state.turn_order.index(player_id)
        return state.turn_order[(index + 1) % len(state.turn_order)]

    def _emit(
        self,
        event_type: str,
        player_id: str | None = None,
        card_id: str | None = None,
        payload: dict[str, object] | None = None,
    ) -> None:
        state = self._require_state()
        state.event_log.append(
            GameEvent(
                sequence=len(state.event_log) + 1,
                event_type=event_type,
                player_id=player_id,
                card_id=card_id,
                payload=payload or {},
            )
        )

    def _require_state(self) -> GameState:
        if self.state is None:
            raise RuntimeError("No hay una partida creada")
        return self.state

    def _require_running_state(self) -> GameState:
        state = self._require_state()
        if state.status is not MatchStatus.RUNNING:
            raise IllegalAction("La partida no está en ejecución")
        return state


def _verify_manager_contexts(engine: GameEngine) -> None:
    """Testigo estático: el coordinador satisface cada contrato por separado."""
    combat: CombatContext = engine
    stack: StackContext = engine
    zones: ZoneContext = engine
    effects: EffectContext = engine
    _ = (combat, stack, zones, effects)
