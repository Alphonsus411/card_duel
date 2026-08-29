"""Paridad observable de la extracción de ``LegalActionEnumerator``.

La función ``_previous_legal_actions`` es la captura literal del cuerpo que vivía
en ``GameEngine.legal_actions`` antes de la extracción.  Se conserva únicamente
como oráculo de caracterización: las aserciones comparan tuplas (no conjuntos) y
también protegen que una consulta sea pura y determinista.
"""

import ast
from copy import deepcopy
from dataclasses import fields
from itertools import combinations, islice, permutations
from pathlib import Path

import pytest

from card_duel_engine import GameEngine, RuleSet
from card_duel_engine.controllers.base import PlayerObservation
from card_duel_engine.domain import (
    AbilityDefinition,
    CardDefinition,
    CardKind,
    CompositeCost,
    EffectDefinition,
    EffectKind,
    MatchStatus,
    MoveReason,
    MoveReplacementDefinition,
    Phase,
    TargetMode,
    Zone,
    ZoneTarget,
)
from card_duel_engine.domain.errors import IllegalAction
from card_duel_engine.domain.models import (
    CombatState,
    PendingMoveReplacement,
    PendingSearch,
    StackItem,
)
from card_duel_engine.engine import (
    ActivateAbility,
    AdvancePhase,
    Concede,
    DeclareAttackers,
    DeclareBlockers,
    DeclareChallenge,
    DiscardCards,
    DrainSteps,
    EquipCard,
    OrderTriggeredAbilities,
    PassPriority,
    PlayCard,
    ResolveCombat,
    ResolveMoveReplacement,
    ResolveSearchChoice,
    SetReplacementOrder,
    TransmutePermanent,
)
from card_duel_engine.engine.actions import LegalActionEnumerator
from card_duel_engine.persistence.codec import encode_value
from card_duel_engine.service import MatchService
from card_duel_engine.storage.base import InMemoryMatchStore

from fixtures import test_deck


def _previous_legal_actions(engine: GameEngine, player_id: str):
    """Cuerpo previo, congelado como oráculo de paridad de la refactorización."""
    state = engine._require_state()
    if state.status in (MatchStatus.FINISHED, MatchStatus.BLOCKED):
        return ()
    if state.status is not MatchStatus.RUNNING:
        raise IllegalAction("La partida no está en ejecución")
    if player_id not in state.players:
        return ()
    actions = []
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
                engine.rules.legal_action_enumeration_limit,
            )
        )
        actions.append(Concede(player_id))
        return tuple(actions[: engine.rules.legal_action_enumeration_limit + 1])

    if state.pending_triggers:
        if player_id != state.priority_player_id:
            return (Concede(player_id),)
        unlocked = next(
            (item for item in state.pending_triggers if not item.targets_locked), None
        )
        if unlocked is not None:
            actions.extend(engine._trigger_target_commands(player_id, unlocked))
            actions.append(Concede(player_id))
            return tuple(actions)
        item_ids = tuple(item.item_id for item in state.pending_triggers)
        actions.extend(
            OrderTriggeredAbilities(player_id, tuple(order))
            for order in islice(
                permutations(item_ids), engine.rules.legal_action_enumeration_limit
            )
        )
        actions.append(Concede(player_id))
        return tuple(actions)

    if state.phase in {Phase.EFFECTS, Phase.COMBAT}:
        actions.extend(engine._combat.legal_actions(player_id))

    if player_id == state.priority_player_id:
        actions.extend(engine._legal_plays(player_id))
        if (
            player_id == state.active_player_id
            and (engine._legacy_019 or state.phase is Phase.EFFECTS)
            and player.drainage_used_turn_serial != state.turn_serial
        ):
            actions.extend(DrainSteps(player_id, amount) for amount in range(1, 6))
        for card_id in player.zones[Zone.BATTLEFIELD]:
            definition = engine._definition(card_id)
            replacements = engine._replacement_definitions(definition)
            if definition.player_orders_replacements and len(replacements) > 1:
                actions.extend(
                    SetReplacementOrder(player_id, card_id, tuple(order))
                    for order in islice(
                        permutations(range(len(replacements))),
                        engine.rules.legal_action_enumeration_limit,
                    )
                    if tuple(order) != state.cards[card_id].replacement_order
                )
            if definition.transmutable:
                actions.append(TransmutePermanent(player_id, card_id))
            actions.extend(engine._legal_ability_activations(player_id, card_id))
            if definition.kind is CardKind.EQUIPMENT:
                for creature_id in player.zones[Zone.BATTLEFIELD]:
                    if engine._is_creature(creature_id) and player.steps >= definition.cost:
                        actions.append(EquipCard(player_id, card_id, creature_id))
        actions.append(PassPriority(player_id))

    if (
        player_id == state.active_player_id
        and state.phase_priority_complete
        and not state.stack
    ):
        if state.phase is Phase.DISCARD:
            excess = max(0, len(player.zones[Zone.HAND]) - engine.rules.hand_limit)
            if excess:
                actions.extend(
                    DiscardCards(player_id, tuple(card_ids))
                    for card_ids in combinations(player.zones[Zone.HAND], excess)
                )
            else:
                actions.append(AdvancePhase(player_id))
        elif not (
            state.phase is Phase.COMBAT and state.combat and not state.combat.resolved
        ):
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


