import pytest
from fastapi.testclient import TestClient

from app import cli, servicios
from app.analisis.falso import AnalizadorFalso
from app.config import RAIZ_REPO, Config
from app.contrato import cargar_contrato
from app.db import conectar, inicializar
from app.main import crear_app


@pytest.fixture
def cfg(tmp_path):
    return Config(
        db_path=tmp_path / "queque.sqlite3",
        contrato_dir=RAIZ_REPO / "contrato",
        archivos_dir=tmp_path / "archivos",
        analizador="falso",
        limite_mem_mb=0,   # sin tope en las pruebas generales; el tope tiene su propia prueba
    )


@pytest.fixture
def contrato(cfg):
    return cargar_contrato(cfg.contrato_dir)


@pytest.fixture
def con(cfg):
    c = conectar(cfg)
    inicializar(c, cfg)
    cli.sembrar(c, cfg)          # Moody 100 %, GESA 40 %, Leo 10 %
    yield c
    c.close()


@pytest.fixture
def cliente(cfg, con):
    with TestClient(crear_app(cfg)) as c:
        yield c


@pytest.fixture
def procesar(cfg, con, contrato):
    """Corre el worker una vez, como lo haría `python -m app.worker`."""
    def _procesar(analizador=None):
        return servicios.procesar_siguiente(con, cfg, contrato, analizador or AnalizadorFalso(contrato.areas))
    return _procesar
