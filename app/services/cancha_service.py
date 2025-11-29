"""
Servicio de Canchas - Lógica de Negocio
Maneja validaciones y reglas de negocio
"""

from sqlalchemy.orm import Session
from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
import logging

from app.repository.cancha_repository import CanchaRepository
from app.schemas.cancha import CanchaCreate, CanchaUpdate
from app.models.cancha import Cancha

logger = logging.getLogger(__name__)


class CanchaService:
    """Servicio para gestión de canchas"""

    def __init__(self, db: Session):
        self.db = db
        self.repository = CanchaRepository(db)

    def crear_cancha(self, sede_id: str, cancha_data: CanchaCreate) -> Cancha:
        """
        Crear una nueva cancha en una sede

        Args:
            sede_id: ID de la sede
            cancha_data: Datos de la cancha a crear

        Returns:
            Cancha creada

        Raises:
            HTTPException: Si la sede no existe o hay conflictos
        """
        # Validar que la sede existe
        if not self.repository.verificar_sede_existe(sede_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "SEDE_NO_ENCONTRADA",
                        "message": f"No se encontró la sede con ID {sede_id}",
                        "details": {"sede_id": sede_id},
                    }
                },
            )

        # Validar que el nombre no exista en la sede
        cancha_existente = self.repository.obtener_por_nombre_en_sede(
            sede_id, cancha_data.nombre
        )

        if cancha_existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": {
                        "code": "UNIQUE_VIOLATION",
                        "message": f"Ya existe una cancha con el nombre '{cancha_data.nombre}' en esta sede",
                        "details": {
                            "nombre": cancha_data.nombre,
                            "sede_id": sede_id,
                            "cancha_existente_id": cancha_existente.id,
                        },
                    }
                },
            )

        try:
            cancha = self.repository.crear(sede_id, cancha_data)
            logger.info(f"Cancha creada exitosamente: {cancha.id}")
            return cancha

        except IntegrityError as e:
            logger.error(f"Error de integridad al crear cancha: {e}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": {
                        "code": "ERROR_INTEGRIDAD",
                        "message": "Error de integridad en la base de datos",
                        "details": str(e),
                    }
                },
            )
        except Exception as e:
            logger.error(f"Error inesperado al crear cancha: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": {
                        "code": "ERROR_INTERNO",
                        "message": "Error interno del servidor",
                        "details": str(e),
                    }
                },
            )

    def obtener_cancha(self, cancha_id: str) -> Cancha:
        """Obtener cancha por ID"""
        cancha = self.repository.obtener_por_id(cancha_id)

        if not cancha:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "CANCHA_NO_ENCONTRADA",
                        "message": f"No se encontró la cancha con ID {cancha_id}",
                        "details": {"cancha_id": cancha_id},
                    }
                },
            )

        return cancha

    def listar_canchas_por_sede(
        self,
        sede_id: str,
        estado: Optional[str] = None,
        tipo_superficie: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[Cancha], int]:
        """Listar canchas de una sede con filtros"""

        # Validar que la sede existe
        if not self.repository.verificar_sede_existe(sede_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "SEDE_NO_ENCONTRADA",
                        "message": f"No se encontró la sede con ID {sede_id}",
                        "details": {"sede_id": sede_id},
                    }
                },
            )

        # Validar paginación
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 20

        skip = (page - 1) * page_size

        canchas, total = self.repository.listar_por_sede(
            sede_id=sede_id,
            estado=estado,
            tipo_superficie=tipo_superficie,
            skip=skip,
            limit=page_size,
        )

        return canchas, total

    def actualizar_cancha(self, cancha_id: str, cancha_data: CanchaUpdate) -> Cancha:
        """Actualizar cancha existente"""

        # Verificar que la cancha existe
        cancha_actual = self.obtener_cancha(cancha_id)

        # Si se está actualizando el nombre, verificar que no exista en la sede
        if cancha_data.nombre and cancha_data.nombre != cancha_actual.nombre:
            cancha_con_mismo_nombre = self.repository.obtener_por_nombre_en_sede(
                cancha_actual.sede_id, cancha_data.nombre
            )

            if cancha_con_mismo_nombre:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "error": {
                            "code": "UNIQUE_VIOLATION",
                            "message": f"Ya existe una cancha con el nombre '{cancha_data.nombre}' en esta sede",
                            "details": {"nombre": cancha_data.nombre},
                        }
                    },
                )

        try:
            cancha_actualizada = self.repository.actualizar(cancha_id, cancha_data)
            logger.info(f"Cancha actualizada: {cancha_id}")
            return cancha_actualizada

        except Exception as e:
            logger.error(f"Error al actualizar cancha: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": {
                        "code": "ERROR_ACTUALIZACION",
                        "message": "Error al actualizar la cancha",
                        "details": str(e),
                    }
                },
            )

    def eliminar_cancha(self, cancha_id: str) -> bool:
        """Eliminar cancha (con validación de reservas futuras)"""

        # Verificar que la cancha existe
        self.obtener_cancha(cancha_id)

        # Verificar reservas futuras
        tiene_reservas, count_reservas = self.repository.tiene_reservas_futuras(
            cancha_id
        )

        if tiene_reservas:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": {
                        "code": "CONFLICTO_RELACIONAL",
                        "message": "La cancha tiene reservas futuras",
                        "details": {"reservas_futuras": count_reservas},
                    }
                },
            )

        try:
            resultado = self.repository.eliminar(cancha_id)
            logger.info(f"Cancha eliminada: {cancha_id}")
            return resultado

        except Exception as e:
            logger.error(f"Error al eliminar cancha: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": {
                        "code": "ERROR_ELIMINACION",
                        "message": "Error al eliminar la cancha",
                        "details": str(e),
                    }
                },
            )
