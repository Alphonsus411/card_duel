from __future__ import annotations

import json
from pathlib import Path

import pytest

from card_duel_engine.domain.enums import CardKind, LordDomain
from card_duel_engine.domain.models import CardDefinition, CardFilter
from card_duel_engine.persistence import load_snapshot, replay_from_log
from card_duel_engine.persistence.codec import decode_value, encode_value


ARTIFACTS = Path(__file__).parent / "artifacts" / "0.19.0"


def test_subtype_vocabulary_remains_literal_without_implicit_aliases() -> None:
    definition = CardDefinition(
        "taxonomy-t5-pixy",
        "Pixy de prueba",
        CardKind.CREATURE,
        1,
        base_strength=1,
        subtypes=frozenset({"Pixy"}),
    )

    assert CardFilter(subtypes=frozenset({"Pixy"})).matches(definition)
    assert not CardFilter(subtypes=frozenset({"Pixie"})).matches(definition)


def test_codec_rejects_an_unknown_lord_domain_without_fallback() -> None:
    definition = CardDefinition(
        "taxonomy-t5-lord",
        "Señor de prueba",
        CardKind.LORD,
        4,
        lord_domain=LordDomain.REALMS,
    )
    encoded = encode_value(definition)
    encoded["fields"]["lord_domain"]["name"] = "FUTURE_DOMAIN"

    with pytest.raises(ValueError, match="Miembro de enum desconocido"):
        decode_value(encoded)


def test_legacy_snapshot_and_replay_keep_absent_lord_domain_absent() -> None:
    snapshot = load_snapshot((ARTIFACTS / "snapshot-v1.json").read_text(encoding="utf-8"))
    replay = replay_from_log((ARTIFACTS / "replay-v2.json").read_text(encoding="utf-8"))

    for engine in (snapshot, replay):
        definitions = engine.catalog.definitions()
        assert definitions
        assert all(definition.lord_domain is None for definition in definitions)


def test_legacy_taxonomy_artifacts_declare_their_original_schemas() -> None:
    snapshot = json.loads((ARTIFACTS / "snapshot-v1.json").read_text(encoding="utf-8"))
    replay = json.loads((ARTIFACTS / "replay-v2.json").read_text(encoding="utf-8"))

    assert snapshot["body"]["schema_version"] == "1"
    assert replay["body"]["schema_version"] == "2"
