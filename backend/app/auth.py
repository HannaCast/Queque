"""Inicio de sesión: usuarios, contraseñas y sesiones.

- Contraseñas con scrypt (biblioteca estándar, sin dependencias nuevas) y una sal distinta por usuario.
- La sesión es un token aleatorio que viaja en una cookie HttpOnly; en la base solo queda su SHA-256.
- Tras varios intentos fallidos la cuenta se bloquea unos minutos.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .db import transaccion
from .errores import Bloqueado, Invalido, NoAutorizado

ROLES = ("admin", "coordinador", "consulta")
ROLES_QUE_EDITAN = ("admin", "coordinador")

MIN_LONGITUD = 8
MAX_INTENTOS = 5
MINUTOS_BLOQUEO = 15

# scrypt: n=2^14, r=8, p=1 es el mínimo recomendado para contraseñas interactivas.
_N, _R, _P = 2**14, 8, 1
_MAXMEM = 64 * 1024 * 1024

MENSAJE_CREDENCIALES = "Correo o contraseña incorrectos."


@dataclass(frozen=True)
class Usuario:
    id: int
    correo: str
    nombre: str
    rol: str

    def a_dict(self) -> dict:
        return {"id": self.id, "correo": self.correo, "nombre": self.nombre, "rol": self.rol}


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


def _iso(momento: datetime) -> str:
    return momento.astimezone(timezone.utc).isoformat(timespec="seconds")


# --- Contraseñas ---
def cifrar_contrasena(contrasena: str) -> str:
    sal = secrets.token_bytes(16)
    clave = hashlib.scrypt(contrasena.encode("utf-8"), salt=sal, n=_N, r=_R, p=_P, maxmem=_MAXMEM)
    return f"scrypt${_N}${_R}${_P}${sal.hex()}${clave.hex()}"


def verificar_contrasena(contrasena: str, guardado: str) -> bool:
    try:
        esquema, n, r, p, sal, clave = guardado.split("$")
        if esquema != "scrypt":
            return False
        calculada = hashlib.scrypt(contrasena.encode("utf-8"), salt=bytes.fromhex(sal),
                                   n=int(n), r=int(r), p=int(p), maxmem=_MAXMEM)
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(calculada.hex(), clave)


# Se compara contra este hash cuando el correo no existe, para tardar lo mismo y no revelar qué correos hay.
_HASH_SEÑUELO = cifrar_contrasena(secrets.token_urlsafe(16))


def _validar_contrasena(contrasena: str) -> None:
    if len(contrasena) < MIN_LONGITUD:
        raise Invalido(f"La contraseña debe tener al menos {MIN_LONGITUD} caracteres.")


# --- Usuarios ---
def crear_usuario(con: sqlite3.Connection, correo: str, nombre: str, contrasena: str, rol: str) -> Usuario:
    correo = correo.strip().lower()
    nombre = nombre.strip()
    if "@" not in correo or correo.startswith("@") or correo.endswith("@"):
        raise Invalido("Escribe un correo válido.")
    if not nombre:
        raise Invalido("El nombre no puede ir vacío.")
    if rol not in ROLES:
        raise Invalido(f"Rol desconocido: {rol}. Usa uno de: {', '.join(ROLES)}.")
    _validar_contrasena(contrasena)
    try:
        cur = con.execute(
            "INSERT INTO usuarios (correo, nombre, hash_contrasena, rol, creado_en) VALUES (?, ?, ?, ?, ?)",
            (correo, nombre, cifrar_contrasena(contrasena), rol, _iso(_ahora())),
        )
    except sqlite3.IntegrityError:
        raise Invalido(f"Ya existe un usuario con el correo {correo}.") from None
    return Usuario(cur.lastrowid, correo, nombre, rol)


def cambiar_contrasena(con: sqlite3.Connection, correo: str, contrasena: str) -> None:
    _validar_contrasena(contrasena)
    with transaccion(con):
        fila = con.execute("SELECT id FROM usuarios WHERE correo = ?", (correo.strip(),)).fetchone()
        if fila is None:
            raise Invalido(f"No existe el usuario {correo}.")
        con.execute(
            "UPDATE usuarios SET hash_contrasena = ?, intentos_fallidos = 0, bloqueado_hasta = NULL WHERE id = ?",
            (cifrar_contrasena(contrasena), fila["id"]),
        )
        con.execute("DELETE FROM sesiones WHERE usuario_id = ?", (fila["id"],))   # cierra sus sesiones abiertas


def cambiar_activo(con: sqlite3.Connection, correo: str, activo: bool) -> None:
    with transaccion(con):
        fila = con.execute("SELECT id FROM usuarios WHERE correo = ?", (correo.strip(),)).fetchone()
        if fila is None:
            raise Invalido(f"No existe el usuario {correo}.")
        con.execute("UPDATE usuarios SET activo = ? WHERE id = ?", (1 if activo else 0, fila["id"]))
        if not activo:
            con.execute("DELETE FROM sesiones WHERE usuario_id = ?", (fila["id"],))


def listar_usuarios(con: sqlite3.Connection) -> list[sqlite3.Row]:
    return con.execute("SELECT id, correo, nombre, rol, activo FROM usuarios ORDER BY id").fetchall()


# --- Sesiones ---
def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def iniciar_sesion(con: sqlite3.Connection, correo: str, contrasena: str, horas: int) -> tuple[str, Usuario]:
    """Devuelve (token, usuario). El token solo existe aquí y en la cookie del navegador."""
    ahora = _ahora()
    with transaccion(con):
        fila = con.execute("SELECT * FROM usuarios WHERE correo = ?", ((correo or "").strip(),)).fetchone()
        if fila is None or not fila["activo"]:
            verificar_contrasena(contrasena or "", _HASH_SEÑUELO)
            raise NoAutorizado(MENSAJE_CREDENCIALES)

        if fila["bloqueado_hasta"] and datetime.fromisoformat(fila["bloqueado_hasta"]) > ahora:
            raise Bloqueado(f"Demasiados intentos fallidos. Intenta de nuevo en {MINUTOS_BLOQUEO} minutos.")

        if not verificar_contrasena(contrasena or "", fila["hash_contrasena"]):
            intentos = fila["intentos_fallidos"] + 1
            if intentos >= MAX_INTENTOS:
                con.execute("UPDATE usuarios SET intentos_fallidos = 0, bloqueado_hasta = ? WHERE id = ?",
                            (_iso(ahora + timedelta(minutes=MINUTOS_BLOQUEO)), fila["id"]))
            else:
                con.execute("UPDATE usuarios SET intentos_fallidos = ? WHERE id = ?", (intentos, fila["id"]))
            # El intento fallido se guarda aunque respondamos error: por eso se hace COMMIT antes de lanzar.
            error = NoAutorizado(MENSAJE_CREDENCIALES)
        else:
            error = None
            con.execute("UPDATE usuarios SET intentos_fallidos = 0, bloqueado_hasta = NULL WHERE id = ?", (fila["id"],))
            con.execute("DELETE FROM sesiones WHERE expira_en <= ?", (_iso(ahora),))   # limpieza de vencidas
            token = secrets.token_urlsafe(32)
            con.execute(
                "INSERT INTO sesiones (token_hash, usuario_id, creada_en, expira_en) VALUES (?, ?, ?, ?)",
                (_hash_token(token), fila["id"], _iso(ahora), _iso(ahora + timedelta(hours=horas))),
            )
    if error is not None:
        raise error
    return token, Usuario(fila["id"], fila["correo"], fila["nombre"], fila["rol"])


def usuario_de_token(con: sqlite3.Connection, token: str | None) -> Usuario | None:
    if not token:
        return None
    fila = con.execute(
        """SELECT u.id, u.correo, u.nombre, u.rol, s.expira_en
             FROM sesiones s JOIN usuarios u ON u.id = s.usuario_id
            WHERE s.token_hash = ? AND u.activo = 1""",
        (_hash_token(token),),
    ).fetchone()
    if fila is None or datetime.fromisoformat(fila["expira_en"]) <= _ahora():
        return None
    return Usuario(fila["id"], fila["correo"], fila["nombre"], fila["rol"])


def cerrar_sesion(con: sqlite3.Connection, token: str | None) -> None:
    if token:
        con.execute("DELETE FROM sesiones WHERE token_hash = ?", (_hash_token(token),))
