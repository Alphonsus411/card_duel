"""Paridad observable de los cinco helpers extraídos a ``ActionOptionResolver``.

Los helpers ``_historical_*`` congelan únicamente los cuerpos que fueron
extraídos. Las dependencias semánticas siguen delegándose al motor, evitando
duplicar validadores de jugadas, activaciones, disparos, objetivos o efectos.
"""

import json
from dataclasses import fields
from itertools import combinations, islice

import pytest

from card_duel_engine import EngineSemantics, GameEngine, RuleSet
from card_duel_engine.domain import (
    AbilityDefinition,
    CardDefinition,
    CardKind,
    CompositeCost,
    CostComponent,
    CostMetric,
    CostTerm,
    DynamicCostDefinition,
    EffectDefinition,
    EffectKind,
    TargetAllocation,
    TargetMode,
    XCostDefinition,
    Zone,
    ZoneTarget,
)
from card_duel_engine.domain.models import StackItem
from card_duel_engine.persistence.codec import encode_value

from fixtures import test_deck
from test_legal_action_enumerator_parity import _previous_legal_actions


SEMANTICS = (EngineSemantics.CURRENT, EngineSemantics.LEGACY_019)


def _serialized_state(engine: GameEngine) -> str:
    """Usa el codec estable y una representación JSON canónica comparable."""
    return json.dumps(encode_value(engine.state), ensure_ascii=False, sort_keys=True)


def _pure_query(engine: GameEngine, query):
    before = _serialized_state(engine)
    result = query()
    assert _serialized_state(engine) == before
    return result


def _engine(semantics: EngineSemantics, limit: int = 50) -> GameEngine:
    special = (
        CardDefinition("NORMAL", "Normal", CardKind.ARTIFACT, 2),
        CardDefinition("QUICK", "Rápida", CardKind.QUICK_RESOURCE, 1, permanent=False),
        CardDefinition("IMMUNE", "Inmune", CardKind.CREATURE, 1, base_strength=2,
                       keywords=frozenset({"IMMUNE_QUICK", "IMMUNE_ABILITIES"})),
        CardDefinition("OPEN", "Objetivo", CardKind.CREATURE, 1, base_strength=2),
    )
    engine = GameEngine(RuleSet(legal_action_enumeration_limit=limit))
    engine.new_match({"A": [*special, *test_deck("A", 12)], "B": test_deck("B", 12)}, seed=7)
    engine._semantics = semantics
    engine.state.players["A"].steps = 7
    engine.state.players["A"].wounds = 3
    for definition_id in ("NORMAL", "IMMUNE", "OPEN"):
        card_id = next(cid for cid, card in engine.state.cards.items()
                       if card.definition_id == definition_id)
        for zone_cards in engine.state.players["A"].zones.values():
            if card_id in zone_cards:
                zone_cards.remove(card_id)
        engine.state.players["A"].zones[Zone.BATTLEFIELD].append(card_id)
        engine.state.cards[card_id].zone = Zone.BATTLEFIELD
    return engine


def _historical_target_selections(engine, effects, mode, candidates):
    targeted = tuple(effect for effect in effects if effect.target is mode)
    if not targeted:
        return ((),)
    minimum = max(effect.minimum_targets for effect in targeted)
    maximum = min(effect.maximum_targets for effect in targeted)
    pool = tuple(candidates)
    maximum = min(maximum, len(pool))
    return tuple(islice((tuple(selection)
                         for count in range(minimum, maximum + 1)
                         for selection in combinations(pool, count)),
                        engine.rules.legal_action_enumeration_limit))


def _historical_zone_target_selections(engine, effects):
    candidates = tuple(ZoneTarget(player_id, zone)
                       for player_id, player in engine.state.players.items()
                       for zone in player.zones)
    targeted = tuple(effect for effect in effects if effect.target is TargetMode.CHOSEN_ZONE)
    if not targeted:
        return ((),)
    minimum = max(effect.minimum_targets for effect in targeted)
    maximum = min(effect.maximum_targets for effect in targeted)
    return tuple(islice((tuple(selection)
                         for count in range(minimum, min(maximum, len(candidates)) + 1)
                         for selection in combinations(candidates, count)),
                        engine.rules.legal_action_enumeration_limit))


def _historical_positive_compositions(total, parts):
    if parts == 1:
        if total >= 1:
            yield (total,)
        return
    for first in range(1, total - parts + 2):
        for rest in _historical_positive_compositions(total - first, parts - 1):
            yield (first, *rest)


