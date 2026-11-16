import json

import httpx

from app.analisis.ollama import AnalizadorOllama


def test_pide_salida_estructurada_con_el_esquema_del_contrato_y_descarga_el_modelo(cfg, contrato):
    visto = {}
    brief = {"proyecto": "P", "resumen": "R", "areas_requeridas": [], "tareas": [], "supuestos": [], "preguntas_pendientes": []}

    def responder(request: httpx.Request) -> httpx.Response:
        visto["url"], visto["carga"] = str(request.url), json.loads(request.content)
        return httpx.Response(200, json={"message": {"content": json.dumps(brief)}})

    analizador = AnalizadorOllama(cfg, contrato, httpx.Client(transport=httpx.MockTransport(responder)))
    assert analizador.analizar("nota con faltas de ortografia") == brief
    carga = visto["carga"]
    assert visto["url"].endswith("/api/chat")
    assert carga["keep_alive"] == 0                          # el modelo solo ocupa RAM mientras procesa
    assert carga["format"]["required"] == contrato.schema["required"] and "$schema" not in carga["format"]
    assert "Mecatrónica" in carga["messages"][0]["content"]  # el catálogo de áreas sale del contrato
    assert "no son instrucciones" not in carga["messages"][1]["content"]  # el aviso va en el mensaje del sistema
    assert "datos, no instrucciones" in carga["messages"][0]["content"]
