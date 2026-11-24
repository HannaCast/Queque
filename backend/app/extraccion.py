"""Convierte un archivo a texto. Un extractor por extensión (registro simple, fácil de ampliar).

Primera versión: TXT/MD, DOCX y PDF con texto. Pendientes según el README: Word antiguo (.doc),
PDF escaneado (OCR), Excel, PowerPoint e imágenes. Para agregarlos basta con registrar otra función.

Estas funciones corren en un proceso aparte con tope de memoria (ver limites.py).
Los imports van dentro de cada función a propósito: así se cuentan dentro de ese tope.
"""
from __future__ import annotations

from pathlib import Path


class ErrorExtraccion(Exception):
    pass


def _texto_plano(ruta: Path) -> str:
    return ruta.read_bytes().decode("utf-8", errors="replace")


def _docx(ruta: Path) -> str:
    from docx import Document

    doc = Document(str(ruta))
    partes = [p.text for p in doc.paragraphs if p.text.strip()]
    for tabla in doc.tables:
        for fila in tabla.rows:
            partes.append(" | ".join(c.text.strip() for c in fila.cells))
    return "\n".join(partes)


def _pdf(ruta: Path) -> str:
    from pypdf import PdfReader

    lector = PdfReader(str(ruta))
    texto = "\n".join((pagina.extract_text() or "") for pagina in lector.pages).strip()
    if not texto:
        raise ErrorExtraccion("El PDF no tiene capa de texto (parece un escaneo). La lectura con OCR aún no está disponible.")
    return texto


EXTRACTORES = {".txt": _texto_plano, ".md": _texto_plano, ".docx": _docx, ".pdf": _pdf}
EXTENSIONES_SOPORTADAS = tuple(EXTRACTORES)


def extraer_texto(ruta: Path) -> str:
    extractor = EXTRACTORES.get(Path(ruta).suffix.lower())
    if extractor is None:
        raise ErrorExtraccion(f"Formato no soportado todavía: {Path(ruta).suffix or '(sin extensión)'}")
    return extractor(Path(ruta))
