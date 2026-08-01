"""API de aplicación headless para humanos, simuladores y futuros adaptadores AGIX."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import Protocol

from .catalog import CardCatalog
from .content.registry import CollectionRegistry
from .controllers.base import PlayerObservation
from .domain.models import CardDefinition
from .engine.commands import GameCommand
from .engine.game import GameEngine
from .rules.config import RuleSet
from .storage.base import StoredMatch, validate_expected_version


class DeckValidationFailure(ValueError):
    """Las definiciones recibidas no permiten construir una partida."""


class MalformedGameCommand(TypeError):
    """El valor recibido no pertenece al vocabulario cerrado de comandos."""


class MatchStore(Protocol):
    """Contrato de persistencia CAS, independiente del soporte utilizado."""

    def create(self, match_id: str, engine: GameEngine) -> int: ...
    def load(self, match_id: str) -> StoredMatch: ...
    def save(self, match_id: str, engine: GameEngine, *, expected_version: int) -> int: ...


class CommandSource(Protocol):
    """Punto de extensión mínimo para controladores o agentes externos."""

    def choose_action(
        self, observation: PlayerObservation, legal_actions: tuple[GameCommand, ...]
    ) -> GameCommand: ...


@dataclass(frozen=True)
class MatchView:
    match_id: str
    version: int
    observation: PlayerObservation
    legal_actions: tuple[GameCommand, ...]


class MatchService:
    """Coordina ciclo de vida, consultas y comandos sin exponer estado mutable."""

    def __init__(
        self,
        store: MatchStore,
        *,
        engine_factory: Callable[[], GameEngine] | None = None,
        catalog: CardCatalog | CollectionRegistry | None = None,
    ) -> None:
        self.store = store
        if engine_factory is not None and catalog is not None:
            raise ValueError("No se puede combinar engine_factory y catalog")
        self._engine_factory = engine_factory or (lambda: GameEngine(catalog=catalog))

    def create_match(
        self,
        match_id: str,
        decks: Mapping[str, Iterable[CardDefinition]],
        *,
        seed: int = 0,
        auto_start: bool = True,
    ) -> int:
        engine = self._engine_factory()
        try:
            engine.new_match(decks, seed=seed, auto_start=auto_start)
        except (TypeError, ValueError) as exc:
            raise DeckValidationFailure from exc
        return self.store.create(match_id, engine)

    def get_match(self, match_id: str) -> StoredMatch:
        """Carga una partida para administración/persistencia dentro del proceso.

        El resultado contiene un ``GameEngine`` deserializado. Por ello esta es una
        operación interna: nunca debe usarse como respuesta de un adaptador remoto
        ni atravesar la frontera R-06. Los clientes reciben exclusivamente los DTO
        seguros construidos por ``AuthenticatedMatchApplication`` desde ``MatchView``.
        Modificar la copia retornada no altera el almacén.
        """
        return self.store.load(match_id)

    def view(self, match_id: str, player_id: str) -> MatchView:
        stored = self.store.load(match_id)
        return self._view_for(
            match_id, stored.version, stored.engine, player_id
        )

    @staticmethod
    def _view_for(
        match_id: str, version: int, engine: GameEngine, player_id: str
    ) -> MatchView:
        return MatchView(
            match_id,
            version,
            engine.observe(player_id),
            engine.legal_actions(player_id),
        )

    def submit(
        self,
        match_id: str,
        command: GameCommand,
        *,
        expected_version: int,
    ) -> MatchView:
        expected_version = validate_expected_version(expected_version)
        self.validate_command(command)
        stored = self.store.load(match_id)
        # El CAS se comprueba antes de ejecutar para evitar trabajo y errores engañosos.
        if stored.version != expected_version:
            from .storage.base import VersionConflict

            raise VersionConflict(
                f"Versión esperada {expected_version}; actual {stored.version}"
            )
        stored.engine.execute(command)
        version = self.store.save(
            match_id, stored.engine, expected_version=expected_version
        )
        return self._view_for(
            match_id, version, stored.engine, command.player_id
        )

    @staticmethod
    def validate_command(command: object) -> None:
        """Rechaza objetos ajenos sin ejecutar ni ocultar errores del motor."""
        if (
            not isinstance(command, GameCommand)
            or type(command) not in GameCommand.__subclasses__()
            or type(command.player_id) is not str
            or not command.player_id
        ):
            raise MalformedGameCommand

    def submit_from(
        self, match_id: str, player_id: str, source: CommandSource
    ) -> MatchView:
        """Adaptador común para una decisión humana automatizada o un agente."""
        view = self.view(match_id, player_id)
        command = source.choose_action(view.observation, view.legal_actions)
        if command.player_id != player_id:
            raise ValueError("La fuente intentó actuar por otro jugador")
        return self.submit(match_id, command, expected_version=view.version)
