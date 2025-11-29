import pytest
import sys
import os
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, patch

# Agregar el directorio app al path para que pytest pueda importar
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Importaciones de los módulos a testear
from app.payment_gateway.simulated_gateway import SimulatedGateway
from app.payment_gateway.models import PaymentRequest, GatewayStatus
from app.invoices.invoice_service import InvoiceService, InvoiceData
from app.services.payment_service import PaymentProcessingService
from app.schemas.payment_gateway import PaymentProcessingRequest


class TestSimulatedGateway:
    """Pruebas unitarias para la pasarela simulada"""
    
    def setup_method(self):
        self.gateway = SimulatedGateway()
        self.valid_request = PaymentRequest(
            pago_id=uuid4(),
            card_number="4111111111111111",
            card_holder="Juan Perez",
            expiry_date="12/25",
            cvv="123",
            customer_email="juan@example.com",
            amount=150000.0,
            description="Reserva de cancha"
        )
    
    def test_process_payment_approved(self):
        """Test: Pago aprobado con datos válidos"""
        # Ejecutar
        response = self.gateway.process_payment(self.valid_request)
        
        # Verificar
        assert response.transaction_id is not None
        assert len(response.transaction_id) == 36  # UUID length
        assert response.timestamp is not None
        assert response.message != ""
    
    def test_process_payment_invalid_card(self):
        """Test: Pago rechazado por tarjeta inválida"""
        # Configurar
        invalid_request = self.valid_request.model_copy()
        invalid_request.card_number = "123"  # Tarjeta inválida
        
        # Ejecutar
        response = self.gateway.process_payment(invalid_request)
        
        # Verificar
        assert response.status == GatewayStatus.DECLINED
        assert "inválido" in response.message.lower()
        assert response.approval_code == ""
    
    def test_process_payment_invalid_cvv(self):
        """Test: Pago rechazado por CVV inválido"""
        # Configurar
        invalid_request = self.valid_request.model_copy()
        invalid_request.cvv = "12"  # CVV inválido
        
        # Ejecutar
        response = self.gateway.process_payment(invalid_request)
        
        # Verificar
        assert response.status == GatewayStatus.DECLINED
        assert "cvv" in response.message.lower()
    
    def test_process_payment_invalid_expiry(self):
        """Test: Pago rechazado por fecha de expiración inválida"""
        # Configurar
        invalid_request = self.valid_request.model_copy()
        invalid_request.expiry_date = "13/25"  # Fecha inválida
        
        # Ejecutar
        response = self.gateway.process_payment(invalid_request)
        
        # Verificar
        assert response.status == GatewayStatus.DECLINED
        assert "expiración" in response.message.lower()
    
    def test_process_payment_zero_amount(self):
        """Test: Pago rechazado por monto cero"""
        # Configurar
        invalid_request = self.valid_request.model_copy()
        invalid_request.amount = 0
        
        # Ejecutar
        response = self.gateway.process_payment(invalid_request)
        
        # Verificar
        assert response.status == GatewayStatus.DECLINED
        assert "monto" in response.message.lower()
    
    def test_validate_payment_valid_data(self):
        """Test: Validación de datos de pago válidos"""
        # Ejecutar
        error = self.gateway._validate_payment(self.valid_request)
        
        # Verificar
        assert error == ""  # Sin errores
    
    def test_validate_payment_invalid_data(self):
        """Test: Validación de datos de pago inválidos"""
        test_cases = [
            ({"card_number": "123"}, "tarjeta"),
            ({"cvv": "12"}, "cvv"),
            ({"expiry_date": "invalid"}, "expiración"),
            ({"amount": 0}, "monto"),
        ]
        
        for field_update, expected_error in test_cases:
            invalid_request = self.valid_request.model_copy()
            for key, value in field_update.items():
                setattr(invalid_request, key, value)
            
            error = self.gateway._validate_payment(invalid_request)
            assert expected_error in error.lower()


