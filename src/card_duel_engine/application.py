"""Frontera de aplicación autenticada para adaptadores de transporte.

El transporte autentica las credenciales y entrega una :class:`ExternalIdentity`.
Esta capa resuelve la identidad a un jugador; los parámetros públicos nunca
permiten seleccionar un ``player_id``.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Protocol, TypeVar

from .domain.errors import IllegalAction
from .domain.models import CardDefinition
from .engine.commands import GameCommand
from .service import CommandSource, MatchService, MatchView
from .storage.base import MatchNotFound, VersionConflict


class Capability(Enum):
    """Operaciones autorizables de forma independiente."""

    CREATE_MATCH = "create_match"
    OBSERVE = "observe"
    SUBMIT_COMMAND = "submit_command"
    ADMINISTER = "administer"


@dataclass(frozen=True)
class ExternalIdentity:
    """Identidad estable producida por un autenticador de confianza."""

    issuer: str
    subject: str
    authenticated: bool = True


class ApplicationError(RuntimeError):
    """Error público seguro; no conserva la excepción interna como argumento."""

    code = "application_error"
    public_message = "La operación no pudo completarse"

    def __init__(self) -> None:
        super().__init__(self.public_message)


class AuthenticationRequired(ApplicationError):
    code = "authentication_required"
    public_message = "Se requiere una identidad autenticada"


class InvalidIdentity(ApplicationError):
    code = "invalid_identity"
    public_message = "La identidad autenticada no es válida"


class AccessDenied(ApplicationError):
    code = "access_denied"
    public_message = "La identidad no está autorizada para esta operación"


class ResourceNotFound(ApplicationError):
    code = "resource_not_found"
    public_message = "El recurso solicitado no existe"


class WriteConflict(ApplicationError):
    code = "write_conflict"
    public_message = "La versión de escritura ya no es vigente"


class CommandRejected(ApplicationError):
    code = "command_rejected"
    public_message = "El comando fue rechazado"


class IdentityAuthorization(Protocol):
    """Resolución externa de capacidades y asociaciones de jugadores."""

    def allows_global(self, identity: ExternalIdentity, capability: Capability) -> bool: ...

    def player_for(
        self, identity: ExternalIdentity, match_id: str, capability: Capability
    ) -> str | None: ...

    def allows_match(
        self, identity: ExternalIdentity, match_id: str, capability: Capability
    ) -> bool: ...


IdentityKey = tuple[str, str]


class InMemoryIdentityAuthorization:
    """Política explícita útil para composición local y pruebas de adaptadores."""

    def __init__(self) -> None:
        self._global: set[tuple[IdentityKey, Capability]] = set()
        self._players: dict[tuple[IdentityKey, str, Capability], str] = {}
        self._matches: set[tuple[IdentityKey, str, Capability]] = set()

    @staticmethod
    def _key(identity: ExternalIdentity) -> IdentityKey:
        return identity.issuer, identity.subject

    def grant_global(self, identity: ExternalIdentity, capability: Capability) -> None:
        self._global.add((self._key(identity), capability))

    def bind_player(
        self,
        identity: ExternalIdentity,
        match_id: str,
        player_id: str,
        *,
        capabilities: Iterable[Capability] = (
            Capability.OBSERVE,
            Capability.SUBMIT_COMMAND,
        ),
    ) -> None:
        for capability in capabilities:
            if capability not in (Capability.OBSERVE, Capability.SUBMIT_COMMAND):
                raise ValueError("Una asociación de jugador solo admite observar o enviar")
            self._players[(self._key(identity), match_id, capability)] = player_id

    def grant_match(
        self, identity: ExternalIdentity, match_id: str, capability: Capability
    ) -> None:
        self._matches.add((self._key(identity), match_id, capability))

    def allows_global(self, identity: ExternalIdentity, capability: Capability) -> bool:
        return (self._key(identity), capability) in self._global

    def player_for(
        self, identity: ExternalIdentity, match_id: str, capability: Capability
    ) -> str | None:
        return self._players.get((self._key(identity), match_id, capability))

    def allows_match(
        self, identity: ExternalIdentity, match_id: str, capability: Capability
    ) -> bool:
        return (self._key(identity), match_id, capability) in self._matches


T = TypeVar("T")


class AuthenticatedMatchApplication:
    """Casos de uso seguros consumidos por HTTP u otros transportes."""

    def __init__(
        self, service: MatchService, authorization: IdentityAuthorization
    ) -> None:
        self._service = service
        self._authorization = authorization

    @staticmethod
    def _identity(identity: ExternalIdentity | None) -> ExternalIdentity:
        if identity is None:
            raise AuthenticationRequired
        if not identity.authenticated or not identity.issuer.strip() or not identity.subject.strip():
            raise InvalidIdentity
        return identity

    @staticmethod
    def _translate(operation: Callable[[], T]) -> T:
        try:
            return operation()
        except MatchNotFound:
            raise ResourceNotFound from None
        except VersionConflict:
            raise WriteConflict from None
        except IllegalAction:
            raise CommandRejected from None

    def create_match(
        self,
        identity: ExternalIdentity | None,
        match_id: str,
        decks: Mapping[str, Iterable[CardDefinition]],
        *,
        seed: int = 0,
        auto_start: bool = True,
    ) -> int:
        principal = self._identity(identity)
        if not self._authorization.allows_global(principal, Capability.CREATE_MATCH):
            raise AccessDenied
        return self._translate(
            lambda: self._service.create_match(
                match_id, decks, seed=seed, auto_start=auto_start
            )
        )

    def view(self, identity: ExternalIdentity | None, match_id: str) -> MatchView:
        principal = self._identity(identity)
        player_id = self._authorization.player_for(
            principal, match_id, Capability.OBSERVE
        )
        if player_id is None:
            raise AccessDenied
        return self._translate(lambda: self._service.view(match_id, player_id))

    def submit(
        self,
        identity: ExternalIdentity | None,
        match_id: str,
        command: GameCommand,
        *,
        expected_version: int,
    ) -> MatchView:
        principal = self._identity(identity)
        player_id = self._authorization.player_for(
            principal, match_id, Capability.SUBMIT_COMMAND
        )
        if player_id is None or command.player_id != player_id:
            raise AccessDenied
        return self._translate(
            lambda: self._service.submit(
                match_id, command, expected_version=expected_version
            )
        )

    def submit_from(
        self,
        identity: ExternalIdentity | None,
        match_id: str,
        source: CommandSource,
        *,
        expected_version: int,
    ) -> MatchView:
        principal = self._identity(identity)
        player_id = self._authorization.player_for(
            principal, match_id, Capability.SUBMIT_COMMAND
        )
        if player_id is None:
            raise AccessDenied
        view = self._translate(lambda: self._service.view(match_id, player_id))
        if view.version != expected_version:
            raise WriteConflict
        command = source.choose_action(view.observation, view.legal_actions)
        if command.player_id != player_id:
            raise AccessDenied
        return self._translate(
            lambda: self._service.submit(
                match_id, command, expected_version=expected_version
            )
        )

    def administrative_version(
        self, identity: ExternalIdentity | None, match_id: str
    ) -> int:
        """Consulta administrativa mínima sin devolver una instantánea."""
        principal = self._identity(identity)
        if not self._authorization.allows_match(
            principal, match_id, Capability.ADMINISTER
        ):
            raise AccessDenied
        return self._translate(lambda: self._service.get_match(match_id).version)
