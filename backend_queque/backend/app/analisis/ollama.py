"""Adaptador al modelo local (Ollama). Se puede reemplazar sin tocar el resto del sistema."""
from __future__ import annotations

import json

import httpx

from ..config import Config
from ..contrato import Contrato
from .prompt import mensaje_sistema, mensaje_usuario


class AnalizadorOllama:
    def __init__(self, cfg: Config, contrato: Contrato, cliente: httpx.Client | None = None):
        self.cfg = cfg
        self.contrato = contrato
        self.cliente = cliente or httpx.Client(timeout=cfg.ollama_timeout_s)

    def analizar(self, texto: str, error_previo: str | None = None) -> dict:
        carga = {
            "model": self.cfg.ollama_modelo,
            "messages": [
                {"role": "system", "content": mensaje_sistema(self.contrato.areas)},
                {"role": "user", "content": mensaje_usuario(texto, error_previo)},
            ],
            "stream": False,
            # El esquema del contrato obliga al modelo a responder con esa forma (salida estructurada).
            "format": self.contrato.schema_para_modelo(),
            # 0 = descarga el modelo de la RAM apenas responde: solo ocupa memoria mientras procesa.
            "keep_alive": 0,
            "options": {"temperature": 0, "num_ctx": self.cfg.ollama_num_ctx},
        }
        respuesta = self.cliente.post(f"{self.cfg.ollama_url}/api/chat", json=carga)
        respuesta.raise_for_status()
        return json.loads(respuesta.json()["message"]["content"])
