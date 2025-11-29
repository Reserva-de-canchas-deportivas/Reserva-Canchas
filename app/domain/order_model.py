from enum import Enum
from datetime import datetime
from uuid import uuid4


class EstadoReserva(str, Enum):
    HOLD = "hold"
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    EXPIRADA = "expirada"

class Reserva:
    def __init__(self, cancha_id: str, usuario_id: str, fecha_reserva: datetime, estado: EstadoReserva = EstadoReserva.HOLD):
        self.id = str(uuid4())
        self.cancha_id = cancha_id
        self.usuario_id = usuario_id
        self.fecha_reserva = fecha_reserva
        self.estado = estado
        self.fecha_creacion = datetime.now()
        self.fecha_actualizacion = datetime.now()

class ReservaHistorial:
    def __init__(self, reserva_id: str, estado_anterior: EstadoReserva, estado_nuevo: EstadoReserva, usuario_id: str):
        self.id = str(uuid4())
        self.reserva_id = reserva_id
        self.estado_anterior = estado_anterior
        self.estado_nuevo = estado_nuevo
        self.usuario_id = usuario_id
        self.fecha = datetime.now()
