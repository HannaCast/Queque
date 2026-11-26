import pytest
from fastapi.testclient import TestClient

from app import auth, cli, servicios
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


CONTRASENA_PRUEBA = "clave-de-prueba-123"


def crear_y_entrar(cfg, con, rol: str) -> TestClient:
    """Crea un usuario con ese rol y devuelve un cliente con su sesión ya iniciada."""
    correo = f"{rol}@prueba.local"
    if con.execute("SELECT 1 FROM usuarios WHERE correo = ?", (correo,)).fetchone() is None:
        auth.crear_usuario(con, correo, rol.capitalize(), CONTRASENA_PRUEBA, rol)
    c = TestClient(crear_app(cfg))
    r = c.post("/api/auth/login", json={"correo": correo, "contrasena": CONTRASENA_PRUEBA})
    assert r.status_code == 200, r.text
    return c


@pytest.fixture
def cliente(cfg, con):
    """Cliente con sesión de coordinador: puede crear solicitudes y confirmar (lo que prueban los tests de la API)."""
    with crear_y_entrar(cfg, con, "coordinador") as c:
        yield c


@pytest.fixture
def anonimo(cfg, con):
    """Cliente sin sesión."""
    with TestClient(crear_app(cfg)) as c:
        yield c


@pytest.fixture
def procesar(cfg, con, contrato):
    """Corre el worker una vez, como lo haría `python -m app.worker`."""
    def _procesar(analizador=None):
        return servicios.procesar_siguiente(con, cfg, contrato, analizador or AnalizadorFalso(contrato.areas))
    return _procesar
