"""API de Queque.   Arranque:  uvicorn app.main:crear_app --factory --reload"""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import Config, cargar_config
from .db import conectar, inicializar
from .errores import ErrorNegocio
from .rutas import router


def crear_app(cfg: Config | None = None) -> FastAPI:
    cfg = cfg or cargar_config()
    con = conectar(cfg)
    try:
        inicializar(con, cfg)
    finally:
        con.close()

    app = FastAPI(title="Queque API", version="0.1.0")
    app.state.cfg = cfg
    app.add_middleware(CORSMiddleware, allow_origins=list(cfg.origenes_cors), allow_methods=["*"], allow_headers=["*"])
    app.include_router(router)

    @app.exception_handler(ErrorNegocio)
    async def _negocio(_: Request, exc: ErrorNegocio):
        return JSONResponse(status_code=exc.status, content={"detail": str(exc)})

    return app
