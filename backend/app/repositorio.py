"""Acceso a datos (SQL). Aquí no hay reglas de negocio ni transacciones: las abre quien lo llama."""
from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path

from .asignacion import Candidata, Sugerencia


def ahora() -> str:
    return datetime.now().isoformat(timespec="seconds")   # mismo formato que personas_ejemplo.sql


# ---------- personas ----------
def candidatas(con: sqlite3.Connection) -> list[Candidata]:
    habilidades: dict[int, set[str]] = {}
    for f in con.execute("SELECT persona_id, area FROM habilidades"):
        habilidades.setdefault(f["persona_id"], set()).add(f["area"])
    filas = con.execute(
        """SELECT p.id, p.nombre, p.porcentaje_ocupado, p.proyecto_intranet,
                  (SELECT MAX(a.confirmada_en) FROM asignaciones a
                    WHERE a.persona_id = p.id AND a.estado = 'confirmada') AS ultimo,
                  (SELECT pr.nombre FROM asignaciones a JOIN proyectos pr ON pr.id = a.proyecto_id
                    WHERE a.persona_id = p.id AND a.estado = 'confirmada'
                    ORDER BY a.confirmada_en DESC, a.id DESC LIMIT 1) AS actual
             FROM personas p ORDER BY p.id"""
    ).fetchall()
    return [
        Candidata(
            id=f["id"], nombre=f["nombre"], areas=frozenset(habilidades.get(f["id"], ())),
            ocupado=f["porcentaje_ocupado"], ultimo_proyecto=f["ultimo"],
            proyecto_actual=f["actual"] or f["proyecto_intranet"],
        )
        for f in filas
    ]


def reemplazar_habilidades(con: sqlite3.Connection, persona_id: int, areas: list[str]) -> None:
    con.execute("DELETE FROM habilidades WHERE persona_id = ?", (persona_id,))
    con.executemany(
        "INSERT INTO habilidades (persona_id, area) VALUES (?, ?)", [(persona_id, a) for a in sorted(set(areas))]
    )


# ---------- solicitudes y trabajos ----------
def _nombre_provisional(texto: str, nombre_archivo: str | None) -> str:
    if nombre_archivo:
        return Path(nombre_archivo).stem[:80] or "Solicitud sin título"
    una_linea = re.sub(r"\s+", " ", texto).strip()
    return una_linea[:60] or "Solicitud sin título"


def crear_solicitud(con: sqlite3.Connection, texto: str, nombre_archivo: str | None) -> dict:
    t = ahora()
    trabajo_id = con.execute(
        """INSERT INTO trabajos (nombre_archivo, texto_crudo, estado, creado_en, actualizado_en)
           VALUES (?, ?, 'pendiente', ?, ?)""",
        (nombre_archivo, texto or None, t, t),
    ).lastrowid
    # El proyecto existe desde que llega la solicitud, para que la pantalla tenga a dónde ir mientras
    # el modelo trabaja. brief_json es NOT NULL en el contrato, por eso lleva '{}' hasta tener el brief.
    proyecto_id = con.execute(
        """INSERT INTO proyectos (trabajo_id, nombre, resumen, estado, brief_json, creado_en)
           VALUES (?, ?, 'Pendiente de análisis', 'nuevo', '{}', ?)""",
        (trabajo_id, _nombre_provisional(texto, nombre_archivo), t),
    ).lastrowid
    return {"id": proyecto_id, "trabajo_id": trabajo_id}


def reclamar_trabajo(con: sqlite3.Connection) -> sqlite3.Row | None:
    """Toma el trabajo pendiente más antiguo, y solo si no hay otro en proceso (un documento a la vez)."""
    return con.execute(
        """UPDATE trabajos SET estado = 'procesando', error = NULL, actualizado_en = ?
            WHERE id = (SELECT id FROM trabajos WHERE estado = 'pendiente' ORDER BY id LIMIT 1)
              AND NOT EXISTS (SELECT 1 FROM trabajos WHERE estado = 'procesando')
        RETURNING *""",
        (ahora(),),
    ).fetchone()


def marcar_error(con: sqlite3.Connection, trabajo_id: int, mensaje: str) -> None:
    con.execute(
        "UPDATE trabajos SET estado = 'error', error = ?, actualizado_en = ? WHERE id = ?",
        (mensaje[:500], ahora(), trabajo_id),
    )


def cerrar_trabajo(con: sqlite3.Connection, trabajo_id: int, estado: str, texto: str, brief: dict) -> None:
    con.execute(
        "UPDATE trabajos SET estado = ?, texto_crudo = ?, brief_json = ?, error = NULL, actualizado_en = ? WHERE id = ?",
        (estado, texto, json.dumps(brief, ensure_ascii=False), ahora(), trabajo_id),
    )


def recuperar_atascados(con: sqlite3.Connection) -> int:
    """Al arrancar el worker: lo que quedó 'procesando' se interrumpió. Se marca error; se reintenta a mano."""
    return con.execute(
        "UPDATE trabajos SET estado = 'error', error = 'Interrumpido durante el procesamiento; usa Reintentar', "
        "actualizado_en = ? WHERE estado = 'procesando'",
        (ahora(),),
    ).rowcount


