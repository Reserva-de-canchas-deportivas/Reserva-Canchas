from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.domain.order_model import EstadoReserva

class TransicionRequest(BaseModel):
    estado_nuevo: EstadoReserva
    usuario_id: str  # Usuario que realiza el cambio

class TransicionResponse(BaseModel):
    mensaje: str
    data: dict
    success: bool

class HistorialItem(BaseModel):
    id: str
    reserva_id: str
    estado_anterior: EstadoReserva
    estado_nuevo: EstadoReserva
    usuario_id: str
    fecha: datetime

class HistorialResponse(BaseModel):
    items: list[HistorialItem]
    total: int