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

from ..catalog import CardCatalog
from .manifest import CollectionManifest, dump_manifest


class CollectionTrustPolicy(Protocol):
    """Punto de extensión de confianza, sin cargar ni ejecutar código externo."""

    def validate(
        self, manifest: CollectionManifest, canonical_content: bytes, digest: str
    ) -> None:
        """Acepta el manifiesto o lanza una excepción para rechazarlo."""


@dataclass(frozen=True)
class CollectionProvenance:
    """Datos inmutables que identifican exactamente una colección cargada."""

    collection_id: str
    revision: int
    dependencies: tuple[str, ...]
    manifest_sha256: str


class CollectionRegistry:
    """Coordina un catálogo único y registra lotes con semántica todo-o-nada."""

    def __init__(
        self,
        catalog: CardCatalog | None = None,
        *,
        trust_policy: CollectionTrustPolicy | None = None,
    ) -> None:
        self._catalog = catalog if catalog is not None else CardCatalog()
        self._trust_policy = trust_policy
        self._collections: dict[str, CollectionProvenance] = {}

    @property
    def catalog(self) -> CardCatalog:
        """Catálogo coordinado; se comparte con el motor por inyección."""
        return self._catalog

    @property
    def collections(self) -> Mapping[str, CollectionProvenance]:
        """Vista de solo lectura de la procedencia de colecciones cargadas."""
        return MappingProxyType(self._collections)

    def provenance(self, collection_id: str) -> CollectionProvenance:
        return self._collections[collection_id]

    def register(self, manifest: CollectionManifest) -> CollectionProvenance:
        return self.register_batch((manifest,))[manifest.collection_id]

    def register_batch(
        self, manifests: tuple[CollectionManifest, ...] | list[CollectionManifest]
    ) -> Mapping[str, CollectionProvenance]:
        """Valida y aplica un lote completo en orden topológico determinista."""
        pending: dict[str, CollectionManifest] = {}
        for manifest in manifests:
            if manifest.collection_id in pending:
                raise ValueError(f"Colección duplicada en el lote: {manifest.collection_id}")
            existing = self._collections.get(manifest.collection_id)
            if existing is not None:
                canonical, digest = self._identity(manifest)
                if manifest.revision < existing.revision:
                    raise ValueError("La revisión es inferior a la registrada")
                if manifest.revision == existing.revision and digest != existing.manifest_sha256:
                    raise ValueError("El manifiesto registrado fue alterado")
                if manifest.revision > existing.revision:
                    raise ValueError("La revisión es incompatible con el registro inmutable")
                raise ValueError(f"Colección ya registrada: {manifest.collection_id}")
            pending[manifest.collection_id] = manifest

        order = self._topological_order(pending)
        staged: dict[str, CollectionProvenance] = {}
        seen_cards = set(card.card_id for card in self._catalog.definitions())
        for collection_id in order:
            manifest = pending[collection_id]
            canonical, digest = self._identity(manifest)
            if self._trust_policy is not None:
                self._trust_policy.validate(manifest, canonical, digest)
            for card in manifest.cards:
                if card.card_id in seen_cards:
                    raise ValueError(f"La colección colisiona con el catálogo: {card.card_id}")
                seen_cards.add(card.card_id)
            staged[collection_id] = CollectionProvenance(
                collection_id, manifest.revision, tuple(manifest.dependencies), digest
            )

        # No puede fallar: todas las colisiones y políticas se validaron antes.
        for collection_id in order:
            for card in pending[collection_id].cards:
                self._catalog.register(card)
            self._collections[collection_id] = staged[collection_id]
        return MappingProxyType(dict(staged))

    @staticmethod
    def _identity(manifest: CollectionManifest) -> tuple[bytes, str]:
        canonical = dump_manifest(manifest, indent=None).encode("utf-8")
        return canonical, hashlib.sha256(canonical).hexdigest()

    def _topological_order(self, pending: Mapping[str, CollectionManifest]) -> list[str]:
        available = set(self._collections)
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
