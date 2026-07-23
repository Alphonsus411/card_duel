"""Motor headless y extensible del nuevo juego de cartas."""

from .catalog import CardCatalog
from .content import CollectionManifest, load_manifest
from .engine.game import GameEngine
from .persistence import dump_replay, dump_snapshot, load_snapshot, replay_from_log
from .rules.config import RuleSet
from .storage import SQLiteMatchStore, VersionConflict

__all__ = [
    "CardCatalog",
    "CollectionManifest",
    "GameEngine",
    "RuleSet",
    "SQLiteMatchStore",
    "VersionConflict",
    "dump_replay",
    "dump_snapshot",
    "load_manifest",
    "load_snapshot",
    "replay_from_log",
]
__version__ = "0.10.0"
