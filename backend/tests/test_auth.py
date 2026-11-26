"""Inicio de sesión, sesiones y permisos por rol."""
from datetime import datetime, timedelta, timezone

import pytest

from app import auth
from tests.conftest import CONTRASENA_PRUEBA, crear_y_entrar


def test_contrasena_se_guarda_cifrada_y_se_verifica(con):
    u = auth.crear_usuario(con, "Ana@Utez.MX", "Ana", "una-clave-larga", "admin")
    assert u.correo == "ana@utez.mx"                                   # el correo se normaliza
    guardado = con.execute("SELECT hash_contrasena FROM usuarios WHERE id = ?", (u.id,)).fetchone()[0]
    assert "una-clave-larga" not in guardado and guardado.startswith("scrypt$")
    assert auth.verificar_contrasena("una-clave-larga", guardado)
    assert not auth.verificar_contrasena("otra", guardado)


def test_validaciones_al_crear_usuario(con):
    with pytest.raises(auth.Invalido):
        auth.crear_usuario(con, "corta@x.mx", "X", "1234567", "admin")         # menos de 8
    with pytest.raises(auth.Invalido):
        auth.crear_usuario(con, "sin-arroba", "X", "12345678", "admin")
    with pytest.raises(auth.Invalido):
        auth.crear_usuario(con, "rol@x.mx", "X", "12345678", "jefe")
    auth.crear_usuario(con, "dup@x.mx", "X", "12345678", "consulta")
    with pytest.raises(auth.Invalido):
        auth.crear_usuario(con, "DUP@x.mx", "Y", "12345678", "consulta")      # mismo correo, otra capitalización


def test_sin_sesion_la_api_responde_401(anonimo):
    for metodo, ruta in [("get", "/api/proyectos"), ("get", "/api/proyectos/1"), ("get", "/api/personas"),
                         ("get", "/api/dashboard"), ("get", "/api/auth/yo"), ("post", "/api/proyectos/1/confirmar")]:
        assert getattr(anonimo, metodo)(ruta).status_code == 401, ruta
    assert anonimo.post("/api/solicitudes", data={"texto": "algo"}).status_code == 401
    assert anonimo.get("/api/salud").status_code == 200                       # salud sigue abierta


def test_login_correcto_cookie_y_logout(anonimo, con):
    auth.crear_usuario(con, "coord@x.mx", "Coord", CONTRASENA_PRUEBA, "coordinador")
    r = anonimo.post("/api/auth/login", json={"correo": "COORD@x.mx", "contrasena": CONTRASENA_PRUEBA})
    assert r.status_code == 200
    assert r.json() == {"id": r.json()["id"], "correo": "coord@x.mx", "nombre": "Coord", "rol": "coordinador"}
    cookie = r.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=lax" in cookie and "path=/api" in cookie

    assert anonimo.get("/api/auth/yo").json()["correo"] == "coord@x.mx"
    assert anonimo.get("/api/proyectos").status_code == 200
    token_en_base = con.execute("SELECT token_hash FROM sesiones").fetchone()[0]
    assert token_en_base not in r.headers["set-cookie"]                       # en la base solo queda el hash

    assert anonimo.post("/api/auth/logout").status_code == 204
    assert anonimo.get("/api/proyectos").status_code == 401
    assert con.execute("SELECT COUNT(*) FROM sesiones").fetchone()[0] == 0


def test_credenciales_incorrectas_mismo_mensaje(anonimo, con):
    auth.crear_usuario(con, "u@x.mx", "U", CONTRASENA_PRUEBA, "consulta")
    mala = anonimo.post("/api/auth/login", json={"correo": "u@x.mx", "contrasena": "equivocada"})
    no_existe = anonimo.post("/api/auth/login", json={"correo": "nadie@x.mx", "contrasena": "equivocada"})
    assert mala.status_code == no_existe.status_code == 401
    assert mala.json()["detail"] == no_existe.json()["detail"] == auth.MENSAJE_CREDENCIALES   # no revela qué correos existen


def test_bloqueo_tras_varios_intentos(anonimo, con):
    auth.crear_usuario(con, "b@x.mx", "B", CONTRASENA_PRUEBA, "consulta")
    for _ in range(auth.MAX_INTENTOS):
        assert anonimo.post("/api/auth/login", json={"correo": "b@x.mx", "contrasena": "mal"}).status_code == 401
    r = anonimo.post("/api/auth/login", json={"correo": "b@x.mx", "contrasena": CONTRASENA_PRUEBA})
    assert r.status_code == 429                                               # ni con la correcta mientras dure
    con.execute("UPDATE usuarios SET bloqueado_hasta = ? WHERE correo = 'b@x.mx'",
                ((datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(timespec="seconds"),))
    assert anonimo.post("/api/auth/login", json={"correo": "b@x.mx", "contrasena": CONTRASENA_PRUEBA}).status_code == 200


def test_sesion_vencida_ya_no_sirve(cfg, con):
    c = crear_y_entrar(cfg, con, "coordinador")
    con.execute("UPDATE sesiones SET expira_en = ?",
                ((datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat(timespec="seconds"),))
    assert c.get("/api/proyectos").status_code == 401


def test_usuario_desactivado_pierde_la_sesion(cfg, con):
    c = crear_y_entrar(cfg, con, "coordinador")
    auth.cambiar_activo(con, "coordinador@prueba.local", False)
    assert c.get("/api/proyectos").status_code == 401
    r = c.post("/api/auth/login", json={"correo": "coordinador@prueba.local", "contrasena": CONTRASENA_PRUEBA})
    assert r.status_code == 401


def test_cambiar_contrasena_cierra_sesiones(cfg, con):
    c = crear_y_entrar(cfg, con, "coordinador")
    auth.cambiar_contrasena(con, "coordinador@prueba.local", "nueva-clave-456")
    assert c.get("/api/proyectos").status_code == 401
    assert c.post("/api/auth/login", json={"correo": "coordinador@prueba.local",
                                           "contrasena": "nueva-clave-456"}).status_code == 200


def test_rol_consulta_solo_ve(cfg, con, cliente, procesar):
    pid = cliente.post("/api/solicitudes", data={"texto": "sistema web de inventario"}).json()["id"]
    procesar()
    consulta = crear_y_entrar(cfg, con, "consulta")
    assert consulta.get("/api/proyectos").status_code == 200
    assert consulta.get(f"/api/proyectos/{pid}").status_code == 200
    assert consulta.get("/api/personas").status_code == 200
    assert consulta.get("/api/dashboard").status_code == 200
    r = consulta.post("/api/solicitudes", data={"texto": "otra"})
    assert r.status_code == 403 and "consulta" in r.json()["detail"]
    for accion in ("confirmar", "resugerir", "reintentar"):
        assert consulta.post(f"/api/proyectos/{pid}/{accion}").status_code == 403, accion
    assert cliente.get(f"/api/proyectos/{pid}").json()["estado"] == "sugerido"   # nada cambió


def test_admin_puede_editar(cfg, con, procesar):
    admin = crear_y_entrar(cfg, con, "admin")
    pid = admin.post("/api/solicitudes", data={"texto": "sistema web"}).json()["id"]
    procesar()
    assert admin.post(f"/api/proyectos/{pid}/confirmar").json()["estado"] == "confirmado"


def test_intranet_no_usa_la_sesion(anonimo):
    """La sincronización de la intranet sigue con su propio token (aquí no hay token configurado), no con login."""
    r = anonimo.post("/api/intranet/sync", json={"personas": []})
    assert r.status_code == 200
