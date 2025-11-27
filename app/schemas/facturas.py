from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional
from enum import Enum

class EstadoFactura(str, Enum):
    PENDIENTE = "pendiente"
    EMITIDA = "emitida"
    ERROR = "error"
    PENDIENTE_REINTENTO = "pending_retry"

class FacturaCreate(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    reserva_id: UUID
    pago_id: UUID
    serie: str = "FCT"

class FacturaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    factura_id: UUID
    reserva_id: UUID
    pago_id: UUID
    serie: str
    numero: int
    total: float
    moneda: str
    estado: EstadoFactura
    url_pdf: Optional[str]
    url_xml: Optional[str]
    fecha_emision: datetime

class FacturaEmitidaResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "mensaje": "Factura emitida correctamente",
                "data": {
                    "factura_id": "uuid",
                    "reserva_id": "uuid",
                    "serie": "FCT",
                    "numero": 1023,
                    "total": 150000,
                    "moneda": "COP",
                    "url_pdf": "https://cdn.example.com/facturas/FCT-1023.pdf",
                    "url_xml": "https://cdn.example.com/facturas/FCT-1023.xml"
                },
                "success": True
            }
        }
    )
    
    mensaje: str
    data: dict
    success: bool