"""
Schemas Pydantic para Sede
Validacion de datos de entrada/salida
"""

import json
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SedeCreate(BaseModel):
    """Schema para crear una sede"""

    nombre: str = Field(
        ..., min_length=3, max_length=200, description="Nombre de la sede"
    )
    direccion: str = Field(
        ..., min_length=10, max_length=500, description="Direccion fisica de la sede"
    )
    zona_horaria: str = Field(default="America/Bogota", description="Zona horaria IANA")
    horario_apertura_json: Dict[str, List[str]] = Field(
        ...,
        description="Horarios de apertura por dia. Formato: {'lunes': ['08:00-20:00']}",
    )
    minutos_buffer: int = Field(
        default=10, ge=0, le=60, description="Minutos de buffer entre reservas (0-60)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nombre": "Complejo Norte",
                "direccion": "Cra 1 # 23-45",
                "zona_horaria": "America/Bogota",
                "horario_apertura_json": {
                    "lunes": ["08:00-20:00"],
                    "martes": ["08:00-20:00"],
                    "miercoles": ["08:00-20:00"],
                    "jueves": ["08:00-20:00"],
                    "viernes": ["08:00-22:00"],
                    "sabado": ["09:00-22:00"],
                    "domingo": ["09:00-18:00"],
                },
                "minutos_buffer": 10,
            }
        }
    )


class SedeUpdate(BaseModel):
    """Schema para actualizar una sede (campos opcionales)"""

    nombre: Optional[str] = Field(None, min_length=3, max_length=200)
    direccion: Optional[str] = Field(None, min_length=10, max_length=500)
    zona_horaria: Optional[str] = None
    horario_apertura_json: Optional[Dict[str, List[str]]] = None
    minutos_buffer: Optional[int] = Field(None, ge=0, le=60)
    activo: Optional[bool] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "minutos_buffer": 15,
                "horario_apertura_json": {"lunes": ["08:00-21:00"]},
            }
        }
    )


class SedeResponse(BaseModel):
    """Schema de respuesta de sede"""

    sede_id: str = Field(validation_alias="id", serialization_alias="sede_id")
    nombre: str
    direccion: str
    zona_horaria: str
    horario_apertura_json: Dict[str, List[str]]
    minutos_buffer: int
    created_at: str
    updated_at: str
    activo: bool

    @field_validator("horario_apertura_json", mode="before")
    @classmethod
    def parse_horario(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return {}
        return v

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class SedeListResponse(BaseModel):
    """Schema de respuesta para lista de sedes con paginacion"""

    total: int
    page: int
    page_size: int
    sedes: List[SedeResponse]


class ApiResponse(BaseModel):
    """Schema generico de respuesta API"""

    mensaje: str
    data: Optional[dict | SedeResponse | SedeListResponse] = None
    success: bool

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "mensaje": "Sede creada correctamente",
                "data": {
                    "sede_id": "123e4567-e89b-12d3-a456-426614174000",
                    "nombre": "Complejo Norte",
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
                    "message": "La sede tiene canchas o reservas asociadas",
                    "details": {"canchas": 3, "reservas": 12},
                }
            }
        }
    )


class HorarioValidacionRequest(BaseModel):
    zona_horaria: str
    horario_apertura_json: Dict[str, List[str]]


class HorarioValidacionData(BaseModel):
    zona_horaria: str
    errores: List[Dict[str, str]]


class HorarioValidacionResponse(BaseModel):
    mensaje: str
    data: HorarioValidacionData
    success: bool
