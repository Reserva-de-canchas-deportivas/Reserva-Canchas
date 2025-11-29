import logging
import structlog
from fastapi import Request

def get_logger(name: str = "app") -> logging.Logger:
    """Obtiene un logger con configuración estructurada"""
    return logging.getLogger(name)

def get_request_logger(request: Request) -> logging.LoggerAdapter:
    """Obtiene un logger con el contexto de la request actual"""
    logger = get_logger("app.request")
    
    # Obtener información del contexto de la request
    request_id = getattr(request.state, "request_id", "unknown")
    usuario = getattr(request.state, "usuario", "anonimo")
    endpoint = f"{request.method} {request.url.path}"
    
    return logging.LoggerAdapter(
        logger,
        extra={
            "request_id": request_id,
            "usuario": usuario,
            "endpoint": endpoint
        }
    )

def setup_structlog():
    """Configura structlog para logging estructurado"""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