def _special_definitions():
    return (
        CardDefinition("PLAY", "Jugable", CardKind.ARTIFACT, 1),
        CardDefinition(
            "ABILITY",
            "Habilidad",
            CardKind.ARTIFACT,
            1,
            abilities=(
                AbilityDefinition(
                    "gain", (EffectDefinition(EffectKind.GAIN_STEPS, 1),), CompositeCost()
                ),
            ),
        ),
        CardDefinition("EQUIP", "Equipo", CardKind.EQUIPMENT, 1),
        CardDefinition(
            "ORDER",
            "Ordenador",
            CardKind.ARTIFACT,
            1,
            move_replacements=(
                MoveReplacementDefinition(Zone.HAND),
                MoveReplacementDefinition(Zone.EXILE),
            ),
            player_orders_replacements=True,
        ),
        CardDefinition(
            "TARGET_TRIGGER",
            "Disparo",
            CardKind.CREATURE,
            1,
            base_strength=2,
            abilities=(
                AbilityDefinition(
                    "hit",
                    (EffectDefinition(EffectKind.DEAL_WOUNDS, 1, TargetMode.CHOSEN_PLAYER),),
                ),
            ),
        ),
    )


def _engine(enumeration_limit=20) -> GameEngine:
    engine = GameEngine(
        RuleSet(legal_action_enumeration_limit=enumeration_limit)
    )
    engine.new_match(
        {
            "A": [*_special_definitions(), *test_deck("A", 14)],
            "B": test_deck("B", 14),
        },
        seed=20201,
    )
    engine.state.phase = Phase.EFFECTS
    engine.state.priority_player_id = "A"
    engine.state.players["A"].steps = 10
    return engine


def _force_zone(engine, definition_id, player_id, zone):
    card_id = next(
        card_id
        for card_id, card in engine.state.cards.items()
        if card.definition_id == definition_id and card.owner_id == player_id
    )
    for player in engine.state.players.values():
        for cards in player.zones.values():
            if card_id in cards:
                cards.remove(card_id)
    engine.state.players[player_id].zones[zone].append(card_id)
    engine.state.cards[card_id].zone = zone
    engine.state.cards[card_id].controller_id = player_id
    return card_id


def _normal():
    return _engine()


def _all_priority_options():
    engine = _engine()
    for definition_id in ("ABILITY", "EQUIP", "ORDER", "A-000"):
        _force_zone(engine, definition_id, "A", Zone.BATTLEFIELD)
    _force_zone(engine, "PLAY", "A", Zone.HAND)
    return engine


def _replacement():
    engine = _engine()
    card_id = _force_zone(engine, "ORDER", "A", Zone.BATTLEFIELD)
    engine.state.pending_move_replacement = PendingMoveReplacement(
        Concede("A"), "A", card_id, MoveReason.DESTROY, (0, 1),
        (Zone.HAND, Zone.EXILE), "A"
    )
    return engine


def _search():
    engine = _engine()
    eligible = tuple(engine.state.players["A"].zones[Zone.DECK][:3])
    source = _force_zone(engine, "PLAY", "A", Zone.BATTLEFIELD)
    item = StackItem("search", "A", source, ())
    engine.state.pending_search = PendingSearch(
        item, 0, "A", ZoneTarget("A", Zone.DECK), eligible, 1, 2,
        Zone.HAND, True, False
    )
    return engine


