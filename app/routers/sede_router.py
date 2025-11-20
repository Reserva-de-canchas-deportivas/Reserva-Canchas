"""
Router de Sedes - Endpoints API
Adaptado para SQLite (UUID como string)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.database import get_db  
from app.services.sede_service import SedeService
from app.schemas.sede import (
    SedeCreate,
    SedeUpdate,
    SedeResponse,
    SedeListResponse,
    ApiResponse,
    ErrorResponse
)
from app.services.rbac import require_role_dependency

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/sedes",
    tags=["Sedes"],
    responses={
        404: {"model": ErrorResponse, "description": "Sede no encontrada"},
        409: {"model": ErrorResponse, "description": "Conflicto de integridad"},
        500: {"model": ErrorResponse, "description": "Error interno del servidor"}
    }
)

ALL_ROLES = ("admin", "personal", "cliente")
ANY_ROLE_DEP = require_role_dependency(*ALL_ROLES)
ADMIN_PERSONAL_DEP = require_role_dependency("admin", "personal")
ADMIN_ONLY_DEP = require_role_dependency("admin")


def get_sede_service(db: Session = Depends(get_db)) -> SedeService:
    """Dependencia para obtener instancia del servicio"""
    return SedeService(db)


@router.post(
    "/",
    response_model=ApiResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nueva sede",
    description="""
    Crea una nueva sede deportiva con validación de:
    - Nombre único (3-200 caracteres)
    - Dirección física (10-500 caracteres)
    - Zona horaria IANA válida (ej: America/Bogota)
    - Horarios por día en formato HH:MM-HH:MM
    - Buffer entre reservas (0-60 minutos)
    """,
    dependencies=[Depends(ADMIN_PERSONAL_DEP)],
)
async def crear_sede(
    sede: SedeCreate,
    service: SedeService = Depends(get_sede_service)
) -> ApiResponse:
    """Crear nueva sede."""
    logger.info("POST /sedes - Creando nueva sede")
    
    try:
        nueva_sede = service.crear_sede(sede)
        return ApiResponse(
            mensaje="Sede creada exitosamente",
            data=SedeResponse.model_validate(nueva_sede),
            success=True
        )
    except ValueError as e:
        logger.error(f"Error de validación: {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": str(e)}
        )
    except Exception as e:
        logger.error(f"Error interno: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": f"Error al crear sede: {str(e)}"}
        )


@router.get(
    "/",
    response_model=ApiResponse,
    summary="Listar sedes",
    description="""
    Obtiene lista de sedes con filtros opcionales y paginación.
    """,
    dependencies=[Depends(ANY_ROLE_DEP)],
)
async def listar_sedes(
    activo: Optional[bool] = Query(None, description="Filtrar por estado activo"),
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(20, ge=1, le=100, description="Resultados por página"),
    service: SedeService = Depends(get_sede_service)
) -> ApiResponse:
    """Listar todas las sedes con paginación."""
    logger.info(f"GET /sedes - page={page}, page_size={page_size}, activo={activo}")
    
    try:
        resultado = service.listar_sedes(
            activo=activo,
            page=page,
            page_size=page_size
        )
        
        return ApiResponse(
            mensaje=f"Se encontraron {resultado['total']} sede(s)",
            data=resultado,
            success=True
        )
    except Exception as e:
        logger.error(f"Error al listar sedes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": f"Error al listar sedes: {str(e)}"}
        )


@router.get(
    "/{sede_id}",
    response_model=ApiResponse,
    summary="Obtener detalle de sede",
    dependencies=[Depends(ANY_ROLE_DEP)],
)
async def obtener_sede(
    sede_id: str = Path(..., description="ID de la sede"),
    service: SedeService = Depends(get_sede_service)
) -> ApiResponse:
    """Obtener detalle completo de una sede específica"""
    logger.info(f"GET /sedes/{sede_id}")
    
    try:
        sede = service.obtener_sede(sede_id)
        return ApiResponse(
            mensaje="Detalle de sede",
            data=SedeResponse.model_validate(sede),
            success=True
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": str(e)}
        )
    except Exception as e:
        logger.error(f"Error al obtener sede: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": f"Error al obtener sede: {str(e)}"}
        )


@router.patch(
    "/{sede_id}",
    response_model=ApiResponse,
    summary="Actualizar sede",
    description="""
    Actualiza campos específicos de una sede existente.
    Solo se actualizan los campos proporcionados.
    """,
    dependencies=[Depends(ADMIN_PERSONAL_DEP)],
)
async def actualizar_sede(
    sede_id: str = Path(..., description="ID de la sede"),
    sede_data: SedeUpdate = Body(...),
    service: SedeService = Depends(get_sede_service)
) -> ApiResponse:
    """Actualizar sede por ID."""
    logger.info(f"PATCH /sedes/{sede_id}")
    
    try:
        sede_actualizada = service.actualizar_sede(sede_id, sede_data)
        return ApiResponse(
            mensaje="Sede actualizada exitosamente",
            data=SedeResponse.model_validate(sede_actualizada),
            success=True
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": str(e)}
        )
    except Exception as e:
        logger.error(f"Error al actualizar sede: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": f"Error al actualizar sede: {str(e)}"}
        )


@router.delete(
    "/{sede_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar sede",
    description="""
    Elimina una sede si no tiene canchas o reservas asociadas.
    """,
    dependencies=[Depends(ADMIN_ONLY_DEP)],
)
async def eliminar_sede(
    sede_id: str = Path(..., description="ID de la sede"),
    service: SedeService = Depends(get_sede_service)
):
    """Eliminar sede"""
    logger.info(f"DELETE /sedes/{sede_id}")
    
    try:
        service.eliminar_sede(sede_id)
        return None
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": str(e)}
        )
    except Exception as e:
        logger.error(f"Error al eliminar sede: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": f"Error al eliminar sede: {str(e)}"}
        )
    
