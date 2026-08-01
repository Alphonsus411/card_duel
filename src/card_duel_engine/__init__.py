"""Motor headless y extensible del nuevo juego de cartas."""

from .catalog import CardCatalog
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
    CollectionSignatureEnvelope,
    CollectionTrustPolicy,
    PermissiveCollectionTrustPolicy,
    TrustedKey,
    load_manifest,
)
from .engine.game import GameEngine
from .persistence import dump_replay, dump_snapshot, load_snapshot, replay_from_log
from .rules.config import RuleSet
from .service import CommandSource, MatchService, MatchView
from .storage import InMemoryMatchStore, SQLiteMatchStore, VersionConflict

__all__ = [
    "CardCatalog",
    "AccessDenied",
    "AuthenticatedMatchApplication",
    "AuthenticationRequired",
    "Capability",
    "CommandRejected",
    "ExternalIdentity",
    "InMemoryIdentityAuthorization",
    "InternalLoadFailure",
    "InvalidDeck",
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
    "CollectionTrustPolicy",
    "CollectionSignatureEnvelope",
    "PermissiveCollectionTrustPolicy",
    "TrustedKey",
    "GameEngine",
    "InMemoryMatchStore",
    "MatchService",
    "MatchView",
    "CommandSource",
    "RuleSet",
    "SQLiteMatchStore",
    "VersionConflict",
    "dump_replay",
    "dump_snapshot",
    "load_manifest",
    "load_snapshot",
    "replay_from_log",
]
__version__ = "0.19.0"
