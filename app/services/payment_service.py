from app.payment_gateway.simulated_gateway import SimulatedGateway
from app.invoices.invoice_service import InvoiceService
from app.schemas.payment_gateway import PaymentProcessingResponse
from datetime import datetime

class PaymentService:
    def __init__(self):
        self.gateway = SimulatedGateway()
        self.invoice_service = InvoiceService()
    
    def process_payment(self, pago_id: str, monto: float, moneda: str = "COP") -> PaymentProcessingResponse:
        # 1) Simular llamada al gateway
        gateway_resp = self.gateway.process_payment(pago_id=pago_id, amount=monto, currency=moneda)
        if gateway_resp.status != "approved":
            return PaymentProcessingResponse(
                pago_id=pago_id,
                status=gateway_resp.status,
                transaction_id=gateway_resp.transaction_id,
                approval_code=gateway_resp.approval_code,
                message=gateway_resp.message,
                timestamp=datetime.utcnow(),
            )
        # 2) Si aprobado, emitir factura
        factura = self.invoice_service.emitir_factura_para_pago(pago_id)
        return PaymentProcessingResponse(
            pago_id=pago_id,
            status=gateway_resp.status,
            transaction_id=gateway_resp.transaction_id,
            approval_code=gateway_resp.approval_code,
            message=gateway_resp.message,
            timestamp=datetime.utcnow(),
            factura_id=factura.id if factura else None,
        )
