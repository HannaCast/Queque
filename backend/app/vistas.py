"""Arma los objetos que consume el frontend a partir de las filas de la base."""
from __future__ import annotations

import json
import sqlite3

from . import repositorio as repo
from .asignacion import Candidata, saltados_para


def persona_a_dict(c: Candidata) -> dict:
    return {"id": c.id, "nombre": c.nombre, "porcentaje_ocupado": c.ocupado, "areas": sorted(c.areas),
            "proyecto_actual": c.proyecto_actual, "libre": c.libre}


def proyecto_a_dict(con: sqlite3.Connection, p: sqlite3.Row, gente: list[Candidata]) -> dict:
    trabajo = repo.trabajo_de(con, p["trabajo_id"])
    brief = json.loads(p["brief_json"]) or None            # '{}' = aún sin brief
    estado = p["estado"]
    error = None
    if estado == "nuevo" and trabajo is not None and trabajo["estado"] == "error":
        estado, error = "error", trabajo["error"]          # el contrato no tiene 'error' en proyectos: se deriva del trabajo
    saltados = []
    if brief and estado in ("sugerido", "en_espera"):      # no se guardan: se calculan con la ocupación de hoy
        saltados = [{"persona_id": s.persona_id, "motivo": s.motivo}
                    for s in saltados_para({a["area"] for a in brief["areas_requeridas"]}, gente)]
    return {
        "id": p["id"], "nombre": p["nombre"], "resumen": p["resumen"] or "", "estado": estado,
        "creado_en": p["creado_en"], "brief": brief,
        "texto_crudo": trabajo["texto_crudo"] if trabajo is not None else None,
        "sugerencias": [{k: a[k] for k in ("persona_id", "area", "porcentaje", "motivo", "estado")} | {"motivo": a["motivo"] or ""}
                        for a in repo.asignaciones(con, p["id"])],
        "saltados": saltados,
        "requiere_revision": trabajo is not None and trabajo["estado"] == "revision",
        "error": error,
    }
