from __future__ import annotations

from card_duel_engine.domain.enums import CardKind, CardRank, LordDomain
from card_duel_engine.domain.models import CardDefinition, CardFilter
from card_duel_engine.persistence.codec import decode_value, encode_value
from card_duel_engine.presentation import CardPresentation
from card_duel_engine.public_catalog import PublicCard


def _lord_definition() -> CardDefinition:
    return CardDefinition(
        card_id="taxonomy-t1-lord",
        name="Señor de prueba",
        kind=CardKind.LORD,
        cost=4,
        rank=CardRank.LEGENDARY,
        set_id="taxonomy-t1",
        lord_domain=LordDomain.REALMS,
        subtypes=frozenset({"Pixy", "spirit"}),
    )


def test_filter_conjoins_dimensions_and_keeps_subtype_intersection_semantics() -> None:
    definition = _lord_definition()

    assert CardFilter(
        kinds=frozenset({CardKind.LORD}),
        ranks=frozenset({CardRank.LEGENDARY}),
        subtypes=frozenset({"Pixy", "angel"}),
        definition_ids=frozenset({definition.card_id}),
    ).matches(definition)
    assert not CardFilter(subtypes=frozenset({"angel"})).matches(definition)
    assert not CardFilter(definition_ids=frozenset({"other-card"})).matches(definition)
    assert not CardFilter(kinds=frozenset({CardKind.CREATURE})).matches(definition)


def test_codec_roundtrip_keeps_each_current_dimension_separate() -> None:
    definition = _lord_definition()

    restored = decode_value(encode_value(definition))

    assert restored == definition
    assert restored.kind is CardKind.LORD
    assert restored.rank is CardRank.LEGENDARY
    assert restored.lord_domain is LordDomain.REALMS
    assert restored.subtypes == frozenset({"Pixy", "spirit"})
    assert restored.card_id == "taxonomy-t1-lord"


def test_public_catalog_does_not_infer_or_project_lord_domain() -> None:
    definition = _lord_definition()
    public = PublicCard.from_sources(
        definition,
        CardPresentation(definition.card_id, "Token", "Señor", "", "lord.webp"),
    )

    assert public.kind == "lord"
    assert public.rank == "legendary"
    assert public.subtypes == ("Pixy", "spirit")
    assert public.card_id == definition.card_id
    assert "lord_domain" not in public.to_dict()
