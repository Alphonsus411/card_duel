"""Contenido externo y metadatos editoriales desacoplados del motor."""
from .manifest import (
    CollectionManifest,
    dump_manifest,
    load_manifest,
    load_manifest_file,
    register_manifest,
    save_manifest_file,
)
from .registry import CollectionProvenance, CollectionRegistry, CollectionTrustPolicy
from .registry import PermissiveCollectionTrustPolicy, TrustedKey, TrustedKeyResolver, TrustPolicy
from .presentation import (
    CardPresentation,
    CardPresentationCatalog,
    CardPresentationSnapshot,
)
from .signature import (
    CollectionSignatureEnvelope,
    dump_signature_envelope,
    load_signature_envelope,
)

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
    "PermissiveCollectionTrustPolicy",
    "TrustedKey",
    "TrustedKeyResolver",
    "TrustPolicy",
    "CardPresentation",
    "CardPresentationCatalog",
    "CardPresentationSnapshot",
    "CollectionSignatureEnvelope",
    "dump_signature_envelope",
    "load_signature_envelope",
]
