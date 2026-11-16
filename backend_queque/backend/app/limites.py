"""Ejecuta una función en un proceso hijo con tope de memoria y de tiempo.

Cumple con el README: "si el análisis se pasa de memoria, ese trabajo queda en error y el
dashboard sigue respondiendo". Si el hijo se pasa, muere solo él; la API y el worker siguen vivos.

Alcance real: el tope de memoria usa RLIMIT_AS y solo existe en Linux. Cubre la lectura de
archivos. El modelo local corre en su propio proceso (Ollama): su tope de CPU/RAM se pone ahí
(ver deploy/ollama.compose.yml), no desde Python.
"""
from __future__ import annotations

import multiprocessing as mp
import os
import queue
import time

from .errores import ErrorProcesamiento

try:
    import resource
except ImportError:  # Windows
    resource = None  # type: ignore[assignment]


def _memoria_virtual_actual() -> int:
    with open("/proc/self/statm", encoding="ascii") as f:
        return int(f.read().split()[0]) * os.sysconf("SC_PAGE_SIZE")


def _hijo(salida, fn, args, mem_mb):
    try:
        if resource is not None and mem_mb:
            # El tope es sobre la memoria ADICIONAL: se suma lo que el intérprete ya ocupa al arrancar.
            tope = _memoria_virtual_actual() + mem_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (tope, tope))
        salida.put(("ok", fn(*args)))
    except MemoryError:
        salida.put(("error", "Se superó el tope de memoria al leer el documento"))
    except Exception as e:  # noqa: BLE001 - cualquier falla del extractor se reporta como texto
        salida.put(("error", str(e) or type(e).__name__))


def ejecutar_aislado(fn, args=(), mem_mb: int = 0, timeout_s: float = 60):
    ctx = mp.get_context("spawn")
    salida = ctx.Queue()
    proceso = ctx.Process(target=_hijo, args=(salida, fn, args, mem_mb), daemon=True)
    proceso.start()
    limite = time.monotonic() + timeout_s
    try:
        while True:
            try:
                estado, valor = salida.get(timeout=0.2)
                break
            except queue.Empty:
                if not proceso.is_alive():
                    try:  # puede haber dejado el resultado justo antes de terminar
                        estado, valor = salida.get(timeout=0.5)
                        break
                    except queue.Empty:
                        raise ErrorProcesamiento(
                            "El proceso de lectura terminó sin resultado (posible falta de memoria)"
                        ) from None
                if time.monotonic() > limite:
                    raise ErrorProcesamiento(f"La lectura del documento superó {timeout_s:.0f} s") from None
    finally:
        proceso.join(timeout=2)
        if proceso.is_alive():
            proceso.kill()
    if estado == "error":
        raise ErrorProcesamiento(valor)
    return valor
