import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.trace import Status, StatusCode

class TelemetryService:
    def __init__(self):
        self.tracer_provider = None
        self.setup_tracing()
    
    def setup_tracing(self):
        """Configurar OpenTelemetry para pruebas unitarias"""
        try:
            # Configurar recurso para pruebas
            resource = Resource.create({
                "service.name": "reserva-canchas-api-test",
                "service.version": "1.0.0", 
                "deployment.environment": "testing"
            })
            
            # Configurar proveedor de trazas
            self.tracer_provider = TracerProvider(resource=resource)
            
            # Usar ConsoleSpanExporter para pruebas (no requiere servidor)
            span_exporter = ConsoleSpanExporter()
            span_processor = BatchSpanProcessor(span_exporter)
            self.tracer_provider.add_span_processor(span_processor)
            
            # Establecer como proveedor global
            trace.set_tracer_provider(self.tracer_provider)
            
        except Exception as e:
            # Fallback seguro para pruebas
            self.tracer_provider = TracerProvider()
            trace.set_tracer_provider(self.tracer_provider)
    
    def get_tracer(self, name="telemetry-service"):
        """Obtener tracer para crear spans"""
        return trace.get_tracer(name)
    
    def create_reserva_span(self, reserva_data):
        """Crear span para operación de reserva - PARA PRUEBAS"""
        tracer = self.get_tracer("reserva-service")
        
        with tracer.start_as_current_span("crear_reserva") as span:
            # Atributos básicos
            span.set_attribute("reserva.usuario_id", reserva_data.get("usuario_id", "unknown"))
            span.set_attribute("reserva.cancha_id", reserva_data.get("cancha_id", "unknown"))
            span.set_attribute("reserva.fecha", reserva_data.get("fecha", "unknown"))
            
            # Simular sub-operaciones
            with tracer.start_as_current_span("validar_disponibilidad") as sub_span:
                sub_span.set_attribute("validacion.estado", "exitoso")
                sub_span.add_event("disponibilidad_verificada")
            
            with tracer.start_as_current_span("procesar_pago") as sub_span:
                sub_span.set_attribute("pago.monto", reserva_data.get("monto", 0))
                sub_span.set_attribute("pago.estado", "completado")
                sub_span.add_event("pago_procesado")
            
            # Retornar información de traza para pruebas
            trace_info = {
                "trace_id": format(span.get_span_context().trace_id, '032x'),
                "span_id": format(span.get_span_context().span_id, '016x'),
                "operation": "crear_reserva",
                "spans_count": 3  # parent + 2 children
            }
            
            return trace_info
    
    def create_error_span(self, operation_name, error_message):
        """Crear span con error - PARA PRUEBAS"""
        tracer = self.get_tracer("error-service")
        
        with tracer.start_as_current_span(operation_name) as span:
            span.set_attribute("operation.type", "error_flow")
            
            try:
                # Simular operación que falla
                raise Exception(error_message)
            except Exception as e:
                # Registrar el error en el span
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("error.occurred", True)
                span.set_attribute("error.message", str(e))
                
                return {
                    "trace_id": format(span.get_span_context().trace_id, '032x'),
                    "error": True,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                }
    
    def simulate_complex_operation(self):
        """Simular operación compleja con múltiples spans - PARA PRUEBAS"""
        tracer = self.get_tracer("complex-operation")
        
        with tracer.start_as_current_span("operacion_compleja") as parent_span:
            parent_span.set_attribute("system.operation", "reserva_flow")
            
            # Fase 1: Validación
            with tracer.start_as_current_span("fase_validacion") as phase1:
                phase1.set_attribute("phase", "validation")
                with tracer.start_as_current_span("validar_usuario") as sub1:
                    sub1.set_attribute("user.status", "active")
                
                with tracer.start_as_current_span("validar_cancha") as sub2:
                    sub2.set_attribute("court.available", True)
            
            # Fase 2: Procesamiento
            with tracer.start_as_current_span("fase_procesamiento") as phase2:
                phase2.set_attribute("phase", "processing")
                with tracer.start_as_current_span("calcular_precio") as sub3:
                    sub3.set_attribute("price.calculated", 150.0)
                
                with tracer.start_as_current_span("aplicar_descuento") as sub4:
                    sub4.set_attribute("discount.applied", 0.0)
            
            # Fase 3: Confirmación
            with tracer.start_as_current_span("fase_confirmacion") as phase3:
                phase3.set_attribute("phase", "confirmation")
                phase3.add_event("reserva_confirmada")
            
            return {
                "trace_id": format(parent_span.get_span_context().trace_id, '032x'),
                "total_spans": 7,  # parent + 3 phases + 3 sub-spans
                "operation_completed": True,
                "phases": ["validation", "processing", "confirmation"]
            }

# Instancia global para pruebas
telemetry_service = TelemetryService()