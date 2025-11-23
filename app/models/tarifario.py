"""
Modelo de Tarifario - SQLAlchemy
Representa las tarifas por franjas horarias para sedes y canchas
"""

from sqlalchemy import Column, String, Integer, ForeignKey, Index, Numeric
from datetime import datetime
import uuid

# Importar Base desde donde la tienes
from app.domain.user_model import Base


class Tarifario(Base):
    """
    Tarifario con franjas horarias y prioridad cancha > sede
    """

    __tablename__ = "tarifario"

    # Campos principales
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
        nullable=False,
    )

    sede_id = Column(
        String(36),
        ForeignKey("sedes.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="ID de la sede (obligatorio)",
    )

    cancha_id = Column(
        String(36),
        ForeignKey("canchas.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
        comment="ID de la cancha (opcional - null = tarifa general de sede)",
    )

    dia_semana = Column(
        Integer,
        nullable=False,
        comment="Día de la semana: 0=Lunes, 1=Martes, ..., 6=Domingo",
    )

    hora_inicio = Column(
        String(5), nullable=False, comment="Hora de inicio de la franja (HH:MM)"
    )

    hora_fin = Column(
        String(5), nullable=False, comment="Hora de fin de la franja (HH:MM)"
    )

    precio_por_bloque = Column(
        Numeric(10, 2), nullable=False, comment="Precio por bloque de tiempo"
    )

    moneda = Column(
        String(3),
        nullable=False,
        default="COP",
        comment="Código de moneda ISO 4217 (3 letras)",
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

    # Relaciones
    # sede = relationship("Sede", back_populates="tarifas")
    # cancha = relationship("Cancha", back_populates="tarifas")

    # Índices para optimizar consultas y validaciones
    __table_args__ = (
        Index("idx_tarifario_sede_dia", "sede_id", "dia_semana"),
        Index("idx_tarifario_cancha_dia", "cancha_id", "dia_semana"),
        Index(
            "idx_tarifario_sede_dia_hora",
            "sede_id",
            "dia_semana",
            "hora_inicio",
            "hora_fin",
        ),
        Index(
            "idx_tarifario_cancha_dia_hora",
            "cancha_id",
            "dia_semana",
            "hora_inicio",
            "hora_fin",
        ),
    )

    def __repr__(self):
        nivel = f"Cancha {self.cancha_id}" if self.cancha_id else f"Sede {self.sede_id}"
        return f"<Tarifario({nivel}, Día {self.dia_semana}, {self.hora_inicio}-{self.hora_fin})>"

    def to_dict(self):
        """Convertir a diccionario"""
        return {
            "tarifa_id": self.id,
            "sede_id": self.sede_id,
            "cancha_id": self.cancha_id,
            "dia_semana": self.dia_semana,
            "hora_inicio": self.hora_inicio,
            "hora_fin": self.hora_fin,
            "precio_por_bloque": float(self.precio_por_bloque),
            "moneda": self.moneda,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "activo": bool(self.activo),
        }

    def es_tarifa_especifica(self) -> bool:
        """Verifica si es una tarifa específica de cancha"""
        return self.cancha_id is not None

    def es_tarifa_general(self) -> bool:
        """Verifica si es una tarifa general de sede"""
        return self.cancha_id is None
