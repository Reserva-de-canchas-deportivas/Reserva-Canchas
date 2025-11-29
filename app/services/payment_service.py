from typing import Optional

from app.payment_gateway.simulated_gateway import SimulatedGateway
from app.payment_gateway.models import PaymentRequest, GatewayStatus
from app.invoices.invoice_service import InvoiceService
from app.schemas.payment_gateway import PaymentProcessingRequest, PaymentProcessingResponse


class PaymentProcessingService:
    """Servicio de pasarela simulada para procesamiento de pagos y emisión de factura."""

    def __init__(
        self,
        gateway: Optional[SimulatedGateway] = None,
        invoice_service: Optional[InvoiceService] = None,
        pago_service=None,
    ):
        self.gateway = gateway or SimulatedGateway()
        self.invoice_service = invoice_service or InvoiceService()
        self.pago_service = pago_service  # opcional para pruebas/unit tests

    async def process_payment(self, payment_request: PaymentProcessingRequest) -> PaymentProcessingResponse:
        payment_model = PaymentRequest(
            pago_id=payment_request.pago_id,
            card_number=payment_request.card_number,
            card_holder=payment_request.card_holder,
            expiry_date=payment_request.expiry_date,
            cvv=payment_request.cvv,
            amount=payment_request.amount,
            currency=payment_request.currency,
            description=payment_request.description,
            customer_email=payment_request.customer_email,
        )

        gateway_resp = self.gateway.process_payment(payment_model)

        if gateway_resp.status != GatewayStatus.APPROVED:
            return PaymentProcessingResponse(
                success=False,
                message=gateway_resp.message,
                transaction_id=gateway_resp.transaction_id,
                invoice_html="",
                invoice_number="",
                timestamp=gateway_resp.timestamp,
            )

        invoice_data = self.invoice_service.generate_invoice(
            payment_data={
                "transaction_id": gateway_resp.transaction_id,
                "amount": payment_request.amount,
                "currency": payment_request.currency,
                "description": payment_request.description,
            },
            customer_data={
                "name": payment_request.card_holder,
                "email": payment_request.customer_email,
            },
        )
        invoice_html = self.invoice_service.generate_invoice_html(invoice_data)

        return PaymentProcessingResponse(
            success=True,
            message="Pago aprobado exitosamente",
            transaction_id=gateway_resp.transaction_id,
            invoice_html=invoice_html,
            invoice_number=invoice_data.invoice_number,
            timestamp=gateway_resp.timestamp,
        )
