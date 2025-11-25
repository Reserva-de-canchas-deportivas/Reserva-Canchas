from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class WebhookPayload(BaseModel):
    """Esquema para el payload del webhook"""
    event_type: str = Field(..., description="Tipo de evento: payment_intent.succeeded, payment_failed, etc.")
    provider_ref: str = Field(..., description="ID único del proveedor para idempotencia")
    payment_id: Optional[str] = Field(None, description="ID del pago si existe")
    order_id: str = Field(..., description="ID de la orden/reserva")
    amount: float = Field(..., description="Monto del pago")
    currency: str = Field("USD", description="Moneda")
    status: str = Field(..., description="Estado del pago")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadatos adicionales")
    timestamp: Optional[datetime] = Field(None, description="Timestamp del evento")

class WebhookResponse(BaseModel):
    """Esquema para la respuesta del webhook"""
    mensaje: str = Field(..., description="Mensaje de respuesta")
    data: Optional[Dict[str, Any]] = Field(None, description="Datos adicionales")
    success: bool = Field(..., description="Indica si fue exitoso")

class PaymentResponse(BaseModel):
    """Esquema para respuesta de pago"""
    id: str
    provider_ref: str
    order_id: str
    amount: str
    currency: str
    status: str
    payment_method: Optional[str]
    created_at: str
    updated_at: str