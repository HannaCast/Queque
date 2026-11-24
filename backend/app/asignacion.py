"""Motor de sugerencia. Código puro: no toca la base ni la red, por eso es fácil de probar.

Implementa las "Reglas de asignación" del README:
  1. Solo entran personas que cubren un área pedida por el brief.
  2. Quien está al 100 % no recibe otro proyecto.
  3. Entre quienes sí pueden, se propone a quien tiene más porcentaje libre.
  4. Si empatan, a quien lleva más tiempo sin un proyecto nuevo.
  5. Si nadie puede, esa área queda en espera.
  6. Un proyecto puede pedir varias áreas y, por lo tanto, varias personas.

La IA nunca decide a quién asignar: solo dice qué áreas hacen falta.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Candidata:
    id: int
    nombre: str
    areas: frozenset[str]
    ocupado: float
    ultimo_proyecto: str | None = None   # fecha ISO de su última asignación confirmada
    proyecto_actual: str | None = None

    @property
    def libre(self) -> float:
        return max(0.0, 100.0 - self.ocupado)


@dataclass(frozen=True)
class Sugerencia:
    persona_id: int
    area: str
    porcentaje: float
    motivo: str


@dataclass(frozen=True)
class Saltado:
    persona_id: int
    motivo: str


@dataclass
class Resultado:
    sugerencias: list[Sugerencia] = field(default_factory=list)
    saltados: list[Saltado] = field(default_factory=list)
    sin_candidato: list[str] = field(default_factory=list)   # áreas que quedan en espera


def _pct(x: float) -> str:
    return f"{x:.0f}" if float(x).is_integer() else f"{x:.1f}"


def fusionar_areas(areas: list[dict]) -> list[dict]:
    """Si el modelo repite un área, se suman sus porcentajes (tope 100)."""
    fusion: dict[str, float] = {}
    for a in areas:
        fusion[a["area"]] = min(100.0, fusion.get(a["area"], 0.0) + float(a["porcentaje_sugerido"]))
    return [{"area": area, "porcentaje": pct} for area, pct in fusion.items()]


def saltados_para(areas: set[str], personas: list[Candidata]) -> list[Saltado]:
    """Personas que cubren alguna de las áreas pero están al 100 %: la pantalla dice 'a quién se saltó'."""
    resultado = []
    for p in personas:
        if p.areas & areas and p.libre <= 0:
            donde = f" en {p.proyecto_actual}" if p.proyecto_actual else ""
            resultado.append(Saltado(p.id, f"Está al 100 %{donde}"))
    return resultado


def sugerir(areas_requeridas: list[dict], personas: list[Candidata]) -> Resultado:
    pedidas = fusionar_areas(areas_requeridas)
    libre = {p.id: p.libre for p in personas}
    elegidas: set[int] = set()
    res = Resultado(saltados=saltados_para({a["area"] for a in pedidas}, personas))

    def candidatas(area: str) -> list[Candidata]:
        return [p for p in personas if area in p.areas and libre[p.id] > 0]

    por_area: dict[str, Sugerencia] = {}
    # Primero las áreas con menos candidatas, para no gastar a quien es la única opción de otra área.
    for pedida in sorted(pedidas, key=lambda a: (len(candidatas(a["area"])), a["area"])):
        area = pedida["area"]
        cands = candidatas(area)
        if not cands:
            res.sin_candidato.append(area)
            continue
        mejor = min(
            cands,
            key=lambda p: (
                p.id in elegidas,              # preferir a alguien que aún no esté en este proyecto
                -libre[p.id],                  # más porcentaje libre
                p.ultimo_proyecto or "",       # más tiempo sin proyecto (sin historial = el primero)
                p.id,                          # desempate estable
            ),
        )
        libre_antes = libre[mejor.id]
        asignado = min(pedida["porcentaje"], libre_antes)
        motivo = f"{mejor.nombre} tiene {area} y {_pct(libre_antes)} % libre."
        if asignado < pedida["porcentaje"]:
            motivo += f" Se propone {_pct(asignado)} % de los {_pct(pedida['porcentaje'])} % pedidos: es lo que le queda libre."
        if mejor.id in elegidas:
            motivo += " También cubre otra área de este proyecto porque no hay otra persona disponible."
        libre[mejor.id] = libre_antes - asignado
        elegidas.add(mejor.id)
        por_area[area] = Sugerencia(mejor.id, area, asignado, motivo)

    # Se devuelven en el mismo orden en que el brief pidió las áreas.
    res.sugerencias = [por_area[a["area"]] for a in pedidas if a["area"] in por_area]
    return res
