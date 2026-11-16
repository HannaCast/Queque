from app.asignacion import Candidata, sugerir

MOODY = Candidata(1, "Moody", frozenset({"Software"}), 100, proyecto_actual="Portal de alumnos")
GESA = Candidata(2, "GESA", frozenset({"Software", "Redes"}), 40)
LEO = Candidata(3, "Leo", frozenset({"Software", "Mecatrónica"}), 10)


def area(nombre, pct=40):
    return {"area": nombre, "porcentaje_sugerido": pct}


def test_se_salta_al_que_esta_al_100_y_se_elige_al_que_mas_libre_tiene():
    r = sugerir([area("Software")], [MOODY, GESA, LEO])
    assert [s.persona_id for s in r.sugerencias] == [3]            # Leo: 90 % libre > GESA: 60 %
    assert [s.persona_id for s in r.saltados] == [1]
    assert "Portal de alumnos" in r.saltados[0].motivo


def test_empate_gana_quien_lleva_mas_tiempo_sin_proyecto():
    a = Candidata(10, "A", frozenset({"Software"}), 50, ultimo_proyecto="2026-10-20T10:00:00")
    b = Candidata(11, "B", frozenset({"Software"}), 50, ultimo_proyecto="2026-09-01T10:00:00")
    c = Candidata(12, "C", frozenset({"Software"}), 50, ultimo_proyecto=None)   # nunca ha tenido uno
    assert sugerir([area("Software")], [a, b, c]).sugerencias[0].persona_id == 12
    assert sugerir([area("Software")], [a, b]).sugerencias[0].persona_id == 11


def test_si_pide_mas_de_lo_que_le_queda_se_propone_lo_que_le_queda():
    casi_lleno = Candidata(5, "Ana", frozenset({"Redes"}), 85)
    s = sugerir([area("Redes", 40)], [casi_lleno]).sugerencias[0]
    assert s.porcentaje == 15 and "15 % de los 40 %" in s.motivo


def test_varias_areas_piden_varias_personas():
    r = sugerir([area("Software", 40), area("Redes", 20)], [MOODY, GESA, LEO])
    assert {(s.area, s.persona_id) for s in r.sugerencias} == {("Redes", 2), ("Software", 3)}


def test_si_solo_hay_una_persona_cubre_las_dos_areas_con_su_porcentaje_restante():
    r = sugerir([area("Software", 30), area("Redes", 50)], [GESA])      # GESA tiene 60 % libre
    por_area = {s.area: s.porcentaje for s in r.sugerencias}
    assert por_area == {"Redes": 50, "Software": 10}


def test_area_sin_nadie_queda_en_espera_y_las_demas_siguen():
    r = sugerir([area("Marketing"), area("Software")], [MOODY, GESA, LEO])
    assert r.sin_candidato == ["Marketing"]
    assert [s.area for s in r.sugerencias] == ["Software"]


def test_un_area_repetida_por_el_modelo_se_fusiona():
    r = sugerir([area("Software", 30), area("Software", 20)], [LEO])
    assert len(r.sugerencias) == 1 and r.sugerencias[0].porcentaje == 50
