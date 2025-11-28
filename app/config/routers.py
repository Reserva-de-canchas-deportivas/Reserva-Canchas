from fastapi import FastAPI

from app.routers.auth_router import router as auth_router
from app.routers.sede_router import router as sede_router
from app.routers.cancha_router import router as cancha_router
from app.routers.tarifario_router import router as tarifario_router
from app.routers.disponibilidad_router import router as disponibilidad_router
from app.routers.user_router import router as user_router
from app.routers.reserva_router import router as reserva_router
from app.routers.profile_router import router as profile_router

from app.routers.pago_router import router as pago_router

from app.routers.payment_router import router as payment_router

from app.routers.factura_router import router as factura_router

from app.api.reserva_api import router as reserva_router

def include_routers(app: FastAPI) -> None:
    app.include_router(auth_router)
    app.include_router(sede_router)
    app.include_router(cancha_router)
    app.include_router(tarifario_router)
    app.include_router(disponibilidad_router)
    app.include_router(user_router)
    app.include_router(reserva_router)
    app.include_router(profile_router)
    app.include_router(pago_router)
    app.include_router(payment_router)
    app.include_router(factura_router)
    app.include_router(reserva_router, prefix="/api/v1", tags=["Reservas"])


