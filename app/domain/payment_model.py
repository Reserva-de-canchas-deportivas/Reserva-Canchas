from datetime import datetime
import uuid

class Payment:
    """Modelo de Pago para datos en memoria"""
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.provider_ref = kwargs.get('provider_ref')  # Para idempotencia
        self.order_id = kwargs.get('order_id')
        self.amount = kwargs.get('amount')
        self.currency = kwargs.get('currency', 'USD')
        self.status = kwargs.get('status', 'pending')  # pending, captured, failed, refunded
        self.payment_method = kwargs.get('payment_method')
        self.provider_data = kwargs.get('provider_data')  # Datos adicionales
        self.created_at = kwargs.get('created_at', datetime.utcnow())
        self.updated_at = kwargs.get('updated_at', datetime.utcnow())
        self.webhook_processed = kwargs.get('webhook_processed', False)
    
    def to_dict(self):
        """Convertir a diccionario para respuestas JSON"""
        return {
            "id": self.id,
            "provider_ref": self.provider_ref,
            "order_id": self.order_id,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status,
            "payment_method": self.payment_method,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }