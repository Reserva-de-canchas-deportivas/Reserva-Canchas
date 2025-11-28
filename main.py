import argparse
import json
import logging
import os
import sys
import time
import asyncio
from contextvars import ContextVar
from uuid import uuid4

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.base import BaseHTTPMiddleware

from app.config.routers import include_routers
from app.database import SessionLocal, init_db
from app.soap.soap_config import get_soap_info, setup_soap_services
from app.services.reserva_service import ReservaService
from app.repository.user_repository import seed_users

from fastapi import FastAPI
from app.config.routers import include_routers

import logging
import structlog
from typing import Any, Dict, Optional
from fastapi import Request
from app.routers.example_router import router as example_router

from fastapi import FastAPI, Depends
from prometheus_fastapi_instrumentator import Instrumentator
from app.middleware.metrics_middleware import MetricsMiddleware
from app.services.metrics_service import metrics_service
import asyncio

# Importar tus routers existentes
from app.routers import (
    auth_router, cancha_router, disponibilidad_router,
    reserva_router, pago_router, user_router, sede_router
)

from fastapi import FastAPI, Depends
from prometheus_fastapi_instrumentator import Instrumentator

# Importar middlewares
from app.middleware.metrics_middleware import MetricsMiddleware
from app.middleware.telemetry_middleware import TelemetryMiddleware

# Importar servicios
from app.services.metrics_service import metrics_service
from app.services.telemetry_service import telemetry_service

# OpenTelemetry
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
import os

# Importar routers existentes
from app.routers import (
    auth_router, cancha_router, disponibilidad_router,
    reserva_router, pago_router, user_router, sede_router
)

from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
FastAPIInstrumentor().instrument_app(app)

request_id_ctx_var: ContextVar[str] = ContextVar("request_id", default="-")
start_time = time.time()


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        request_id_ctx_var.set(request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_ctx_var.get()
        return True


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.addFilter(RequestIdFilter())
    formatter = logging.Formatter(
        '{"timestamp":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s","request_id":"%(request_id)s"}'
    )
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers = [handler]


def configure_tracing(app: FastAPI) -> None:  # pragma: no cover
    if os.getenv("DISABLE_TRACING") == "1":
        return

    try:
        from opentelemetry import trace
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import (
            BatchSpanProcessor,
            ConsoleSpanExporter,
        )

        try:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
                OTLPSpanExporter,
            )

            otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
            exporter = (
                OTLPSpanExporter(endpoint=otlp_endpoint)
                if otlp_endpoint
                else ConsoleSpanExporter()
            )
        except Exception:
            exporter = ConsoleSpanExporter()

        resource = Resource.create(
            {"service.name": os.getenv("OTEL_SERVICE_NAME", "reserva-canchas-api")}
        )
        provider = TracerProvider(resource=resource)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        FastAPIInstrumentor.instrument_app(app)
    except ImportError:
        logging.getLogger(__name__).warning(
            "OpenTelemetry no disponible; trazas deshabilitadas"
        )


def configure_metrics(app: FastAPI) -> None:  # pragma: no cover
    try:
        from prometheus_fastapi_instrumentator import Instrumentator

        Instrumentator().instrument(app).expose(
            app, include_in_schema=False, endpoint="/metrics"
        )
    except ImportError:
        logging.getLogger(__name__).warning(
            "prometheus-fastapi-instrumentator no disponible; /metrics deshabilitado"
        )


def create_app() -> FastAPI:
    application = FastAPI(
        title="Reserva Canchas API",
        description="API REST para gestion de reservas con servicios SOAP complementarios.",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    def custom_openapi() -> dict:
        if application.openapi_schema:
            return application.openapi_schema
        openapi_schema = get_openapi(
            title=application.title,
            version=application.version,
            description=application.description,
            routes=application.routes,
            contact={
                "name": "Equipo Reserva Canchas",
                "url": "https://github.com/Reserva-de-canchas-deportivas",
                "email": "devops@example.com",
            },
            license_info={"name": "MIT"},
            servers=[{"url": "/", "description": "Default"}],
        )
        application.openapi_schema = openapi_schema
        return application.openapi_schema

    application.openapi = custom_openapi
    return application


app = create_app()

# Inicializar DB en memoria al arranque (para health/readiness)
init_db(create_all=True)
# Seed de usuarios base (admin) para ambientes de prueba/demo
with SessionLocal() as seed_db:
    seed_users(seed_db)

# Observabilidad basica
configure_logging()
app.add_middleware(RequestIDMiddleware)
configure_tracing(app)
configure_metrics(app)

# Configurar SOAP primero
setup_soap_services(app)

# Incluir routers REST
include_routers(app)


@app.get("/")
async def root():
    """Endpoint de bienvenida."""
    return {
        "message": "Bienvenido a mi API con FastAPI!",
        "status": "online",
        "version": "1.0.0",
    }


@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str | None = None):
    """Ejemplo con parametros de ruta y query."""
    return {"item_id": item_id, "query": q}


