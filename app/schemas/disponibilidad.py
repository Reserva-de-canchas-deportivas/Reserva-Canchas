"""
Schemas Pydantic para Consulta de Disponibilidad
Validación de datos de entrada/salida
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import date, datetime
import re


class SlotDisponibilidad(BaseModel):
    """Schema de un slot de tiempo"""
    
    hora_inicio: str = Field(
        ...,
        description="Hora de inicio del slot (HH:MM)"
    )
    
    hora_fin: str = Field(
        ...,
        description="Hora de fin del slot (HH:MM)"
    )
    
    reservable: bool = Field(
        ...,
        description="Indica si el slot está disponible para reservar"
    )
    
    motivo: Optional[str] = Field(
        None,
        description="Motivo por el que no es reservable (si aplica)"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "hora_inicio": "08:00",
                "hora_fin": "09:00",
                "reservable": True,
                "motivo": None
            }
        }
    )


class DisponibilidadResponse(BaseModel):
    """Schema de respuesta de disponibilidad"""
    
    fecha: str = Field(
        ...,
        description="Fecha consultada (YYYY-MM-DD)"
    )
    
    sede_id: str
    cancha_id: str
    
    sede_nombre: Optional[str] = None
    cancha_nombre: Optional[str] = None
    
    zona_horaria: str = Field(
        ...,
        description="Zona horaria de la sede"
    )
    
    horario_apertura: Optional[str] = Field(
        None,
        description="Horario de apertura del día consultado"
    )
    
    minutos_buffer: int = Field(
        ...,
        description="Minutos de buffer entre reservas"
    )
    
    slots: List[SlotDisponibilidad] = Field(
        ...,
        description="Lista de slots de tiempo"
    )
    
    total_slots: int = Field(
        ...,
        description="Total de slots en el día"
    )
    
    slots_disponibles: int = Field(
        ...,
        description="Número de slots disponibles"
    )
    
    slots_ocupados: int = Field(
        ...,
        description="Número de slots ocupados"
    )
    
    dia_cerrado: bool = Field(
        default=False,
        description="Indica si la sede está cerrada ese día"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "fecha": "2025-07-31",
                "sede_id": "abc123...",
                "cancha_id": "xyz789...",
                "sede_nombre": "Complejo Norte",
                "cancha_nombre": "Cancha 1",
                "zona_horaria": "America/Bogota",
                "horario_apertura": "08:00-22:00",
                "minutos_buffer": 10,
                "slots": [
                    {
                        "hora_inicio": "08:00",
                        "hora_fin": "09:00",
                        "reservable": True,
                        "motivo": None
                    }
                ],
                "total_slots": 14,
                "slots_disponibles": 10,
                "slots_ocupados": 4,
                "dia_cerrado": False
            }
        }
    )


class DisponibilidadQuery(BaseModel):
    """Schema para validar parámetros de consulta"""
    
    fecha: str = Field(
        ...,
        description="Fecha a consultar (YYYY-MM-DD)"
    )
    
    sede_id: str = Field(
        ...,
        description="ID de la sede"
    )
    
    cancha_id: str = Field(
        ...,
        description="ID de la cancha"
    )
    
    duracion_slot: int = Field(
        default=60,
        ge=15,
        le=240,
        description="Duración de cada slot en minutos (15-240)"
    )
    
    @field_validator('fecha')
    @classmethod
    def validar_fecha(cls, v: str) -> str:
        """Validar formato de fecha YYYY-MM-DD"""
        try:
            fecha_obj = datetime.strptime(v, "%Y-%m-%d").date()
            
            # Validar que no sea fecha pasada
            hoy = date.today()
            if fecha_obj < hoy:
                raise ValueError(
                    f"La fecha {v} es pasada. "
                    f"Solo se puede consultar disponibilidad desde hoy ({hoy})"
                )
            
            # Validar que no sea muy en el futuro (ej: máximo 90 días)
            from datetime import timedelta
            max_fecha = hoy + timedelta(days=90)
            if fecha_obj > max_fecha:
                raise ValueError(
                    f"La fecha {v} está muy en el futuro. "
                    f"Solo se puede consultar hasta {max_fecha}"
                )
            
            return v
            
        except ValueError as e:
            if "does not match format" in str(e):
                raise ValueError(
                    f"Formato de fecha inválido: '{v}'. "
                    f"Debe ser YYYY-MM-DD"
                )
            raise
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "fecha": "2025-07-31",
                "sede_id": "abc123-...",
                "cancha_id": "xyz789-...",
                "duracion_slot": 60
            }
        }
    )


class ApiResponse(BaseModel):
    """Schema genérico de respuesta API"""
    
    mensaje: str
    data: Optional[DisponibilidadResponse] = None
    success: bool
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "mensaje": "Disponibilidad calculada correctamente",
                "data": {
                    "fecha": "2025-07-31",
                    "slots": []
                },
                "success": True
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
                    "code": "CANCHA_NO_ENCONTRADA",
                    "message": "No se encontró la cancha especificada",
                    "details": {
                        "cancha_id": "xyz789..."
                    }
                }
            }
        }
    )