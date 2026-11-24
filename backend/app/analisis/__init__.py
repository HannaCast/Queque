"""Análisis del texto: la IA solo devuelve un brief. Detrás de una interfaz para poder cambiar el modelo."""
from __future__ import annotations

from typing import Protocol

from ..config import Config
from ..contrato import Contrato


class Analizador(Protocol):
    def analizar(self, texto: str, error_previo: str | None = None) -> dict:
        """Devuelve un dict con la forma de contrato/brief.schema.json (aún sin validar)."""
        ...


def crear_analizador(cfg: Config, contrato: Contrato) -> Analizador:
    if cfg.analizador == "falso":
        from .falso import AnalizadorFalso

        return AnalizadorFalso(contrato.areas)
    from .ollama import AnalizadorOllama

    return AnalizadorOllama(cfg, contrato)
