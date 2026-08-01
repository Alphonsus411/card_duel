from __future__ import annotations

import sqlite3
from pathlib import Path
from uuid import uuid4

from ..domain.errors import InvariantViolation
from ..engine.game import GameEngine
from ..persistence.snapshot import dump_snapshot, load_snapshot
from .base import (
    InvalidStoredSnapshot,
    MatchNotFound,
    StoredMatch,
    VersionConflict,
    validate_match_id,
)


class SQLiteMatchStore:
    """Almacén SQLite con CAS que no admite operaciones después de ``close``.

    ``close()`` es idempotente. El almacén también puede usarse como gestor de
    contexto; al salir del bloque queda cerrado de forma definitiva.
    """

    _CLOSED_ERROR = "SQLiteMatchStore está cerrado"

    def __init__(self, path: str | Path, *, timeout: float = 5.0) -> None:
        self.path = str(path)
        self.timeout = timeout
        self._uri = False
        self._keeper: sqlite3.Connection | None = None
        self._closed = False
        if self.path == ":memory:":
            # Cada conexion a ``:memory:`` crea una base distinta. El almacen usa
            # conexiones cortas, asi que necesita una URI compartida y una conexion
            # viva que conserve la base entre operaciones.
            self.path = f"file:card-duel-{uuid4().hex}?mode=memory&cache=shared"
            self._uri = True
            self._keeper = self._connect()
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS matches (
                    match_id TEXT PRIMARY KEY,
                    version INTEGER NOT NULL CHECK (version >= 1),
                    snapshot TEXT NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        if self._closed:
            raise RuntimeError(self._CLOSED_ERROR)
        return sqlite3.connect(self.path, timeout=self.timeout, uri=self._uri)

    def close(self) -> None:
        """Cierra el almacén; las llamadas posteriores no tienen efecto."""
        if self._closed:
            return
        self._closed = True
        if self._keeper is not None:
            self._keeper.close()
            self._keeper = None

    def __enter__(self) -> SQLiteMatchStore:
        """Devuelve este almacén mientras su ciclo de vida siga abierto."""
        if self._closed:
            raise RuntimeError(self._CLOSED_ERROR)
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        """Cierra el almacén al abandonar el bloque de contexto."""
        self.close()

    def create(self, match_id: str, engine: GameEngine) -> int:
        validate_match_id(match_id)
        payload = dump_snapshot(engine, indent=None)
        try:
            with self._connect() as connection:
                connection.execute(
                    "INSERT INTO matches(match_id, version, snapshot) VALUES (?, 1, ?)",
                    (match_id, payload),
                )
        except sqlite3.IntegrityError as exc:
            raise VersionConflict("La partida ya existe") from exc
        return 1

    def load(self, match_id: str) -> StoredMatch:
        validate_match_id(match_id)
        with self._connect() as connection:
            row = connection.execute(
                "SELECT version, snapshot FROM matches WHERE match_id = ?",
                (match_id,),
            ).fetchone()
        if row is None:
            raise MatchNotFound(match_id)
        try:
            engine = load_snapshot(row[1])
        except (InvariantViolation, KeyError, TypeError, UnicodeError, ValueError) as exc:
            raise InvalidStoredSnapshot from exc
        return StoredMatch(match_id, int(row[0]), engine)

    def save(
        self, match_id: str, engine: GameEngine, *, expected_version: int
    ) -> int:
        validate_match_id(match_id)
        if expected_version < 1:
            raise ValueError("La versión esperada debe ser positiva")
        payload = dump_snapshot(engine, indent=None)
        new_version = expected_version + 1
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            cursor = connection.execute(
                """
                UPDATE matches
                SET version = ?, snapshot = ?, updated_at = CURRENT_TIMESTAMP
                WHERE match_id = ? AND version = ?
                """,
                (new_version, payload, match_id, expected_version),
            )
            if cursor.rowcount != 1:
                row = connection.execute(
                    "SELECT version FROM matches WHERE match_id = ?", (match_id,)
                ).fetchone()
                connection.rollback()
                if row is None:
                    raise MatchNotFound(match_id)
                raise VersionConflict(
                    f"Versión esperada {expected_version}; actual {int(row[0])}"
                )
            connection.commit()
        return new_version
