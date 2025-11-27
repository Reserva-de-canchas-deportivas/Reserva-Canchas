from fastapi import APIRouter, Depends, HTTPException
from app.schemas.payment_gateway import PaymentProcessingRequest, PaymentProcessingResponse
from app.services.payment_service import PaymentProcessingService

router = APIRouter(prefix="/api/v1/payments", tags=["Payments"])

@router.post(
    "/process", 
    response_model=PaymentProcessingResponse,
    summary="Procesar pago con pasarela simulada",
    description="""
    Procesa un pago mediante nuestra pasarela simulada de desarrollo.
    
    **Características:**
    - ✅ Validación de datos de tarjeta (simulada)
    - ✅ Procesamiento de pago (85% tasa de éxito simulada)
    - ✅ Generación de factura HTML
    - 🔒 No se conecta con bancos reales
    - 🎯 Para fines de desarrollo y testing
    """
)
async def process_payment(
    payment_request: PaymentProcessingRequest,
    payment_service: PaymentProcessingService = Depends()
):
    """
    Endpoint principal para procesamiento de pagos
    """
    try:
        result = await payment_service.process_payment(payment_request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error procesando pago: {str(e)}"
        )

@router.get("/health")
async def payment_health_check():
    """
    Health check del módulo de pagos
    """
    return {
        "status": "healthy",
        "module": "payment_gateway",
        "version": "1.0.0",
        "simulated": True
    }