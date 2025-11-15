"""
Repositorio para operaciones de base de datos de Cancha
Capa de acceso a datos
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional
import logging
from datetime import datetime

from app.models.cancha import Cancha
from app.schemas.cancha import CanchaCreate, CanchaUpdate

logger = logging.getLogger(__name__)


class CanchaRepository:
    """Repositorio para gestionar canchas en la base de datos"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def crear(self, sede_id: str, cancha_data: CanchaCreate) -> Cancha:
        """Crear una nueva cancha en la base de datos"""
        try:
            cancha = Cancha(
                sede_id=sede_id,
                nombre=cancha_data.nombre,
                tipo_superficie=cancha_data.tipo_superficie.value,
                estado=cancha_data.estado.value
            )
            
            self.db.add(cancha)
            self.db.commit()
            self.db.refresh(cancha)
            
            logger.info(f"Cancha creada: {cancha.id} - {cancha.nombre}")
            return cancha
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error al crear cancha: {e}")
            raise
    
    def obtener_por_id(self, cancha_id: str) -> Optional[Cancha]:
        """Obtener cancha por ID"""
        return self.db.query(Cancha).filter(
            Cancha.id == cancha_id,
            Cancha.activo == 1
        ).first()
    
    def obtener_por_nombre_en_sede(self, sede_id: str, nombre: str) -> Optional[Cancha]:
        """Obtener cancha por nombre en una sede específica"""
        return self.db.query(Cancha).filter(
            and_(
                Cancha.sede_id == sede_id,
                Cancha.nombre == nombre,
                Cancha.activo == 1
            )
        ).first()
    
    def listar_por_sede(
        self,
        sede_id: str,
        estado: Optional[str] = None,
        tipo_superficie: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Cancha], int]:
        """
        Listar canchas de una sede con filtros
        
        Returns:
            Tupla (lista de canchas, total de registros)
        """
        query = self.db.query(Cancha).filter(
            Cancha.sede_id == sede_id,
            Cancha.activo == 1
        )
        
        # Aplicar filtros
        if estado:
            query = query.filter(Cancha.estado == estado)
        
        if tipo_superficie:
            query = query.filter(Cancha.tipo_superficie == tipo_superficie)
        
        # Contar total
        total = query.count()
        
        # Aplicar paginación
        canchas = query.offset(skip).limit(limit).all()
        
        return canchas, total
    
    def actualizar(self, cancha_id: str, cancha_data: CanchaUpdate) -> Optional[Cancha]:
        """Actualizar cancha existente"""
        cancha = self.obtener_por_id(cancha_id)
        
        if not cancha:
            return None
        
        # Actualizar solo campos proporcionados
        update_data = cancha_data.model_dump(exclude_unset=True)
        
        for campo, valor in update_data.items():
            if campo == 'activo':
                setattr(cancha, campo, 1 if valor else 0)
            elif campo in ['tipo_superficie', 'estado']:
                # Obtener el valor del Enum
                setattr(cancha, campo, valor.value if hasattr(valor, 'value') else valor)
            else:
                setattr(cancha, campo, valor)
        
        # Actualizar timestamp
        cancha.updated_at = datetime.utcnow().isoformat()
        
        try:
            self.db.commit()
            self.db.refresh(cancha)
            logger.info(f"Cancha actualizada: {cancha.id}")
            return cancha
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error al actualizar cancha: {e}")
            raise
    
    def eliminar(self, cancha_id: str) -> bool:
        """Eliminar cancha (soft delete)"""
        cancha = self.obtener_por_id(cancha_id)
        
        if not cancha:
            return False
        
        try:
            cancha.activo = 0
            self.db.commit()
            logger.info(f"Cancha eliminada (soft delete): {cancha.id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error al eliminar cancha: {e}")
            raise
    
    def tiene_reservas_futuras(self, cancha_id: str) -> tuple[bool, int]:
        """
        Verificar si la cancha tiene reservas futuras
        
        Returns:
            Tupla (tiene_reservas, cantidad)
        """
        # TODO: Implementar cuando tengas el modelo Reserva
        # from app.models.reserva import Reserva
        # from datetime import datetime
        # 
        # count = self.db.query(func.count(Reserva.id)).filter(
        #     Reserva.cancha_id == cancha_id,
        #     Reserva.fecha_hora_inicio >= datetime.utcnow(),
        #     Reserva.activo == 1
        # ).scalar()
        # 
        # return count > 0, count
        
        # Por ahora retornar False (no tiene reservas)
        return False, 0
    
    def verificar_sede_existe(self, sede_id: str) -> bool:
        """Verificar que la sede existe"""
        from app.models.sede import Sede
        
        sede = self.db.query(Sede).filter(
            Sede.id == sede_id,
            Sede.activo == 1
        ).first()
        
        return sede is not None