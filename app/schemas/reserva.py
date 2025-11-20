from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator


class ReservaHoldRequest(BaseModel):
    sede_id: str
    cancha_id: str
    fecha: date
    hora_inicio: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    hora_fin: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    clave_idempotencia: str = Field(..., min_length=6, max_length=120)

    @field_validator("hora_fin")
    @classmethod
    def validar_horas(cls, v: str, info: ValidationInfo) -> str:
        inicio = info.data.get("hora_inicio")
        if inicio and v <= inicio:
            raise ValueError("hora_fin debe ser mayor que hora_inicio")
        return v


class ReservaHoldData(BaseModel):
    reserva_id: str
    estado: str
    sede_id: str
    cancha_id: str
    inicio: str
    fin: str
    vence_hold: str
    total: float
    moneda: str

    model_config = ConfigDict(from_attributes=True)


class ReservaApiResponse(BaseModel):
    mensaje: str
    data: ReservaHoldData | None
    success: bool
