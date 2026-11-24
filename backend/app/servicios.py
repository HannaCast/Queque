"""Casos de uso del pipeline: recepción → conversión a texto → análisis → validación → sugerencia → confirmación."""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

from . import repositorio as repo
from .analisis import Analizador
from .asignacion import sugerir
from .config import Config
from .contrato import Contrato
from .db import transaccion
from .errores import Conflicto, ErrorProcesamiento, FormatoNoSoportado, Invalido, NoEncontrado
from .extraccion import EXTENSIONES_SOPORTADAS, extraer_texto
from .limites import ejecutar_aislado


# ============ 1. Recepción ============
def _nombre_seguro(nombre: str | None) -> str:
    base = Path(nombre or "archivo").name                      # sin carpetas: evita ../../
    base = re.sub(r"[^\w.\- ]", "_", base).strip(" .")[:100]
    return base or "archivo"


def recibir_solicitud(con: sqlite3.Connection, cfg: Config, texto: str, nombre_archivo: str | None = None,
                      contenido: bytes | None = None) -> dict:
    texto = (texto or "").strip()
    if not texto and not contenido:
        raise Invalido("Envía una nota o un archivo.")
    nombre = None
    if contenido is not None:
        nombre = _nombre_seguro(nombre_archivo)
        if Path(nombre).suffix.lower() not in EXTENSIONES_SOPORTADAS:
            raise FormatoNoSoportado(
                f"Formato no soportado todavía. Por ahora: {', '.join(EXTENSIONES_SOPORTADAS)}. "
                "También puedes pegar el contenido como nota."
            )
        if len(contenido) > cfg.max_upload_mb * 1024 * 1024:
            raise Invalido(f"El archivo supera el máximo de {cfg.max_upload_mb} MB.")
    with transaccion(con):
        ids = repo.crear_solicitud(con, texto, nombre)
        if contenido is not None:
            # El archivo se guarda ANTES del commit: así el worker nunca ve un trabajo sin su archivo.
            carpeta = cfg.archivos_dir / str(ids["trabajo_id"])
            carpeta.mkdir(parents=True, exist_ok=True)
            (carpeta / nombre).write_bytes(contenido)
    return ids


# ============ 2-5. Procesamiento (lo ejecuta el worker) ============
def _analizar_y_validar(analizador: Analizador, contrato: Contrato, texto: str) -> dict:
    error: str | None = None
    for _ in range(2):                                          # un reintento corrigiendo al modelo
        try:
            brief = analizador.analizar(texto, error)
        except json.JSONDecodeError as e:
            error = f"la respuesta no era JSON válido: {e.msg}"
            continue
        errores = contrato.errores(brief)
        if not errores:
            return brief
        error = "; ".join(errores[:5])
    raise ErrorProcesamiento(f"El modelo no devolvió un brief válido: {error}")


def advertencias_de_coherencia(brief: dict) -> list[str]:
    """Lo que el esquema JSON no puede ver: incoherencias entre las partes del brief."""
    avisos = []
    areas = {a["area"] for a in brief["areas_requeridas"]}
    titulos = {t["titulo"] for t in brief["tareas"]}
    if not areas:
        avisos.append("El modelo no detectó ninguna área requerida")
    for t in brief["tareas"]:
        if t["area"] not in areas:
            avisos.append(f"La tarea «{t['titulo']}» pide el área {t['area']}, que no está en las áreas requeridas")
        for dep in t["depende_de"]:
            if dep not in titulos:
                avisos.append(f"La tarea «{t['titulo']}» depende de «{dep}», que no existe")
    return avisos


def requiere_revision(brief: dict, avisos: list[str]) -> bool:
    return bool(avisos) or any(
        a["confianza"] == "baja" or a["porcentaje_sugerido"] <= 0 for a in brief["areas_requeridas"]
    )


def _sugerir_y_guardar(con: sqlite3.Connection, proyecto_id: int, brief: dict) -> str:
    """Calcula y guarda sugerencias para las áreas aún sin confirmar. Devuelve el estado del proyecto."""
    ya = repo.areas_confirmadas(con, proyecto_id)
    pedidas = [a for a in brief["areas_requeridas"] if a["area"] not in ya]
    resultado = sugerir(pedidas, repo.candidatas(con))
    repo.borrar_sugeridas(con, proyecto_id)
    for s in resultado.sugerencias:
        repo.insertar_sugerencia(con, proyecto_id, s)
    repo.marcar_tareas(con, proyecto_id, {s.area for s in resultado.sugerencias})
    return "sugerido" if resultado.sugerencias else "en_espera"


