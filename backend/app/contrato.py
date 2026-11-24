"""Lee el contrato del repositorio (contrato/brief.schema.json) como única fuente de verdad.

Las áreas válidas salen del enum del esquema, no de una lista escrita a mano en el código.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from jsonschema import Draft202012Validator


class Contrato:
    def __init__(self, contrato_dir: Path):
        self.dir = contrato_dir
        self.schema = json.loads((contrato_dir / "brief.schema.json").read_text(encoding="utf-8"))
        self._validador = Draft202012Validator(self.schema)
        items = self.schema["properties"]["areas_requeridas"]["items"]
        self.areas: tuple[str, ...] = tuple(items["properties"]["area"]["enum"])

    def errores(self, brief: object) -> list[str]:
        """Lista legible de incumplimientos; vacía si el brief es válido."""
        encontrados = sorted(self._validador.iter_errors(brief), key=lambda e: [str(p) for p in e.absolute_path])
        return [f"{'/'.join(str(p) for p in e.absolute_path) or '(raíz)'}: {e.message}" for e in encontrados]

    def schema_para_modelo(self) -> dict:
        """Esquema sin metadatos ($schema, $id), para pasarlo como formato de salida al modelo."""
        return {k: v for k, v in self.schema.items() if k not in ("$schema", "$id")}


@lru_cache(maxsize=4)
def cargar_contrato(contrato_dir: Path) -> Contrato:
    return Contrato(contrato_dir)
