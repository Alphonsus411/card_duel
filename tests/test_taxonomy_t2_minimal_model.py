from __future__ import annotations

from card_duel_engine.domain.enums import CardKind, LordDomain
from card_duel_engine.domain.models import CardDefinition


def test_lord_domain_preserves_both_accredited_card_kind_forms() -> None:
    explicit_lord = CardDefinition(
        "explicit-lord", "Señor", CardKind.LORD, 4,
        lord_domain=LordDomain.REALMS,
    )
    creature_lord = CardDefinition(
        "creature-lord", "Criatura Señor", CardKind.CREATURE, 4,
        lord_domain=LordDomain.REALMS,
    )

    assert explicit_lord.kind is CardKind.LORD
    assert creature_lord.kind is CardKind.CREATURE
    assert explicit_lord.lord_domain is LordDomain.REALMS
    assert creature_lord.lord_domain is LordDomain.REALMS
