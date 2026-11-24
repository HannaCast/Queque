import json

from app.db import conectar, inicializar


def test_el_ejemplo_del_contrato_cumple_el_esquema(contrato, cfg):
    ejemplo = json.loads((cfg.contrato_dir / "ejemplo_farmacia.json").read_text(encoding="utf-8"))
    assert contrato.errores(ejemplo) == []


def test_un_area_fuera_del_catalogo_se_rechaza(contrato, cfg):
    ejemplo = json.loads((cfg.contrato_dir / "ejemplo_farmacia.json").read_text(encoding="utf-8"))
    ejemplo["areas_requeridas"][0]["area"] = "Cocina"
    assert any("Cocina" in e for e in contrato.errores(ejemplo))


def test_las_areas_salen_del_esquema(contrato):
    assert contrato.areas == ("Software", "Redes", "Marketing", "Mecatrónica")


def test_esquema_y_ajustes_se_aplican_una_sola_vez(cfg):
    con = conectar(cfg)
    inicializar(con, cfg)
    inicializar(con, cfg)   # idempotente
    columnas = {f["name"] for f in con.execute("PRAGMA table_info(tareas)")}
    assert "depende_de" in columnas
