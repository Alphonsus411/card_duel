"""Registro transaccional y autoritativo de colecciones de cartas.

El digest SHA-256 prueba integridad (que los bytes canónicos no cambiaron), no
autenticidad. Una aplicación que necesite confianza debe proporcionar una
``CollectionTrustPolicy`` y validar firmas fuera del motor.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Protocol
import hashlib
import hmac
import threading

from ..catalog import CardCatalog, CardCatalogSnapshot
from .manifest import CollectionManifest, dump_manifest
from .signature import CollectionSignatureEnvelope


@dataclass(frozen=True)
class TrustedKey:
    """Material de clave entregado por la aplicación, nunca por el contenido."""

    key_id: str
    material: bytes
    revoked: bool = False


class TrustedKeyResolver(Protocol):
    def resolve(self, key_id: str) -> TrustedKey | None:
        """Devuelve una clave configurada por la aplicación, si existe."""


class TrustPolicy(Protocol):
    """Contrato para políticas alternativas proporcionadas por la aplicación."""

    def validate(
        self,
        manifest: CollectionManifest,
        canonical_content: bytes,
        digest: str,
        envelope: CollectionSignatureEnvelope | None,
    ) -> None:
        """Acepta el contenido o lanza ``ValueError`` sin producir efectos."""


class CollectionTrustPolicy:
    """Política HMAC inyectable con lista cerrada de algoritmos."""

    def __init__(
        self,
        key_resolver: TrustedKeyResolver,
        *,
        require_signature: bool = True,
        allowed_algorithms: frozenset[str] = frozenset({"hmac-sha256"}),
    ) -> None:
        self._key_resolver = key_resolver
        self._require_signature = require_signature
        self._allowed_algorithms = allowed_algorithms

    def validate(
        self,
        manifest: CollectionManifest,
        canonical_content: bytes,
        digest: str,
        envelope: CollectionSignatureEnvelope | None,
    ) -> None:
        del manifest, digest
        if envelope is None:
            if self._require_signature:
                raise ValueError("La política exige una colección firmada")
            return
        if (
            envelope.algorithm != "hmac-sha256"
            or envelope.algorithm not in self._allowed_algorithms
        ):
            raise ValueError(f"Algoritmo de firma no permitido: {envelope.algorithm}")
        key = self._key_resolver.resolve(envelope.key_id)
        if key is None or key.key_id != envelope.key_id:
            raise ValueError(f"Clave de firma desconocida: {envelope.key_id}")
        if key.revoked:
            raise ValueError(f"Clave de firma revocada: {envelope.key_id}")
        expected = hmac.new(key.material, canonical_content, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, envelope.signature):
            raise ValueError("Firma de colección inválida")


class PermissiveCollectionTrustPolicy:
    """Política explícita que admite contenido firmado o sin firma sin autenticarlo."""

    def validate(
        self,
        manifest: CollectionManifest,
        canonical_content: bytes,
        digest: str,
        envelope: CollectionSignatureEnvelope | None,
    ) -> None:
        del manifest, canonical_content, digest, envelope


@dataclass(frozen=True)
class CollectionProvenance:
    """Datos inmutables que identifican exactamente una colección cargada."""

    collection_id: str
    revision: int
    dependencies: tuple[str, ...]
    manifest_sha256: str


@dataclass(frozen=True)
class CollectionRegistrySnapshot:
    """Fotografía coherente del catálogo y su procedencia publicada."""

    catalog: CardCatalogSnapshot
    collections: Mapping[str, CollectionProvenance]


@dataclass(frozen=True)
class _PublishedState:
    catalog: CardCatalogSnapshot
    collections: Mapping[str, CollectionProvenance]


class CollectionRegistry:
    """Coordina un catálogo único y registra lotes con semántica todo-o-nada.

    ``register_batch()`` serializa la lectura, validación y commit del catálogo
    y su procedencia como una única operación lógica. Cada acceso de lectura
    devuelve una fotografía coherente e inmutable. Para relacionar catálogo y
    procedencia capturados en una sola operación, use :meth:`snapshot`.

    ``catalog`` ya no expone operaciones de escritura: la migración consiste en
    usar :meth:`register` o :meth:`register_batch` para publicar contenido.
    """

    def __init__(
        self,
        catalog: CardCatalog | None = None,
        *,
        trust_policy: TrustPolicy | None = None,
    ) -> None:
        self._trust_policy = trust_policy
        self._lock = threading.RLock()
        initial = CardCatalog(
            {card.card_id: card for card in (catalog or CardCatalog()).definitions()}
        )
        self._state = _PublishedState(
            initial.snapshot(), MappingProxyType({})
        )

    @property
    def catalog(self) -> CardCatalogSnapshot:
        """Fotografía de solo lectura del catálogo publicado."""
        with self._lock:
            return self._state.catalog

    @property
    def collections(self) -> Mapping[str, CollectionProvenance]:
        """Vista de solo lectura de la procedencia de colecciones cargadas."""
        with self._lock:
            return self._state.collections

    def provenance(self, collection_id: str) -> CollectionProvenance:
        with self._lock:
            return self._state.collections[collection_id]

    def snapshot(self) -> CollectionRegistrySnapshot:
        """Captura catálogo y procedencia pertenecientes al mismo commit."""
        with self._lock:
            state = self._state
            return CollectionRegistrySnapshot(state.catalog, state.collections)

    def register(
        self, item: CollectionManifest | CollectionSignatureEnvelope
    ) -> CollectionProvenance:
        manifest = (
            item.collection_manifest()
            if isinstance(item, CollectionSignatureEnvelope)
            else item
        )
        return self.register_batch((item,))[manifest.collection_id]

    def register_batch(
        self,
        manifests: tuple[CollectionManifest | CollectionSignatureEnvelope, ...]
        | list[CollectionManifest | CollectionSignatureEnvelope],
    ) -> Mapping[str, CollectionProvenance]:
        """Valida y aplica un lote completo en orden topológico determinista."""
        with self._lock:
            return self._register_batch_locked(manifests)

    def _register_batch_locked(
        self,
        manifests: tuple[CollectionManifest | CollectionSignatureEnvelope, ...]
        | list[CollectionManifest | CollectionSignatureEnvelope],
    ) -> Mapping[str, CollectionProvenance]:
        published = self._state
        materialized = tuple(manifests)
        pending: dict[
            str, tuple[CollectionManifest, CollectionSignatureEnvelope | None]
        ] = {}
        for item in materialized:
            if isinstance(item, CollectionSignatureEnvelope):
                envelope: CollectionSignatureEnvelope | None = item
                manifest = item.collection_manifest()
            else:
                envelope = None
                manifest = item
            if manifest.collection_id in pending:
                raise ValueError(f"Colección duplicada en el lote: {manifest.collection_id}")
            existing = published.collections.get(manifest.collection_id)
            if existing is not None:
                canonical, digest = self._identity(manifest)
                if manifest.revision < existing.revision:
                    raise ValueError("La revisión es inferior a la registrada")
                if manifest.revision == existing.revision and digest != existing.manifest_sha256:
                    raise ValueError("El manifiesto registrado fue alterado")
                if manifest.revision > existing.revision:
                    raise ValueError("La revisión es incompatible con el registro inmutable")
                raise ValueError(f"Colección ya registrada: {manifest.collection_id}")
            pending[manifest.collection_id] = (manifest, envelope)

        manifest_map = {key: value[0] for key, value in pending.items()}
        order = self._topological_order(manifest_map, published.collections)
        staged: dict[str, CollectionProvenance] = {}
        candidate_catalog = CardCatalog(
            {card.card_id: card for card in published.catalog.definitions()}
        )
        seen_cards = set(card.card_id for card in candidate_catalog.definitions())
        for collection_id in order:
            manifest, envelope = pending[collection_id]
            canonical, digest = self._identity(manifest)
            if self._trust_policy is not None:
                self._trust_policy.validate(manifest, canonical, digest, envelope)
            for card in manifest.cards:
                if card.card_id in seen_cards:
                    raise ValueError(f"La colección colisiona con el catálogo: {card.card_id}")
                seen_cards.add(card.card_id)
                candidate_catalog.register(card)
            staged[collection_id] = CollectionProvenance(
                collection_id, manifest.revision, tuple(manifest.dependencies), digest
            )

        candidate_collections = dict(published.collections)
        candidate_collections.update(staged)
        candidate_state = _PublishedState(
            candidate_catalog.snapshot(), MappingProxyType(candidate_collections)
        )
        result = MappingProxyType(dict(staged))
        # Único punto de publicación, posterior a toda operación que puede fallar.
        self._state = candidate_state
        return result

    @staticmethod
    def _identity(manifest: CollectionManifest) -> tuple[bytes, str]:
        canonical = dump_manifest(manifest, indent=None).encode("utf-8")
        return canonical, hashlib.sha256(canonical).hexdigest()

    def _topological_order(
        self,
        pending: Mapping[str, CollectionManifest],
        published: Mapping[str, CollectionProvenance],
    ) -> list[str]:
        available = set(published)
        for manifest in pending.values():
            missing = set(manifest.dependencies) - available - set(pending)
            if missing:
                raise ValueError(f"Dependencias ausentes: {tuple(sorted(missing))}")
        remaining = set(pending)
        order: list[str] = []
        while remaining:
            ready = sorted(
                item
                for item in remaining
                if set(pending[item].dependencies) <= available
            )
            if not ready:
                raise ValueError(f"Ciclo de dependencias: {tuple(sorted(remaining))}")
            for item in ready:
                order.append(item)
                available.add(item)
                remaining.remove(item)
        return order
