"""Endpoints. Cada uno corresponde a una acción que hoy hace el QuequeContext del frontend con datos de ejemplo."""
from __future__ import annotations

import hmac
import sqlite3
from collections import Counter

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Request, UploadFile

from . import repositorio as repo, servicios, vistas
from .db import conectar
from .errores import NoEncontrado
from .schemas import (ConfirmarIn, PersonaOut, ProyectoOut, SincronizacionIn, SolicitudCreada)

router = APIRouter(prefix="/api")
SIN_NULOS = {"response_model_exclude_none": True}   # el frontend usa campos opcionales (?), no null


def obtener_con(request: Request):
    con = conectar(request.app.state.cfg)
    try:
        yield con
    finally:
        con.close()


def _proyecto(con: sqlite3.Connection, proyecto_id: int) -> dict:
    fila = repo.proyecto(con, proyecto_id)
    if fila is None:
        raise NoEncontrado("No encontramos ese proyecto.")
    return vistas.proyecto_a_dict(con, fila, repo.candidatas(con))


@router.get("/salud")
def salud(con: sqlite3.Connection = Depends(obtener_con)):
    cuentas = dict(con.execute("SELECT estado, COUNT(*) FROM trabajos GROUP BY estado").fetchall())
    return {"ok": True, "trabajos": cuentas}


# --- Cola / Proyecto ---
@router.get("/proyectos", response_model=list[ProyectoOut], **SIN_NULOS)
def listar_proyectos(con: sqlite3.Connection = Depends(obtener_con)):
    gente = repo.candidatas(con)
    return [vistas.proyecto_a_dict(con, p, gente) for p in repo.listar_proyectos(con)]


@router.get("/proyectos/{proyecto_id}", response_model=ProyectoOut, **SIN_NULOS)
def ver_proyecto(proyecto_id: int, con: sqlite3.Connection = Depends(obtener_con)):
    return _proyecto(con, proyecto_id)


# --- Nueva solicitud: responde 202 enseguida; el análisis lo hace el worker ---
@router.post("/solicitudes", response_model=SolicitudCreada, status_code=202)
def nueva_solicitud(request: Request, texto: str = Form(""), archivo: UploadFile | None = File(None),
                    con: sqlite3.Connection = Depends(obtener_con)):
    cfg = request.app.state.cfg
    contenido = nombre = None
    if archivo is not None and archivo.filename:
        nombre = archivo.filename
        contenido = archivo.file.read(cfg.max_upload_mb * 1024 * 1024 + 1)   # +1 para detectar que se pasó
    return servicios.recibir_solicitud(con, cfg, texto, nombre, contenido)


@router.post("/proyectos/{proyecto_id}/confirmar", response_model=ProyectoOut, **SIN_NULOS)
def confirmar(proyecto_id: int, cuerpo: ConfirmarIn | None = None, con: sqlite3.Connection = Depends(obtener_con)):
    cambios = [c.model_dump() for c in cuerpo.cambios] if cuerpo else []
    servicios.confirmar(con, proyecto_id, cambios)
    return _proyecto(con, proyecto_id)


@router.post("/proyectos/{proyecto_id}/resugerir", response_model=ProyectoOut, **SIN_NULOS)
def resugerir(proyecto_id: int, con: sqlite3.Connection = Depends(obtener_con)):
    servicios.resugerir(con, proyecto_id)
    return _proyecto(con, proyecto_id)


@router.post("/proyectos/{proyecto_id}/reintentar", response_model=ProyectoOut, **SIN_NULOS)
def reintentar(proyecto_id: int, con: sqlite3.Connection = Depends(obtener_con)):
    servicios.reintentar(con, proyecto_id)
    return _proyecto(con, proyecto_id)


# --- Equipo / Dashboard ---
@router.get("/personas", response_model=list[PersonaOut], **SIN_NULOS)
def listar_personas(con: sqlite3.Connection = Depends(obtener_con)):
    return [vistas.persona_a_dict(c) for c in repo.candidatas(con)]


@router.get("/dashboard")
def dashboard(con: sqlite3.Connection = Depends(obtener_con)):
    gente = repo.candidatas(con)
    proyectos = [vistas.proyecto_a_dict(con, p, gente) for p in repo.listar_proyectos(con)]
    en_proceso = con.execute("SELECT COUNT(*) FROM trabajos WHERE estado = 'procesando'").fetchone()[0]
    return {
        "personas": [vistas.persona_a_dict(c) for c in gente],
        "cola": dict(Counter(p["estado"] for p in proyectos)),
        "analizando_ahora": en_proceso > 0,
    }


# --- Intranet: las personas llegan solas desde allá ---
def exigir_token(request: Request, authorization: str | None = Header(None)):
    token = request.app.state.cfg.token_intranet
    if token and not hmac.compare_digest(authorization or "", f"Bearer {token}"):
        raise HTTPException(status_code=401, detail="Token de la intranet inválido.")


@router.post("/intranet/sync", dependencies=[Depends(exigir_token)])
def sincronizar(cuerpo: SincronizacionIn, request: Request, con: sqlite3.Connection = Depends(obtener_con)):
    from .contrato import cargar_contrato

    contrato = cargar_contrato(request.app.state.cfg.contrato_dir)
    return servicios.sincronizar_intranet(con, contrato, [p.model_dump() for p in cuerpo.personas])
