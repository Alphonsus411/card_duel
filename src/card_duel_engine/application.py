"""Frontera de aplicación autenticada para adaptadores de transporte.

El transporte autentica las credenciales y entrega una :class:`ExternalIdentity`.
Esta capa resuelve la identidad a un jugador; los parámetros públicos nunca
permiten seleccionar un ``player_id``.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Protocol, TypeVar

from .domain.errors import IllegalAction
from .domain.models import CardDefinition
from .engine.commands import GameCommand
from .service import (
    CommandSource,
    DeckValidationFailure,
    MalformedGameCommand,
    MatchService,
    MatchView,
)
from .storage.base import (
    InvalidStoredSnapshot,
    MatchNotFound,
    VersionConflict,
    validate_expected_version,
    validate_match_id,
)

if TYPE_CHECKING:
    from .controllers.base import PlayerObservation


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


@dataclass(frozen=True)
class PublicPlayerObservation:
    """DTO serializable con la observación autorizada de una sola identidad."""

    player_id: str
    active_player_id: str
    phase: str
    own_hand: tuple[str, ...]
    own_steps: int
    own_wounds: int
    opponent_hand_sizes: dict[str, int]
    public_event_count: int
    own_battlefield: tuple[str, ...]
    opponent_battlefields: dict[str, tuple[str, ...]]
    stack_size: int

    @classmethod
    def from_observation(
        cls, observation: "PlayerObservation"
    ) -> "PublicPlayerObservation":
        """Copia solo campos observables; nunca inspecciona motor ni estado."""
        return cls(
            player_id=observation.player_id,
            active_player_id=observation.active_player_id,
            phase=observation.phase.name,
            own_hand=observation.own_hand,
            own_steps=observation.own_steps,
            own_wounds=observation.own_wounds,
            opponent_hand_sizes=dict(observation.opponent_hand_sizes),
            public_event_count=observation.public_event_count,
            own_battlefield=observation.own_battlefield,
            opponent_battlefields=dict(observation.opponent_battlefields or {}),
            stack_size=observation.stack_size,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "player_id": self.player_id,
            "active_player_id": self.active_player_id,
            "phase": self.phase,
            "own_hand": list(self.own_hand),
            "own_steps": self.own_steps,
            "own_wounds": self.own_wounds,
            "opponent_hand_sizes": dict(self.opponent_hand_sizes),
            "public_event_count": self.public_event_count,
            "own_battlefield": list(self.own_battlefield),
            "opponent_battlefields": {
                player_id: list(cards)
                for player_id, cards in self.opponent_battlefields.items()
            },
            "stack_size": self.stack_size,
        }


@dataclass(frozen=True)
class PublicLegalAction:
    """Alternativa pública seleccionable, sin elecciones ni objetos internos."""

    option_id: str
    action: str


@dataclass(frozen=True)
class PublicMatchView:
    """DTO de salida R-06 construido exclusivamente desde ``MatchView``."""

    match_id: str
    version: int
    observation: PublicPlayerObservation
    legal_actions: tuple[PublicLegalAction, ...]

    @classmethod
    def from_view(
        cls,
        view: MatchView,
        *,
        option_ids: Iterable[str] | None = None,
    ) -> "PublicMatchView":
        if option_ids is None:
            if view.legal_actions:
                raise ValueError(
                    "Las acciones legales requieren identificadores autoritativos"
                )
            identifiers = ()
        else:
            identifiers = tuple(option_ids)
        if len(identifiers) != len(view.legal_actions):
            raise ValueError("Cada acción legal necesita un identificador público")
        return cls(
            match_id=view.match_id,
            version=view.version,
            observation=PublicPlayerObservation.from_observation(view.observation),
            # Del comando solo se publica su discriminador. Sus campos pueden
            # representar elecciones privadas y no pertenecen a un DTO remoto.
            legal_actions=tuple(
                PublicLegalAction(option_id, type(action).__name__)
                for option_id, action in zip(identifiers, view.legal_actions)
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "match_id": self.match_id,
            "version": self.version,
            "observation": self.observation.to_dict(),
            "legal_actions": [
                {"id": action.option_id, "action": action.action}
                for action in self.legal_actions
            ],
        }


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


class InvalidExpectedVersion(ApplicationError):
    """La versión CAS pública no satisface el contrato del dominio."""

    code = "invalid_expected_version"
    public_message = "La versión esperada no es válida"


class CommandRejected(ApplicationError):
    code = "command_rejected"
    public_message = "El comando fue rechazado"


class OptionRejected(ApplicationError):
    """Una referencia pública no resuelve a una alternativa legal vigente."""

    code = "option_rejected"
    public_message = "La alternativa pública fue rechazada"


class InvalidDeck(ApplicationError):
    """Las definiciones públicas de mazo son incompatibles o inválidas."""

    code = "invalid_deck"
    public_message = "La definición de los mazos no es válida"


class MalformedCommand(ApplicationError):
    """El objeto recibido no tiene la forma de un comando admitido."""

    code = "malformed_command"
    public_message = "El comando no tiene un formato válido"


class InternalLoadFailure(ApplicationError):
    """La partida existe, pero su instantánea no se puede cargar."""

    code = "internal_load_failure"
    public_message = "No se pudo cargar el recurso solicitado"


class InvalidMatchId(ApplicationError):
    """Entrada pública inválida, identificada por el código ``invalid_match_id``."""

    code = "invalid_match_id"
    public_message = "El identificador de partida no es válido"


class IdentityAuthorization(Protocol):
    """Resolución externa de capacidades y asociaciones de jugadores."""

    def allows_global(
        self, identity: ExternalIdentity, capability: Capability
    ) -> bool: ...

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
                raise ValueError(
                    "Una asociación de jugador solo admite observar o enviar"
                )
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
        # Secreto efímero de esta frontera. Los tokens sólo contienen un MAC y
        # nunca una carga decodificable ni un GameCommand serializado.
        self._option_secret = secrets.token_bytes(32)

    def _option_id(
        self, match_id: str, player_id: str, version: int, index: int
    ) -> str:
        binding = b"\0".join(
            (
                match_id.encode("utf-8"),
                player_id.encode("utf-8"),
                str(version).encode("ascii"),
                str(index).encode("ascii"),
            )
        )
        return hmac.new(self._option_secret, binding, hashlib.sha256).hexdigest()

    def _public_view(self, view: MatchView, player_id: str) -> PublicMatchView:
        return PublicMatchView.from_view(
            view,
            option_ids=(
                self._option_id(view.match_id, player_id, view.version, index)
                for index in range(len(view.legal_actions))
            ),
        )

    @staticmethod
    def _identity(identity: ExternalIdentity | None) -> ExternalIdentity:
        if identity is None:
            raise AuthenticationRequired
        if not isinstance(identity, ExternalIdentity):
            raise InvalidIdentity
        if (
            type(identity.authenticated) is not bool
            or identity.authenticated is not True
            or type(identity.issuer) is not str
            or type(identity.subject) is not str
            or not identity.issuer.strip()
            or not identity.subject.strip()
        ):
            raise InvalidIdentity
        return identity

    @staticmethod
    def _match_id(match_id: str) -> None:
        """Valida antes de consultar autorización o persistencia."""
        try:
            validate_match_id(match_id)
        except ValueError:
            raise InvalidMatchId from None

    @staticmethod
    def _expected_version(value: object) -> int:
        """Traduce el contrato CAS antes de autorización o persistencia."""
        try:
            return validate_expected_version(value)
        except ValueError:
            raise InvalidExpectedVersion from None

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
        except DeckValidationFailure:
            raise InvalidDeck from None
        except MalformedGameCommand:
            raise MalformedCommand from None
        except InvalidStoredSnapshot:
            raise InternalLoadFailure from None

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
        self._match_id(match_id)
        if not self._authorization.allows_global(principal, Capability.CREATE_MATCH):
            raise AccessDenied
        return self._translate(
            lambda: self._service.create_match(
                match_id, decks, seed=seed, auto_start=auto_start
            )
        )

    def view(self, identity: ExternalIdentity | None, match_id: str) -> PublicMatchView:
        principal = self._identity(identity)
        self._match_id(match_id)
        player_id = self._authorization.player_for(
            principal, match_id, Capability.OBSERVE
        )
        if player_id is None:
            raise AccessDenied
        view = self._translate(lambda: self._service.view(match_id, player_id))
        return self._public_view(view, player_id)

    def submit(
        self,
        identity: ExternalIdentity | None,
        match_id: str,
        command: GameCommand,
        *,
        expected_version: int,
    ) -> PublicMatchView:
        principal = self._identity(identity)
        self._match_id(match_id)
        expected_version = self._expected_version(expected_version)
        player_id = self._authorization.player_for(
            principal, match_id, Capability.SUBMIT_COMMAND
        )
        if player_id is None:
            raise AccessDenied
        self._translate(lambda: self._service.validate_command(command))
        if command.player_id != player_id:
            raise AccessDenied
        view = self._translate(
            lambda: self._service.submit(
                match_id, command, expected_version=expected_version
            )
        )
        return self._public_view(view, player_id)

    def submit_option(
        self,
        identity: ExternalIdentity | None,
        match_id: str,
        option_id: str,
        *,
        expected_version: int,
    ) -> PublicMatchView:
        """Resuelve y ejecuta una alternativa opaca del conjunto legal actual."""
        principal = self._identity(identity)
        self._match_id(match_id)
        expected_version = self._expected_version(expected_version)
        player_id = self._authorization.player_for(
            principal, match_id, Capability.SUBMIT_COMMAND
        )
        if player_id is None:
            raise AccessDenied
        view = self._translate(lambda: self._service.view(match_id, player_id))
        if view.version != expected_version:
            raise WriteConflict
        if type(option_id) is not str:
            raise OptionRejected
        command = next(
            (
                action
                for index, action in enumerate(view.legal_actions)
                if hmac.compare_digest(
                    option_id,
                    self._option_id(match_id, player_id, expected_version, index),
                )
            ),
            None,
        )
        if command is None:
            raise OptionRejected
        submitted = self._translate(
            lambda: self._service.submit(
                match_id, command, expected_version=expected_version
            )
        )
        return self._public_view(submitted, player_id)

    def submit_from(
        self,
        identity: ExternalIdentity | None,
        match_id: str,
        source: CommandSource,
        *,
        expected_version: int,
    ) -> PublicMatchView:
        principal = self._identity(identity)
        self._match_id(match_id)
        expected_version = self._expected_version(expected_version)
        player_id = self._authorization.player_for(
            principal, match_id, Capability.SUBMIT_COMMAND
        )
        if player_id is None:
            raise AccessDenied
        view = self._translate(lambda: self._service.view(match_id, player_id))
        if view.version != expected_version:
            raise WriteConflict
        command = source.choose_action(view.observation, view.legal_actions)
        self._translate(lambda: self._service.validate_command(command))
        if command.player_id != player_id:
            raise AccessDenied
        submitted = self._translate(
            lambda: self._service.submit(
                match_id, command, expected_version=expected_version
            )
        )
        return self._public_view(submitted, player_id)

    def administrative_version(
        self, identity: ExternalIdentity | None, match_id: str
    ) -> int:
        """Consulta administrativa mínima sin devolver una instantánea."""
        principal = self._identity(identity)
        self._match_id(match_id)
        if not self._authorization.allows_match(
            principal, match_id, Capability.ADMINISTER
        ):
            raise AccessDenied
        return self._translate(lambda: self._service.get_match(match_id).version)
