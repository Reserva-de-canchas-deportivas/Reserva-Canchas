from fastapi import Request, Response
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
import time
import json

class TelemetryMiddleware:
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, request: Request, call_next):
        # Excluir endpoints de métricas y health de tracing detallado
        if request.url.path in ['/metrics', '/health']:
            return await call_next(request)
        
        tracer = trace.get_tracer(__name__)
        start_time = time.time()
        
        # Crear span para la request HTTP
        with tracer.start_as_current_span(
            f"HTTP {request.method} {request.url.path}",
            attributes={
                "http.method": request.method,
                "http.url": str(request.url),
                "http.route": request.url.path,
                "http.host": request.url.hostname,
                "http.scheme": request.url.scheme,
                "http.user_agent": request.headers.get("user-agent", ""),
            }
        ) as span:
            try:
                response = await call_next(request)
                duration = time.time() - start_time
                
                # Agregar atributos de respuesta
                span.set_attributes({
                    "http.status_code": response.status_code,
                    "http.response_size": int(response.headers.get("content-length", 0)),
                    "http.duration_ms": duration * 1000
                })
                
                # Marcar error si es código 5xx
                if response.status_code >= 500:
                    span.set_status(Status(StatusCode.ERROR))
                    span.set_attribute("error", True)
                
                return response
                
            except Exception as e:
                duration = time.time() - start_time
                
                # Registrar excepción en el span
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attributes({
                    "http.duration_ms": duration * 1000,
                    "error": True,
                    "error.type": type(e).__name__,
                    "error.message": str(e)
                })
                
                raise e

# Middleware para propagación de contexto
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.b3 import B3Format

# Configurar propagador B3 (compatible con Jaeger)
set_global_textmap(B3Format())