def _triggers(targets_locked):
    engine = _engine()
    source = _force_zone(engine, "TARGET_TRIGGER", "A", Zone.BATTLEFIELD)
    effect = EffectDefinition(EffectKind.DEAL_WOUNDS, 1, TargetMode.CHOSEN_PLAYER)
    engine.state.pending_triggers = [
        StackItem("trigger-1", "A", source, (effect,), ability_id="hit", targets_locked=targets_locked),
        StackItem("trigger-2", "A", source, (effect,), ability_id="hit", targets_locked=True),
    ]
    return engine


def _combat():
    engine = _engine()
    attacker = _force_zone(engine, "A-000", "A", Zone.BATTLEFIELD)
    _force_zone(engine, "B-000", "B", Zone.BATTLEFIELD)
    engine.state.phase = Phase.COMBAT
    engine.state.combat = CombatState("A", "B", (attacker,))
    engine.state.priority_player_id = "B"
    return engine


def _discard():
    engine = _engine()
    engine.state.phase = Phase.DISCARD
    engine.state.phase_priority_complete = True
    while len(engine.state.players["A"].zones[Zone.HAND]) <= engine.rules.hand_limit:
        card_id = engine.state.players["A"].zones[Zone.DECK][0]
        _force_zone(engine, engine.state.cards[card_id].definition_id, "A", Zone.HAND)
    return engine


def _advance():
    engine = _engine()
    engine.state.phase_priority_complete = True
    engine.state.priority_player_id = "B"
    return engine


def _status(status):
    engine = _engine()
    engine.state.status = status
    return engine


CASES = (
    ("partida normal", _normal, "A"),
    ("jugador sin prioridad", _normal, "B"),
    ("sustitución", _replacement, "A"),
    ("sustitución de otro jugador", _replacement, "B"),
    ("búsqueda con múltiples alternativas", _search, "A"),
    ("búsqueda de otro jugador", _search, "B"),
    ("triggers con objetivos bloqueados", lambda: _triggers(True), "A"),
    ("triggers sin objetivos bloqueados", lambda: _triggers(False), "A"),
    ("combate", _combat, "B"),
    ("juego habilidades transmutación equipo drenaje y orden", _all_priority_options, "A"),
    ("descarte", _discard, "A"),
    ("avance de fase", _advance, "A"),
    ("FINISHED", lambda: _status(MatchStatus.FINISHED), "A"),
    ("BLOCKED", lambda: _status(MatchStatus.BLOCKED), "A"),
    ("no iniciada", lambda: _status(MatchStatus.SETUP), "A"),
    ("jugador desconocido", _normal, "DESCONOCIDO"),
)


@pytest.mark.parametrize(("description", "factory", "player_id"), CASES, ids=lambda value: value if isinstance(value, str) else None)
def test_legal_action_enumerator_preserves_previous_tuple_and_state(
    description, factory, player_id
):
    del description
    engine = factory()
    state_before = deepcopy(engine.state)
    serialized_before = deepcopy(encode_value(engine.state))

    if engine.state.status is MatchStatus.SETUP:
        with pytest.raises(IllegalAction, match="no está en ejecución"):
            _previous_legal_actions(engine, player_id)
        with pytest.raises(IllegalAction, match="no está en ejecución"):
            LegalActionEnumerator(engine).legal_actions(player_id)
        with pytest.raises(IllegalAction, match="no está en ejecución"):
            engine.legal_actions(player_id)
        with pytest.raises(IllegalAction, match="no está en ejecución"):
            engine.legal_actions(player_id)
    else:
        previous = _previous_legal_actions(engine, player_id)
        direct = LegalActionEnumerator(engine).legal_actions(player_id)
        facade = engine.legal_actions(player_id)
        repeated = engine.legal_actions(player_id)
        assert isinstance(previous, tuple)
        assert direct == previous
        assert facade == previous
        assert repeated == previous

    assert engine.state == state_before
    assert encode_value(engine.state) == serialized_before


