from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ReservaHistorialBase(BaseModel):
    estado_anterior: str
    estado_nuevo: str
    usuario_id: str
    comentario: Optional[str] = None

class ReservaHistorialCreate(ReservaHistorialBase):
    pass

class ReservaHistorialResponse(ReservaHistorialBase):
    id: str
    reserva_id: str
    fecha: datetime
    
    class Config:
        from_attributes = True