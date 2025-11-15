"""
Modelo de Cancha - SQLAlchemy
Representa las canchas deportivas de cada sede
"""

from sqlalchemy import Column, String, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

# Importar Base desde donde la tienes
from app.domain.user_model import Base


class Cancha(Base):
    """
    Cancha deportiva asociada a una sede
    """
    __tablename__ = "canchas"
    
    # Campos principales
    id = Column(
        String(36),  # UUID como string en SQLite
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
        nullable=False
    )
    
    sede_id = Column(
        String(36),
        ForeignKey('sedes.id', ondelete='RESTRICT'),
        nullable=False,
        index=True,
        comment="ID de la sede a la que pertenece"
    )
    
    nombre = Column(
        String(100),
        nullable=False,
        comment="Nombre de la cancha (único por sede)"
    )
    
    tipo_superficie = Column(
        String(50),
        nullable=False,
        comment="Tipo de superficie: césped, sintético, cemento, madera"
    )
    
    estado = Column(
        String(20),
        nullable=False,
        default="activo",
        comment="Estado: activo, mantenimiento"
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
        comment="1=activo, 0=inactivo"
    )
    
    # Relaciones
    # sede = relationship("Sede", back_populates="canchas")
    # reservas = relationship("Reserva", back_populates="cancha")
    
    # Índices y constraints
    __table_args__ = (
        Index('idx_cancha_sede_id', 'sede_id'),
        Index('idx_cancha_estado', 'estado'),
        Index('idx_cancha_nombre_sede', 'sede_id', 'nombre', unique=True),  # Nombre único por sede
    )
    
    def __repr__(self):
        return f"<Cancha(id={self.id}, nombre='{self.nombre}', sede_id={self.sede_id})>"
    
    def to_dict(self):
        """Convertir a diccionario"""
        return {
            "cancha_id": self.id,
            "sede_id": self.sede_id,
            "nombre": self.nombre,
            "tipo_superficie": self.tipo_superficie,
            "estado": self.estado,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "activo": bool(self.activo)
        }