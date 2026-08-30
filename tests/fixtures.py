from card_duel_engine.domain.enums import CardKind, CardRank, EffectKind, TargetMode
from card_duel_engine.domain.models import CardDefinition, EffectDefinition


def test_deck(prefix: str, size: int = 12) -> list[CardDefinition]:
    return [
        CardDefinition(
            card_id=f"{prefix}-{index:03d}",
            name=f"Criatura de prueba {index}",
            kind=CardKind.CREATURE,
            cost=5,
            base_strength=5,
            set_id="test-fixtures",
        )
        for index in range(size)
    ]


# Fábrica compartida; el nombre histórico no representa una prueba pytest.
test_deck.__test__ = False


def legendary_fixture(card_id: str = "TEST-LEGENDARY") -> CardDefinition:
    return CardDefinition(
        card_id=card_id,
        name="Legendario de prueba",
        kind=CardKind.CREATURE,
        rank=CardRank.LEGENDARY,
        cost=20,
        base_strength=20,
        legendary_effects=(EffectDefinition(EffectKind.GAIN_STEPS, 3),),
        set_id="test-fixtures",
    )


def quick_damage_fixture(card_id: str = "TEST-QUICK-DAMAGE") -> CardDefinition:
    return CardDefinition(
        card_id=card_id,
        name="Daño rápido de prueba",
        kind=CardKind.QUICK_RESOURCE,
        cost=5,
        permanent=False,
        transmutable=False,
        effects=(
            EffectDefinition(EffectKind.DEAL_WOUNDS, 5, TargetMode.CHOSEN_PLAYER),
        ),
        set_id="test-fixtures",
    )


def public_card_fixture(card_id: str = "TEST-PUBLIC-CARD") -> CardDefinition:
    """Definición inequívoca para probar proyecciones, no contenido de producción."""

    return CardDefinition(
        card_id=card_id,
        name="Nombre mecánico que no debe publicarse",
        kind=CardKind.CREATURE,
        cost=17,
        rank=CardRank.DIVINE,
        base_strength=23,
        set_id="test-public-catalog",
        revision=41,
        keywords=frozenset(("zeta", "alfa")),
        subtypes=frozenset(("sabio", "arcano")),
    )
