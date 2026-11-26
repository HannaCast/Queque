import io

import pytest
from docx import Document

from app.errores import ErrorProcesamiento


def enviar(cliente, texto="hay que hacer un sistema de inventarios para una farmacia", **extra):
    r = cliente.post("/api/solicitudes", data={"texto": texto}, **extra)
    assert r.status_code == 202, r.text
    return r.json()["id"]


def test_flujo_completo_nota_pegada_sugerencia_y_confirmacion(cliente, procesar):
    pid = enviar(cliente)
    p = cliente.get(f"/api/proyectos/{pid}").json()
    assert p["estado"] == "nuevo" and "brief" not in p              # aún sin analizar

    assert procesar() is True
    p = cliente.get(f"/api/proyectos/{pid}").json()
    assert p["estado"] == "sugerido"
    assert [s["persona_id"] for s in p["sugerencias"]] == [3]       # Leo: el que más libre tiene
    assert [s["persona_id"] for s in p["saltados"]] == [1]          # Moody al 100 %
    assert {t["id"]: t["porcentaje_ocupado"] for t in cliente.get("/api/personas").json()}[3] == 10   # nada cambia sin confirmar

    p = cliente.post(f"/api/proyectos/{pid}/confirmar").json()
    assert p["estado"] == "confirmado" and p["sugerencias"][0]["estado"] == "confirmada"
    leo = {x["id"]: x for x in cliente.get("/api/personas").json()}[3]
    assert leo["porcentaje_ocupado"] == 40 and leo["libre"] == 60
    assert leo["proyecto_actual"] == p["nombre"]

    assert cliente.post(f"/api/proyectos/{pid}/confirmar").status_code == 409   # no se confirma dos veces


def test_cambiar_la_sugerencia_al_confirmar(cliente, procesar):
    pid = enviar(cliente)
    procesar()
    p = cliente.post(f"/api/proyectos/{pid}/confirmar", json={"cambios": [{"area": "Software", "persona_id": 2}]}).json()
    assert p["sugerencias"][0]["persona_id"] == 2 and "Cambiado a mano" in p["sugerencias"][0]["motivo"]
    # Moody no cubre... sí cubre Software, pero está al 100 %: no puede recibirlo
    pid2 = enviar(cliente, "otro sistema web")
    procesar()
    r = cliente.post(f"/api/proyectos/{pid2}/confirmar", json={"cambios": [{"area": "Software", "persona_id": 1}]})
    assert r.status_code == 409 and "Moody" in r.json()["detail"]
    r = cliente.post(f"/api/proyectos/{pid2}/confirmar", json={"cambios": [{"area": "Redes", "persona_id": 2}]})
    assert r.status_code == 422                                      # el proyecto no pidió Redes


def test_sugerencia_vieja_se_detecta_al_confirmar(cliente, procesar, con):
    pid = enviar(cliente)
    procesar()
    con.execute("UPDATE personas SET porcentaje_ocupado = 100 WHERE id = 3")   # la intranet reporta a Leo lleno
    r = cliente.post(f"/api/proyectos/{pid}/confirmar")
    assert r.status_code == 409 and "Leo" in r.json()["detail"]
    p = cliente.post(f"/api/proyectos/{pid}/resugerir").json()
    assert [s["persona_id"] for s in p["sugerencias"]] == [2]       # ahora GESA


def test_en_espera_se_reintenta_cuando_la_intranet_trae_a_alguien(cliente, procesar):
    pid = enviar(cliente, "campaña de difusión para el evento de egresados")
    procesar()
    p = cliente.get(f"/api/proyectos/{pid}").json()
    assert p["estado"] == "en_espera" and p["sugerencias"] == []
    assert cliente.post(f"/api/proyectos/{pid}/confirmar").status_code == 409

    r = cliente.post("/api/intranet/sync", json={"personas": [
        {"id_externo": "emp-77", "nombre": "Marina", "areas": ["Marketing"], "porcentaje_ocupado": 20, "proyecto_actual": "Revista"}]})
    assert r.json() == {"creadas": 1, "actualizadas": 0, "proyectos_reevaluados": 1}
    p = cliente.get(f"/api/proyectos/{pid}").json()
    assert p["estado"] == "sugerido" and p["sugerencias"][0]["area"] == "Marketing"

    # Mismo id_externo otra vez: actualiza, no duplica.
    cliente.post("/api/intranet/sync", json={"personas": [
        {"id_externo": "emp-77", "nombre": "Marina R.", "areas": ["Marketing", "Redes"], "porcentaje_ocupado": 30}]})
    marina = [x for x in cliente.get("/api/personas").json() if x["nombre"].startswith("Marina")]
    assert len(marina) == 1 and marina[0]["areas"] == ["Marketing", "Redes"]


def test_sync_rechaza_areas_fuera_del_catalogo_y_exige_token_si_esta_configurado(cliente, cfg):
    mala = {"personas": [{"id_externo": "x", "nombre": "Z", "areas": ["Cocina"], "porcentaje_ocupado": 0}]}
    assert cliente.post("/api/intranet/sync", json=mala).status_code == 422
    from dataclasses import replace
    from fastapi.testclient import TestClient
    from app.main import crear_app
    with TestClient(crear_app(replace(cfg, token_intranet="secreto"))) as protegido:
        assert protegido.post("/api/intranet/sync", json={"personas": []}).status_code == 401
        ok = protegido.post("/api/intranet/sync", json={"personas": []}, headers={"Authorization": "Bearer secreto"})
        assert ok.status_code == 200


