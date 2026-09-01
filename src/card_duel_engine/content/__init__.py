"""Contenido canónico y contratos para colecciones extensibles."""
from .base_set import BASE_CARD_DEFINITIONS, BASE_SET_ID, BASE_SET_REVISION
from .manifest import (
    CollectionManifest,
    dump_manifest,
    load_manifest,
    load_manifest_file,
    register_manifest,
    save_manifest_file,
)
from .registry import (
    CollectionProvenance,
    CollectionRegistry,
    CollectionRegistrySnapshot,
    CollectionTrustPolicy,
)
from .registry import PermissiveCollectionTrustPolicy, TrustedKey, TrustedKeyResolver, TrustPolicy
from .signature import (
    CollectionSignatureEnvelope,
    dump_signature_envelope,
    load_signature_envelope,
)

__all__ = [
    "BASE_CARD_DEFINITIONS",
    "BASE_SET_ID",
    "BASE_SET_REVISION",
    "CollectionManifest",
    "dump_manifest",
    "load_manifest",
    "load_manifest_file",
    "register_manifest",
    "save_manifest_file",
    "CollectionProvenance",
    "CollectionRegistry",
    "CollectionRegistrySnapshot",
    "CollectionTrustPolicy",
    "PermissiveCollectionTrustPolicy",
    "TrustedKey",
    "TrustedKeyResolver",
    "TrustPolicy",
    "CollectionSignatureEnvelope",
    "dump_signature_envelope",
    "load_signature_envelope",
]