def procesar_siguiente(con: sqlite3.Connection, cfg: Config, contrato: Contrato, analizador: Analizador) -> bool:
    """Procesa UN trabajo pendiente. Devuelve False si no había ninguno."""
    trabajo = repo.reclamar_trabajo(con)
    if trabajo is None:
        return False
    try:
        texto = (trabajo["texto_crudo"] or "").strip()
        if trabajo["nombre_archivo"]:
            ruta = cfg.archivos_dir / str(trabajo["id"]) / trabajo["nombre_archivo"]
            del_archivo = ejecutar_aislado(extraer_texto, (ruta,), cfg.limite_mem_mb, cfg.limite_tiempo_s)
            texto = f"{texto}\n\n{del_archivo}".strip()
        if not texto:
            raise ErrorProcesamiento("La solicitud no tiene texto que analizar")

        recortado = len(texto) > cfg.max_chars
        brief = _analizar_y_validar(analizador, contrato, texto[: cfg.max_chars])
        avisos = advertencias_de_coherencia(brief)
        if recortado:
            avisos.append(f"El documento se recortó a {cfg.max_chars} caracteres para analizarlo")
        brief["supuestos"] = [*brief["supuestos"], *avisos]
        revision = requiere_revision(brief, avisos)

        with transaccion(con):
            proyecto_id = con.execute("SELECT id FROM proyectos WHERE trabajo_id = ?", (trabajo["id"],)).fetchone()["id"]
            repo.completar_proyecto(con, proyecto_id, brief)
            repo.insertar_tareas(con, proyecto_id, brief["tareas"])
            repo.estado_proyecto(con, proyecto_id, _sugerir_y_guardar(con, proyecto_id, brief))
            repo.cerrar_trabajo(con, trabajo["id"], "revision" if revision else "listo", texto, brief)
    except Exception as e:  # noqa: BLE001 - un documento malo no debe tumbar al worker
        repo.marcar_error(con, trabajo["id"], str(e) or type(e).__name__)
        return True
    # Modo automático: lo dudoso (revisión) NO se confirma solo; queda para que una persona lo mire.
    if cfg.confirmacion_automatica and not revision:
        try:
            confirmar(con, proyecto_id)
        except (Conflicto, Invalido):
            pass   # nadie disponible o la sugerencia ya cambió: queda sugerido/en espera, sin tumbar al worker
    return True


# ============ 6. Sugerir de nuevo, confirmar o cambiar ============
def _proyecto_con_brief(con: sqlite3.Connection, proyecto_id: int) -> tuple[sqlite3.Row, dict]:
    p = repo.proyecto(con, proyecto_id)
    if p is None:
        raise NoEncontrado("No encontramos ese proyecto.")
    brief = json.loads(p["brief_json"])
    if not brief:
        raise Conflicto("El proyecto todavía no tiene brief.")
    return p, brief


def _resugerir_dentro(con: sqlite3.Connection, proyecto_id: int) -> None:
    _, brief = _proyecto_con_brief(con, proyecto_id)
    repo.estado_proyecto(con, proyecto_id, _sugerir_y_guardar(con, proyecto_id, brief))


def resugerir(con: sqlite3.Connection, proyecto_id: int) -> None:
    with transaccion(con):
        p, _ = _proyecto_con_brief(con, proyecto_id)
        if p["estado"] == "confirmado":
            raise Conflicto("El proyecto ya está confirmado.")
        _resugerir_dentro(con, proyecto_id)


