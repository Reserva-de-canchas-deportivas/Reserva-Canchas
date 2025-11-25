from fastapi import APIRouter, Request, HTTPException, status, Query
from app.services.payment_service import PaymentService
from app.schemas.payment_schemas import WebhookPayload, WebhookResponse, PaymentResponse
from typing import List, Optional
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
payment_service = PaymentService()

def verify_webhook_security(request: Request):
    """Verificar seguridad del webhook"""
    
    # Verificar firma
    signature = request.headers.get("X-Signature")
    if not signature:
        logger.warning("Firma no proporcionada en headers")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="SIGNATURE_MISSING"
        )
    
    return signature

@router.post("/webhook", response_model=WebhookResponse)
async def process_payment_webhook(request: Request):
    """
    Endpoint para recibir webhooks de la pasarela de pagos
    
    - Valida firma HMAC
    - Procesa eventos de pago
    - Garantiza idempotencia
    - Actualiza estados de transacciones
    """
    try:
        # Obtener payload raw para verificar firma
        body_bytes = await request.body()
        
        # Verificar seguridad
        signature = verify_webhook_security(request)
        
        # Verificar firma
        if not payment_service.verify_webhook_signature(body_bytes, signature):
            logger.error("Firma de webhook inválida")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="SIGNATURE_INVALID"
            )
        
        # Parsear JSON
        try:
            webhook_json = json.loads(body_bytes.decode('utf-8'))
            webhook_data = WebhookPayload(**webhook_json)
        except Exception as e:
            logger.error(f"Error parsing JSON: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="INVALID_JSON"
            )
        
        # Procesar webhook
        result = payment_service.process_webhook(webhook_data)
        
        logger.info(f"Webhook procesado exitosamente: {webhook_data.provider_ref}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error interno procesando webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="INTERNAL_SERVER_ERROR"
        )

@router.get("/payments", response_model=List[PaymentResponse])
async def get_all_payments():
    """Obtener todos los pagos (para debugging y desarrollo)"""
    return payment_service.get_all_payments()

@router.get("/payments/{payment_id}", response_model=Optional[PaymentResponse])
async def get_payment_by_id(payment_id: str):
    """Obtener pago por ID"""
    payment = payment_service.get_payment_by_id(payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PAYMENT_NOT_FOUND"
        )
    return payment

@router.get("/orders/{order_id}/payments", response_model=List[PaymentResponse])
async def get_payments_by_order(order_id: str):
    """Obtener pagos por order_id"""
    return payment_service.get_payments_by_order(order_id)