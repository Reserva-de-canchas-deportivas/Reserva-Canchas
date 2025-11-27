from app.payment_gateway.simulated_gateway import SimulatedGateway
from app.invoices.invoice_service import InvoiceService, InvoiceData
from app.schemas.payment_gateway import PaymentProcessingResponse
from datetime import datetime

class PaymentProcessingService:
    """
    Servicio de dominio para orquestar el procesamiento de pagos
    Coordina: Gateway + Facturación + Actualización de estado
    """
    
    def __init__(self, pago_service=None):  # 🆕 Hacer el parámetro opcional
        self.gateway = SimulatedGateway()
        self.invoice_service = InvoiceService()
        self.pago_service = pago_service  # 🆕 Puede ser None para pruebas
    
    async def process_payment(self, payment_data) -> PaymentProcessingResponse:
        """
        Procesa pago completo: gateway + facturación
        """
        try:
            # 🆕 Solo validar pago si el servicio está disponible
            if self.pago_service:
                pago = await self.pago_service.obtener_pago_por_id(payment_data.pago_id)
                if not pago:
                    return PaymentProcessingResponse(
                        success=False,
                        message="Pago no encontrado",
                        transaction_id="",
                        invoice_html="",
                        invoice_number="",
                        timestamp=datetime.now()
                    )
                
                if pago.estado in ["capturado", "completado"]:
                    return PaymentProcessingResponse(
                        success=False,
                        message="El pago ya fue procesado anteriormente",
                        transaction_id="",
                        invoice_html="",
                        invoice_number="",
                        timestamp=datetime.now()
                    )
            
            # Procesar con gateway simulado
            gateway_response = self.gateway.process_payment(payment_data)
            
            if gateway_response.status.value == "approved":
                # 🆕 Actualizar estado solo si el servicio está disponible
                if self.pago_service:
                    await self.pago_service.actualizar_estado_pago(
                        pago_id=payment_data.pago_id,
                        nuevo_estado="capturado",
                        metadata={
                            "transaction_id": gateway_response.transaction_id,
                            "approval_code": gateway_response.approval_code
                        }
                    )
                
                # Generar factura
                invoice = self.invoice_service.generate_invoice(
                    {
                        "transaction_id": gateway_response.transaction_id,
                        "amount": payment_data.amount,
                        "description": payment_data.description,
                        "currency": payment_data.currency
                    },
                    {
                        "name": payment_data.card_holder,
                        "email": payment_data.customer_email
                    }
                )
                
                invoice_html = self.invoice_service.generate_invoice_html(invoice)
                
                return PaymentProcessingResponse(
                    success=True,
                    message=gateway_response.message,
                    transaction_id=gateway_response.transaction_id,
                    invoice_html=invoice_html,
                    invoice_number=invoice.invoice_number,
                    timestamp=datetime.now()
                )
            else:
                # 🆕 Actualizar estado a fallido solo si el servicio está disponible
                if self.pago_service:
                    await self.pago_service.actualizar_estado_pago(
                        pago_id=payment_data.pago_id,
                        nuevo_estado="fallido",
                        metadata={
                            "transaction_id": gateway_response.transaction_id,
                            "reason": gateway_response.message
                        }
                    )
                
                return PaymentProcessingResponse(
                    success=False,
                    message=gateway_response.message,
                    transaction_id=gateway_response.transaction_id,
                    invoice_html="",
                    invoice_number="",
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            # 🆕 Manejar error solo si el servicio está disponible
            if self.pago_service:
                try:
                    await self.pago_service.actualizar_estado_pago(
                        pago_id=payment_data.pago_id,
                        nuevo_estado="fallido",
                        metadata={"error": str(e)}
                    )
                except:
                    pass  # Si falla el update, continuar
            
            return PaymentProcessingResponse(
                success=False,
                message=f"Error interno procesando pago: {str(e)}",
                transaction_id="",
                invoice_html="",
                invoice_number="",
                timestamp=datetime.now()
            )