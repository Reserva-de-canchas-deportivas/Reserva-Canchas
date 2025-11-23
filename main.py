import logging
import os
import time
from contextvars import ContextVar
from uuid import uuid4

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.base import BaseHTTPMiddleware

from app.config.routers import include_routers
from app.database import SessionLocal, init_db
from app.soap.soap_config import get_soap_info, setup_soap_services

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


app = FastAPI(title="Reserva Canchas API", description="API REST", version="1.0.0")

# Inicializar DB en memoria al arranque (para health/readiness)
init_db(create_all=True)

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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