class TestInvoiceService:
    """Pruebas unitarias para el servicio de facturas"""
    
    def setup_method(self):
        self.invoice_service = InvoiceService()
        self.sample_payment_data = {
            "transaction_id": "TEST-TXN-12345",
            "amount": 175000.0,
            "description": "Reserva cancha tenis",
            "currency": "COP"
        }
        self.sample_customer_data = {
            "name": "Maria Gonzalez",
            "email": "maria@example.com"
        }
    
    def test_generate_invoice_success(self):
        """Test: Generación exitosa de factura"""
        # Ejecutar
        invoice = self.invoice_service.generate_invoice(
            self.sample_payment_data,
            self.sample_customer_data
        )
        
        # Verificar
        assert isinstance(invoice, InvoiceData)
        assert invoice.invoice_number.startswith("INV-")
        assert invoice.transaction_id == "TEST-TXN-12345"
        assert invoice.customer_name == "Maria Gonzalez"
        assert invoice.customer_email == "maria@example.com"
        assert invoice.amount == 175000.0
        assert invoice.currency == "COP"
        assert len(invoice.items) == 1
        assert invoice.items[0]["description"] == "Reserva cancha tenis"
        assert invoice.items[0]["total"] == 175000.0
    
    def test_generate_invoice_html(self):
        """Test: Generación de HTML de factura"""
        # Configurar
        invoice = self.invoice_service.generate_invoice(
            self.sample_payment_data,
            self.sample_customer_data
        )
        
        # Ejecutar
        html_content = self.invoice_service.generate_invoice_html(invoice)
        
        # Verificar
        assert isinstance(html_content, str)
        assert "FACTURA" in html_content
        assert invoice.invoice_number in html_content
        assert "Maria Gonzalez" in html_content
        assert "175,000.00" in html_content  # Formato con separadores
        assert "<html>" in html_content
        assert "</body>" in html_content
    
    def test_generate_invoice_default_values(self):
        """Test: Valores por defecto en factura"""
        # Configurar - datos mínimos
        minimal_payment_data = {
            "transaction_id": "TEST-MIN-123",
            "amount": 100000.0
        }
        minimal_customer_data = {}
        
        # Ejecutar
        invoice = self.invoice_service.generate_invoice(
            minimal_payment_data,
            minimal_customer_data
        )
        
        # Verificar valores por defecto
        assert invoice.customer_name == "Cliente"
        assert invoice.customer_email == ""
        assert invoice.currency == "COP"
        assert invoice.items[0]["description"] == "Reserva de cancha deportiva"


