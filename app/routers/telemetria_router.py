from fastapi import APIRouter, HTTPException, status
from opentelemetry import trace
import random
import asyncio

router = APIRouter()

@router.get("/telemetria/prueba")
async def prueba_telemetria():
    """
    Endpoint para probar la telemetría OpenTelemetry
    Genera trazas con múltiples spans y posibles errores
    """
    tracer = trace.get_tracer(__name__)
    
    with tracer.start_as_current_span("prueba_telemetria_endpoint") as parent_span:
        # Simular procesamiento con múltiples spans
        parent_span.set_attribute("test.type", "integration")
        parent_span.set_attribute("test.user", "demo")
        
        # Span 1: Validación
        with tracer.start_as_current_span("validacion_datos") as validation_span:
            validation_span.set_attribute("validation.step", "input_check")
            await asyncio.sleep(0.1)
            validation_span.add_event("validacion_completada")
        
        # Span 2: Procesamiento de negocio
        with tracer.start_as_current_span("procesamiento_negocio") as business_span:
            business_span.set_attribute("business.operation", "reserva_simulation")
            
            # Simular diferentes caminos
            if random.random() < 0.3:  # 30% de probabilidad de error simulado
                business_span.set_attribute("error", True)
                business_span.record_exception(Exception("Error simulado en procesamiento"))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error simulado para testing de telemetría"
                )
            
            # Sub-span: Cálculo de tarifas
            with tracer.start_as_current_span("calculo_tarifas") as pricing_span:
                pricing_span.set_attribute("pricing.metodo", "dynamic")
                await asyncio.sleep(0.2)
                pricing_span.set_attribute("pricing.resultado", "exitoso")
        
        # Span 3: Persistencia
        with tracer.start_as_current_span("persistencia_datos") as persistence_span:
            persistence_span.set_attribute("db.operation", "simulated_write")
            await asyncio.sleep(0.15)
            persistence_span.add_event("persistencia_completada")
        
        return {
            "status": "success",
            "message": "Prueba de telemetría completada",
            "trace_data": {
                "trace_id": format(parent_span.get_span_context().trace_id, '032x'),
                "test_scenarios": ["validación", "procesamiento", "persistencia"],
                "duration_ms": 450  # Simulado
            }
        }

@router.get("/telemetria/info")
async def info_telemetria():
    """Información sobre la configuración de telemetría"""
    import os
    
    config = {
        "otel_service_name": os.getenv("OTEL_SERVICE_NAME", "reserva-canchas-api"),
        "otel_endpoint": os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "no configurado"),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "tracing_enabled": True,
        "exporters": ["OTLP/HTTP"]
    }
    
    return {
        "telemetry_config": config,
        "endpoints_available": {
            "health": "/health",
            "metrics": "/metrics", 
            "tracing_test": "/api/v1/telemetria/prueba"
        }
    }