def test_legal_action_enumerator_preserves_unstarted_engine_behavior_and_state():
    engine = GameEngine()
    assert engine.state is None
    serialized_before = encode_value(engine.state)

    for query in (
        lambda: _previous_legal_actions(engine, "A"),
        lambda: LegalActionEnumerator(engine).legal_actions("A"),
        lambda: engine.legal_actions("A"),
        lambda: engine.legal_actions("A"),
    ):
        with pytest.raises(RuntimeError, match="No hay una partida creada"):
            query()

    assert engine.state is None
    assert encode_value(engine.state) == serialized_before


@pytest.mark.parametrize("limit", (1, 2))
def test_small_limit_search_has_an_exact_tuple(limit):
    engine = _engine(limit)
    eligible = tuple(engine.state.players["A"].zones[Zone.DECK][:3])
    source = _force_zone(engine, "PLAY", "A", Zone.BATTLEFIELD)
    engine.state.pending_search = PendingSearch(
        StackItem("search", "A", source, ()),
        0,
        "A",
        ZoneTarget("A", Zone.DECK),
        eligible,
        1,
        2,
        Zone.HAND,
        True,
        False,
    )

    # La segunda cardinalidad ocupa el hueco previo al corte final; por eso, con
    # este intervalo concreto, Concede queda fuera de la tupla caracterizada.
    enumerated = tuple(
        ResolveSearchChoice("A", tuple(selection))
        for count in (1, 2)
        for selection in tuple(combinations(eligible, count))[:limit]
    )
    expected = enumerated[: limit + 1]
    assert engine.legal_actions("A") == expected


@pytest.mark.parametrize("limit", (1, 2))
def test_small_limit_trigger_order_has_an_exact_tuple(limit):
    engine = _triggers(True)
    engine.rules = RuleSet(legal_action_enumeration_limit=limit)
    orders = (
        ("trigger-1", "trigger-2"),
        ("trigger-2", "trigger-1"),
    )

    assert engine.legal_actions("A") == tuple(
        OrderTriggeredAbilities("A", order) for order in orders[:limit]
    ) + (Concede("A"),)


@pytest.mark.parametrize("limit", (1, 2))
def test_small_limit_is_per_play_cost_and_not_global(limit):
    """El límite acota cada producto de objetivos/coste; no la tupla global."""
    targeted = CardDefinition(
        "TARGET_COST",
        "Objetivo con alternativa",
        CardKind.ARTIFACT,
        1,
        effects=(
            EffectDefinition(EffectKind.GAIN_STEPS, 1, TargetMode.CHOSEN_PLAYER),
        ),
        alternative_costs=(CompositeCost(discard_count=1),),
    )
    fodder = CardDefinition("FODDER", "Coste", CardKind.ARTIFACT, 100)
    engine = GameEngine(RuleSet(legal_action_enumeration_limit=limit))
    engine.new_match(
        {"A": [targeted, fodder, *test_deck("A", 12)], "B": test_deck("B", 14)},
        seed=20201,
    )
    engine.state.phase = Phase.EFFECTS
    engine.state.priority_player_id = "A"
    engine.state.players["A"].steps = 10
    target_id = _force_zone(engine, "TARGET_COST", "A", Zone.HAND)
    fodder_id = _force_zone(engine, "FODDER", "A", Zone.HAND)
    for card_id in tuple(engine.state.players["A"].zones[Zone.HAND]):
        if card_id not in {target_id, fodder_id}:
            definition_id = engine.state.cards[card_id].definition_id
            _force_zone(engine, definition_id, "A", Zone.DECK)

    target_choices = (("A",), ("B",))[:limit]
    expected_plays = tuple(
        PlayCard("A", target_id, chosen_player_ids=choice)
        for choice in target_choices
    ) + tuple(
        PlayCard(
            "A",
            target_id,
            chosen_player_ids=choice,
            cost_option_index=0,
            discard_card_ids=(fodder_id,),
        )
        for choice in target_choices
    )
    expected = expected_plays + tuple(
        DrainSteps("A", amount) for amount in range(1, 6)
    ) + (PassPriority("A"), Concede("A"))

    assert len(expected_plays) == 2 * limit  # Prueba explícita: no es un tope global.
    assert engine.legal_actions("A") == expected