def _historical_allocation_selections(engine, effects, source_definition,
                                      *, from_ability=False, source_card_id=None, x_value=0):
    effect = next((item for item in effects if item.distributed), None)
    if effect is None:
        return ((),)
    candidates = [*engine.state.turn_order]
    candidates.extend(card_id for player in engine.state.players.values()
                      for card_id in player.zones[Zone.BATTLEFIELD]
                      if engine._card_can_be_targeted(source_definition, card_id,
                                                      from_ability, source_card_id))
    results = []
    for count in range(effect.minimum_targets, min(effect.maximum_targets, len(candidates)) + 1):
        for selected in combinations(candidates, count):
            for amounts in _historical_positive_compositions(engine._effect_amount(effect, x_value), count):
                results.append(tuple(TargetAllocation(target_id, amount)
                                     for target_id, amount in zip(selected, amounts, strict=True)))
                if len(results) >= engine.rules.legal_action_enumeration_limit:
                    return tuple(results)
    return tuple(results)


def _historical_card_cost_options(engine, definition, player_id):
    result = []
    if definition.x_cost is not None:
        result.extend((None, x, engine._resolve_x_cost(definition.x_cost, x))
                      for x in islice(range(definition.x_cost.minimum,
                                            definition.x_cost.maximum + 1),
                                      engine.rules.legal_action_enumeration_limit))
    else:
        normal = (engine._resolve_dynamic_cost(definition.dynamic_cost, player_id)
                  if definition.dynamic_cost is not None else CompositeCost(steps=definition.cost))
        result.append((None, None, normal))
    alternatives = [*definition.alternative_costs]
    alternatives.extend(engine._resolve_dynamic_cost(item, player_id)
                        for item in definition.dynamic_alternative_costs)
    result.extend((index, None, cost) for index, cost in enumerate(alternatives))
    first_x_index = len(alternatives)
    for offset, x_cost in enumerate(definition.x_alternative_costs):
        result.extend((first_x_index + offset, x, engine._resolve_x_cost(x_cost, x))
                      for x in islice(range(x_cost.minimum, x_cost.maximum + 1),
                                      engine.rules.legal_action_enumeration_limit))
    return tuple(result)


@pytest.mark.parametrize("semantics", SEMANTICS)
def test_resolver_has_only_its_context(semantics):
    engine = _engine(semantics)
    assert vars(engine._options) == {"_context": engine}


@pytest.mark.parametrize("semantics", SEMANTICS)
@pytest.mark.parametrize(("effects", "pool", "limit"), [
    ((), ("a", "b"), 20),
    ((EffectDefinition(EffectKind.DEAL_WOUNDS, 1, TargetMode.CHOSEN_PLAYER, minimum_targets=0),), ("a", "b"), 20),
    ((EffectDefinition(EffectKind.DEAL_WOUNDS, 1, TargetMode.CHOSEN_PLAYER, minimum_targets=1, maximum_targets=1),), ("b", "a"), 20),
    ((EffectDefinition(EffectKind.DEAL_WOUNDS, 1, TargetMode.CHOSEN_PLAYER, minimum_targets=1, maximum_targets=3),), ("c", "a", "b"), 20),
    ((EffectDefinition(EffectKind.DEAL_WOUNDS, 1, TargetMode.CHOSEN_PLAYER, minimum_targets=0, maximum_targets=9),), (), 20),
    ((EffectDefinition(EffectKind.DEAL_WOUNDS, 1, TargetMode.CHOSEN_PLAYER, minimum_targets=0, maximum_targets=3),), ("a", "b", "c"), 3),
    ((EffectDefinition(EffectKind.DEAL_WOUNDS, 1, TargetMode.CHOSEN_PLAYER, minimum_targets=0, maximum_targets=3), EffectDefinition(EffectKind.HEAL_WOUNDS, 1, TargetMode.CHOSEN_PLAYER, minimum_targets=1, maximum_targets=2)), ("a", "b", "c"), 20),
])
def test_target_selections_parity_and_exact_order(semantics, effects, pool, limit):
    engine = _engine(semantics, limit)
    expected = _pure_query(engine, lambda: _historical_target_selections(engine, effects, TargetMode.CHOSEN_PLAYER, pool))
    actual = _pure_query(engine, lambda: engine._options.target_selections(effects, TargetMode.CHOSEN_PLAYER, pool))
    assert actual == expected


