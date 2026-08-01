from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from threading import RLock

from ..domain.errors import InvariantViolation
from ..engine.game import GameEngine
from ..persistence.snapshot import dump_snapshot, load_snapshot


class MatchNotFound(KeyError):
    pass


class VersionConflict(RuntimeError):
    pass


EXPECTED_VERSION_ERROR = "La versión esperada debe ser un entero positivo"


def validate_expected_version(value: object) -> int:
    """Devuelve una versión CAS válida o produce un error de dominio estable."""
    if not (type(value) is int and value >= 1):
        raise ValueError(EXPECTED_VERSION_ERROR)
    return value


class InvalidStoredSnapshot(RuntimeError):
    """La carga encontró una instantánea persistida que no puede reconstruirse."""


@dataclass(frozen=True)
class StoredMatch:
    match_id: str
    version: int
    engine: GameEngine


def validate_match_id(match_id: str) -> None:
    """Valida únicamente las restricciones necesarias para almacenar una clave.

    Una clave válida es una cadena de 1 a 128 caracteres, no tiene espacio
    Unicode periférico y no contiene caracteres de la categoría Unicode de
    control (``Cc``). No se recorta ni normaliza: el almacenamiento y la
    autorización deben observar exactamente la misma identidad.
    """
    if (
        not isinstance(match_id, str)
        or not match_id.strip()
        or len(match_id) > 128
        or match_id != match_id.strip()
        or any(unicodedata.category(character) == "Cc" for character in match_id)
    ):
        raise ValueError(
            "El identificador de partida debe ser una cadena de 1 a 128 "
            "caracteres, sin espacios periféricos ni controles Unicode"
        )


class InMemoryMatchStore:
    """Repositorio de pruebas con la misma semántica CAS que SQLite."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._records: dict[str, tuple[int, str]] = {}

    def create(self, match_id: str, engine: GameEngine) -> int:
        validate_match_id(match_id)
        payload = dump_snapshot(engine, indent=None)
        with self._lock:
            if match_id in self._records:
                raise VersionConflict("La partida ya existe")
            self._records[match_id] = (1, payload)
            return 1

    def load(self, match_id: str) -> StoredMatch:
        validate_match_id(match_id)
        with self._lock:
            try:
                version, payload = self._records[match_id]
            except KeyError as exc:
                raise MatchNotFound(match_id) from exc
        try:
            engine = load_snapshot(payload)
        except (InvariantViolation, KeyError, TypeError, UnicodeError, ValueError) as exc:
            raise InvalidStoredSnapshot from exc
        return StoredMatch(match_id, version, engine)

    def save(self, match_id: str, engine: GameEngine, *, expected_version: int) -> int:
        validate_match_id(match_id)
        expected_version = validate_expected_version(expected_version)
        payload = dump_snapshot(engine, indent=None)
        with self._lock:
            if match_id not in self._records:
                raise MatchNotFound(match_id)
            current_version, _ = self._records[match_id]
            if current_version != expected_version:
                raise VersionConflict(
                    f"Versión esperada {expected_version}; actual {current_version}"
                )
            new_version = current_version + 1
            self._records[match_id] = (new_version, payload)
            return new_version
