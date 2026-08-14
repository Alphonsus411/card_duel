"""Caracterización de la caché local usada al enumerar objetivos legales.

El oráculo de este módulo ejecuta el mismo enumerador anulando explícitamente
el ``query_context``.  Así se compara la optimización con una consulta fresca
de cada definición, keyword y efecto continuo, sin duplicar las reglas.
"""

import hashlib
import json
from types import MethodType

import pytest

from card_duel_engine import EngineSemantics, GameEngine, RuleSet
from card_duel_engine.domain import (
    AbilityDefinition,
    AppliedTextPatch,
    CardDefinition,
    CardKind,
    CardRank,
    CompositeCost,
    ContinuousEffectDefinition,
    ControllerScope,
    EffectDefinition,
    EffectKind,
    TargetMode,
    TextPatchDefinition,
    Zone,
)
from card_duel_engine.engine import ActivateAbility, PlayCard
from card_duel_engine.engine.actions import LegalActionEnumerator
from card_duel_engine.domain.errors import IllegalAction
from card_duel_engine.persistence.codec import encode_value

from fixtures import test_deck


SEMANTICS = (EngineSemantics.CURRENT, EngineSemantics.LEGACY_019)


def _canonical(value) -> str:
    return json.dumps(
        encode_value(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def _digest(commands) -> str:
    return hashlib.sha256(_canonical(commands).encode()).hexdigest()


def _query(engine: GameEngine, callback):
    """Una consulta legal debe ser exactamente pura, no solo equivalente."""
    before = _canonical(engine.state)
    result = callback()
    assert _canonical(engine.state) == before
    return result


def _without_local_cache(engine: GameEngine):
    """Oráculo baseline: ejecuta el enumerador ignorando toda caché de consulta."""
    names = ("_definition", "_continuous_effects_for", "_effective_keywords")
    originals = {name: getattr(engine, name) for name in names}

    def definition(self, card_id, query_context=None):
        return originals["_definition"](card_id)

    def continuous(self, card_id, query_context=None):
        return originals["_continuous_effects_for"](card_id)

    def keywords(self, card_id, query_context=None):
        return originals["_effective_keywords"](card_id)

    try:
        engine._definition = MethodType(definition, engine)
        engine._continuous_effects_for = MethodType(continuous, engine)
        engine._effective_keywords = MethodType(keywords, engine)
        return LegalActionEnumerator(engine).legal_actions("A")
    finally:
        for name, original in originals.items():
            setattr(engine, name, original)


def _definitions():
    chosen = (EffectDefinition(EffectKind.DEAL_DAMAGE, 1, TargetMode.CHOSEN_PERMANENT),)
    distributed = (
        EffectDefinition(
            EffectKind.DEAL_HARM,
            2,
            TargetMode.CHOSEN_ENTITY,
            minimum_targets=1,
            maximum_targets=2,
            distributed=True,
        ),
    )
    return (
        CardDefinition("EVENT", "Evento", CardKind.EVENT, 0, permanent=False, effects=chosen),
        CardDefinition("QUICK", "Rápida", CardKind.QUICK_RESOURCE, 0, permanent=False, effects=chosen),
        CardDefinition("DISTRIBUTE", "Reparto", CardKind.EVENT, 0, permanent=False, effects=distributed),
        CardDefinition(
            "ABILITY", "Fuente de habilidad", CardKind.ARTIFACT, 0,
            abilities=(AbilityDefinition("aim", chosen, CompositeCost()),),
        ),
        CardDefinition("OPEN", "Normal", CardKind.ARTIFACT, 0),
        CardDefinition("IA", "Inmune habilidad", CardKind.CREATURE, 0, base_strength=2,
                       keywords=frozenset({"IMMUNE_ABILITIES"})),
        CardDefinition("IE", "Inmune evento", CardKind.CREATURE, 0, base_strength=2,
                       keywords=frozenset({"IMMUNE_EVENT"})),
        CardDefinition("IQ", "Inmune rápida", CardKind.CREATURE, 0, base_strength=2,
                       keywords=frozenset({"IMMUNE_QUICK"})),
        CardDefinition("DIVINE", "Divina", CardKind.CREATURE, 0, CardRank.DIVINE, 2),
        CardDefinition(
            "AURA", "Aura", CardKind.ARTIFACT, 0,
            continuous_effects=(ContinuousEffectDefinition(
                grant_keywords=frozenset({"IMMUNE_EVENT"}),
                controller_scope=ControllerScope.OPPONENTS,
                affected_kinds=frozenset({CardKind.CREATURE}),
            ),),
        ),
        CardDefinition(
            "REMOVE", "Retira", CardKind.ARTIFACT, 0,
            continuous_effects=(ContinuousEffectDefinition(
                remove_keywords=frozenset({"IMMUNE_EVENT"}),
                controller_scope=ControllerScope.OPPONENTS,
            ),),
        ),
        CardDefinition("EQUIP", "Equipo", CardKind.EQUIPMENT, 0,
                       equipment_granted_keywords=frozenset({"IMMUNE_QUICK"})),
        CardDefinition("ALT", "Definición inmune", CardKind.CREATURE, 0, base_strength=3,
                       keywords=frozenset({"IMMUNE_EVENT"})),
    )


def _engine(semantics: EngineSemantics):
    engine = GameEngine(RuleSet(legal_action_enumeration_limit=5_000))
    engine.new_match(
        {"A": [*_definitions(), *test_deck("A", 13)], "B": test_deck("B", 13)},
        seed=919,
    )
    engine._semantics = semantics
    engine.state.phase = engine.state.phase.EFFECTS
    engine.state.priority_player_id = "A"
    engine.state.players["A"].steps = 30
    ids = {}
    for definition in _definitions():
        card_id = next(
            cid for cid, instance in engine.state.cards.items()
            if instance.definition_id == definition.card_id
        )
        ids[definition.card_id] = card_id
        destination = (Zone.HAND if definition.card_id in {"EVENT", "QUICK", "DISTRIBUTE"}
                       else Zone.DISCARD if definition.card_id in {"AURA", "REMOVE"}
                       else Zone.BATTLEFIELD)
        for player in engine.state.players.values():
            for cards in player.zones.values():
                if card_id in cards:
                    cards.remove(card_id)
        engine.state.players["A"].zones[destination].append(card_id)
        engine.state.cards[card_id].zone = destination
    # Los objetivos pertenecen al rival, para hacer sensibles control y auras.
    for key in ("OPEN", "IA", "IE", "IQ", "DIVINE", "ALT"):
        card_id = ids[key]
        engine.state.players["A"].zones[Zone.BATTLEFIELD].remove(card_id)
        engine.state.players["B"].zones[Zone.BATTLEFIELD].append(card_id)
        engine.state.cards[card_id].controller_id = "B"
    engine.state.cards[ids["EQUIP"]].attached_to = ids["OPEN"]
    return engine, ids


def _assert_parity(engine: GameEngine):
    cached = _query(engine, lambda: engine.legal_actions("A"))
    baseline = _query(engine, lambda: _without_local_cache(engine))
    # Igualdad de tupla preserva tipo, contenido, conteo y orden.
    assert cached == baseline
    assert tuple(type(command) for command in cached) == tuple(type(command) for command in baseline)
    assert _canonical(cached) == _canonical(baseline)
    assert _digest(cached) == _digest(baseline)
    return cached


@pytest.mark.parametrize("semantics", SEMANTICS)
def test_hand_field_permanent_distributed_immunities_and_divine_match_baseline(semantics):
    engine, ids = _engine(semantics)
    actions = _assert_parity(engine)

    assert any(isinstance(action, PlayCard) and action.card_id == ids["EVENT"] for action in actions)
    assert any(isinstance(action, PlayCard) and action.card_id == ids["DISTRIBUTE"]
               and action.allocations for action in actions)
    assert any(isinstance(action, ActivateAbility) and action.source_card_id == ids["ABILITY"]
               for action in actions)
    encoded = _canonical(actions)
    assert ids["IA"] in encoded and ids["IE"] in encoded and ids["IQ"] in encoded
    assert ids["DIVINE"] in encoded


def _mutate(engine, ids, category):
    target = engine.state.cards[ids["OPEN"]]
    if category == "keyword":
        target.definition_id = "IE"
    elif category == "continuous":
        aura = engine.state.cards[ids["AURA"]]
        aura.zone = Zone.BATTLEFIELD
        engine.state.players["A"].zones[Zone.DISCARD].remove(ids["AURA"])
        engine.state.players["A"].zones[Zone.BATTLEFIELD].append(ids["AURA"])
    elif category == "transformation":
        target.transformed_as_creature = not target.transformed_as_creature
    elif category == "override":
        target.overridden_definition_id = "ALT"
    elif category == "control":
        target.controller_id = "A"
    elif category == "zone":
        engine.state.players["B"].zones[Zone.BATTLEFIELD].remove(ids["OPEN"])
        engine.state.players["B"].zones[Zone.EXILE].append(ids["OPEN"])
        target.zone = Zone.EXILE
    elif category == "ability_source":
        source = engine.state.cards[ids["ABILITY"]]
        engine.state.players["A"].zones[Zone.BATTLEFIELD].remove(ids["ABILITY"])
        engine.state.players["A"].zones[Zone.DISCARD].append(ids["ABILITY"])
        source.zone = Zone.DISCARD
    elif category == "text_patch":
        engine.state.text_patches.append(AppliedTextPatch(
            "patch-cache", ids["OPEN"], TextPatchDefinition(
                grant_keywords=frozenset({"IMMUNE_EVENT"})
            )
        ))
    else:  # equipment
        engine.state.cards[ids["EQUIP"]].attached_to = None


def _prepare_sensitive_category(engine, ids, category):
    """Activa la dependencia que transformación/control van a invalidar."""
    if category in {"transformation", "control"}:
        aura = engine.state.cards[ids["AURA"]]
        aura.zone = Zone.BATTLEFIELD
        engine.state.players["A"].zones[Zone.DISCARD].remove(ids["AURA"])
        engine.state.players["A"].zones[Zone.BATTLEFIELD].append(ids["AURA"])
    if category == "control":
        engine.state.cards[ids["OPEN"]].transformed_as_creature = True
    if category == "transformation":
        # Antes no es criatura y el aura no lo afecta; después sí.
        assert not engine.state.cards[ids["OPEN"]].transformed_as_creature


@pytest.mark.parametrize("semantics", SEMANTICS)
@pytest.mark.parametrize(
    "category",
    ("keyword", "continuous", "transformation", "override", "text_patch",
     "equipment", "control", "zone", "ability_source"),
)
def test_authoritative_mutation_is_visible_to_next_call_and_third_is_deterministic(
    semantics, category
):
    engine, ids = _engine(semantics)
    _prepare_sensitive_category(engine, ids, category)
    first = _assert_parity(engine)
    _mutate(engine, ids, category)
    second = _assert_parity(engine)
    third = _assert_parity(engine)

    assert second != first
    assert third == second
    assert _digest(third) == _digest(second)


@pytest.mark.parametrize("semantics", SEMANTICS)
def test_execution_validation_paths_do_not_reuse_enumeration_cache(semantics):
    engine, ids = _engine(semantics)
    actions = _assert_parity(engine)
    play = next(action for action in actions if isinstance(action, PlayCard)
                and action.card_id == ids["EVENT"] and action.chosen_card_ids == (ids["OPEN"],))
    ability = next(action for action in actions if isinstance(action, ActivateAbility)
                   and action.source_card_id == ids["ABILITY"]
                   and action.chosen_card_ids == (ids["OPEN"],))

    # Las tres rutas vuelven a consultar estado autoritativo tras enumerar.
    engine.state.cards[ids["OPEN"]].overridden_definition_id = "ALT"
    with pytest.raises(IllegalAction, match="inmune"):
        engine._play_card(play)
    engine.state.cards[ids["OPEN"]].overridden_definition_id = "IA"
    with pytest.raises(IllegalAction, match="inmune"):
        engine._activate_ability(ability)
    engine.state.cards[ids["OPEN"]].overridden_definition_id = "ALT"
    with pytest.raises(IllegalAction, match="inmune"):
        engine._validate_effect_targets(
            engine._definition(ids["EVENT"]).effects, (), (ids["OPEN"],), (), (),
            engine._definition(ids["EVENT"]),
        )
