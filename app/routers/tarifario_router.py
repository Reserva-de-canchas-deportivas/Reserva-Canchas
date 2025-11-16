"""
Router de Tarifario - Endpoints API
Implementa CRUD completo de tarifas con prioridad y validaciones
"""

from fastapi import APIRouter, Depends, Query, status, Path
from sqlalchemy.orm import Session
from typing import Optional
import logging
import sys
import os

# Ajustar path para imports
sys.path.insert(0, os.path.abspath('.'))
from app.database import get_db

from app.services.tarifario_service import TarifarioService
from app.schemas.tarifario import (
    TarifarioCreate,
    TarifarioUpdate,
    TarifarioResponse,
    TarifarioListResponse,
    ApiResponse,
    ErrorResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/tarifario",
    tags=["Tarifario"],
    responses={
        404: {"model": ErrorResponse, "description": "Tarifa, Sede o Cancha no encontrada"},
        409: {"model": ErrorResponse, "description": "Conflicto de solapamiento"},
        500: {"model": ErrorResponse, "description": "Error interno del servidor"}
    }
)


def get_tarifario_service(db: Session = Depends(get_db)) -> TarifarioService:
    """Dependencia para obtener instancia del servicio"""
    return TarifarioService(db)


@router.post(
    "",
    response_model=ApiResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nueva tarifa",
    description="Crea una nueva tarifa con validación de solapamiento y prioridad"
)
def crear_tarifa(
    tarifa_data: TarifarioCreate,
    service: TarifarioService = Depends(get_tarifario_service)
):
    """
    Crear una nueva tarifa:
    
    - **sede_id**: ID de la sede (obligatorio)
    - **cancha_id**: ID de la cancha (opcional - null = tarifa general de sede)
    - **dia_semana**: Día de la semana (0=Lunes, 6=Domingo)
    - **hora_inicio**: Hora de inicio en formato HH:MM
    - **hora_fin**: Hora de fin en formato HH:MM
    - **precio_por_bloque**: Precio por bloque de tiempo (positivo)
    - **moneda**: Código ISO de moneda (3 letras, ej: COP, USD)
    
    **Validaciones:**
    - No puede haber solapamiento en el mismo nivel (sede o cancha)
    - La cancha debe pertenecer a la sede
    - hora_inicio < hora_fin
    """
    logger.info(f"POST /tarifario - Crear tarifa")
    
    tarifa = service.crear_tarifa(tarifa_data)
    
    return ApiResponse(
        mensaje="Tarifa creada correctamente",
        data=TarifarioResponse.model_validate(tarifa),
        success=True
    )


@router.get(
    "",
    response_model=ApiResponse,
    summary="Listar tarifas",
    description="Obtiene lista de tarifas con filtros opcionales y paginación"
)
def listar_tarifas(
    sede_id: Optional[str] = Query(None, description="Filtrar por sede"),
    cancha_id: Optional[str] = Query(None, description="Filtrar por cancha"),
    dia_semana: Optional[int] = Query(None, ge=0, le=6, description="Filtrar por día (0-6)"),
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(20, ge=1, le=100, description="Tamaño de página"),
    service: TarifarioService = Depends(get_tarifario_service)
):
    """
    Listar tarifas con opciones de filtrado:
    
    - **sede_id**: Filtro por sede
    - **cancha_id**: Filtro por cancha
    - **dia_semana**: Filtro por día de la semana (0-6)
    - **page**: Número de página (default: 1)
    - **page_size**: Elementos por página (default: 20, max: 100)
    
    Las tarifas se ordenan por prioridad (cancha específica primero)
    """
    logger.info(f"GET /tarifario (page={page}, size={page_size})")
    
    tarifas, total = service.listar_tarifas(
        sede_id=sede_id,
        cancha_id=cancha_id,
        dia_semana=dia_semana,
        page=page,
        page_size=page_size
    )
    
    tarifas_response = [TarifarioResponse.model_validate(t) for t in tarifas]
    
    return ApiResponse(
        mensaje=f"Se encontraron {total} tarifa(s)",
        data=TarifarioListResponse(
            total=total,
            tarifas=tarifas_response
        ),
        success=True
    )


