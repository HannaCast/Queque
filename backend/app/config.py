"""Configuración leída del entorno. Todo tiene un valor por defecto razonable."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

RAIZ_BACKEND = Path(__file__).resolve().parent.parent
RAIZ_REPO = RAIZ_BACKEND.parent  # el backend vive en <repo>/backend, junto a <repo>/contrato


@dataclass(frozen=True)
class Config:
    db_path: Path
    contrato_dir: Path
    archivos_dir: Path
    analizador: str = "ollama"            # "ollama" | "falso"
    ollama_url: str = "http://localhost:11434"
    ollama_modelo: str = "qwen2.5:3b"
    ollama_timeout_s: int = 600
    ollama_num_ctx: int = 8192
    max_upload_mb: int = 10
    max_chars: int = 24000                # texto máximo que se manda al modelo
    limite_mem_mb: int = 1024             # RAM adicional permitida al leer un archivo
    limite_tiempo_s: int = 120
    poll_s: float = 2.0
    confirmacion_automatica: bool = False  # False = una persona confirma (README). True = se confirma sola (documento original)
    token_intranet: str | None = None
    sesion_horas: int = 8                 # cuánto dura una sesión iniciada
    cookie_segura: bool = False           # True en producción (HTTPS): la cookie solo viaja cifrada
    origenes_cors: tuple[str, ...] = ("http://localhost:5173",)


def cargar_config() -> Config:
    env = os.environ.get
    datos = Path(env("QUEQUE_DATOS", str(RAIZ_BACKEND / "datos")))
    return Config(
        db_path=Path(env("QUEQUE_DB", str(datos / "queque.sqlite3"))),
        contrato_dir=Path(env("QUEQUE_CONTRATO", str(RAIZ_REPO / "contrato"))),
        archivos_dir=Path(env("QUEQUE_ARCHIVOS", str(datos / "archivos"))),
        analizador=env("QUEQUE_ANALIZADOR", "ollama"),
        ollama_url=env("QUEQUE_OLLAMA_URL", "http://localhost:11434"),
        ollama_modelo=env("QUEQUE_OLLAMA_MODELO", "qwen2.5:3b"),
        ollama_timeout_s=int(env("QUEQUE_OLLAMA_TIMEOUT_S", "600")),
        max_upload_mb=int(env("QUEQUE_MAX_UPLOAD_MB", "10")),
        limite_mem_mb=int(env("QUEQUE_LIMITE_MEM_MB", "1024")),
        limite_tiempo_s=int(env("QUEQUE_LIMITE_TIEMPO_S", "120")),
        confirmacion_automatica=env("QUEQUE_CONFIRMACION_AUTOMATICA", "0").lower() in ("1", "true", "si", "sí"),
        token_intranet=env("QUEQUE_TOKEN_INTRANET") or None,
        sesion_horas=int(env("QUEQUE_SESION_HORAS", "8")),
        cookie_segura=env("QUEQUE_COOKIE_SEGURA", "0").lower() in ("1", "true", "si", "sí"),
        origenes_cors=tuple(o.strip() for o in env("QUEQUE_CORS", "http://localhost:5173").split(",") if o.strip()),
    )
