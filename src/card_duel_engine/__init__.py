"""Motor headless y extensible del nuevo juego de cartas."""

from ._version import resolve_version

__version__: str = resolve_version()

from .catalog import CardCatalog, CardCatalogSnapshot
from .application import (
    AccessDenied,
    AuthenticatedMatchApplication,
    AuthenticationRequired,
    Capability,
    CommandRejected,
    ExternalIdentity,
    InMemoryIdentityAuthorization,
    InternalLoadFailure,
    InvalidDeck,
    InvalidExpectedVersion,
    InvalidIdentity,
    InvalidMatchId,
    MalformedCommand,
    PublicLegalAction,
    PublicMatchView,
    PublicPlayerObservation,
    ResourceNotFound,
    WriteConflict,
)
from .content import (
    CollectionManifest,
    CollectionRegistry,
    CollectionRegistrySnapshot,
    CollectionSignatureEnvelope,
    CollectionTrustPolicy,
    PermissiveCollectionTrustPolicy,
    TrustedKey,
    load_manifest,
)
from .engine.game import GameEngine
from .persistence import dump_replay, dump_snapshot, load_snapshot, replay_from_log
from .rules import (
    DeckConstructionPolicy,
    DeckValidationIssue,
    DeckValidationResult,
    InvalidDeckConstruction,
    RuleSet,
    classic_deck_policy,
    mythic_deck_policy,
)
from .service import CommandSource, MatchService, MatchView
from .storage import InMemoryMatchStore, SQLiteMatchStore, VersionConflict

__all__ = [
    "CardCatalog",
    "CardCatalogSnapshot",
    "AccessDenied",
    "AuthenticatedMatchApplication",
    "AuthenticationRequired",
    "Capability",
    "CommandRejected",
    "ExternalIdentity",
    "InMemoryIdentityAuthorization",
    "InternalLoadFailure",
    "InvalidDeck",
    "InvalidExpectedVersion",
    "InvalidIdentity",
    "InvalidMatchId",
    "MalformedCommand",
    "PublicLegalAction",
    "PublicMatchView",
    "PublicPlayerObservation",
    "ResourceNotFound",
    "WriteConflict",
    "CollectionManifest",
    "CollectionRegistry",
    "CollectionRegistrySnapshot",
    "CollectionTrustPolicy",
    "CollectionSignatureEnvelope",
    "PermissiveCollectionTrustPolicy",
    "TrustedKey",
    "GameEngine",
    "InMemoryMatchStore",
    "MatchService",
    "MatchView",
    "CommandSource",
    "DeckConstructionPolicy",
    "DeckValidationIssue",
    "DeckValidationResult",
    "InvalidDeckConstruction",
    "RuleSet",
    "classic_deck_policy",
    "mythic_deck_policy",
    "SQLiteMatchStore",
    "VersionConflict",
    "dump_replay",
    "dump_snapshot",
    "load_manifest",
    "load_snapshot",
    "replay_from_log",
]
