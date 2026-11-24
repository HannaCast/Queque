"""Utilidades de desarrollo.   python -m app.cli seed   → carga Moody, GESA y Leo (contrato/personas_ejemplo.sql)"""
from __future__ import annotations

import sqlite3
import sys

from .config import Config, cargar_config
from .db import conectar, inicializar


def sembrar(con: sqlite3.Connection, cfg: Config) -> bool:
    if con.execute("SELECT COUNT(*) FROM personas").fetchone()[0]:
        return False
    con.executescript((cfg.contrato_dir / "personas_ejemplo.sql").read_text(encoding="utf-8"))
    return True


if __name__ == "__main__":
    if sys.argv[1:] != ["seed"]:
        sys.exit("Uso: python -m app.cli seed")
    cfg = cargar_config()
    con = conectar(cfg)
    inicializar(con, cfg)
    print("Personas de ejemplo cargadas." if sembrar(con, cfg) else "Ya había personas; no se cambió nada.")