@app.get("/health")
async def health_check():
    """Verifica estado general (DB) y uptime (liveness + readiness ligera)."""
    uptime = int(time.time() - start_time)
    db_state = "up"
    cache_state = os.getenv("CACHE_URL", "not_configured")
    success = True
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        logging.getLogger(__name__).warning("Health DB check failed: %s", exc)
        db_state = "down"
        success = False

    return {
        "mensaje": "OK" if success else "DEGRADED",
        "data": {"db": db_state, "cache": cache_state, "uptime_seg": uptime},
        "success": success,
    }


@app.get("/soap/info")
async def soap_info():
    """Informacion sobre servicios SOAP disponibles."""
    return JSONResponse(content=get_soap_info())


@app.get("/docs/info")
async def docs_info():
    """Ubicaciones de la documentacion y contratos."""
    return {
        "mensaje": "Documentacion disponible",
        "data": {
            "openapi": app.openapi_url,
            "swagger": app.docs_url,
            "redoc": app.redoc_url,
            "wsdl": [
                "/soap/auth?wsdl",
                "/soap/booking?wsdl",
                "/soap/billing?wsdl",
            ],
        },
        "success": True,
    }


# Scheduler simple para expirar HOLDs
async def _hold_cleaner_loop(interval_seconds: int = 60) -> None:
    while True:
        try:
            with SessionLocal() as db:
                ReservaService(db).expirar_holds_vencidos()
        except Exception as exc:
            logging.getLogger(__name__).warning("Error en limpieza de HOLD: %s", exc)
        await asyncio.sleep(interval_seconds)


@app.on_event("startup")
async def start_hold_cleaner() -> None:
    import asyncio

    asyncio.create_task(_hold_cleaner_loop(60))


def _export_openapi(path: str) -> None:  # pragma: no cover
    schema = app.openapi()
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(schema, fh, indent=2, ensure_ascii=False)
    print(f"OpenAPI schema exported to {path}")


def _cli(argv: list[str]) -> None:  # pragma: no cover
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--export-openapi",
        dest="export_openapi",
        help="Ruta de salida para OpenAPI JSON",
    )
    args = parser.parse_args(argv)

    if args.export_openapi:
        _export_openapi(args.export_openapi)
        return

    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    _cli(sys.argv[1:])  # pragma: no cover




app = FastAPI(title="Sistema de Reservas", version="1.0.0")

# Incluir routers
include_routers(app)