@pytest.mark.parametrize("limit", (1, 2))
def test_small_limit_orderable_replacements_have_an_exact_tuple(limit):
    engine = _engine(limit)
    card_id = _force_zone(engine, "ORDER", "A", Zone.BATTLEFIELD)
    engine.state.phase = Phase.MAINTENANCE
    orders = ((0, 1), (1, 0))

    assert engine.legal_actions("A") == (
        TransmutePermanent("A", card_id),
        PassPriority("A"),
        *(SetReplacementOrder("A", card_id, order) for order in orders[:limit]),
        Concede("A"),
    )


@pytest.mark.parametrize("limit", (1, 2))
def test_small_limit_attackers_have_an_exact_tuple(limit):
    engine = _engine(limit)
    attackers = tuple(
        _force_zone(engine, definition_id, "A", Zone.BATTLEFIELD)
        for definition_id in ("A-000", "A-001")
    )
    engine.state.phase = Phase.COMBAT
    engine.state.phase_priority_complete = True

    declarations = (
        DeclareAttackers("A", (attackers[0],), "B"),
        DeclareAttackers("A", (attackers[1],), "B"),
    )
    assert engine.legal_actions("A") == declarations[:limit] + (
        AdvancePhase("A"),
        TransmutePermanent("A", attackers[0]),
        TransmutePermanent("A", attackers[1]),
        PassPriority("A"),
        Concede("A"),
    )


@pytest.mark.parametrize("limit", (1, 2))
def test_small_limit_blockers_have_an_exact_tuple(limit):
    engine = _engine(limit)
    attacker = _force_zone(engine, "A-000", "A", Zone.BATTLEFIELD)
    blocker = _force_zone(engine, "B-000", "B", Zone.BATTLEFIELD)
    engine.state.phase = Phase.COMBAT
    engine.state.priority_player_id = "B"
    engine.state.combat = CombatState("A", "B", (attacker,))

    declarations = (
        DeclareBlockers("B"),
        DeclareBlockers("B", ((attacker, (blocker,)),)),
    )
    assert engine.legal_actions("B") == declarations[:limit] + (
        TransmutePermanent("B", blocker),
        PassPriority("B"),
        Concede("B"),
    )


@pytest.mark.parametrize("limit", (1, 2))
def test_small_limit_does_not_currently_limit_discard_combinations(limit):
    """Caracteriza el descarte no limitado, sin optimizarlo ni corregirlo aquí."""
    engine = _engine(limit)
    engine.state.phase = Phase.DISCARD
    engine.state.phase_priority_complete = True
    engine.state.priority_player_id = "B"
    while len(engine.state.players["A"].zones[Zone.HAND]) < engine.rules.hand_limit + 2:
        card_id = engine.state.players["A"].zones[Zone.DECK][0]
        _force_zone(
            engine, engine.state.cards[card_id].definition_id, "A", Zone.HAND
        )
    hand = tuple(engine.state.players["A"].zones[Zone.HAND])
    discards = tuple(
        DiscardCards("A", tuple(card_ids)) for card_ids in combinations(hand, 2)
    )

    assert len(discards) > limit
    assert engine.legal_actions("A") == discards + (Concede("A"),)


def _engine_with_identifiable_private_zones():
    """Sitúa cartas inequívocas en las zonas privadas de los dos jugadores."""
    public_target = CardDefinition(
        "PUBLIC_TARGET",
        "Objetivo público de B",
        CardKind.CREATURE,
        1,
        base_strength=1,
    )
    targeted_play = CardDefinition(
        "TARGET_PUBLIC",
        "Hechizo que elige permanente público",
        CardKind.ARTIFACT,
        1,
        effects=(
            EffectDefinition(EffectKind.DEAL_DAMAGE, 1, TargetMode.CHOSEN_PERMANENT),
        ),
    )
    engine = GameEngine()
    engine.new_match(
        {
            "A": [targeted_play, *test_deck("A-PRIVATE", 13)],
            "B": [public_target, *test_deck("B-PRIVATE", 13)],
        },
        seed=713,
    )
    engine.state.phase = Phase.EFFECTS
    engine.state.priority_player_id = "A"
    engine.state.players["A"].steps = 10

    identifiable = {
        "a_hand": _force_zone(engine, "TARGET_PUBLIC", "A", Zone.HAND),
        "a_deck": _force_zone(engine, "A-PRIVATE-000", "A", Zone.DECK),
        "a_deck_2": _force_zone(engine, "A-PRIVATE-001", "A", Zone.DECK),
        "b_hand": _force_zone(engine, "B-PRIVATE-000", "B", Zone.HAND),
        "b_deck": _force_zone(engine, "B-PRIVATE-001", "B", Zone.DECK),
        "b_public": _force_zone(engine, "PUBLIC_TARGET", "B", Zone.BATTLEFIELD),
    }
    return engine, identifiable


