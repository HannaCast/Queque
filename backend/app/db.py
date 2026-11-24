"""SQLite: conexión, esquema y transacciones.

El esquema base es contrato/esquema.sql, tal cual está en el repositorio. Encima se aplican
solo ajustes ADITIVOS (app/ajustes_001.sql); ver README del backend para el porqué.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .config import Config

VERSION_ESQUEMA = 1


def conectar(cfg: Config) -> sqlite3.Connection:
    cfg.db_path.parent.mkdir(parents=True, exist_ok=True)
    # check_same_thread=False: FastAPI puede crear la conexión y usarla en hilos distintos.
    con = sqlite3.connect(cfg.db_path, timeout=10, isolation_level=None, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")      # la API y el worker leen/escriben a la vez
    con.execute("PRAGMA busy_timeout=10000")
    con.execute("PRAGMA foreign_keys=ON")
    return con


def inicializar(con: sqlite3.Connection, cfg: Config) -> None:
    if con.execute("PRAGMA user_version").fetchone()[0] >= VERSION_ESQUEMA:
        return
    con.executescript((cfg.contrato_dir / "esquema.sql").read_text(encoding="utf-8"))
    con.executescript((Path(__file__).parent / "ajustes_001.sql").read_text(encoding="utf-8"))
    con.execute(f"PRAGMA user_version={VERSION_ESQUEMA}")


@contextmanager
def transaccion(con: sqlite3.Connection):
    """BEGIN IMMEDIATE: toma el candado de escritura al inicio, así dos confirmaciones no se pisan."""
    con.execute("BEGIN IMMEDIATE")
    try:
        yield con
    except BaseException:
        con.execute("ROLLBACK")
        raise
    else:
        con.execute("COMMIT")
