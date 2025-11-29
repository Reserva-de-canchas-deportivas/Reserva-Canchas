"""
Router de Canchas - Endpoints API
Implementa CRUD completo de canchas por sede
"""

from fastapi import APIRouter, Depends, Query, status, Path
from sqlalchemy.orm import Session
from typing import Optional
import logging
import sys
import os

# Ajustar path para imports
sys.path.insert(0, os.path.abspath("."))  # ← LÍNEA CORREGIDA
from app.database import get_db

from app.services.cancha_service import CanchaService
from app.schemas.cancha import (
    CanchaCreate,
    CanchaUpdate,
    CanchaResponse,
    CanchaListResponse,
    ApiResponse,
    ErrorResponse,
    EstadoCancha,
    TipoSuperficie,
)
from app.services.rbac import require_role_dependency

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1",
    tags=["Canchas"],
    responses={
        404: {"model": ErrorResponse, "description": "Cancha o Sede no encontrada"},
        409: {"model": ErrorResponse, "description": "Conflicto de integridad"},
        500: {"model": ErrorResponse, "description": "Error interno del servidor"},
    },
)

ALL_ROLES = ("admin", "personal", "cliente")
ANY_ROLE_DEP = require_role_dependency(*ALL_ROLES)
ADMIN_PERSONAL_DEP = require_role_dependency("admin", "personal")
ADMIN_ONLY_DEP = require_role_dependency("admin")


def get_cancha_service(db: Session = Depends(get_db)) -> CanchaService:
    """Dependencia para obtener instancia del servicio"""
    return CanchaService(db)


def _serialize_cancha(cancha) -> CanchaResponse:
    if hasattr(cancha, "to_dict"):
        return CanchaResponse.model_validate(cancha.to_dict())
    return CanchaResponse(
        cancha_id=getattr(cancha, "id"),
        sede_id=getattr(cancha, "sede_id"),
        nombre=getattr(cancha, "nombre"),
        tipo_superficie=getattr(cancha, "tipo_superficie"),
        estado=getattr(cancha, "estado"),
        created_at=getattr(cancha, "created_at"),
        updated_at=getattr(cancha, "updated_at"),
        activo=bool(getattr(cancha, "activo", True)),
    )


@router.post(
    "/sedes/{sede_id}/canchas/",
    response_model=ApiResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nueva cancha en una sede",
    description="Crea una nueva cancha deportiva asociada a una sede específica",
)
def crear_cancha(
    sede_id: str = Path(..., description="ID de la sede"),
    cancha_data: CanchaCreate = ...,
    service: CanchaService = Depends(get_cancha_service),
    _: object = Depends(ADMIN_PERSONAL_DEP),
):
    """
    Crear una nueva cancha en una sede:

    - **sede_id**: ID de la sede donde se creará la cancha
    - **nombre**: Nombre único de la cancha (dentro de la sede)
    - **tipo_superficie**: césped, sintético, cemento o madera
    - **estado**: activo o mantenimiento (default: activo)
    """
    logger.info(f"POST /sedes/{sede_id}/canchas - Crear cancha: {cancha_data.nombre}")

    cancha = service.crear_cancha(sede_id, cancha_data)

    return ApiResponse(
        mensaje="Cancha creada correctamente",
        data=_serialize_cancha(cancha),
        success=True,
    )


@router.get(
    "/sedes/{sede_id}/canchas/",
    response_model=ApiResponse,
    summary="Listar canchas de una sede",
    description="Obtiene la lista de canchas de una sede con filtros opcionales",
)
def listar_canchas_por_sede(
    sede_id: str = Path(..., description="ID de la sede"),
    estado: Optional[EstadoCancha] = Query(None, description="Filtrar por estado"),
    tipo_superficie: Optional[TipoSuperficie] = Query(
        None, description="Filtrar por tipo de superficie"
    ),
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(20, ge=1, le=100, description="Tamaño de página"),
    service: CanchaService = Depends(get_cancha_service),
    _: object = Depends(ANY_ROLE_DEP),
):
    """
    Listar canchas de una sede con opciones de filtrado:

    - **sede_id**: ID de la sede
    - **estado**: Filtro por estado (activo, mantenimiento)
    - **tipo_superficie**: Filtro por tipo de superficie
    - **page**: Número de página (default: 1)
    - **page_size**: Elementos por página (default: 20, max: 100)
    """
    logger.info(f"GET /sedes/{sede_id}/canchas (page={page}, size={page_size})")

    # Convertir enums a strings si existen
    estado_str = estado.value if estado else None
    tipo_str = tipo_superficie.value if tipo_superficie else None

    canchas, total = service.listar_canchas_por_sede(
        sede_id=sede_id,
        estado=estado_str,
        tipo_superficie=tipo_str,
        page=page,
        page_size=page_size,
    )

    canchas_response = [_serialize_cancha(cancha) for cancha in canchas]

    return ApiResponse(
        mensaje=f"Se encontraron {total} cancha(s) en la sede",
        data=CanchaListResponse(total=total, canchas=canchas_response),
        success=True,
    )


@router.get(
    "/canchas/{cancha_id}",
    response_model=ApiResponse,
    summary="Obtener detalle de cancha",
    description="Obtiene la información completa de una cancha por su ID",
)
def obtener_cancha(
    cancha_id: str = Path(..., description="ID de la cancha"),
    service: CanchaService = Depends(get_cancha_service),
    _: object = Depends(ANY_ROLE_DEP),
):
    """
    Obtener detalle completo de una cancha específica.

    - **cancha_id**: UUID de la cancha
    """
    logger.info(f"GET /canchas/{cancha_id}")

    cancha = service.obtener_cancha(cancha_id)

    return ApiResponse(
        mensaje="Detalle de cancha", data=_serialize_cancha(cancha), success=True
    )


@router.patch(
    "/canchas/{cancha_id}",
    response_model=ApiResponse,
    summary="Actualizar cancha",
    description="Actualiza campos específicos de una cancha existente",
)
def actualizar_cancha(
    cancha_id: str = Path(..., description="ID de la cancha"),
    cancha_data: CanchaUpdate = ...,
    service: CanchaService = Depends(get_cancha_service),
    _: object = Depends(ADMIN_PERSONAL_DEP),
):
    """
    Actualizar cancha existente (solo campos proporcionados):

    - **nombre**: Nuevo nombre (opcional)
    - **tipo_superficie**: Nuevo tipo de superficie (opcional)
    - **estado**: Nuevo estado (opcional) - útil para marcar en mantenimiento
    - **activo**: Estado activo/inactivo (opcional)
    """
    logger.info(f"PATCH /canchas/{cancha_id}")

    cancha = service.actualizar_cancha(cancha_id, cancha_data)

    return ApiResponse(
        mensaje="Cancha actualizada correctamente",
        data=_serialize_cancha(cancha),
        success=True,
    )


@router.delete(
    "/canchas/{cancha_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar cancha",
    description="Elimina una cancha si no tiene reservas futuras asociadas",
)
def eliminar_cancha(
    cancha_id: str = Path(..., description="ID de la cancha"),
    service: CanchaService = Depends(get_cancha_service),
    _: object = Depends(ADMIN_ONLY_DEP),
):
    """
    Eliminar cancha (solo si no tiene reservas futuras):

    - **cancha_id**: UUID de la cancha a eliminar

    **Nota**: Retorna 409 Conflict si la cancha tiene reservas futuras.
    """
    logger.info(f"DELETE /canchas/{cancha_id}")

    service.eliminar_cancha(cancha_id)

    # No retorna contenido (204 No Content)
    return None
