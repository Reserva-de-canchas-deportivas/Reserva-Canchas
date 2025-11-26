from enum import Enum
from typing import Set, Dict
from pydantic import BaseModel

class EstadoReserva(str, Enum):
    HOLD = "hold"
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    EXPIRADA = "expirada"

class TransicionInvalidaError(Exception):
    def __init__(self, estado_actual: EstadoReserva, estado_nuevo: EstadoReserva):
        super().__init__(f"TRANSICION_INVALIDA: {estado_actual} → {estado_nuevo}")

class ReservaFSM:
    TRANSICIONES_VALIDAS: Dict[EstadoReserva, Set[EstadoReserva]] = {
        EstadoReserva.HOLD: {EstadoReserva.PENDING, EstadoReserva.EXPIRADA},
        EstadoReserva.PENDING: {EstadoReserva.CONFIRMED},
        EstadoReserva.CONFIRMED: {EstadoReserva.CANCELLED, EstadoReserva.NO_SHOW},
        EstadoReserva.CANCELLED: set(),
        EstadoReserva.NO_SHOW: set(),
        EstadoReserva.EXPIRADA: set()
    }
    
    @classmethod
    def validar_transicion(cls, estado_actual: EstadoReserva, estado_nuevo: EstadoReserva) -> bool:
        return estado_nuevo in cls.TRANSICIONES_VALIDAS.get(estado_actual, set())
    
    @classmethod
    def transicionar(cls, estado_actual: EstadoReserva, estado_nuevo: EstadoReserva) -> EstadoReserva:
        """Realiza la transición de estado si es válida"""
        if not cls.validar_transicion(estado_actual, estado_nuevo):
            raise TransicionInvalidaError(estado_actual, estado_nuevo)
        return estado_nuevo

class TransicionRequest(BaseModel):
    estado_nuevo: EstadoReserva
    usuario_id: str

class TransicionResponse(BaseModel):
    mensaje: str
    data: dict
    success: bool