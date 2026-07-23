from __future__ import annotations

from dataclasses import replace

from ..domain.enums import CostMetric, Zone
from ..domain.models import (
    CardDefinition,
    CompositeCost,
    DynamicCostDefinition,
    GameState,
    TextPatchDefinition,
    XCostDefinition,
)


def resolve_dynamic_cost(
    definition: DynamicCostDefinition, state: GameState, player_id: str
) -> CompositeCost:
    """Evalúa una fórmula sin depender del motor ni modificar el estado."""

    player = state.players[player_id]
    metrics = {
        CostMetric.OWN_WOUNDS: player.wounds,
        CostMetric.OWN_STEPS: player.steps,
        CostMetric.OWN_HAND_SIZE: len(player.zones[Zone.HAND]),
        CostMetric.OWN_BATTLEFIELD_SIZE: len(player.zones[Zone.BATTLEFIELD]),
        CostMetric.OWN_DISCARD_SIZE: len(player.zones[Zone.DISCARD]),
        CostMetric.OWN_EXILE_SIZE: len(player.zones[Zone.EXILE]),
        CostMetric.OPPONENT_BATTLEFIELD_SIZE: sum(
            len(other.zones[Zone.BATTLEFIELD])
            for other_id, other in state.players.items()
            if other_id != player_id
        ),
        CostMetric.TURN_NUMBER: state.turn_number,
    }
    dynamic_value = definition.offset + sum(
        metrics[term.metric] * term.multiplier for term in definition.terms
    )
    dynamic_value = max(definition.minimum, dynamic_value)
    if definition.maximum is not None:
        dynamic_value = min(definition.maximum, dynamic_value)
    component = definition.component.value
    return replace(
        definition.base,
        **{component: getattr(definition.base, component) + dynamic_value},
    )


def resolve_x_cost(definition: XCostDefinition, x_value: int) -> CompositeCost:
    """Convierte X en un coste compuesto concreto e inmutable."""

    if not definition.minimum <= x_value <= definition.maximum:
        raise ValueError("El valor de X no pertenece al intervalo permitido")
    component = definition.component.value
    amount = x_value * definition.multiplier
    return replace(
        definition.base,
        **{component: getattr(definition.base, component) + amount},
    )


def apply_text_patch(
    definition: CardDefinition, patch: TextPatchDefinition
) -> CardDefinition:
    """Construye una vista efectiva sin mutar la definición del catálogo."""

    abilities = [
        ability
        for ability in definition.abilities
        if ability.ability_id not in patch.remove_ability_ids
    ]
    for granted in patch.add_abilities:
        abilities = [
            ability for ability in abilities if ability.ability_id != granted.ability_id
        ]
        abilities.append(granted)
    definition = replace(
        definition,
        keywords=(definition.keywords | patch.grant_keywords) - patch.remove_keywords,
        subtypes=(definition.subtypes | patch.grant_subtypes) - patch.remove_subtypes,
        abilities=tuple(abilities),
        transmutable=(
            definition.transmutable
            if patch.set_transmutable is None
            else patch.set_transmutable
        ),
    )
    for effect_patch in patch.effect_patches:
        if effect_patch.ability_id is not None:
            ability_index = next(
                (
                    index
                    for index, ability in enumerate(definition.abilities)
                    if ability.ability_id == effect_patch.ability_id
                ),
                None,
            )
            if ability_index is None:
                raise IndexError("Habilidad de parche inexistente")
            effects = list(definition.abilities[ability_index].effects)
        elif effect_patch.legendary:
            effects = list(definition.legendary_effects)
        else:
            effects = list(definition.effects)
        if effect_patch.effect_index >= len(effects):
            raise IndexError("Efecto de parche inexistente")
        original = effects[effect_patch.effect_index]
        effects[effect_patch.effect_index] = replace(
            original,
            amount=original.amount + effect_patch.amount_delta,
            minimum_targets=(
                original.minimum_targets
                if effect_patch.set_minimum_targets is None
                else effect_patch.set_minimum_targets
            ),
            maximum_targets=(
                original.maximum_targets
                if effect_patch.set_maximum_targets is None
                else effect_patch.set_maximum_targets
            ),
            target=(
                original.target
                if effect_patch.set_target is None
                else effect_patch.set_target
            ),
        )
        if effect_patch.ability_id is not None:
            abilities = list(definition.abilities)
            abilities[ability_index] = replace(
                abilities[ability_index], effects=tuple(effects)
            )
            definition = replace(definition, abilities=tuple(abilities))
        elif effect_patch.legendary:
            definition = replace(definition, legendary_effects=tuple(effects))
        else:
            definition = replace(definition, effects=tuple(effects))
    return definition
