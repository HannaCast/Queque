"""Utilidades de línea de comandos.

    python -m app.cli seed                                   → carga Moody, GESA y Leo (contrato/personas_ejemplo.sql)
    python -m app.cli crear-usuario --correo X --nombre Y --rol coordinador
    python -m app.cli listar-usuarios
    python -m app.cli cambiar-contrasena --correo X
    python -m app.cli desactivar-usuario --correo X          (y activar-usuario)

La contraseña se pide en la terminal sin mostrarse. Si la entrada no es una terminal (un script), se lee una línea de stdin.
"""
from __future__ import annotations

import argparse
import getpass
import sqlite3
import sys

from . import auth
from .config import Config, cargar_config
from .db import conectar, inicializar
from .errores import ErrorNegocio


def sembrar(con: sqlite3.Connection, cfg: Config) -> bool:
    if con.execute("SELECT COUNT(*) FROM personas").fetchone()[0]:
        return False
    con.executescript((cfg.contrato_dir / "personas_ejemplo.sql").read_text(encoding="utf-8"))
    return True


def _pedir_contrasena() -> str:
    if not sys.stdin.isatty():
        return sys.stdin.readline().rstrip("\n")
    primera = getpass.getpass("Contraseña: ")
    if getpass.getpass("Repite la contraseña: ") != primera:
        sys.exit("Las contraseñas no coinciden.")
    return primera


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m app.cli", description="Utilidades de Queque")
    sub = parser.add_subparsers(dest="comando", required=True)

    sub.add_parser("seed", help="carga las personas de ejemplo")

    crear = sub.add_parser("crear-usuario", help="crea un usuario para iniciar sesión")
    crear.add_argument("--correo", required=True)
    crear.add_argument("--nombre", required=True)
    crear.add_argument("--rol", required=True, choices=auth.ROLES)

    sub.add_parser("listar-usuarios", help="muestra los usuarios")

    for nombre, ayuda in (("cambiar-contrasena", "cambia la contraseña y cierra sus sesiones"),
                          ("desactivar-usuario", "impide que entre y cierra sus sesiones"),
                          ("activar-usuario", "vuelve a permitir que entre")):
        p = sub.add_parser(nombre, help=ayuda)
        p.add_argument("--correo", required=True)

    args = parser.parse_args(argv)
    cfg = cargar_config()
    con = conectar(cfg)
    inicializar(con, cfg)

    try:
        if args.comando == "seed":
            print("Personas de ejemplo cargadas." if sembrar(con, cfg) else "Ya había personas; no se cambió nada.")
        elif args.comando == "crear-usuario":
            u = auth.crear_usuario(con, args.correo, args.nombre, _pedir_contrasena(), args.rol)
            print(f"Usuario creado: {u.correo} ({u.rol}).")
        elif args.comando == "listar-usuarios":
            filas = auth.listar_usuarios(con)
            if not filas:
                print("Todavía no hay usuarios. Crea uno con: python -m app.cli crear-usuario ...")
            for f in filas:
                print(f"{f['id']:>3}  {f['correo']:<32} {f['rol']:<12} {f['nombre']}{'' if f['activo'] else '  (desactivado)'}")
        elif args.comando == "cambiar-contrasena":
            auth.cambiar_contrasena(con, args.correo, _pedir_contrasena())
            print("Contraseña actualizada. Sus sesiones abiertas se cerraron.")
        elif args.comando in ("desactivar-usuario", "activar-usuario"):
            activo = args.comando == "activar-usuario"
            auth.cambiar_activo(con, args.correo, activo)
            print("Usuario activado." if activo else "Usuario desactivado. Sus sesiones abiertas se cerraron.")
    except ErrorNegocio as e:
        sys.exit(f"Error: {e}")
    finally:
        con.close()


if __name__ == "__main__":
    main()
