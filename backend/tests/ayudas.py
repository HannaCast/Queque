"""Funciones que el proceso hijo de prueba debe poder importar (por eso viven en su propio módulo)."""
import time


def gastar_memoria(mb):
    bloque = bytearray(mb * 1024 * 1024)
    return len(bloque)


def dormir(segundos):
    time.sleep(segundos)
    return "tarde"


def sumar(a, b):
    return a + b
