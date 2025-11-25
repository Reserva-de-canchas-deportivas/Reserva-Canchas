import hmac
import hashlib
from fastapi import HTTPException, status
from app.repository.payment_repository import PaymentRepository
from app.schemas.payment_schemas import WebhookPayload
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class PaymentService:
    """Servicio para procesar pagos y webhooks"""
    
    def __init__(self):
        self.payment_repository = PaymentRepository()
        self.webhook_secret = "webhook-secret-dev-12345"  # Secreto para desarrollo
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verificar firma HMAC del webhook"""
        try:
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            # En desarrollo, aceptamos "test_signature" para facilitar pruebas
            if signature == "test_signature":
                return True
                
            return hmac.compare_digest(expected_signature, signature)
        except Exception as e:
            logger.error(f"Error verificando firma: {e}")
            return False
    
    def process_webhook(self, webhook_data: WebhookPayload) -> dict:
        """Procesar webhook y actualizar estado del pago"""
        
        # 1. Validar evento conocido
        valid_events = {
            "payment_intent.succeeded", 
            "payment_intent.failed", 
            "payment_intent.canceled"
        }
        if webhook_data.event_type not in valid_events:
            logger.warning(f"Evento desconocido: {webhook_data.event_type}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="EVENT_TYPE_UNKNOWN"
            )
        
        # 2. Verificar idempotencia (evitar duplicados)
        if self.payment_repository.payment_exists_by_provider_ref(webhook_data.provider_ref):
            logger.info(f"Webhook duplicado para provider_ref: {webhook_data.provider_ref}")
            return {
                "mensaje": "Webhook ya procesado",
                "data": None,
                "success": True
            }
        
        # 3. Mapear estado del evento al estado interno
        status_mapping = {
            "payment_intent.succeeded": "capturado",
            "payment_intent.failed": "fallido", 
            "payment_intent.canceled": "cancelado"
        }
        new_status = status_mapping.get(webhook_data.event_type, webhook_data.status)
        
        # 4. Crear o actualizar pago
        if webhook_data.payment_id:
            # Actualizar pago existente
            payment = self.payment_repository.update_payment_status(
                webhook_data.payment_id, 
                new_status,
                webhook_data.metadata
            )
            if not payment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="PAYMENT_NOT_FOUND"
                )
        else:
            # Crear nuevo pago
            payment_data = {
                "provider_ref": webhook_data.provider_ref,
                "order_id": webhook_data.order_id,
                "amount": str(webhook_data.amount),
                "currency": webhook_data.currency,
                "status": new_status,
                "payment_method": webhook_data.metadata.get("payment_method") if webhook_data.metadata else None,
                "provider_data": str(webhook_data.metadata) if webhook_data.metadata else None
            }
            payment = self.payment_repository.create_payment(payment_data)
        
        # 5. Marcar webhook como procesado para idempotencia
        self.payment_repository.mark_webhook_processed(webhook_data.provider_ref)
        
        logger.info(f"Pago {payment.id} procesado - Estado: {new_status}")
        
        return {
            "mensaje": "Webhook procesado",
            "data": {
                "evento": webhook_data.event_type,
                "pago_id": payment.id,
                "estado_nuevo": new_status
            },
            "success": True
        }
    
    def get_all_payments(self):
        """Obtener todos los pagos"""
        payments = self.payment_repository.get_all_payments()
        return [payment.to_dict() for payment in payments]
    
    def get_payment_by_id(self, payment_id: str):
        """Obtener pago por ID"""
        payment = self.payment_repository.get_payment_by_id(payment_id)
        return payment.to_dict() if payment else None
    
    def get_payments_by_order(self, order_id: str):
        """Obtener pagos por order_id"""
        payments = self.payment_repository.get_payments_by_order_id(order_id)
        return [payment.to_dict() for payment in payments]