def reintentar_trabajo(con: sqlite3.Connection, trabajo_id: int) -> None:
    con.execute(
        "UPDATE trabajos SET estado = 'pendiente', error = NULL, actualizado_en = ? WHERE id = ?",
        (ahora(), trabajo_id),
    )


# ---------- proyectos, tareas, asignaciones ----------
def proyecto(con: sqlite3.Connection, proyecto_id: int) -> sqlite3.Row | None:
    return con.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,)).fetchone()


def listar_proyectos(con: sqlite3.Connection) -> list[sqlite3.Row]:
    return con.execute("SELECT * FROM proyectos ORDER BY creado_en DESC, id DESC").fetchall()


def trabajo_de(con: sqlite3.Connection, trabajo_id: int | None) -> sqlite3.Row | None:
    if trabajo_id is None:
        return None
    return con.execute("SELECT * FROM trabajos WHERE id = ?", (trabajo_id,)).fetchone()


def completar_proyecto(con: sqlite3.Connection, proyecto_id: int, brief: dict) -> None:
    con.execute(
        "UPDATE proyectos SET nombre = ?, resumen = ?, brief_json = ? WHERE id = ?",
        (brief["proyecto"], brief["resumen"], json.dumps(brief, ensure_ascii=False), proyecto_id),
    )


def insertar_tareas(con: sqlite3.Connection, proyecto_id: int, tareas: list[dict]) -> None:
    con.executemany(
        "INSERT INTO tareas (proyecto_id, titulo, area, prioridad, estado, depende_de) VALUES (?, ?, ?, ?, 'pendiente', ?)",
        [(proyecto_id, t["titulo"], t["area"], t["prioridad"], json.dumps(t["depende_de"], ensure_ascii=False)) for t in tareas],
    )


def borrar_sugeridas(con: sqlite3.Connection, proyecto_id: int) -> None:
    con.execute("DELETE FROM asignaciones WHERE proyecto_id = ? AND estado = 'sugerida'", (proyecto_id,))


def insertar_sugerencia(con: sqlite3.Connection, proyecto_id: int, s: Sugerencia) -> None:
    con.execute(
        "INSERT INTO asignaciones (proyecto_id, tarea_id, persona_id, area, porcentaje, estado, motivo) "
        "VALUES (?, NULL, ?, ?, ?, 'sugerida', ?)",
        (proyecto_id, s.persona_id, s.area, s.porcentaje, s.motivo),
    )


def asignaciones(con: sqlite3.Connection, proyecto_id: int, estado: str | None = None) -> list[dict]:
    sql, args = "SELECT * FROM asignaciones WHERE proyecto_id = ?", [proyecto_id]
    if estado:
        sql, args = sql + " AND estado = ?", args + [estado]
    return [dict(f) for f in con.execute(sql + " ORDER BY id", args)]


def areas_confirmadas(con: sqlite3.Connection, proyecto_id: int) -> set[str]:
    return {f["area"] for f in con.execute(
        "SELECT area FROM asignaciones WHERE proyecto_id = ? AND estado = 'confirmada'", (proyecto_id,))}


def marcar_tareas(con: sqlite3.Connection, proyecto_id: int, areas_con_sugerencia: set[str]) -> None:
    """Tareas aún no confirmadas: 'sugerida' si su área tiene sugerencia; si no, 'en_espera'."""
    con.execute("UPDATE tareas SET estado = 'en_espera' WHERE proyecto_id = ? AND estado != 'confirmada'", (proyecto_id,))
    if areas_con_sugerencia:
        marcas = ",".join("?" * len(areas_con_sugerencia))
        con.execute(
            f"UPDATE tareas SET estado = 'sugerida' WHERE proyecto_id = ? AND estado != 'confirmada' AND area IN ({marcas})",
            [proyecto_id, *sorted(areas_con_sugerencia)],
        )


def confirmar_tareas_de_area(con: sqlite3.Connection, proyecto_id: int, area: str) -> None:
    con.execute("UPDATE tareas SET estado = 'confirmada' WHERE proyecto_id = ? AND area = ?", (proyecto_id, area))


def tareas_sin_confirmar(con: sqlite3.Connection, proyecto_id: int) -> int:
    return con.execute(
        "SELECT COUNT(*) FROM tareas WHERE proyecto_id = ? AND estado != 'confirmada'", (proyecto_id,)
    ).fetchone()[0]


def estado_proyecto(con: sqlite3.Connection, proyecto_id: int, estado: str) -> None:
    con.execute("UPDATE proyectos SET estado = ? WHERE id = ?", (estado, proyecto_id))


def proyectos_con_espera(con: sqlite3.Connection) -> list[int]:
    return [f[0] for f in con.execute(
        """SELECT DISTINCT p.id FROM proyectos p JOIN tareas t ON t.proyecto_id = p.id
            WHERE p.estado != 'confirmado' AND t.estado = 'en_espera' ORDER BY p.id""")]
