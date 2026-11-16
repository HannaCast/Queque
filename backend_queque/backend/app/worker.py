"""Worker: procesa la cola de documentos, uno a la vez.   Arranque:  python -m app.worker

Es un proceso aparte de la API. Si un análisis se cae o se pasa de memoria, la API y el dashboard siguen respondiendo.
"""
from __future__ import annotations

import logging
import signal
import time

from . import repositorio as repo, servicios
from .analisis import crear_analizador
from .config import cargar_config
from .contrato import cargar_contrato
from .db import conectar, inicializar

log = logging.getLogger("queque.worker")
_seguir = True


def _parar(*_):
    global _seguir
    _seguir = False


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    cfg = cargar_config()
    contrato = cargar_contrato(cfg.contrato_dir)
    con = conectar(cfg)
    inicializar(con, cfg)
    interrumpidos = repo.recuperar_atascados(con)
    if interrumpidos:
        log.warning("%d trabajo(s) quedaron interrumpidos y se marcaron como error", interrumpidos)
    analizador = crear_analizador(cfg, contrato)
    signal.signal(signal.SIGINT, _parar)
    signal.signal(signal.SIGTERM, _parar)
    log.info("Worker listo (analizador=%s)", cfg.analizador)
    while _seguir:
        if not servicios.procesar_siguiente(con, cfg, contrato, analizador):
            time.sleep(cfg.poll_s)


if __name__ == "__main__":
    main()
