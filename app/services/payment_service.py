from datetime import datetime

from app.payment_gateway.simulated_gateway import SimulatedGateway
from app.invoices.invoice_service import InvoiceService
from app.schemas.payment_gateway import PaymentProcessingRequest, PaymentProcessingResponse


class PaymentProcessingService:
    """Servicio de pasarela simulada para procesamiento de pagos y emisión de factura."""

    def __init__(self):
        self.gateway = SimulatedGateway()
        self.invoice_service = InvoiceService()

    async def process_payment(self, payment_request: PaymentProcessingRequest) -> PaymentProcessingResponse:
        # Simular llamada al gateway (sin I/O real, por eso no se espera nada)
        gateway_resp = self.gateway.process_payment(
            pago_id=str(payment_request.pago_id),
            amount=payment_request.amount,
            currency=payment_request.currency,
        )

        # Si el gateway no aprueba, retornamos sin factura
        if gateway_resp.status != "approved":
            return PaymentProcessingResponse(
                pago_id=payment_request.pago_id,
                status=gateway_resp.status,
                transaction_id=gateway_resp.transaction_id,
                approval_code=gateway_resp.approval_code,
                message=gateway_resp.message,
                timestamp=datetime.utcnow(),
            )

        # Si aprueba, intentamos emitir factura (puede ser None si falla)
        factura = self.invoice_service.emitir_factura_para_pago(str(payment_request.pago_id))

        return PaymentProcessingResponse(
            pago_id=payment_request.pago_id,
            status=gateway_resp.status,
            transaction_id=gateway_resp.transaction_id,
            approval_code=gateway_resp.approval_code,
            message=gateway_resp.message,
            timestamp=datetime.utcnow(),
            factura_id=factura.id if factura else None,
        )
