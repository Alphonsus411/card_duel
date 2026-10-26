from card_duel_engine import GameEngine
from card_duel_engine.catalog import CardCatalog
from card_duel_engine.domain.enums import (
    EffectKind,
    Phase,
    RevealExhaustionPolicy,
    TargetMode,
    Zone,
)
from card_duel_engine.domain.models import (
    CardFilter,
    EffectDefinition,
    TextPatchDefinition,
)


PLAYER_KINDS = frozenset(
    {
        EffectKind.DEAL_WOUNDS,
        EffectKind.HEAL_WOUNDS,
        EffectKind.GAIN_STEPS,
        EffectKind.DRAW_CARDS,
        EffectKind.PREVENT_WOUNDS,
        EffectKind.SKIP_PHASE,
    }
)
PERMANENT_KINDS = frozenset(
    {
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
)
ZONE_KINDS = frozenset(
    {
        EffectKind.MOVE_CARDS,
        EffectKind.SEARCH_ZONE,
        EffectKind.SHUFFLE_ZONE,
        EffectKind.REVEAL_UNTIL,
    }
)
ALLOCATED_KINDS = frozenset({EffectKind.DEAL_HARM})


def _definition_for(kind: EffectKind) -> EffectDefinition:
    if kind in PLAYER_KINDS:
        return EffectDefinition(
            kind,
            1,
            phase=Phase.DRAW if kind is EffectKind.SKIP_PHASE else None,
        )
    if kind in PERMANENT_KINDS:
        kwargs: dict[str, object] = {"target": TargetMode.CHOSEN_PERMANENT}
        if kind is EffectKind.MODIFY_STRENGTH:
            return EffectDefinition(kind, -1, **kwargs)
        if kind is EffectKind.TRANSFORM_DEFINITION:
            kwargs["transform_definition_id"] = "target-definition"
        if kind is EffectKind.MODIFY_TEXT:
            kwargs["text_patch"] = TextPatchDefinition(
                grant_keywords=frozenset({"FLYING"})
            )
        return EffectDefinition(kind, 1, **kwargs)
    if kind is EffectKind.DEAL_HARM:
        return EffectDefinition(
            kind, 1, TargetMode.CHOSEN_ENTITY, distributed=True
        )
    if kind is EffectKind.MOVE_CARDS:
        return EffectDefinition(
            kind, 1, TargetMode.CHOSEN_ZONE, destination_zone=Zone.HAND
        )
    if kind is EffectKind.SEARCH_ZONE:
        return EffectDefinition(
            kind, 0, TargetMode.CHOSEN_ZONE, destination_zone=Zone.HAND,
            selection_minimum=0,
        )
    if kind is EffectKind.SHUFFLE_ZONE:
        return EffectDefinition(kind, 0, TargetMode.CHOSEN_ZONE)
    if kind is EffectKind.REVEAL_UNTIL:
        return EffectDefinition(
            kind,
            0,
            TargetMode.CHOSEN_ZONE,
            destination_zone=Zone.HAND,
            failure_destination_zone=Zone.DISCARD,
            search_filter=CardFilter(),
            exhaustion_policy=RevealExhaustionPolicy.COMPLETE,
        )
    raise AssertionError(f"EffectKind no clasificado: {kind}")


def test_effect_kind_categories_are_closed_and_exhaustive() -> None:
    categories = PLAYER_KINDS, PERMANENT_KINDS, ZONE_KINDS, ALLOCATED_KINDS
    assert set().union(*categories) == set(EffectKind)
    assert sum(len(category) for category in categories) == len(EffectKind)


def test_each_effect_kind_has_a_valid_declarative_shape() -> None:
    definitions = {_definition_for(kind) for kind in EffectKind}
    assert {definition.kind for definition in definitions} == set(EffectKind)


def test_effect_manager_registry_matches_the_closed_contract() -> None:
    manager = GameEngine(catalog=CardCatalog())._effects
    assert manager.supported_kinds == frozenset(EffectKind)
