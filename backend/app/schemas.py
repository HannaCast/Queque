"""Formas de entrada/salida de la API. Salida = src/types.ts del frontend, para que encaje sin tocar nada."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class PersonaOut(BaseModel):
    id: int
    nombre: str
    porcentaje_ocupado: float
    areas: list[str]
    proyecto_actual: str | None = None
    libre: float


class AsignacionOut(BaseModel):
    persona_id: int
    area: str
    porcentaje: float
    motivo: str
    estado: Literal["sugerida", "confirmada"]


class SaltadoOut(BaseModel):
    persona_id: int
    motivo: str


class ProyectoOut(BaseModel):
    id: int
    nombre: str
    resumen: str
    estado: Literal["nuevo", "sugerido", "confirmado", "en_espera", "error"]
    creado_en: str
    sugerencias: list[AsignacionOut]
    saltados: list[SaltadoOut]
    brief: dict | None = None
    texto_crudo: str | None = None
    requiere_revision: bool = False        # extra: el frontend actual la ignora
    error: str | None = None               # extra: motivo cuando estado == 'error'


class SolicitudCreada(BaseModel):
    id: int
    trabajo_id: int


class CambioIn(BaseModel):
    area: str
    persona_id: int


class ConfirmarIn(BaseModel):
    cambios: list[CambioIn] = Field(default_factory=list)


class PersonaExternaIn(BaseModel):
    id_externo: str = Field(min_length=1)
    nombre: str = Field(min_length=1)
    areas: list[str] = Field(min_length=1)
    porcentaje_ocupado: float = Field(ge=0, le=100)
    proyecto_actual: str | None = None


class SincronizacionIn(BaseModel):
    personas: list[PersonaExternaIn]


# --- Inicio de sesión ---
class LoginIn(BaseModel):
    correo: str = Field(min_length=3, max_length=254)
    contrasena: str = Field(min_length=1, max_length=256)


class UsuarioOut(BaseModel):
    id: int
    correo: str
    nombre: str
    rol: Literal["admin", "coordinador", "consulta"]
