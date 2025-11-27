from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from app.database import Base
import enum

class EstadoFactura(str, enum.Enum):
    PENDIENTE = "pendiente"
    EMITIDA = "emitida"
    ERROR = "error"
    PENDIENTE_REINTENTO = "pending_retry"

class Factura(Base):
    __tablename__ = "facturas"

    id = Column(String(36), primary_key=True, index=True)
    reserva_id = Column(String(36), ForeignKey("reservas.id"), nullable=False, index=True)
    pago_id = Column(String(36), ForeignKey("pagos.id"), nullable=False, index=True)
    
    # Datos fiscales
    serie = Column(String(10), nullable=False)
    numero = Column(Integer, nullable=False)
    total = Column(Float, nullable=False)
    moneda = Column(String(3), default="COP")
    
    # Estado y URLs
    estado = Column(SQLEnum(EstadoFactura), default=EstadoFactura.PENDIENTE)
    url_pdf = Column(String(500), nullable=True)
    url_xml = Column(String(500), nullable=True)
    
    # Auditoría
    fecha_emision = Column(DateTime(timezone=True), server_default=func.now())
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Factura {self.serie}-{self.numero:06d}>"