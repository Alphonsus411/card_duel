"""Punto de extensión para colecciones futuras; vacío deliberadamente."""
from .manifest import (
    CollectionManifest,
    dump_manifest,
    load_manifest,
    load_manifest_file,
    register_manifest,
    save_manifest_file,
)
from .registry import CollectionProvenance, CollectionRegistry, CollectionTrustPolicy

__all__ = [
    "CollectionManifest",
    "dump_manifest",
    "load_manifest",
    "load_manifest_file",
    "register_manifest",
    "save_manifest_file",
    "CollectionProvenance",
    "CollectionRegistry",
    "CollectionTrustPolicy",
]
