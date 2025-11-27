from enum import Enum
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

class GatewayStatus(str, Enum):
    APPROVED = "approved"
    DECLINED = "declined"
    PENDING = "pending"

class PaymentRequest(BaseModel):
    pago_id: UUID
    card_number: str
    card_holder: str
    expiry_date: str  # "MM/YY"
    cvv: str
    amount: float
    currency: str = "COP"
    description: str = "Reserva de cancha"
    customer_email: str

class PaymentResponse(BaseModel):
    transaction_id: str
    status: GatewayStatus
    approval_code: str
    message: str
    timestamp: datetime