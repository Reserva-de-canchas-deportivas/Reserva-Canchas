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


class ReservaConfirmRequest(BaseModel):
    clave_idempotencia: str | None = None


class ReservaConfirmData(BaseModel):
    reserva_id: str
    estado: str
    total: float
    moneda: str


class ReservaConfirmResponse(BaseModel):
    mensaje: str
    data: ReservaConfirmData
    success: bool = True


class ReservaCancelRequest(BaseModel):
    motivo: str
    clave_idempotencia: str | None = None


class ReservaCancelData(BaseModel):
    reserva_id: str
    estado: str
    reembolso: dict


class ReservaCancelResponse(BaseModel):
    mensaje: str
    data: ReservaCancelData
    success: bool = True


class ReservaReprogramarRequest(BaseModel):
    fecha: date
    hora_inicio: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    hora_fin: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    cancha_id: str | None = None

    @field_validator("hora_fin")
    @classmethod
    def validar_horas(cls, v: str, info: ValidationInfo) -> str:
        inicio = info.data.get("hora_inicio")
        if inicio and v <= inicio:
            raise ValueError("hora_fin debe ser mayor que hora_inicio")
        return v


class DiferenciaPrecio(BaseModel):
    monto: float
    moneda: str
    tipo: str


class ReservaReprogramarData(BaseModel):
    reserva_original: str
    reserva_nueva: str
    diferencia: DiferenciaPrecio


class ReservaReprogramarResponse(BaseModel):
    mensaje: str
    data: ReservaReprogramarData
    success: bool = True
