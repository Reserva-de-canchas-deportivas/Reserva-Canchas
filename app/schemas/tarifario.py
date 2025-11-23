"""
Schemas Pydantic para Tarifario
Validación de datos de entrada/salida con validaciones complejas
"""

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import Optional, List, Literal
from decimal import Decimal
import re


class TarifarioCreate(BaseModel):
    """Schema para crear una tarifa"""

    sede_id: str = Field(..., description="ID de la sede (obligatorio)")

    cancha_id: Optional[str] = Field(
        None, description="ID de la cancha (opcional - null = tarifa general de sede)"
    )

    dia_semana: int = Field(
        ...,
        ge=0,
        le=6,
        description="Día de la semana: 0=Lunes, 1=Martes, ..., 6=Domingo",
    )

    hora_inicio: str = Field(..., description="Hora de inicio en formato HH:MM (24h)")

    hora_fin: str = Field(..., description="Hora de fin en formato HH:MM (24h)")

    precio_por_bloque: Decimal = Field(
        ..., gt=0, description="Precio por bloque de tiempo (debe ser positivo)"
    )

    moneda: str = Field(
        default="COP", description="Código de moneda ISO 4217 (3 letras mayúsculas)"
    )

    @field_validator("hora_inicio", "hora_fin")
    @classmethod
    def validar_formato_hora(cls, v: str) -> str:
        """Validar formato HH:MM"""
        patron = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
        if not patron.match(v):
            raise ValueError(
                f"Formato de hora inválido: '{v}'. "
                f"Debe ser HH:MM en formato 24h (ej: 08:00, 18:30)"
            )
        return v

    @field_validator("moneda")
    @classmethod
    def validar_moneda(cls, v: str) -> str:
        """Validar código de moneda ISO 4217"""
        patron = re.compile(r"^[A-Z]{3}$")
        if not patron.match(v):
            raise ValueError(
                f"Código de moneda inválido: '{v}'. "
                f"Debe ser un código ISO de 3 letras mayúsculas (ej: COP, USD, EUR)"
            )
        return v

    @model_validator(mode="after")
    def validar_rango_horario(self):
        """Validar que hora_inicio < hora_fin"""
        if self.hora_inicio >= self.hora_fin:
            raise ValueError(
                f"La hora de inicio ({self.hora_inicio}) debe ser menor "
                f"que la hora de fin ({self.hora_fin})"
            )
        return self

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sede_id": "abc123-...",
                "cancha_id": None,
                "dia_semana": 2,
                "hora_inicio": "18:00",
                "hora_fin": "20:00",
                "precio_por_bloque": 120000,
                "moneda": "COP",
            }
        }
    )


class TarifarioUpdate(BaseModel):
    """Schema para actualizar una tarifa (campos opcionales)"""

    dia_semana: Optional[int] = Field(None, ge=0, le=6)

    hora_inicio: Optional[str] = None
    hora_fin: Optional[str] = None
    precio_por_bloque: Optional[Decimal] = Field(None, gt=0)
    moneda: Optional[str] = None
    activo: Optional[bool] = None

    # Reutilizar validadores de TarifarioCreate
    _validar_hora_inicio = field_validator("hora_inicio")(
        TarifarioCreate.validar_formato_hora.__func__
    )
    _validar_hora_fin = field_validator("hora_fin")(
        TarifarioCreate.validar_formato_hora.__func__
    )
    _validar_moneda = field_validator("moneda")(TarifarioCreate.validar_moneda.__func__)

    model_config = ConfigDict(
        json_schema_extra={"example": {"precio_por_bloque": 150000, "moneda": "COP"}}
    )


class TarifarioResponse(BaseModel):
    """Schema de respuesta de tarifa"""

    tarifa_id: str = Field(
        validation_alias="id",
        serialization_alias="tarifa_id",
        description="Identificador único de la tarifa",
    )
    sede_id: str
    cancha_id: Optional[str]
    dia_semana: int
    hora_inicio: str
    hora_fin: str
    precio_por_bloque: float
    moneda: str
    created_at: str
    updated_at: str
    activo: bool

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class TarifarioListResponse(BaseModel):
    """Schema de respuesta para lista de tarifas"""

    total: int
    tarifas: List[TarifarioResponse]


class ApiResponse(BaseModel):
    """Schema genérico de respuesta API"""

    mensaje: str
    data: Optional[dict | TarifarioResponse | TarifarioListResponse] = None
    success: bool

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "mensaje": "Tarifa creada correctamente",
                "data": {
                    "tarifa_id": "123e4567-...",
                    "sede_id": "abc123-...",
                    "cancha_id": None,
                    "dia_semana": 2,
                    "hora_inicio": "18:00",
                    "hora_fin": "20:00",
                    "precio_por_bloque": 120000.00,
                    "moneda": "COP",
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
                    "code": "FRANJA_SOLAPADA",
                    "message": "Existe una tarifa que se cruza en la misma especificidad",
                    "details": {"tarifa_existente": "uuid123..."},
                }
            }
        }
    )


class TarifaResolverData(BaseModel):
    origen: Literal["cancha", "sede"]
    tarifa_id: str
    moneda: str
    precio_por_bloque: float


class TarifaResolverResponse(BaseModel):
    mensaje: str
    data: TarifaResolverData
    success: bool = True
