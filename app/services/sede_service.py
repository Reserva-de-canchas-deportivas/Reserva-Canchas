"""
Servicio de Sedes - Lógica de Negocio
Adaptado para SQLite (UUID como string)
"""

from sqlalchemy.orm import Session
from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
import logging

from app.repository.sede_repository import SedeRepository
from app.schemas.sede import SedeCreate, SedeUpdate, SedeResponse
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
                            "sede_existente_id": sede_existente.id
                        }
                    }
                }
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
                        "details": str(e)
                    }
                }
            )
        except Exception as e:
            logger.error(f"Error inesperado al crear sede: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": {
                        "code": "ERROR_INTERNO",
                        "message": "Error interno del servidor",
                        "details": str(e)
                    }
                }
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
                        "details": {"sede_id": sede_id}
                    }
                }
            )
        
        return sede
    
    # ... resto de métodos igual pero usando str en lugar de UUID