class TestPaymentProcessingService:
    """Pruebas unitarias para el servicio de procesamiento de pagos"""
    
    def setup_method(self):
        # Mock del PagoService
        self.mock_pago_service = AsyncMock()
        self.mock_pago_service.obtener_pago_por_id = AsyncMock()
        self.mock_pago_service.actualizar_estado_pago = AsyncMock()
        
        # 🆕 CORREGIDO: Pasar el mock como parámetro
        self.payment_service = PaymentProcessingService(pago_service=self.mock_pago_service)
        
        self.valid_payment_request = PaymentProcessingRequest(
            pago_id=uuid4(),
            card_number="4111111111111111",
            card_holder="Carlos Ruiz",
            expiry_date="06/26",
            cvv="456",
            customer_email="carlos@example.com",
            amount=200000.0
            
        )
    
    @pytest.mark.asyncio
    async def test_process_payment_success(self):
        """Test: Procesamiento exitoso de pago"""
        # Configurar mocks
        self.mock_pago_service.obtener_pago_por_id.return_value = Mock(estado="iniciado")
        self.mock_pago_service.actualizar_estado_pago.return_value = Mock()
        
        # Ejecutar
        result = await self.payment_service.process_payment(self.valid_payment_request)
        
        # Verificar
        assert result.success is True
        assert result.transaction_id is not None
        assert result.invoice_html != ""
        assert result.invoice_number.startswith("INV-")
        assert "aprobado" in result.message.lower()
        
        # Verificar llamadas a dependencias
        self.mock_pago_service.obtener_pago_por_id.assert_called_once()
        self.mock_pago_service.actualizar_estado_pago.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_payment_pago_not_found(self):
        """Test: Pago no encontrado"""
        # Configurar mock
        self.mock_pago_service.obtener_pago_por_id.return_value = None
        
        # Ejecutar
        result = await self.payment_service.process_payment(self.valid_payment_request)
        
        # Verificar
        assert result.success is False
        assert "no encontrado" in result.message.lower()
        assert result.transaction_id == ""
        assert result.invoice_html == ""
    
    @pytest.mark.asyncio
    async def test_process_payment_already_processed(self):
        """Test: Pago ya procesado anteriormente"""
        # Configurar mock - pago ya completado
        mock_pago = Mock(estado="capturado")
        self.mock_pago_service.obtener_pago_por_id.return_value = mock_pago
        
        # Ejecutar
        result = await self.payment_service.process_payment(self.valid_payment_request)
        
        # Verificar
        assert result.success is False
        assert "ya fue procesado" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_process_payment_gateway_declined(self):
        """Test: Pago rechazado por el gateway"""
        # Configurar mocks
        self.mock_pago_service.obtener_pago_por_id.return_value = Mock(estado="iniciado")
        
        # Forzar rechazo del gateway (simular el 15% de rechazo)
        with patch.object(self.payment_service.gateway, 'process_payment') as mock_gateway:
            mock_gateway.return_value.status.value = "declined"
            mock_gateway.return_value.message = "Fondos insuficientes"
            mock_gateway.return_value.transaction_id = "TXN-DECLINED-123"
            
            # Ejecutar
            result = await self.payment_service.process_payment(self.valid_payment_request)
        
        # Verificar
        assert result.success is False
        assert "fondos" in result.message.lower()
        assert result.transaction_id == "TXN-DECLINED-123"
        assert result.invoice_html == ""
        
        # Verificar que se actualizó estado a fallido
        self.mock_pago_service.actualizar_estado_pago.assert_called_once_with(
            pago_id=self.valid_payment_request.pago_id,
            nuevo_estado="fallido",
            metadata={
                "transaction_id": "TXN-DECLINED-123",
                "reason": "Fondos insuficientes"
            }
        )
    
    @pytest.mark.asyncio
    async def test_process_payment_exception_handling(self):
        """Test: Manejo de excepciones durante el procesamiento"""
        # Configurar mock para lanzar excepción
        self.mock_pago_service.obtener_pago_por_id.side_effect = Exception("Error de base de datos")
        
        # Ejecutar
        result = await self.payment_service.process_payment(self.valid_payment_request)
        
        # Verificar
        assert result.success is False
        assert "error interno" in result.message.lower()
        assert "base de datos" in result.message.lower()


# Tests de esquemas Pydantic
class TestSchemas:
    """Pruebas para los esquemas de datos"""
    
    def test_payment_processing_request_validation(self):
        """Test: Validación de esquema de request"""
        # Datos válidos
        valid_data = {
            "pago_id": str(uuid4()),
            "card_number": "4111111111111111",
            "card_holder": "Test User",
            "expiry_date": "12/25",
            "cvv": "123",
            "customer_email": "test@example.com",
            "amount": 100000.0
        }
        
        # Debe crear el objeto sin errores
        request = PaymentProcessingRequest(**valid_data)
        assert request.pago_id is not None
        assert request.card_number == "4111111111111111"
        assert request.amount == 100000.0
    
    def test_payment_processing_request_defaults(self):
        """Test: Valores por defecto en el request"""
        minimal_data = {
            "pago_id": str(uuid4()),
            "card_number": "4111111111111111",
            "card_holder": "Test User",
            "expiry_date": "12/25",
            "cvv": "123",
            "customer_email": "test@example.com",
            "amount": 100000.0
            # description omitted - should use default
        }
        
        request = PaymentProcessingRequest(**minimal_data)
        assert request.description == "Reserva de cancha deportiva"


if __name__ == "__main__":
    # Ejecutar pruebas manualmente
    pytest.main([__file__, "-v", "--tb=short"])