def confirmar(con: sqlite3.Connection, proyecto_id: int, cambios: list[dict] | None = None) -> None:
    """Confirma las sugerencias (opcionalmente cambiando a quién). Aquí recién cambia la ocupación."""
    with transaccion(con):
        p, _ = _proyecto_con_brief(con, proyecto_id)
        if p["estado"] == "confirmado":
            raise Conflicto("El proyecto ya está confirmado.")
        sugeridas = {a["area"]: a for a in repo.asignaciones(con, proyecto_id, "sugerida")}
        if not sugeridas:
            raise Conflicto("No hay sugerencias que confirmar: el proyecto sigue en espera.")
        gente = {c.id: c for c in repo.candidatas(con)}

        for cambio in cambios or []:
            actual = sugeridas.get(cambio["area"])
            nueva = gente.get(cambio["persona_id"])
            if actual is None:
                raise Invalido(f"El proyecto no tiene sugerencia para el área {cambio['area']}.")
            if nueva is None or cambio["area"] not in nueva.areas:
                raise Invalido(f"Esa persona no existe o no cubre el área {cambio['area']}.")
            actual["persona_id"] = nueva.id
            actual["motivo"] = f"Cambiado a mano: {nueva.nombre}."

        # La sugerencia pudo quedar vieja (otra confirmación, o la intranet cambió la ocupación).
        carga: dict[int, float] = {}
        for a in sugeridas.values():
            carga[a["persona_id"]] = carga.get(a["persona_id"], 0.0) + a["porcentaje"]
        for persona_id, total in carga.items():
            if total > gente[persona_id].libre + 1e-9:
                raise Conflicto(
                    f"{gente[persona_id].nombre} ya no tiene {total:.0f} % libre (le queda {gente[persona_id].libre:.0f} %). "
                    "Pide la sugerencia de nuevo o elige a otra persona."
                )

        t = repo.ahora()
        for a in sugeridas.values():
            con.execute(
                "UPDATE asignaciones SET persona_id = ?, motivo = ?, estado = 'confirmada', confirmada_en = ? WHERE id = ?",
                (a["persona_id"], a["motivo"], t, a["id"]),
            )
            con.execute(
                "UPDATE personas SET porcentaje_ocupado = MIN(100, porcentaje_ocupado + ?), actualizado_en = ? WHERE id = ?",
                (a["porcentaje"], t, a["persona_id"]),
            )
            repo.confirmar_tareas_de_area(con, proyecto_id, a["area"])
        repo.estado_proyecto(con, proyecto_id, "en_espera" if repo.tareas_sin_confirmar(con, proyecto_id) else "confirmado")


def reintentar(con: sqlite3.Connection, proyecto_id: int) -> None:
    with transaccion(con):
        p = repo.proyecto(con, proyecto_id)
        if p is None:
            raise NoEncontrado("No encontramos ese proyecto.")
        trabajo = repo.trabajo_de(con, p["trabajo_id"])
        if trabajo is None or trabajo["estado"] != "error":
            raise Conflicto("Solo se puede reintentar un proyecto cuyo análisis terminó en error.")
        repo.reintentar_trabajo(con, trabajo["id"])


# ============ Intranet ============
def sincronizar_intranet(con: sqlite3.Connection, contrato: Contrato, personas: list[dict]) -> dict:
    """Crea o actualiza personas por id_externo. La intranet manda: pisa nombre, áreas y ocupación."""
    for p in personas:
        malas = [a for a in p["areas"] if a not in contrato.areas]
        if malas:
            raise Invalido(f"{p['nombre']}: áreas fuera del catálogo {list(contrato.areas)}: {malas}")
    creadas = actualizadas = 0
    with transaccion(con):
        t = repo.ahora()
        for p in personas:
            fila = con.execute("SELECT id FROM personas WHERE id_externo = ?", (p["id_externo"],)).fetchone()
            if fila:
                persona_id = fila["id"]
                con.execute(
                    "UPDATE personas SET nombre = ?, porcentaje_ocupado = ?, proyecto_intranet = ?, actualizado_en = ? WHERE id = ?",
                    (p["nombre"], p["porcentaje_ocupado"], p.get("proyecto_actual"), t, persona_id),
                )
                actualizadas += 1
            else:
                persona_id = con.execute(
                    "INSERT INTO personas (nombre, porcentaje_ocupado, actualizado_en, id_externo, proyecto_intranet) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (p["nombre"], p["porcentaje_ocupado"], t, p["id_externo"], p.get("proyecto_actual")),
                ).lastrowid
                creadas += 1
            repo.reemplazar_habilidades(con, persona_id, p["areas"])
        # Quizá ahora alguien tiene porcentaje libre: se reintenta lo que estaba en espera.
        reintentados = repo.proyectos_con_espera(con)
        for proyecto_id in reintentados:
            _resugerir_dentro(con, proyecto_id)
    return {"creadas": creadas, "actualizadas": actualizadas, "proyectos_reevaluados": len(reintentados)}
