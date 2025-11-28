from fastapi import APIRouter, HTTPException, status
from app.services.order_service import ReservaService
from app.schemas.reserva_schema import TransicionRequest, TransicionResponse, HistorialResponse, HistorialItem
from datetime import datetime

router = APIRouter()

@router.post("/reservas/{reserva_id}/transicionar", response_model=TransicionResponse)
async def transicionar_estado(reserva_id: str, request: TransicionRequest):
    try:
        resultado = ReservaService.transicionar_estado(
            reserva_id=reserva_id,
            estado_nuevo=request.estado_nuevo,
            usuario_id=request.usuario_id
        )
        
        return TransicionResponse(
            mensaje="Estado actualizado correctamente",
            data=resultado,
            success=True
        )
        
    except ValueError as e:
        error_msg = str(e)
        if "TRANSICION_INVALIDA" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="TRANSICION_INVALIDA"
            )
        elif error_msg == "RESERVA_NO_ENCONTRADA":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reserva no encontrada"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )

@router.get("/reservas/{reserva_id}/historial", response_model=HistorialResponse)
async def obtener_historial(reserva_id: str):
    # Verificar que la reserva existe
    reserva = ReservaService.obtener_reserva(reserva_id)
    if not reserva:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reserva no encontrada"
        )
    
    historial_items = ReservaService.obtener_historial(reserva_id)
    
    return HistorialResponse(
        items=[
            HistorialItem(
                id=item.id,
                reserva_id=item.reserva_id,
                estado_anterior=item.estado_anterior,
                estado_nuevo=item.estado_nuevo,
                usuario_id=item.usuario_id,
                fecha=item.fecha
            ) for item in historial_items
        ],
        total=len(historial_items)
    )

# Endpoint auxiliar para crear reservas de prueba - AGREGAR AL ROUTER
@router.post("/reservas", include_in_schema=True)
async def crear_reserva_prueba(cancha_id: str, usuario_id: str):
    reserva = ReservaService.crear_reserva(
        cancha_id=cancha_id,
        usuario_id=usuario_id,
        fecha_reserva=datetime.now()
    )
    
    return {
        "mensaje": "Reserva creada exitosamente",
        "reserva_id": reserva.id,
        "estado": reserva.estado
    }

# Endpoint auxiliar para listar reservas (solo desarrollo) - AGREGAR AL ROUTER
@router.get("/reservas", include_in_schema=True)
async def listar_reservas():
    from app.services.order_service import reservas_db
    return reservas_db