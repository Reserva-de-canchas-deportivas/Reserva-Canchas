"""
Modelo de Reserva - SQLAlchemy
Modelo básico para soportar consulta de disponibilidad
"""

from sqlalchemy import Column, String, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

# Importar Base desde donde la tienes
from app.domain.user_model import Base


class Reserva(Base):
    """
    Reserva de cancha (modelo básico para disponibilidad)
    """
    __tablename__ = "reservas"
    
    # Campos principales
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
        nullable=False
    )
    
    cancha_id = Column(
        String(36),
        ForeignKey('canchas.id', ondelete='RESTRICT'),
        nullable=False,
        index=True,
        comment="ID de la cancha reservada"
    )
    
    fecha = Column(
        String(10),
        nullable=False,
        comment="Fecha de la reserva (YYYY-MM-DD)"
    )
    
    hora_inicio = Column(
        String(5),
        nullable=False,
        comment="Hora de inicio (HH:MM)"
    )
    
    hora_fin = Column(
        String(5),
        nullable=False,
        comment="Hora de fin (HH:MM)"
    )
    
    estado = Column(
        String(20),
        nullable=False,
        default="pending",
        comment="Estado: hold, pending, confirmed, cancelled, completed"
    )
    
    # Información adicional (básica)
    cliente_nombre = Column(
        String(200),
        nullable=True,
        comment="Nombre del cliente (opcional por ahora)"
    )
    
    cliente_email = Column(
        String(200),
        nullable=True,
        comment="Email del cliente (opcional por ahora)"
    )
    
    # Auditoría
    created_at = Column(
        String(50),
        nullable=False,
        default=lambda: datetime.utcnow().isoformat()
    )
    
    updated_at = Column(
        String(50),
        nullable=False,
        default=lambda: datetime.utcnow().isoformat(),
        onupdate=lambda: datetime.utcnow().isoformat()
    )
    
    activo = Column(
        Integer,
        nullable=False,
        default=1,
        comment="1=activo, 0=cancelado/eliminado"
    )
    
    # Relaciones
    # cancha = relationship("Cancha", back_populates="reservas")
    
    # Índices para optimizar consultas de disponibilidad
    __table_args__ = (
        Index('idx_reserva_cancha_fecha', 'cancha_id', 'fecha'),
        Index('idx_reserva_fecha_estado', 'fecha', 'estado'),
        Index('idx_reserva_cancha_fecha_hora', 'cancha_id', 'fecha', 'hora_inicio', 'hora_fin'),
    )
    
    def __repr__(self):
        return f"<Reserva(cancha={self.cancha_id}, fecha={self.fecha}, {self.hora_inicio}-{self.hora_fin})>"
    
    def to_dict(self):
        """Convertir a diccionario"""
        return {
            "reserva_id": self.id,
            "cancha_id": self.cancha_id,
            "fecha": self.fecha,
            "hora_inicio": self.hora_inicio,
            "hora_fin": self.hora_fin,
            "estado": self.estado,
            "cliente_nombre": self.cliente_nombre,
            "cliente_email": self.cliente_email,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "activo": bool(self.activo)
        }
    
    def esta_activa(self) -> bool:
        """Verifica si la reserva está en un estado activo"""
        return self.estado in ['hold', 'pending', 'confirmed'] and self.activo == 1