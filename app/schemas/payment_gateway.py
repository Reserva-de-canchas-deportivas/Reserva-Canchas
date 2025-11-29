from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class PaymentProcessingRequest(BaseModel):
    pago_id: UUID
    card_number: str
    card_holder: str
    expiry_date: str
    cvv: str
    customer_email: str
    amount: float
    description: str = "Reserva de cancha deportiva"
    currency: str = "COP"

class PaymentProcessingResponse(BaseModel):
    success: bool
    message: str
    transaction_id: str
    invoice_html: str
    invoice_number: str
    timestamp: datetime

class InvoiceResponse(BaseModel):
    invoice_number: str
    transaction_id: str
    customer_name: str
    amount: float
    currency: str
    issue_date: datetime