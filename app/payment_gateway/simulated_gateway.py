import uuid
from datetime import datetime
import random
from .models import PaymentRequest, PaymentResponse, GatewayStatus

class SimulatedGateway:
    """
    Pasarela de pagos simulada para desarrollo
    No requiere conexión real con bancos
    """
    
    def process_payment(self, payment_request: PaymentRequest) -> PaymentResponse:
        """Simula procesamiento de pago con validaciones básicas"""
        
        # Validaciones fake
        validation_error = self._validate_payment(payment_request)
        if validation_error:
            return PaymentResponse(
                transaction_id=str(uuid.uuid4()),
                status=GatewayStatus.DECLINED,
                approval_code="",
                message=validation_error,
                timestamp=datetime.now()
            )
        
        # Simular aprobación (85% éxito)
        if random.random() < 0.85:
            return PaymentResponse(
                transaction_id=str(uuid.uuid4()),
                status=GatewayStatus.APPROVED,
                approval_code=f"APP{random.randint(10000, 99999)}",
                message="Pago aprobado exitosamente",
                timestamp=datetime.now()
            )
        else:
            # Razones aleatorias de rechazo
            reasons = [
                "Fondos insuficientes", 
                "Límite de tarjeta excedido", 
                "Tarjeta bloqueada temporalmente",
                "Transacción sospechosa detectada"
            ]
            return PaymentResponse(
                transaction_id=str(uuid.uuid4()),
                status=GatewayStatus.DECLINED,
                approval_code="",
                message=random.choice(reasons),
                timestamp=datetime.now()
            )
    
    def _validate_payment(self, payment: PaymentRequest) -> str:
        """Validaciones básicas de datos de pago"""
        if len(payment.card_number) < 13 or not payment.card_number.isdigit():
            return "Número de tarjeta inválido"
        
        if len(payment.cvv) not in [3, 4] or not payment.cvv.isdigit():
            return "CVV inválido"
            
        # 🆕 MEJORAR validación de fecha
        if not payment.expiry_date or len(payment.expiry_date) != 5:
            return "Fecha de expiración inválida (Use formato MM/YY)"
        
        try:
            month, year = payment.expiry_date.split('/')
            month_int = int(month)
            year_int = int(year)
            
            if month_int < 1 or month_int > 12:
                return "Mes de expiración inválido (debe ser entre 01 y 12)"
                
            # 🆕 Validar que no sea fecha pasada (simplificado)
            current_year = datetime.now().year % 100  # Últimos 2 dígitos
            current_month = datetime.now().month
            
            if year_int < current_year or (year_int == current_year and month_int < current_month):
                return "Tarjeta expirada"
                
        except ValueError:
            return "Fecha de expiración inválida (Use formato MM/YY)"
            
        if payment.amount <= 0:
            return "Monto debe ser mayor a cero"
            
        return ""