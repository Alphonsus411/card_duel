from __future__ import annotations

import pytest

from card_duel_engine.domain.enums import (
    EffectKind,
    Phase,
    RevealExhaustionPolicy,
    TargetMode,
    Zone,
)
from card_duel_engine.domain.models import CardFilter, EffectDefinition, TextPatchDefinition


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        (
            {"kind": EffectKind.DEAL_WOUNDS, "amount": 1, "target": TargetMode.CHOSEN_PERMANENT},
            "objetivo de jugador",
        ),
        (
            {"kind": EffectKind.TAP, "amount": 1, "target": TargetMode.CHOSEN_PLAYER},
            "objetivo de permanente",
        ),
        (
            {"kind": EffectKind.SHUFFLE_ZONE, "amount": 0},
            "zona objetivo",
        ),
        (
            {"kind": EffectKind.DEAL_HARM, "amount": 1, "target": TargetMode.CHOSEN_ENTITY},
            "reparto explícito",
        ),
        (
            {"kind": EffectKind.MOVE_CARDS, "amount": 0, "target": TargetMode.CHOSEN_ZONE},
            "zona de destino",
        ),
        (
            {"kind": EffectKind.SEARCH_ZONE, "amount": 0, "target": TargetMode.CHOSEN_ZONE},
            "zona de destino",
        ),
        (
            {
                "kind": EffectKind.REVEAL_UNTIL,
                "amount": 0,
                "target": TargetMode.CHOSEN_ZONE,
                "destination_zone": Zone.HAND,
            },
            "filtro mecánico",
        ),
        (
            {
                "kind": EffectKind.REVEAL_UNTIL,
                "amount": 0,
                "target": TargetMode.CHOSEN_ZONE,
                "destination_zone": Zone.HAND,
                "failure_destination_zone": Zone.DISCARD,
                "search_filter": CardFilter(),
            },
            "política de agotamiento",
        ),
        (
            {
                "kind": EffectKind.TRANSFORM_DEFINITION,
                "amount": 1,
                "target": TargetMode.CHOSEN_PERMANENT,
            },
            "definición de destino",
        ),
        (
            {
                "kind": EffectKind.MODIFY_TEXT,
                "amount": 1,
                "target": TargetMode.CHOSEN_PERMANENT,
            },
            "parche declarativo",
        ),
        (
            {"kind": EffectKind.SKIP_PHASE, "amount": 1},
            "indicar cuál",
        ),
        (
            {
                "kind": EffectKind.DEAL_WOUNDS,
                "amount": 1,
                "failure_destination_zone": Zone.DISCARD,
            },
            "campos de revelación",
        ),
        (
            {
                "kind": EffectKind.DEAL_WOUNDS,
                "amount": 1,
                "text_patch": TextPatchDefinition(),
            },
            "Solo MODIFY_TEXT",
        ),
        (
            {
                "kind": EffectKind.DEAL_WOUNDS,
                "amount": 1,
                "minimum_targets": 2,
                "maximum_targets": 1,
            },
            "intervalo de objetivos",
        ),
        (
            {"kind": EffectKind.DEAL_WOUNDS, "amount": -1},
            "no puede ser negativa",
        ),
        (
            {"kind": EffectKind.DEAL_WOUNDS, "amount": 1, "x_multiplier": -1},
            "multiplicador de X",
        ),
    ),
)
def test_invalid_effect_definitions_fail_before_reaching_the_stack(
    kwargs: dict[str, object], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        EffectDefinition(**kwargs)  # type: ignore[arg-type]


def test_reveal_until_rejects_reveal_as_a_final_destination() -> None:
    with pytest.raises(ValueError, match="destinos finales"):
        EffectDefinition(
            EffectKind.REVEAL_UNTIL,
            0,
            TargetMode.CHOSEN_ZONE,
            destination_zone=Zone.REVEAL,
            failure_destination_zone=Zone.DISCARD,
            search_filter=CardFilter(),
            exhaustion_policy=RevealExhaustionPolicy.COMPLETE,
        )


def test_valid_phase_suppression_remains_declarative() -> None:
    effect = EffectDefinition(EffectKind.SKIP_PHASE, 1, phase=Phase.DRAW)

    assert effect.kind is EffectKind.SKIP_PHASE
