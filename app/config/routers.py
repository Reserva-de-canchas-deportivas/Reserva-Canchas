from fastapi import FastAPI

from app.routers.auth_router import router as auth_router


def include_routers(app: FastAPI) -> None:
    app.include_router(auth_router) 
