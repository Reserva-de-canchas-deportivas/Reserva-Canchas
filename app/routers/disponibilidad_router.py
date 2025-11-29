"""
Router de Disponibilidad - Endpoint API
Consulta de disponibilidad de canchas
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
import logging
import sys
import os

# Ajustar path para imports
sys.path.insert(0, os.path.abspath("."))
from app.database import get_db

from app.services.disponibilidad_service import DisponibilidadService
from app.schemas.disponibilidad import (
    DisponibilidadQuery,
    ApiResponse,
    ErrorResponse,
)
from app.services.rbac import require_role_dependency

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/disponibilidad",
    tags=["Disponibilidad"],
    responses={
        404: {"model": ErrorResponse, "description": "Sede o Cancha no encontrada"},
        400: {"model": ErrorResponse, "description": "Parámetros inválidos"},
        500: {"model": ErrorResponse, "description": "Error interno del servidor"},
    },
)

ALL_ROLES = ("admin", "personal", "cliente")
ANY_ROLE_DEP = require_role_dependency(*ALL_ROLES)


def get_disponibilidad_service(db: Session = Depends(get_db)) -> DisponibilidadService:
    """Dependencia para obtener instancia del servicio"""
    return DisponibilidadService(db)


@router.get(
    "",
    response_model=ApiResponse,
    summary="Consultar disponibilidad de cancha",
    description="Calcula disponibilidad considerando zona horaria, horarios de apertura y buffer",
)
def consultar_disponibilidad(
    fecha: str = Query(
        ..., description="Fecha a consultar (YYYY-MM-DD)", example="2025-07-31"
    ),
    sede_id: str = Query(..., description="ID de la sede", example="abc123-..."),
    cancha_id: str = Query(..., description="ID de la cancha", example="xyz789-..."),
    duracion_slot: int = Query(
        default=60,
        ge=15,
        le=240,
        description="Duración de cada slot en minutos (15-240)",
    ),
    service: DisponibilidadService = Depends(get_disponibilidad_service),
    _: object = Depends(ANY_ROLE_DEP),
):
    """
    Consultar disponibilidad de una cancha en una fecha específica.

    El cálculo considera:
    - **Zona horaria** de la sede para conversión correcta de fechas
    - **Horario de apertura** configurado para el día de la semana
    - **Minutos de buffer** entre reservas
    - **Reservas existentes** en estados: hold, pending, confirmed

    Parámetros:
    - **fecha**: Fecha a consultar (YYYY-MM-DD). No puede ser pasada ni más de 90 días en el futuro
    - **sede_id**: UUID de la sede
    - **cancha_id**: UUID de la cancha (debe pertenecer a la sede)
    - **duracion_slot**: Duración de cada slot en minutos (default: 60, rango: 15-240)

    Retorna:
    - Lista de slots con horarios y disponibilidad
    - Información de la sede y cancha
    - Estadísticas de ocupación

    Casos especiales:
    - Si la sede está cerrada ese día: retorna slots vacíos con dia_cerrado=true
    - Si no hay reservas: todos los slots del horario de apertura están disponibles
    """
    logger.info(
        f"GET /disponibilidad - Consulta: fecha={fecha}, "
        f"sede={sede_id}, cancha={cancha_id}, slot={duracion_slot}min"
    )

    try:
        query_params = DisponibilidadQuery(
            fecha=fecha,
            sede_id=sede_id,
            cancha_id=cancha_id,
            duracion_slot=duracion_slot,
        )
        disponibilidad = service.calcular_disponibilidad(query_params)
    except ValueError as e:
        logger.error(f"Error de validación en disponibilidad: {e}")
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "VALIDATION_ERROR", "message": str(e)}},
        )
    except HTTPException as exc:
        raise exc
    except Exception as e:
        logger.exception("Error interno al calcular disponibilidad")
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "INTERNAL_ERROR", "message": str(e)}},
        )

    # Determinar mensaje apropiado
    if disponibilidad.dia_cerrado:
        mensaje = f"La sede está cerrada el día {fecha}"
    elif disponibilidad.slots_disponibles == 0:
        mensaje = "No hay slots disponibles para la fecha seleccionada"
    elif disponibilidad.slots_disponibles == disponibilidad.total_slots:
        mensaje = "Todos los slots están disponibles"
    else:
        mensaje = (
            f"Disponibilidad calculada: {disponibilidad.slots_disponibles} "
            f"de {disponibilidad.total_slots} slots disponibles"
        )

    return ApiResponse(mensaje=mensaje, data=disponibilidad, success=True)
