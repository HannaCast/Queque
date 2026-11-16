"""Analizador de mentiras para desarrollar y probar sin modelo. Es determinista: mismas palabras, mismo brief."""
from __future__ import annotations

import re

_REGLAS = {
    "Marketing": r"campañ|publicidad|redes sociales|difusi[oó]n|evento|marca|landing",
    "Mecatrónica": r"sensor|robot|arduino|motor|plc|temperatura|lector|mecatr",
    "Redes": r"\bred(es)?\b|wifi|router|sucursal|conectividad|servidor",
    "Software": r"sistema|app|aplicaci[oó]n|software|inventario|web|base de datos|p[aá]gina",
}


class AnalizadorFalso:
    def __init__(self, areas: tuple[str, ...]):
        self.areas = areas

    def analizar(self, texto: str, error_previo: str | None = None) -> dict:
        minusculas = texto.lower().replace("redes sociales", "marketing")
        encontradas = [a for a, rx in _REGLAS.items() if a in self.areas and re.search(rx, minusculas)]
        confianza = "media"
        if not encontradas:
            encontradas, confianza = ["Software"], "baja"
        primera = next((l.strip() for l in texto.splitlines() if l.strip()), "Solicitud sin título")
        return {
            "proyecto": primera[:60],
            "resumen": primera[:140],
            "areas_requeridas": [
                {"area": a, "horas_estimadas": 80, "porcentaje_sugerido": 30, "confianza": confianza,
                 "justificacion": "Detectado por palabras clave (analizador de prueba)"}
                for a in encontradas
            ],
            "tareas": [
                {"titulo": f"Definir alcance de {a}", "area": a, "prioridad": "alta", "depende_de": []}
                for a in encontradas
            ],
            "supuestos": ["Brief generado por el analizador de prueba, no por el modelo local"],
            "preguntas_pendientes": ["¿Qué fecha de entrega se espera?"],
        }
