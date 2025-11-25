from fastapi import APIRouter
from app.api.payment_webhook_api import router as webhook_router

router = APIRouter(prefix="/api/v1/pagos", tags=["pagos"])

router.include_router(webhook_router)