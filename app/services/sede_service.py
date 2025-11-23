"""
Servicio de Sedes - Lógica de Negocio
Adaptado para SQLite (UUID como string)
"""

import logging
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.repository.sede_repository import SedeRepository
from app.schemas.sede import SedeCreate, SedeResponse
from app.models.sede import Sede

logger = logging.getLogger(__name__)


class SedeService:
    """Servicio para gestión de sedes"""

    def __init__(self, db: Session):
        self.db = db
        self.repository = SedeRepository(db)

    def crear_sede(self, sede_data: SedeCreate) -> Sede:
        """Crear una nueva sede"""
        # Validar que el nombre no exista
        sede_existente = self.repository.obtener_por_nombre(sede_data.nombre)
        if sede_existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": {
                        "code": "NOMBRE_DUPLICADO",
                        "message": f"Ya existe una sede con el nombre '{sede_data.nombre}'",
                        "details": {
                            "nombre": sede_data.nombre,
                            "sede_existente_id": sede_existente.id,
                        },
                    }
                },
            )

        try:
            sede = self.repository.crear(sede_data)
            logger.info(f"Sede creada exitosamente: {sede.id}")
            return sede

        except IntegrityError as e:
            logger.error(f"Error de integridad al crear sede: {e}")
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
            logger.error(f"Error inesperado al crear sede: {e}")
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

    def obtener_sede(self, sede_id: str) -> Sede:
        """Obtener sede por ID (string UUID)"""
        sede = self.repository.obtener_por_id(sede_id)

        if not sede:
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

        return sede

    # ... resto de métodos igual pero usando str en lugar de UUID

    def listar_sedes(
        self,
        *,
        activo: Optional[bool],
        page: int,
        page_size: int,
    ) -> dict:
        """Listar sedes con paginación y filtro de estado."""
        query = self.db.query(Sede)
        if activo is None:
            query = query.filter(Sede.activo == 1)
        else:
            query = query.filter(Sede.activo == (1 if activo else 0))

        total = query.count()
        sedes = (
            query.order_by(Sede.created_at)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        sedes_payload = []
        for sede in sedes:
            if hasattr(sede, "to_dict"):
                data = sede.to_dict()
            else:
                data = {
                    "sede_id": sede.id,
                    "nombre": sede.nombre,
                    "direccion": sede.direccion,
                    "zona_horaria": sede.zona_horaria,
                    "horario_apertura_json": {},
                    "minutos_buffer": sede.minutos_buffer,
                    "created_at": sede.created_at,
                    "updated_at": sede.updated_at,
                    "activo": bool(sede.activo),
                }
            sedes_payload.append(SedeResponse(**data))

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "sedes": [s.model_dump() for s in sedes_payload],
        }
