from fastapi import APIRouter, HTTPException

from app.schemas.payment_gateway import PaymentProcessingRequest
from app.services.payment_service import PaymentProcessingService

router = APIRouter(prefix="/api/v1/payments", tags=["Payments"])


@router.post(
    "/process",
    summary="Procesar pago con pasarela simulada",
    description="Procesa un pago mediante pasarela simulada (solo testing, sin bancos reales).",
)
async def process_payment(payment_request: PaymentProcessingRequest):
    """Endpoint principal para procesamiento de pagos."""
    payment_service = PaymentProcessingService()
    try:
        result = await payment_service.process_payment(payment_request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando pago: {str(e)}",
        )


@router.get("/health")
async def payment_health_check():
    """Health check del módulo de pagos."""
    return {
        "status": "healthy",
        "module": "payment_gateway",
        "version": "1.0.0",
        "simulated": True,
    }
