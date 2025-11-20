from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.domain.user_model import Usuario
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.domain.user_model import Usuario
from app.schemas.reserva import (
    ReservaApiResponse,
    ReservaHoldRequest,
    ReservaConfirmRequest,
    ReservaConfirmResponse,
)
from app.services.reserva_service import ReservaService
from app.services.rbac import require_role_dependency

router = APIRouter(prefix="/api/v1/reservas", tags=["Reservas"])
CLIENT_DEP = require_role_dependency("cliente", "personal", "admin")


@router.post(
    "",
    response_model=ReservaApiResponse,
    summary="Crear pre-reserva HOLD",
    description="Bloquea temporalmente un horario aplicando TTL e idempotencia.",
)
async def crear_hold(
    payload: ReservaHoldRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(CLIENT_DEP),
):
    service = ReservaService(db)
    data, creado = service.crear_hold(payload, current_user)
    status_code = status.HTTP_201_CREATED if creado else status.HTTP_200_OK
    resp = ReservaApiResponse(mensaje="Pre-reserva creada", data=data, success=True)
    return JSONResponse(status_code=status_code, content=resp.model_dump())


@router.post(
    "/{reserva_id}/confirmar",
    response_model=ReservaConfirmResponse,
    summary="Confirmar pre-reserva",
    description="Confirma una reserva en HOLD si está vigente e idempotente.",
)
async def confirmar_reserva(
    reserva_id: str,
    payload: ReservaConfirmRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(CLIENT_DEP),
):
    service = ReservaService(db)
    data = service.confirmar_reserva(reserva_id=reserva_id, payload=payload, usuario=current_user)
    return ReservaConfirmResponse(mensaje="Reserva confirmada", data=data, success=True)
