import sys

import pytest

from app.errores import ErrorProcesamiento
from app.limites import ejecutar_aislado
from tests import ayudas


def test_devuelve_el_resultado():
    assert ejecutar_aislado(ayudas.sumar, (2, 3), mem_mb=0, timeout_s=30) == 5


def test_el_tiempo_maximo_corta_el_trabajo():
    with pytest.raises(ErrorProcesamiento, match="superó"):
        ejecutar_aislado(ayudas.dormir, (30,), mem_mb=0, timeout_s=2)


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="RLIMIT_AS solo se usa en Linux")
def test_pasarse_de_memoria_deja_el_trabajo_en_error_sin_tumbar_al_que_llama():
    with pytest.raises(ErrorProcesamiento, match="memoria"):
        ejecutar_aislado(ayudas.gastar_memoria, (600,), mem_mb=100, timeout_s=30)
    assert ejecutar_aislado(ayudas.sumar, (1, 1), mem_mb=100, timeout_s=30) == 2   # el proceso principal sigue sano
