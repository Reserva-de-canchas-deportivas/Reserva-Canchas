#!/usr/bin/env python3
"""
Pruebas unitarias COMPLETAS para OpenTelemetry - SIN EJECUTAR APP
"""
import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

# Importar servicio
from app.services.telemetry_service import telemetry_service, TelemetryService

class TestTelemetryService:
    """Pruebas del servicio de telemetría"""
    
    def test_service_initialization(self):
        """Test: El servicio se inicializa correctamente"""
        service = TelemetryService()
        
        assert service.tracer_provider is not None
        assert service.get_tracer() is not None
        
        # Verificar que el tracer provider está configurado globalmente
        global_provider = trace.get_tracer_provider()
        assert global_provider is not None
    
    def test_create_reserva_span(self):
        """Test: Crear span para operación de reserva"""
        reserva_data = {
            "usuario_id": 123,
            "cancha_id": 5,
            "fecha": "2024-01-15",
            "monto": 100.0
        }
        
        result = telemetry_service.create_reserva_span(reserva_data)
        
        # Verificar estructura de respuesta
        assert "trace_id" in result
        assert "span_id" in result
        assert "operation" in result
        assert "spans_count" in result
        
        # Verificar valores específicos
        assert result["operation"] == "crear_reserva"
        assert result["spans_count"] == 3
        assert len(result["trace_id"]) == 32  # 16 bytes en hex
        assert len(result["span_id"]) == 16   # 8 bytes en hex
    
    def test_create_error_span(self):
        """Test: Crear span con error"""
        error_message = "Simulated payment error"
        
        result = telemetry_service.create_error_span("procesar_pago", error_message)
        
        # Verificar estructura de error
        assert "trace_id" in result
        assert result["error"] is True
        assert result["error_type"] == "Exception"
        assert result["error_message"] == error_message
        
        # Verificar que se generó trace_id
        assert len(result["trace_id"]) == 32
    
    def test_simulate_complex_operation(self):
        """Test: Simular operación compleja"""
        result = telemetry_service.simulate_complex_operation()
        
        # Verificar estructura completa
        assert "trace_id" in result
        assert "total_spans" in result
        assert "operation_completed" in result
        assert "phases" in result
        
        # Verificar valores específicos
        assert result["total_spans"] == 7
        assert result["operation_completed"] is True
        assert len(result["phases"]) == 3
        assert "validation" in result["phases"]
        assert "processing" in result["phases"]
        assert "confirmation" in result["phases"]
    
    def test_trace_id_uniqueness(self):
        """Test: Los Trace IDs deben ser únicos"""
        # Generar múltiples trazas
        result1 = telemetry_service.create_reserva_span({"usuario_id": 1})
        result2 = telemetry_service.create_reserva_span({"usuario_id": 2})
        result3 = telemetry_service.simulate_complex_operation()
        
        # Todos deben tener trace_ids diferentes
        trace_ids = [result1["trace_id"], result2["trace_id"], result3["trace_id"]]
        unique_trace_ids = set(trace_ids)
        
        assert len(trace_ids) == len(unique_trace_ids), "Trace IDs deben ser únicos"
    
    def test_tracer_provider_consistency(self):
        """Test: El tracer provider es consistente"""
        service1 = TelemetryService()
        service2 = TelemetryService()
        
        # Ambos servicios deben usar el mismo tracer provider global
        tracer1 = service1.get_tracer()
        tracer2 = service2.get_tracer()
        
        assert tracer1 is not None
        assert tracer2 is not None
        
        # Deberían poder crear spans sin problemas
        with tracer1.start_as_current_span("test_span_1"):
            pass
            
        with tracer2.start_as_current_span("test_span_2"):
            pass
    
    def test_error_span_attributes(self):
        """Test: Los spans de error tienen atributos correctos"""
        result = telemetry_service.create_error_span(
            "test_error_operation", 
            "Database connection failed"
        )
        
        # El resultado debe indicar error
        assert result["error"] is True
        assert "connection failed" in result["error_message"].lower()
    
    def test_reserva_span_with_missing_data(self):
        """Test: Crear span de reserva con datos faltantes"""
        # Datos incompletos
        reserva_data = {
            "usuario_id": 999
            # faltan cancha_id, fecha, monto
        }
        
        result = telemetry_service.create_reserva_span(reserva_data)
        
        # Debe funcionar incluso con datos faltantes
        assert "trace_id" in result
        assert result["operation"] == "crear_reserva"
        assert result["spans_count"] == 3

class TestTelemetryEdgeCases:
    """Pruebas de casos edge para telemetría"""
    
    def test_multiple_rapid_operations(self):
        """Test: Múltiples operaciones rápidas sucesivas"""
        results = []
        
        # Ejecutar 10 operaciones rápidas
        for i in range(10):
            result = telemetry_service.create_reserva_span({
                "usuario_id": i,
                "cancha_id": i % 3 + 1,
                "fecha": f"2024-01-{15 + i}",
                "monto": 50.0 + i * 10
            })
            results.append(result)
        
        # Todas deben completarse exitosamente
        assert len(results) == 10
        for result in results:
            assert "trace_id" in result
            assert result["operation"] == "crear_reserva"
    
    def test_concurrent_tracer_usage(self):
        """Test: Uso concurrente del tracer (simulado)"""
        from opentelemetry import trace
        
        tracer = telemetry_service.get_tracer("concurrent-test")
        
        # Simular operaciones "concurrentes" (en serie para pruebas unitarias)
        spans_info = []
        
        for i in range(5):
            with tracer.start_as_current_span(f"operation_{i}") as span:
                span.set_attribute("iteration", i)
                span_info = {
                    "trace_id": format(span.get_span_context().trace_id, '032x'),
                    "span_id": format(span.get_span_context().span_id, '016x'),
                    "operation": f"operation_{i}"
                }
                spans_info.append(span_info)
        
        # Verificar que todas las operaciones generaron trazas
        assert len(spans_info) == 5
        for info in spans_info:
            assert len(info["trace_id"]) == 32
            assert len(info["span_id"]) == 16

def test_telemetry_integration_with_business_logic():
    """Test: Integración de telemetría con lógica de negocio simulada"""
    # Simular lógica de negocio que usa telemetría
    def process_reservation_business_logic(user_id, court_id, date):
        """Lógica de negocio simulada que instrumenta con telemetría"""
        tracer = telemetry_service.get_tracer("business-logic")
        
        with tracer.start_as_current_span("business_process_reservation") as span:
            span.set_attribute("business.user_id", user_id)
            span.set_attribute("business.court_id", court_id)
            span.set_attribute("business.date", date)
            
            # Simular validaciones de negocio
            with tracer.start_as_current_span("validate_business_rules") as sub_span:
                if user_id <= 0:
                    sub_span.set_attribute("validation.error", "invalid_user_id")
                    raise ValueError("ID de usuario inválido")
                sub_span.set_attribute("validation.success", True)
            
            # Simular procesamiento exitoso
            reservation_id = user_id * 1000 + court_id
            span.set_attribute("business.reservation_id", reservation_id)
            
            return {
                "reservation_id": reservation_id,
                "status": "confirmed",
                "trace_id": format(span.get_span_context().trace_id, '032x')
            }
    
    # Probar casos exitosos
    result1 = process_reservation_business_logic(123, 5, "2024-01-15")
    assert result1["reservation_id"] == 123005
    assert result1["status"] == "confirmed"
    assert "trace_id" in result1
    
    # Probar caso con error
    with pytest.raises(ValueError, match="ID de usuario inválido"):
        process_reservation_business_logic(-1, 5, "2024-01-15")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])