@pytest.mark.parametrize("semantics", SEMANTICS)
@pytest.mark.parametrize(("effects", "limit"), [
    ((), 50),
    ((EffectDefinition(EffectKind.SHUFFLE_ZONE, 1, TargetMode.CHOSEN_ZONE),), 50),
    ((EffectDefinition(EffectKind.SHUFFLE_ZONE, 1, TargetMode.CHOSEN_ZONE, minimum_targets=0, maximum_targets=3),), 8),
    ((EffectDefinition(EffectKind.SHUFFLE_ZONE, 1, TargetMode.CHOSEN_ZONE, minimum_targets=1, maximum_targets=9), EffectDefinition(EffectKind.SHUFFLE_ZONE, 1, TargetMode.CHOSEN_ZONE, minimum_targets=2, maximum_targets=4)), 5),
])
def test_zone_target_selections_parity_players_then_all_zones(semantics, effects, limit):
    engine = _engine(semantics, limit)
    expected = _pure_query(engine, lambda: _historical_zone_target_selections(engine, effects))
    actual = _pure_query(engine, lambda: engine._options.zone_target_selections(effects))
    assert actual == expected
    zones = tuple(engine.state.players["A"].zones)
    if effects and limit >= len(zones) * 2:
        assert actual[:len(zones)] == tuple((ZoneTarget("A", zone),) for zone in zones)


@pytest.mark.parametrize(("total", "parts", "exact"), [
    (1, 1, ((1,),)), (2, 1, ((2,),)), (3, 2, ((1, 2), (2, 1))),
    (5, 3, ((1, 1, 3), (1, 2, 2), (1, 3, 1), (2, 1, 2), (2, 2, 1), (3, 1, 1))),
    (2, 3, ()),
])
def test_positive_compositions_parity_and_exact_order(total, parts, exact):
    engine = _engine(EngineSemantics.CURRENT)
    expected = tuple(_historical_positive_compositions(total, parts))
    actual = _pure_query(engine, lambda: tuple(engine._options.positive_compositions(total, parts)))
    assert actual == expected == exact


@pytest.mark.parametrize("semantics", SEMANTICS)
@pytest.mark.parametrize(("minimum", "maximum", "amount", "x_multiplier", "x_value", "ability", "limit"), [
    (1, 1, 3, 0, 0, False, 50), (1, 3, 4, 0, 0, False, 50),
    (2, 4, 5, 0, 0, False, 7), (1, 3, 1, 2, 2, False, 10),
    (1, 4, 4, 0, 0, True, 50),
])
def test_allocation_selections_parity_targets_amounts_immunity_and_truncation(
        semantics, minimum, maximum, amount, x_multiplier, x_value, ability, limit):
    engine = _engine(semantics, limit)
    source = engine.catalog.get("QUICK" if not ability else "NORMAL")
    source_id = next(cid for cid, card in engine.state.cards.items() if card.definition_id == source.card_id)
    effect = EffectDefinition(EffectKind.DEAL_HARM, amount, TargetMode.CHOSEN_ENTITY,
                              minimum_targets=minimum, maximum_targets=maximum,
                              distributed=True, x_multiplier=x_multiplier)
    effects = (effect,)
    expected = _pure_query(engine, lambda: _historical_allocation_selections(
        engine, effects, source, from_ability=ability, source_card_id=source_id, x_value=x_value))
    actual = _pure_query(engine, lambda: engine._options.allocation_selections(
        effects, source, from_ability=ability, source_card_id=source_id, x_value=x_value))
    assert actual == expected
    immune_id = next(cid for cid, card in engine.state.cards.items() if card.definition_id == "IMMUNE")
    assert all(all(allocation.target_id != immune_id for allocation in selection) for selection in actual)


def _dynamic(component=CostComponent.STEPS, metric=CostMetric.OWN_WOUNDS, multiplier=2):
    return DynamicCostDefinition(component, (CostTerm(metric, multiplier),),
                                 base=CompositeCost(wounds=1), offset=1, minimum=0, maximum=20)


