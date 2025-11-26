from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from app.database import Base
import uuid

class ReservaHistorial(Base):
    __tablename__ = "reserva_historial"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    reserva_id = Column(String(36), ForeignKey("reservas.id"), nullable=False)
    estado_anterior = Column(String(20), nullable=False)
    estado_nuevo = Column(String(20), nullable=False)
    usuario_id = Column(String(36), nullable=False)
    fecha = Column(DateTime(timezone=True), server_default=func.now())
    comentario = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<ReservaHistorial {self.estado_anterior} -> {self.estado_nuevo}>"