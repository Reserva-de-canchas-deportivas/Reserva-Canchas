from fastapi import FastAPI

from app.routers.auth_router import router as auth_router
from app.routers.sede_router import router as sede_router
from app.routers.cancha_router import router as cancha_router

def include_routers(app: FastAPI) -> None:
    app.include_router(auth_router)
    app.include_router(sede_router)
    app.include_router(cancha_router)
    