@pytest.mark.parametrize("semantics", SEMANTICS)
@pytest.mark.parametrize(("definition", "limit"), [
    (CardDefinition("C1", "Fijo", CardKind.ARTIFACT, 4), 20),
    (CardDefinition("C2", "Dinámico", CardKind.ARTIFACT, 0, dynamic_cost=_dynamic()), 20),
    (CardDefinition("C3", "X", CardKind.ARTIFACT, 0, x_cost=XCostDefinition(CostComponent.STEPS, CompositeCost(wounds=1), 2, 1, 4)), 20),
    (CardDefinition("C4", "Alternativas", CardKind.ARTIFACT, 3,
                    alternative_costs=(CompositeCost(wounds=2),),
                    dynamic_alternative_costs=(_dynamic(CostComponent.MILL_COUNT),),
                    x_alternative_costs=(XCostDefinition(CostComponent.DISCARD_COUNT, minimum=0, maximum=2),)), 20),
    (CardDefinition("C5", "Todo X", CardKind.ARTIFACT, 0,
                    x_cost=XCostDefinition(CostComponent.STEPS, minimum=2, maximum=8),
                    alternative_costs=(CompositeCost(steps=9),),
                    x_alternative_costs=(XCostDefinition(CostComponent.WOUNDS, minimum=1, maximum=5),)), 2),
])
def test_card_cost_options_parity_indices_x_composite_cost_and_limits(semantics, definition, limit):
    engine = _engine(semantics, limit)
    expected = _pure_query(engine, lambda: _historical_card_cost_options(engine, definition, "A"))
    actual = _pure_query(engine, lambda: engine._options.card_cost_options(definition, "A"))
    assert actual == expected
    assert all(isinstance(item, tuple) and len(item) == 3 and isinstance(item[2], CompositeCost)
               for item in actual)


# Estos escenarios ejercitan los helpers anteriores a través de la API pública.
# El oráculo se importa del test del enumerador: deliberadamente no mantenemos
# aquí una segunda copia de _legal_plays, _legal_ability_activations ni de la
# enumeración de objetivos de triggers.
def _resolver_scenario_definitions():
    player_effect = EffectDefinition(
        EffectKind.DEAL_WOUNDS, 1, TargetMode.CHOSEN_PLAYER
    )
    return (
        CardDefinition("PAR_NORMAL", "Normal", CardKind.ARTIFACT, 1),
        CardDefinition(
            "PAR_X", "X", CardKind.QUICK_RESOURCE, 0, permanent=False,
            x_cost=XCostDefinition(CostComponent.STEPS, minimum=0, maximum=4),
        ),
        CardDefinition(
            "PAR_ALT", "Alternativo", CardKind.ARTIFACT, 99,
            alternative_costs=(CompositeCost(discard_count=1),),
        ),
        CardDefinition(
            "PAR_DYNAMIC", "Dinámico", CardKind.ARTIFACT, 0,
            dynamic_cost=DynamicCostDefinition(
                CostComponent.STEPS, (CostTerm(CostMetric.OWN_WOUNDS),), maximum=9
            ),
        ),
        CardDefinition(
            "PAR_PLAYER", "Objetivo jugador", CardKind.QUICK_RESOURCE, 0,
            permanent=False, effects=(player_effect,),
        ),
        CardDefinition(
            "PAR_PERMANENT", "Objetivo permanente", CardKind.QUICK_RESOURCE, 0,
            permanent=False,
            effects=(EffectDefinition(
                EffectKind.DEAL_DAMAGE, 1, TargetMode.CHOSEN_PERMANENT
            ),),
        ),
        CardDefinition(
            "PAR_ZONE", "Objetivo zona", CardKind.QUICK_RESOURCE, 0,
            permanent=False,
            effects=(EffectDefinition(
                EffectKind.SHUFFLE_ZONE, 1, TargetMode.CHOSEN_ZONE
            ),),
        ),
        CardDefinition(
            "PAR_DISTRIBUTED", "Distribuido", CardKind.QUICK_RESOURCE, 0,
            permanent=False,
            effects=(EffectDefinition(
                EffectKind.DEAL_HARM, 3, TargetMode.CHOSEN_ENTITY,
                minimum_targets=1, maximum_targets=2, distributed=True,
            ),),
        ),
        CardDefinition(
            "PAR_ABILITY", "Habilidad", CardKind.CREATURE, 1, base_strength=2,
            abilities=(AbilityDefinition("pulse", (player_effect,)),),
        ),
        CardDefinition(
            "PAR_ABILITY_X", "Habilidad X", CardKind.CREATURE, 1,
            base_strength=2,
            abilities=(AbilityDefinition(
                "channel",
                (EffectDefinition(
                    EffectKind.DEAL_WOUNDS, 0, TargetMode.CHOSEN_PLAYER,
                    x_multiplier=1,
                ),),
                x_cost=XCostDefinition(CostComponent.STEPS, maximum=4),
            ),),
        ),
        CardDefinition(
            "PAR_TRIGGER", "Trigger con objetivos", CardKind.CREATURE, 1,
            base_strength=2,
            abilities=(AbilityDefinition("hit", (player_effect,)),),
        ),
        CardDefinition("PAR_FODDER", "Descartable", CardKind.ARTIFACT, 99),
        CardDefinition("PAR_TARGET", "Permanente público", CardKind.CREATURE, 1,
                       base_strength=2),
    )


