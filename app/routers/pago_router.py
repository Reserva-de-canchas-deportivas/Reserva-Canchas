from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.domain.user_model import Usuario
from app.services.pago_service import PagoService
from app.models.pago import EstadoPago
from app.services.rbac import require_role_dependency

router = APIRouter(prefix="/api/v1/pagos", tags=["Pagos"])
CLIENT_DEP = require_role_dependency("cliente", "personal", "admin")

# Schemas
class PagoCreateRequest(BaseModel):
    reserva_id: str
    monto: float
    proveedor: str
    moneda: str = "COP"
    referencia_proveedor: Optional[str] = None

class PagoUpdateRequest(BaseModel):
    estado: EstadoPago
    referencia_proveedor: Optional[str] = None

class PagoResponse(BaseModel):
    mensaje: str
    data: dict
    success: bool

@router.post(
    "",
    response_model=PagoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nuevo pago",
    description="Crea un registro de pago asociado a una reserva"
)
async def crear_pago(
    payload: PagoCreateRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(CLIENT_DEP)
):
    try:
        pago_service = PagoService(db)
        resultado = pago_service.crear_pago(
            reserva_id=payload.reserva_id,
            monto=payload.monto,
            proveedor=payload.proveedor,
            moneda=payload.moneda,
            referencia_proveedor=payload.referencia_proveedor
        )
        
        return PagoResponse(
            mensaje="Pago registrado",
            data=resultado,
            success=True
        )
        
    except ValueError as e:
        error_message = str(e)
        if error_message == "RESERVA_NO_ENCONTRADA":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reserva no encontrada"
            )
        elif error_message == "PAGO_DUPLICADO":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="PAGO_DUPLICADO: Ya existe un pago para esta reserva"
            )
        elif error_message == "MONTO_INVALIDO":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El monto debe ser mayor a cero"
            )
        elif error_message == "MONEDA_INVALIDA":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Moneda inválida. Use formato ISO 4217 (3 letras mayúsculas)"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )

@router.patch(
    "/{pago_id}",
    response_model=PagoResponse,
    summary="Actualizar estado de pago",
    description="Actualiza el estado de un pago existente"
)
async def actualizar_pago(
    pago_id: str,
    payload: PagoUpdateRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(CLIENT_DEP)
):
    try:
        pago_service = PagoService(db)
        resultado = pago_service.actualizar_estado_pago(
            pago_id=pago_id,
            nuevo_estado=payload.estado,
            referencia_proveedor=payload.referencia_proveedor
        )
        
        return PagoResponse(
            mensaje="Estado de pago actualizado",
            data=resultado,
            success=True
        )
        
    except ValueError as e:
        error_message = str(e)
        if error_message == "PAGO_NO_ENCONTRADO":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pago no encontrado"
            )
        elif error_message == "ESTADO_INVALIDO":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Estado de pago inválido"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )

@router.get(
    "/{pago_id}",
    response_model=PagoResponse,
    summary="Obtener pago",
    description="Obtiene la información de un pago específico"
)
async def obtener_pago(
    pago_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(CLIENT_DEP)
):
    pago_service = PagoService(db)
    resultado = pago_service.obtener_pago(pago_id)
    
    if not resultado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pago no encontrado"
        )
    
    return PagoResponse(
        mensaje="Pago obtenido",
        data=resultado,
        success=True
    )