@router.get(
    "/{tarifa_id}",
    response_model=ApiResponse,
    summary="Obtener detalle de tarifa",
    description="Obtiene la información completa de una tarifa por su ID"
)
def obtener_tarifa(
    tarifa_id: str = Path(..., description="ID de la tarifa"),
    service: TarifarioService = Depends(get_tarifario_service)
):
    """
    Obtener detalle completo de una tarifa específica.
    
    - **tarifa_id**: UUID de la tarifa
    """
    logger.info(f"GET /tarifario/{tarifa_id}")
    
    tarifa = service.obtener_tarifa(tarifa_id)
    
    return ApiResponse(
        mensaje="Detalle de tarifa",
        data=TarifarioResponse.model_validate(tarifa),
        success=True
    )


@router.get(
    "/consultar/aplicable",
    response_model=ApiResponse,
    summary="Consultar tarifa aplicable",
    description="Obtiene la tarifa aplicable según prioridad cancha > sede"
)
def consultar_tarifa_aplicable(
    sede_id: str = Query(..., description="ID de la sede"),
    cancha_id: str = Query(..., description="ID de la cancha"),
    dia_semana: int = Query(..., ge=0, le=6, description="Día de la semana (0-6)"),
    hora: str = Query(..., description="Hora en formato HH:MM"),
    service: TarifarioService = Depends(get_tarifario_service)
):
    """
    Consultar tarifa aplicable según prioridad:
    
    1. Busca tarifa específica de la cancha
    2. Si no existe, busca tarifa general de la sede
    3. Retorna la tarifa que cubra la hora especificada
    
    - **sede_id**: ID de la sede
    - **cancha_id**: ID de la cancha
    - **dia_semana**: Día de la semana (0-6)
    - **hora**: Hora a consultar (HH:MM)
    """
    logger.info(f"GET /tarifario/consultar/aplicable")
    
    tarifa = service.obtener_tarifa_aplicable(sede_id, cancha_id, dia_semana, hora)
    
    return ApiResponse(
        mensaje="Tarifa aplicable encontrada",
        data=TarifarioResponse.model_validate(tarifa),
        success=True
    )


@router.patch(
    "/{tarifa_id}",
    response_model=ApiResponse,
    summary="Actualizar tarifa",
    description="Actualiza campos específicos de una tarifa existente"
)
def actualizar_tarifa(
    tarifa_id: str = Path(..., description="ID de la tarifa"),
    tarifa_data: TarifarioUpdate = ...,
    service: TarifarioService = Depends(get_tarifario_service)
):
    """
    Actualizar tarifa existente (solo campos proporcionados):
    
    - **dia_semana**: Nuevo día (opcional)
    - **hora_inicio**: Nueva hora de inicio (opcional)
    - **hora_fin**: Nueva hora de fin (opcional)
    - **precio_por_bloque**: Nuevo precio (opcional)
    - **moneda**: Nueva moneda (opcional)
    - **activo**: Estado activo/inactivo (opcional)
    
    **Validaciones:**
    - Si se actualizan franjas, valida que no haya solapamiento
    """
    logger.info(f"PATCH /tarifario/{tarifa_id}")
    
    tarifa = service.actualizar_tarifa(tarifa_id, tarifa_data)
    
    return ApiResponse(
        mensaje="Tarifa actualizada correctamente",
        data=TarifarioResponse.model_validate(tarifa),
        success=True
    )


@router.delete(
    "/{tarifa_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar tarifa",
    description="Elimina una tarifa si no está en uso"
)
def eliminar_tarifa(
    tarifa_id: str = Path(..., description="ID de la tarifa"),
    service: TarifarioService = Depends(get_tarifario_service)
):
    """
    Eliminar tarifa:
    
    - **tarifa_id**: UUID de la tarifa a eliminar
    
    **Nota**: Retorna 409 Conflict si la tarifa está en uso en reservas.
    """
    logger.info(f"DELETE /tarifario/{tarifa_id}")
    
    service.eliminar_tarifa(tarifa_id)
    
    # No retorna contenido (204 No Content)
    return None