from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.facturas import FacturaCreate, FacturaEmitidaResponse, FacturaResponse
from app.services.factura_service import FacturaService

router = APIRouter(prefix="/api/v1/facturas", tags=["Facturacion"])

@router.post(
    "/",
    response_model=FacturaEmitidaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Emitir factura electrónica para una reserva",
    description="""
    Emite una factura electrónica para una reserva con pago confirmado.
    
    Validaciones:
    - El pago debe estar en estado 'capturado'
    - La reserva debe existir
    - No debe existir factura previa para la misma reserva (idempotencia)
    """
)
async def emitir_factura(
    factura_data: FacturaCreate,
    db: Session = Depends(get_db)
):
    try:
        factura_service = FacturaService(db)
        
        # Validar que el pago puede facturarse
        if not factura_service.validar_pago_para_factura(str(factura_data.pago_id)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="NO_FACTURABLE - El pago no está en estado capturado"
            )
        
        # TODO: Obtener monto real del pago desde PagoService
        pago_total = 150000.0  # Simulado
        
        # Crear factura
        factura = factura_service.crear_factura(factura_data, pago_total)
        
        # Emitir factura (generar documentos)
        factura_emitida = factura_service.emitir_factura(factura.id)
        
        return FacturaEmitidaResponse(
            mensaje="Factura emitida correctamente",
            data={
                "factura_id": factura_emitida.id,
                "reserva_id": factura_emitida.reserva_id,
                "pago_id": factura_emitida.pago_id,
                "serie": factura_emitida.serie,
                "numero": factura_emitida.numero,
                "total": factura_emitida.total,
                "moneda": factura_emitida.moneda,
                "url_pdf": factura_emitida.url_pdf,
                "url_xml": factura_emitida.url_xml
            },
            success=True
        )
        
    except ValueError as e:
        error_message = str(e)
        if "no encontrada" in error_message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="FACTURA_NO_ENCONTRADA"
            )
        elif "SERIE_INVALIDA" in error_message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SERIE_INVALIDA"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error emitiendo factura: {str(e)}"
        )

@router.get(
    "/reserva/{reserva_id}",
    response_model=FacturaResponse,
    summary="Obtener factura por ID de reserva"
)
async def obtener_factura_por_reserva(
    reserva_id: str,
    db: Session = Depends(get_db)
):
    """
    Obtiene la factura asociada a una reserva específica.
    """
    factura_service = FacturaService(db)
    factura = factura_service.obtener_factura_por_reserva(reserva_id)
    
    if not factura:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FACTURA_NO_ENCONTRADA"
        )
    
    return factura

@router.get("/health")
async def health_check():
    """Health check del módulo de facturación"""
    return {
        "status": "healthy",
        "module": "facturacion_electronica",
        "version": "1.0.0"
    }