"""Motor headless y extensible del nuevo juego de cartas."""

from .catalog import CardCatalog
from .content import CollectionManifest, CollectionRegistry, CollectionTrustPolicy, load_manifest
from .engine.game import GameEngine
from .persistence import dump_replay, dump_snapshot, load_snapshot, replay_from_log
from .rules.config import RuleSet
from .service import CommandSource, MatchService, MatchView
from .storage import InMemoryMatchStore, SQLiteMatchStore, VersionConflict

__all__ = [
    "CardCatalog",
    "CollectionManifest",
    "CollectionRegistry",
    "CollectionTrustPolicy",
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
__version__ = "0.18.3"
