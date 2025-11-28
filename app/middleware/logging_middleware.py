import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging

class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = logging.getLogger("app.middleware")

    async def dispatch(self, request: Request, call_next):
        # Generar o obtener el Request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Almacenar el request_id en el estado de la request
        request.state.request_id = request_id
        request.state.usuario = "anonimo"  # Por defecto
        
        # Crear logger con contexto
        logger = logging.LoggerAdapter(
            self.logger, 
            extra={
                "request_id": request_id,
                "usuario": request.state.usuario,
                "endpoint": f"{request.method} {request.url.path}"
            }
        )
        
        # Log de inicio de request
        logger.info(
            "Inicio de solicitud",
            extra={
                "method": request.method,
                "url": str(request.url),
                "client_ip": request.client.host if request.client else "unknown"
            }
        )
        
        # Procesar la request
        try:
            response = await call_next(request)
            
            # Agregar el Request ID al header de respuesta
            response.headers["X-Request-ID"] = request_id
            
            # Log de respuesta exitosa
            logger.info(
                "Respuesta enviada",
                extra={
                    "status_code": response.status_code,
                    "content_type": response.headers.get("content-type", "unknown")
                }
            )
            
            return response
            
        except Exception as exc:
            # Log de error
            logger.error(
                "Error en solicitud",
                extra={
                    "error_type": type(exc).__name__,
                    "error_message": str(exc)
                },
                exc_info=True
            )
            raise