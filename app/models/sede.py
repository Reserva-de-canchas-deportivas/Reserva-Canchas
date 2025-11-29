"""
Modelo de Sede - SQLAlchemy
Adaptado para SQLite
"""

from sqlalchemy import Column, String, Integer, Text, Index
from datetime import datetime
import uuid
import json

# Importar Base desde donde la tienes
from app.domain.user_model import Base


class Sede(Base):
    """
    Sede deportiva con canchas y configuración de horarios
    """

    __tablename__ = "sedes"

    # Campos principales
    id = Column(
        String(36),  # UUID como string en SQLite
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
        nullable=False,
    )

    nombre = Column(
        String(200),
        nullable=False,
        unique=True,
        index=True,
        comment="Nombre de la sede deportiva",
    )

    direccion = Column(
        String(500), nullable=False, comment="Dirección física de la sede"
    )

    zona_horaria = Column(
        String(50),
        nullable=False,
        default="America/Bogota",
        comment="Zona horaria IANA (ej: America/Bogota)",
    )

    # JSON como TEXT en SQLite
    horario_apertura_json = Column(
        Text,  # En SQLite usamos TEXT para JSON
        nullable=False,
        comment="Horarios de apertura por día de la semana en formato JSON",
    )

    minutos_buffer = Column(
        Integer,
        nullable=False,
        default=10,
        comment="Minutos de buffer entre reservas consecutivas",
    )

    # Auditoría
    created_at = Column(
        String(50), nullable=False, default=lambda: datetime.utcnow().isoformat()
    )

    updated_at = Column(
        String(50),
        nullable=False,
        default=lambda: datetime.utcnow().isoformat(),
        onupdate=lambda: datetime.utcnow().isoformat(),
    )

    activo = Column(Integer, nullable=False, default=1, comment="1=activo, 0=inactivo")

    # Índices
    __table_args__ = (
        Index("idx_sede_nombre", "nombre"),
        Index("idx_sede_zona_horaria", "zona_horaria"),
    )

    def __repr__(self):
        return f"<Sede(id={self.id}, nombre='{self.nombre}')>"

    def to_dict(self):
        """Convertir a diccionario"""
        # Parsear JSON de horarios
        try:
            horarios = json.loads(self.horario_apertura_json)
        except Exception:
            horarios = {}

        return {
            "sede_id": self.id,
            "nombre": self.nombre,
            "direccion": self.direccion,
            "zona_horaria": self.zona_horaria,
            "horario_apertura_json": horarios,
            "minutos_buffer": self.minutos_buffer,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "activo": bool(self.activo),
        }