def _force_resolver_zone(engine, definition_id, player_id, zone):
    card_id = next(
        card_id for card_id, card in engine.state.cards.items()
        if card.definition_id == definition_id
    )
    for player in engine.state.players.values():
        for cards in player.zones.values():
            if card_id in cards:
                cards.remove(card_id)
    engine.state.players[player_id].zones[zone].append(card_id)
    engine.state.cards[card_id].zone = zone
    engine.state.cards[card_id].controller_id = player_id
    return card_id


@pytest.fixture
def resolver_legal_actions_engine(request):
    """Partida mínima que deja visible únicamente la familia solicitada."""
    scenario, limit, semantics = request.param
    engine = GameEngine(RuleSet(legal_action_enumeration_limit=limit))
    engine.new_match(
        {
            "A": [*_resolver_scenario_definitions(), *test_deck("PA", 14)],
            "B": test_deck("PB", 14),
        },
        seed=813,
    )
    engine._semantics = semantics
    engine.state.players["A"].steps = 10
    engine.state.players["A"].wounds = 2

    # La mano inicial es aleatoria: retiramos primero todas las definiciones de
    # caracterización para que cada caso exponga una sola ruta del resolver.
    for definition in _resolver_scenario_definitions():
        _force_resolver_zone(engine, definition.card_id, "A", Zone.DECK)

    hand_scenarios = {
        "carta normal": "PAR_NORMAL",
        "X": "PAR_X",
        "coste alternativo": "PAR_ALT",
        "coste dinámico": "PAR_DYNAMIC",
        "objetivo jugador": "PAR_PLAYER",
        "objetivo permanente": "PAR_PERMANENT",
        "objetivo zona": "PAR_ZONE",
        "efecto distribuido": "PAR_DISTRIBUTED",
    }
    if scenario in hand_scenarios:
        _force_resolver_zone(engine, hand_scenarios[scenario], "A", Zone.HAND)
    if scenario == "coste alternativo":
        _force_resolver_zone(engine, "PAR_FODDER", "A", Zone.HAND)
    if scenario in {"objetivo permanente", "efecto distribuido"}:
        _force_resolver_zone(engine, "PAR_TARGET", "A", Zone.BATTLEFIELD)
    if scenario in {"habilidad activada", "habilidad X"}:
        definition_id = (
            "PAR_ABILITY" if scenario == "habilidad activada" else "PAR_ABILITY_X"
        )
        _force_resolver_zone(engine, definition_id, "A", Zone.BATTLEFIELD)
    if scenario == "trigger con objetivos":
        source = _force_resolver_zone(engine, "PAR_TRIGGER", "A", Zone.BATTLEFIELD)
        engine.state.pending_triggers = [StackItem(
            "parity-trigger", "A", source,
            (EffectDefinition(
                EffectKind.DEAL_WOUNDS, 1, TargetMode.CHOSEN_PLAYER
            ),),
            ability_id="hit", targets_locked=False,
        )]
    return engine


RESOLVER_LEGAL_ACTION_SCENARIOS = (
    "carta normal", "X", "coste alternativo", "coste dinámico",
    "objetivo jugador", "objetivo permanente", "objetivo zona",
    "efecto distribuido", "habilidad activada", "habilidad X",
    "trigger con objetivos",
)


def _command_shape(command):
    """Firma ordenada que hace explícitos clase y todos los campos del comando."""
    return type(command), tuple(
        (field.name, getattr(command, field.name))
        for field in fields(command)
    )


@pytest.mark.parametrize(
    "resolver_legal_actions_engine",
    tuple(
        (scenario, limit, semantics)
        for semantics in SEMANTICS
        for scenario in RESOLVER_LEGAL_ACTION_SCENARIOS
        for limit in (1, 2)
    ),
    indirect=True,
    ids=lambda value: "-".join(map(str, value)) if isinstance(value, tuple) else None,
)
def test_public_legal_actions_preserve_complete_order_and_small_limit_cutoff(
        resolver_legal_actions_engine):
    engine = resolver_legal_actions_engine
    historical = _pure_query(
        engine, lambda: _previous_legal_actions(engine, "A")
    )
    resolved = _pure_query(engine, lambda: engine.legal_actions("A"))

    # Igualdad de tupla protege cantidad y posición; la firma adicional nombra
    # explícitamente la clase y la totalidad de los campos de cada comando.
    assert resolved == historical
    assert tuple(map(_command_shape, resolved)) == tuple(
        map(_command_shape, historical)
    )
