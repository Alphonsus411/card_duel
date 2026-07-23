"""Punto de extensión para colecciones futuras; vacío deliberadamente."""
from .manifest import (
    CollectionManifest,
    dump_manifest,
    load_manifest,
    load_manifest_file,
    register_manifest,
    save_manifest_file,
)

__all__ = [
    "CollectionManifest",
    "dump_manifest",
    "load_manifest",
    "load_manifest_file",
    "register_manifest",
    "save_manifest_file",
]
