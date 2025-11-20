from fastapi import FastAPI

from app.routers.auth_router import router as auth_router
from app.routers.sede_router import router as sede_router
from app.routers.cancha_router import router as cancha_router
from app.routers.tarifario_router import router as tarifario_router
from app.routers.disponibilidad_router import router as disponibilidad_router
from app.routers.user_router import router as user_router
from app.routers.reserva_router import router as reserva_router

def include_routers(app: FastAPI) -> None:
    app.include_router(auth_router)
    app.include_router(sede_router)
    app.include_router(cancha_router)
    app.include_router(tarifario_router)
    app.include_router(disponibilidad_router)
    app.include_router(user_router)
    app.include_router(reserva_router)
    
    