@app.get("/")
def read_root():
    return {"message": "Sistema de Reservas de Canchas"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

from fastapi import FastAPI
from app.config.routers import include_routers

app = FastAPI(
    title="Sistema de Reservas de Canchas",
    description="API para gestión de reservas con workflow de estados",
    version="1.0.0"
)

# Incluir routers
include_routers(app)

@app.get("/")
def read_root():
    return {"message": "Sistema de Reservas de Canchas - Workflow de Estados"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "reservas"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

    

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

    app.include_router(example_router)



app = FastAPI(title="Sistema de Reservas", version="1.0.0")

# Aplicar middleware de métricas
app.add_middleware(MetricsMiddleware)

# Configurar instrumentador de Prometheus
instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    should_respect_env_var=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=[".*admin.*", "/metrics"],
    inprogress_name="http_requests_inprogress",
    inprogress_labels=True,
)

# Instrumentar la aplicación
instrumentator.instrument(app).expose(app)

# Registrar routers existentes
app.include_router(auth_router.router, prefix="/api/v1", tags=["auth"])
app.include_router(cancha_router.router, prefix="/api/v1", tags=["canchas"])
app.include_router(disponibilidad_router.router, prefix="/api/v1", tags=["disponibilidad"])
app.include_router(reserva_router.router, prefix="/api/v1", tags=["reservas"])
app.include_router(pago_router.router, prefix="/api/v1", tags=["pagos"])
app.include_router(user_router.router, prefix="/api/v1", tags=["usuarios"])
app.include_router(sede_router.router, prefix="/api/v1", tags=["sedes"])

# Endpoint de health check
@app.get("/health")
async def health_check():
    """Endpoint de health check para monitoreo"""
    return {
        "status": "healthy",
        "timestamp": asyncio.get_event_loop().time(),
        "service": "reservas-api",
        "metrics_ready": True
    }

# Endpoint de estado del sistema con métricas básicas
@app.get("/system/status")
async def system_status():
    """Endpoint que muestra el estado del sistema con métricas"""
    from prometheus_client import generate_latest, REGISTRY
    
    metrics_data = generate_latest(REGISTRY).decode('utf-8')
    
    # Extraer algunas métricas clave para mostrar
    reservas_activas = 0
    pagos_pendientes = 0
    
    for line in metrics_data.split('\n'):
        if 'reservas_activas_total' in line and not line.startswith('#'):
            try:
                reservas_activas = float(line.split()[-1])
            except:
                pass
        elif 'pagos_pendientes_total' in line and not line.startswith('#'):
            try:
                pagos_pendientes = float(line.split()[-1])
            except:
                pass
    
    return {
        "status": "operational",
        "reservas_activas": reservas_activas,
        "pagos_pendientes": pagos_pendientes,
        "metrics_endpoint": "/metrics",
        "health_endpoint": "/health"
    }

@app.on_event("startup")
async def startup_event():
    """Evento de inicio de la aplicación"""
    # Inicializar métricas si es necesario
    metrics_service.establecer_reservas_activas(0)
    metrics_service.establecer_pagos_pendientes(0)
    print("✅ Métricas Prometheus inicializadas correctamente")
    print("📊 Endpoint de métricas disponible en: /metrics")
    print("❤️  Health check disponible en: /health")
    print("🔧 Estado del sistema disponible en: /system/status")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)



app = FastAPI(title="Sistema de Reservas", version="1.0.0")

# Aplicar middlewares
app.add_middleware(MetricsMiddleware)
app.add_middleware(TelemetryMiddleware)

# Configurar instrumentador de Prometheus
instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    should_respect_env_var=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=[".*admin.*", "/metrics"],
    inprogress_name="http_requests_inprogress",
    inprogress_labels=True,
)

# Instrumentar la aplicación
instrumentator.instrument(app).expose(app)

# Registrar routers existentes
app.include_router(auth_router.router, prefix="/api/v1", tags=["auth"])
app.include_router(cancha_router.router, prefix="/api/v1", tags=["canchas"])
app.include_router(disponibilidad_router.router, prefix="/api/v1", tags=["disponibilidad"])
app.include_router(reserva_router.router, prefix="/api/v1", tags=["reservas"])
app.include_router(pago_router.router, prefix="/api/v1", tags=["pagos"])
app.include_router(user_router.router, prefix="/api/v1", tags=["usuarios"])
app.include_router(sede_router.router, prefix="/api/v1", tags=["sedes"])

# Nuevo router para telemetría
from app.routers import telemetria_router
app.include_router(telemetria_router.router, prefix="/api/v1", tags=["telemetria"])

# Endpoint de health check mejorado
@app.get("/health")
async def health_check():
    """Endpoint de health check para monitoreo"""
    from opentelemetry import trace
    import asyncio
    
    current_span = trace.get_current_span()
    trace_info = {}
    if current_span:
        span_context = current_span.get_span_context()
        trace_info = {
            "trace_id": format(span_context.trace_id, '032x'),
            "span_id": format(span_context.span_id, '016x')
        }
    
    return {
        "status": "healthy",
        "timestamp": asyncio.get_event_loop().time(),
        "service": "reservas-api",
        "metrics_ready": True,
        "tracing_ready": True,
        "trace_context": trace_info
    }

@app.on_event("startup")
async def startup_event():
    """Evento de inicio de la aplicación"""
    # Inicializar métricas
    metrics_service.establecer_reservas_activas(0)
    metrics_service.establecer_pagos_pendientes(0)
    
    # Instrumentar FastAPI con OpenTelemetry
    try:
        FastAPIInstrumentor().instrument_app(app)
        RequestsInstrumentor().instrument()
        print("✅ OpenTelemetry instrumentado correctamente")
    except Exception as e:
        print(f"⚠️  Advertencia OpenTelemetry: {e}")
    
    print("✅ Sistema de métricas y tracing inicializado")
    print("📊 Métricas disponibles en: /metrics")
    print("🔍 Tracing disponible en: OTEL Collector")
    print("❤️  Health check en: /health")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)