import datetime
from app.domain.payment_model import Payment
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class PaymentRepository:
    """Repositorio para manejar pagos en memoria"""
    
    def __init__(self):
        self.payments: List[Payment] = []
        self.processed_webhooks = set()  # Para idempotencia
    
    def get_payment_by_provider_ref(self, provider_ref: str) -> Optional[Payment]:
        """Obtener pago por referencia del proveedor"""
        for payment in self.payments:
            if payment.provider_ref == provider_ref:
                return payment
        return None
    
    def get_payment_by_id(self, payment_id: str) -> Optional[Payment]:
        """Obtener pago por ID"""
        for payment in self.payments:
            if payment.id == payment_id:
                return payment
        return None
    
    def create_payment(self, payment_data: Dict[str, Any]) -> Payment:
        """Crear nuevo pago"""
        payment = Payment(**payment_data)
        self.payments.append(payment)
        logger.info(f"Pago creado: {payment.id} - Estado: {payment.status}")
        return payment
    
    def update_payment_status(self, payment_id: str, new_status: str, provider_data: Dict[str, Any] = None) -> Optional[Payment]:
        """Actualizar estado del pago"""
        payment = self.get_payment_by_id(payment_id)
        if payment:
            payment.status = new_status
            if provider_data:
                payment.provider_data = str(provider_data)
            payment.webhook_processed = True
            payment.updated_at = datetime.utcnow()
            logger.info(f"Pago {payment_id} actualizado a: {new_status}")
            return payment
        return None
    
    def payment_exists_by_provider_ref(self, provider_ref: str) -> bool:
        """Verificar si un webhook ya fue procesado"""
        return provider_ref in self.processed_webhooks
    
    def mark_webhook_processed(self, provider_ref: str):
        """Marcar webhook como procesado"""
        self.processed_webhooks.add(provider_ref)
        logger.info(f"Webhook marcado como procesado: {provider_ref}")
    
    def get_all_payments(self) -> List[Payment]:
        """Obtener todos los pagos"""
        return self.payments
    
    def get_payments_by_order_id(self, order_id: str) -> List[Payment]:
        """Obtener pagos por order_id"""
        return [p for p in self.payments if p.order_id == order_id]