def test_player_actions_do_not_leak_opponent_private_card_ids():
    engine, card_ids = _engine_with_identifiable_private_zones()

    actions = engine.legal_actions("A")
    encoded_actions = repr(encode_value(actions))

    assert card_ids["b_hand"] not in encoded_actions
    assert card_ids["b_deck"] not in encoded_actions
    # Un objetivo en el campo de batalla sí es información pública y una regla
    # CHOSEN_PERMANENT permite que aparezca legítimamente en el comando.
    assert any(
        isinstance(action, PlayCard)
        and action.chosen_card_ids == (card_ids["b_public"],)
        for action in actions
    )


def test_only_pending_search_chooser_receives_eligible_card_ids():
    engine, card_ids = _engine_with_identifiable_private_zones()
    eligible = (card_ids["a_deck"], card_ids["a_deck_2"])
    source = _force_zone(engine, "TARGET_PUBLIC", "A", Zone.BATTLEFIELD)
    engine.state.pending_search = PendingSearch(
        StackItem("private-search", "A", source, ()),
        0,
        "A",
        ZoneTarget("A", Zone.DECK),
        eligible,
        1,
        1,
        Zone.HAND,
        True,
        False,
    )

    assert engine.legal_actions("A") == tuple(
        ResolveSearchChoice("A", (card_id,)) for card_id in eligible
    ) + (Concede("A"),)
    assert engine.observe("A").searchable_card_ids == eligible
    assert engine.legal_actions("B") == (Concede("B"),)
    assert engine.observe("B").searchable_card_ids == ()


def test_only_pending_move_replacement_chooser_receives_resolution_indices():
    engine, card_ids = _engine_with_identifiable_private_zones()
    engine.state.pending_move_replacement = PendingMoveReplacement(
        Concede("A"),
        "A",
        card_ids["a_hand"],
        MoveReason.DESTROY,
        (2, 5),
        (Zone.HAND, Zone.EXILE),
        "A",
    )

    assert engine.legal_actions("A") == (
        ResolveMoveReplacement("A", 2),
        ResolveMoveReplacement("A", 5),
        Concede("A"),
    )
    assert engine.observe("A").replacement_destinations == (
        (2, "HAND"),
        (5, "EXILE"),
    )
    assert engine.legal_actions("B") == (Concede("B"),)
    assert engine.observe("B").replacement_destinations == ()


def test_match_service_and_player_observation_public_contract_is_unchanged():
    engine, card_ids = _engine_with_identifiable_private_zones()
    store = InMemoryMatchStore()
    store.create("privacy-parity", engine)

    view = MatchService(store).view("privacy-parity", "A")

    assert view.observation == engine.observe("A")
    assert view.legal_actions == engine.legal_actions("A")
    assert tuple(field.name for field in fields(PlayerObservation)) == (
        "player_id", "active_player_id", "phase", "own_hand", "own_steps",
        "own_wounds", "opponent_hand_sizes", "public_event_count",
        "own_battlefield", "opponent_battlefields", "stack_size", "stack_items",
        "pending_triggers", "suppressed_phases", "pending_search_item_id",
        "searchable_card_ids", "replacement_orders",
        "pending_replacement_card_id", "replacement_destinations",
    )
    observation = view.observation
    assert observation.own_hand == engine.observe("A").own_hand
    assert card_ids["b_hand"] not in repr(observation)
    assert card_ids["b_deck"] not in repr(observation)


def test_legal_action_enumerator_stays_in_engine_without_outer_layer_dependencies():
    module_path = __import__(
        "card_duel_engine.engine.actions", fromlist=["__file__"]
    ).__file__
    assert module_path is not None
    path = Path(module_path)
    assert path.parent.name == "engine"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported_modules = {
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, (ast.ImportFrom,))
    } | {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }

    assert imported_modules.isdisjoint({"controllers.base", "service", "application"})