def test_archivo_docx_y_formatos_no_soportados(cliente, procesar):
    doc = Document()
    doc.add_paragraph("Necesitamos una app web para controlar el inventario de la farmacia")
    tabla = doc.add_table(rows=1, cols=2)
    tabla.rows[0].cells[0].text, tabla.rows[0].cells[1].text = "Sucursales", "3"
    buf = io.BytesIO()
    doc.save(buf)
    r = cliente.post("/api/solicitudes", files={"archivo": ("farmacia.docx", buf.getvalue())})
    assert r.status_code == 202
    procesar()
    p = cliente.get(f"/api/proyectos/{r.json()['id']}").json()
    assert p["estado"] == "sugerido" and "Sucursales | 3" in p["texto_crudo"]

    assert cliente.post("/api/solicitudes", files={"archivo": ("hoja.xlsx", b"x")}).status_code == 415
    assert cliente.post("/api/solicitudes", data={"texto": "  "}).status_code == 422


def test_un_documento_malo_queda_en_error_y_se_puede_reintentar(cliente, procesar, con):
    class Roto:
        def analizar(self, texto, error_previo=None):
            raise ErrorProcesamiento("el modelo no respondió")

    pid = enviar(cliente)
    procesar(Roto())
    p = cliente.get(f"/api/proyectos/{pid}").json()
    assert p["estado"] == "error" and "no respondió" in p["error"]
    assert cliente.get("/api/personas").status_code == 200           # el resto sigue respondiendo

    assert cliente.post(f"/api/proyectos/{pid}/reintentar").json()["estado"] == "nuevo"
    procesar()
    assert cliente.get(f"/api/proyectos/{pid}").json()["estado"] == "sugerido"
    assert cliente.post(f"/api/proyectos/{pid}/reintentar").status_code == 409


def test_el_modelo_que_responde_fuera_del_esquema_se_reintenta_una_vez(cliente, procesar):
    llamadas = []

    class Terco:
        def analizar(self, texto, error_previo=None):
            llamadas.append(error_previo)
            return {"proyecto": "x"}            # incompleto: no cumple brief.schema.json

    pid = enviar(cliente)
    procesar(Terco())
    assert len(llamadas) == 2 and llamadas[0] is None and "required" in llamadas[1]
    assert cliente.get(f"/api/proyectos/{pid}").json()["estado"] == "error"


def test_confianza_baja_o_incoherencias_marcan_revision(cliente, procesar):
    pid = enviar(cliente, "algo muy vago")                           # el analizador de prueba duda → confianza baja
    procesar()
    assert cliente.get(f"/api/proyectos/{pid}").json()["requiere_revision"] is True


def test_un_documento_a_la_vez_y_en_orden(cliente, procesar):
    a, b = enviar(cliente, "sistema uno"), enviar(cliente, "sistema dos")
    procesar()
    assert cliente.get(f"/api/proyectos/{a}").json()["estado"] == "sugerido"
    assert cliente.get(f"/api/proyectos/{b}").json()["estado"] == "nuevo"
    procesar()
    assert cliente.get(f"/api/proyectos/{b}").json()["estado"] == "sugerido"
    assert procesar() is False                                       # cola vacía


def test_dashboard_y_cola(cliente, procesar):
    enviar(cliente)
    d = cliente.get("/api/dashboard").json()
    assert d["cola"] == {"nuevo": 1} and len(d["personas"]) == 3
    procesar()
    assert cliente.get("/api/dashboard").json()["cola"] == {"sugerido": 1}
    assert [p["estado"] for p in cliente.get("/api/proyectos").json()] == ["sugerido"]


def test_modo_automatico_confirma_solo_lo_seguro_y_deja_lo_dudoso_para_una_persona(cfg, con, contrato):
    from dataclasses import replace

    from app import servicios
    from app.analisis.falso import AnalizadorFalso
    from tests.conftest import crear_y_entrar

    auto = replace(cfg, confirmacion_automatica=True)
    analizador = AnalizadorFalso(contrato.areas)
    with crear_y_entrar(auto, con, "coordinador") as c:            # el modo automático también exige sesión
        claro = enviar(c, "sistema web de inventario para la farmacia")      # confianza media → se confirma solo
        vago = enviar(c, "algo muy vago")                                    # confianza baja → revisión humana
        servicios.procesar_siguiente(con, auto, contrato, analizador)
        servicios.procesar_siguiente(con, auto, contrato, analizador)
        assert c.get(f"/api/proyectos/{claro}").json()["estado"] == "confirmado"
        p = c.get(f"/api/proyectos/{vago}").json()
        assert p["estado"] == "sugerido" and p["requiere_revision"] is True
        assert {x["id"]: x["porcentaje_ocupado"] for x in c.get("/api/personas").json()}[3] == 40
