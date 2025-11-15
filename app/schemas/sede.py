"""
Schemas Pydantic para Sede
Validación de datos de entrada/salida
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, Dict, List
from datetime import datetime
import re
import pytz


class SedeCreate(BaseModel):
    """Schema para crear una sede"""
    
    nombre: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Nombre de la sede"
    )
    
    direccion: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Dirección física de la sede"
    )
    
    zona_horaria: str = Field(
        default="America/Bogota",
        description="Zona horaria IANA"
    )
    
    horario_apertura_json: Dict[str, List[str]] = Field(
        ...,
        description="Horarios de apertura por día. Formato: {'lunes': ['08:00-20:00']}"
    )
    
    minutos_buffer: int = Field(
        default=10,
        ge=0,
        le=60,
        description="Minutos de buffer entre reservas (0-60)"
    )
    
    @field_validator('zona_horaria')
    @classmethod
    def validar_zona_horaria(cls, v: str) -> str:
        """Validar que la zona horaria sea válida según IANA"""
        try:
            pytz.timezone(v)
            return v
        except pytz.exceptions.UnknownTimeZoneError:
            raise ValueError(
                f"Zona horaria inválida: '{v}'. "
                f"Debe ser una zona IANA válida (ej: America/Bogota)"
            )
    
    @field_validator('horario_apertura_json')
    @classmethod
    def validar_horario_apertura(cls, v: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Validar formato de horarios de apertura"""
        dias_validos = [
            'lunes', 'martes', 'miercoles', 'jueves',
            'viernes', 'sabado', 'domingo'
        ]
        
        # Validar que las claves sean días válidos
        for dia in v.keys():
            if dia.lower() not in dias_validos:
                raise ValueError(
                    f"Día inválido: '{dia}'. "
                    f"Días válidos: {', '.join(dias_validos)}"
                )
        
        # Validar formato de horarios HH:MM-HH:MM
        patron_hora = re.compile(r'^([0-1][0-9]|2[0-3]):[0-5][0-9]-([0-1][0-9]|2[0-3]):[0-5][0-9]$')
        
        for dia, horarios in v.items():
            if not isinstance(horarios, list):
                raise ValueError(f"Los horarios de '{dia}' deben ser una lista")
            
            for horario in horarios:
                if not patron_hora.match(horario):
                    raise ValueError(
                        f"Formato de horario inválido en '{dia}': '{horario}'. "
                        f"Formato esperado: HH:MM-HH:MM (ej: 08:00-20:00)"
                    )
                
                # Validar que hora_inicio < hora_fin
                inicio, fin = horario.split('-')
                if inicio >= fin:
                    raise ValueError(
                        f"En '{dia}', la hora de inicio ({inicio}) "
                        f"debe ser menor que la hora de fin ({fin})"
                    )
        
        return v
    
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
                    "domingo": ["09:00-18:00"]
                },
                "minutos_buffer": 10
            }
        }
    )


class SedeUpdate(BaseModel):
    """Schema para actualizar una sede (campos opcionales)"""
    
    nombre: Optional[str] = Field(
        None,
        min_length=3,
        max_length=200
    )
    
    direccion: Optional[str] = Field(
        None,
        min_length=10,
        max_length=500
    )
    
    zona_horaria: Optional[str] = None
    
    horario_apertura_json: Optional[Dict[str, List[str]]] = None
    
    minutos_buffer: Optional[int] = Field(
        None,
        ge=0,
        le=60
    )
    
    activo: Optional[bool] = None
    
    # Validadores (reutilizar los de SedeCreate)
    _validar_zona_horaria = field_validator('zona_horaria')(
        SedeCreate.validar_zona_horaria.__func__
    )
    
    _validar_horario = field_validator('horario_apertura_json')(
        SedeCreate.validar_horario_apertura.__func__
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "minutos_buffer": 15,
                "horario_apertura_json": {
                    "lunes": ["08:00-21:00"]
                }
            }
        }
    )


class SedeResponse(BaseModel):
    """Schema de respuesta de sede"""
    
    sede_id: str
    nombre: str
    direccion: str
    zona_horaria: str
    horario_apertura_json: Dict[str, List[str]]
    minutos_buffer: int
    created_at: str
    updated_at: str
    activo: bool
    
    model_config = ConfigDict(from_attributes=True)


class SedeListResponse(BaseModel):
    """Schema de respuesta para lista de sedes con paginación"""
    
    total: int
    page: int
    page_size: int
    sedes: List[SedeResponse]


class ApiResponse(BaseModel):
    """Schema genérico de respuesta API"""
    
    mensaje: str
    data: Optional[dict | SedeResponse | SedeListResponse] = None
    success: bool
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "mensaje": "Sede creada correctamente",
                "data": {
                    "sede_id": "123e4567-e89b-12d3-a456-426614174000",
                    "nombre": "Complejo Norte"
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
                    "code": "CONFLICTO_RELACIONAL",
                    "message": "La sede tiene canchas o reservas asociadas",
                    "details": {
                        "canchas": 3,
                        "reservas": 12
                    }
                }
            }
        }
    )