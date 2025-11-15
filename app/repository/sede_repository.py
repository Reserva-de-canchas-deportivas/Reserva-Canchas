"""
Repositorio para operaciones de base de datos de Sede
Adaptado para SQLite
"""

from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List, Optional
import logging
import json

from app.models.sede import Sede
from app.schemas.sede import SedeCreate, SedeUpdate

logger = logging.getLogger(__name__)


class SedeRepository:
    """Repositorio para gestionar sedes en la base de datos"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def crear(self, sede_data: SedeCreate) -> Sede:
        """Crear una nueva sede en la base de datos"""
        try:
            # Serializar JSON a string para SQLite
            horarios_json = json.dumps(sede_data.horario_apertura_json)
            
            sede = Sede(
                nombre=sede_data.nombre,
                direccion=sede_data.direccion,
                zona_horaria=sede_data.zona_horaria,
                horario_apertura_json=horarios_json,  # String JSON
                minutos_buffer=sede_data.minutos_buffer
            )
            
            self.db.add(sede)
            self.db.commit()
            self.db.refresh(sede)
            
            logger.info(f"Sede creada: {sede.id} - {sede.nombre}")
            return sede
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error al crear sede: {e}")
            raise
    
    def obtener_por_id(self, sede_id: str) -> Optional[Sede]:
        """Obtener sede por ID (UUID como string)"""
        return self.db.query(Sede).filter(
            Sede.id == sede_id,
            Sede.activo == 1
        ).first()
    
    def obtener_por_nombre(self, nombre: str) -> Optional[Sede]:
        """Obtener sede por nombre exacto"""
        return self.db.query(Sede).filter(
            Sede.nombre == nombre,
            Sede.activo == 1
        ).first()
    
    def listar(
        self,
        nombre: Optional[str] = None,
        zona_horaria: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Sede], int]:
        """Listar sedes con filtros y paginación"""
        query = self.db.query(Sede).filter(Sede.activo == 1)
        
        # Aplicar filtros
        if nombre:
            query = query.filter(
                Sede.nombre.like(f"%{nombre}%")  # LIKE en SQLite
            )
        
        if zona_horaria:
            query = query.filter(
                Sede.zona_horaria == zona_horaria
            )
        
        # Contar total
        total = query.count()
        
        # Aplicar paginación
        sedes = query.offset(skip).limit(limit).all()
        
        return sedes, total
    
    def actualizar(self, sede_id: str, sede_data: SedeUpdate) -> Optional[Sede]:
        """Actualizar sede existente"""
        sede = self.obtener_por_id(sede_id)
        
        if not sede:
            return None
        
        # Actualizar solo campos proporcionados
        update_data = sede_data.model_dump(exclude_unset=True)
        
        for campo, valor in update_data.items():
            if campo == 'activo':
                setattr(sede, campo, 1 if valor else 0)
            elif campo == 'horario_apertura_json':
                # Serializar a JSON string
                setattr(sede, campo, json.dumps(valor))
            else:
                setattr(sede, campo, valor)
        
        # Actualizar timestamp
        sede.updated_at = datetime.utcnow().isoformat()
        
        try:
            self.db.commit()
            self.db.refresh(sede)
            logger.info(f"Sede actualizada: {sede.id}")
            return sede
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error al actualizar sede: {e}")
            raise
    
    def eliminar(self, sede_id: str) -> bool:
        """Eliminar sede (soft delete)"""
        sede = self.obtener_por_id(sede_id)
        
        if not sede:
            return False
        
        try:
            sede.activo = 0
            self.db.commit()
            logger.info(f"Sede eliminada (soft delete): {sede.id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error al eliminar sede: {e}")
            raise
    
    def tiene_canchas_asociadas(self, sede_id: str) -> tuple[bool, int]:
        """Verificar si la sede tiene canchas asociadas"""
        # TODO: Implementar cuando tengas el modelo Cancha
        return False, 0
    
    def tiene_reservas_asociadas(self, sede_id: str) -> tuple[bool, int]:
        """Verificar si la sede tiene reservas asociadas"""
        # TODO: Implementar cuando tengas el modelo Reserva
        return False, 0