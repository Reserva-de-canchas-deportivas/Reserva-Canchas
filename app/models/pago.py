from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

import uuid

class EstadoPago(str):
    INICIADO = "iniciado"
    AUTORIZADO = "autorizado" 
    CAPTURADO = "capturado"
    FALLIDO = "fallido"
    REEMBOLSADO = "reembolsado"

class Pago(Base):
    __tablename__ = "pagos"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    reserva_id = Column(String(36), ForeignKey("reservas.id"), nullable=False, unique=True)
    monto = Column(Numeric(12, 2), nullable=False)
    moneda = Column(String(3), nullable=False, default="COP")
    proveedor = Column(String(50), nullable=False)  # stripe, paypal, etc.
    referencia_proveedor = Column(String(100), nullable=True)
    estado = Column(String(20), nullable=False, default=EstadoPago.INICIADO)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relación (opcional)
    # reserva = relationship("Reserva", back_populates="pago")
    
    __table_args__ = (
        CheckConstraint(
            estado.in_([
                EstadoPago.INICIADO,
                EstadoPago.AUTORIZADO, 
                EstadoPago.CAPTURADO,
                EstadoPago.FALLIDO,
                EstadoPago.REEMBOLSADO
            ]),
            name="check_estado_pago_valido"
        ),
        CheckConstraint(monto > 0, name="check_monto_positivo"),
    )
    
    def __repr__(self):
        return f"<Pago {self.id} - {self.estado} (Reserva: {self.reserva_id})>"