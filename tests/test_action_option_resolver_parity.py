"""Paridad observable de los cinco helpers extraídos a ``ActionOptionResolver``.

Los helpers ``_historical_*`` congelan únicamente los cuerpos que fueron
extraídos. Las dependencias semánticas siguen delegándose al motor, evitando
duplicar validadores de jugadas, activaciones, disparos, objetivos o efectos.
"""

import json
from itertools import combinations, islice

import pytest

from card_duel_engine import EngineSemantics, GameEngine, RuleSet
from card_duel_engine.domain import (
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
from card_duel_engine.persistence.codec import encode_value

from fixtures import test_deck


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
