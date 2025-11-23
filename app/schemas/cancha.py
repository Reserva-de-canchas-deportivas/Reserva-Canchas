"""
Schemas Pydantic para Cancha
Validación de datos de entrada/salida
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from enum import Enum


class EstadoCancha(str, Enum):
    """Estados posibles de una cancha"""

    ACTIVO = "activo"
    MANTENIMIENTO = "mantenimiento"


class TipoSuperficie(str, Enum):
    """Tipos de superficie disponibles"""

    CESPED = "césped"
    SINTETICO = "sintético"
    CEMENTO = "cemento"
    MADERA = "madera"


class CanchaCreate(BaseModel):
    """Schema para crear una cancha"""

    nombre: str = Field(
        ..., min_length=3, max_length=100, description="Nombre de la cancha"
    )

    tipo_superficie: TipoSuperficie = Field(
        ..., description="Tipo de superficie de la cancha"
    )

    estado: EstadoCancha = Field(
        default=EstadoCancha.ACTIVO,
        description="Estado de la cancha (activo o mantenimiento)",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nombre": "Cancha 1",
                "tipo_superficie": "césped",
                "estado": "activo",
            }
        }
    )


class CanchaUpdate(BaseModel):
    """Schema para actualizar una cancha (campos opcionales)"""

    nombre: Optional[str] = Field(None, min_length=3, max_length=100)

    tipo_superficie: Optional[TipoSuperficie] = None

    estado: Optional[EstadoCancha] = None

    activo: Optional[bool] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"estado": "mantenimiento", "tipo_superficie": "sintético"}
        }
    )


class CanchaResponse(BaseModel):
    """Schema de respuesta de cancha"""

    cancha_id: str
    sede_id: str
    nombre: str
    tipo_superficie: str
    estado: str
    created_at: str
    updated_at: str
    activo: bool

    model_config = ConfigDict(from_attributes=True)


class CanchaListResponse(BaseModel):
    """Schema de respuesta para lista de canchas"""

    total: int
    canchas: List[CanchaResponse]


class ApiResponse(BaseModel):
    """Schema genérico de respuesta API"""

    mensaje: str
    data: Optional[dict | CanchaResponse | CanchaListResponse] = None
    success: bool

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "mensaje": "Cancha creada correctamente",
                "data": {
                    "cancha_id": "123e4567-e89b-12d3-a456-426614174000",
                    "sede_id": "abc123...",
                    "nombre": "Cancha 1",
                    "tipo_superficie": "césped",
                    "estado": "activo",
                },
                "success": True,
            }
        }
    )


class ErrorResponse(BaseModel):
    """Schema de respuesta de error"""

    error: dict

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": {
                    "code": "CONFLICTO_RELACIONAL",
                    "message": "La cancha tiene reservas futuras",
                    "details": {"reservas_futuras": 4},
                }
            }
        }
    )
