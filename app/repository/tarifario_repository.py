"""
Repositorio para operaciones de base de datos de Tarifario
Capa de acceso a datos con validación de solapamiento
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional, Tuple
import logging
from datetime import datetime

from app.models.tarifario import Tarifario
from app.schemas.tarifario import TarifarioCreate, TarifarioUpdate

logger = logging.getLogger(__name__)


class TarifarioRepository:
    """Repositorio para gestionar tarifas en la base de datos"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def crear(self, tarifa_data: TarifarioCreate) -> Tarifario:
        """Crear una nueva tarifa en la base de datos"""
        try:
            tarifa = Tarifario(
                sede_id=tarifa_data.sede_id,
                cancha_id=tarifa_data.cancha_id,
                dia_semana=tarifa_data.dia_semana,
                hora_inicio=tarifa_data.hora_inicio,
                hora_fin=tarifa_data.hora_fin,
                precio_por_bloque=tarifa_data.precio_por_bloque,
                moneda=tarifa_data.moneda
            )
            
            self.db.add(tarifa)
            self.db.commit()
            self.db.refresh(tarifa)
            
            logger.info(f"Tarifa creada: {tarifa.id}")
            return tarifa
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error al crear tarifa: {e}")
            raise
    
    def obtener_por_id(self, tarifa_id: str) -> Optional[Tarifario]:
        """Obtener tarifa por ID"""
        return self.db.query(Tarifario).filter(
            Tarifario.id == tarifa_id,
            Tarifario.activo == 1
        ).first()
    
    def verificar_solapamiento(
        self,
        sede_id: str,
        cancha_id: Optional[str],
        dia_semana: int,
        hora_inicio: str,
        hora_fin: str,
        excluir_tarifa_id: Optional[str] = None
    ) -> Tuple[bool, Optional[Tarifario]]:
        """
        Verificar si existe solapamiento de franjas horarias
        
        Dos franjas se solapan si:
        1. Son del mismo día
        2. Son del mismo nivel de especificidad (ambas de cancha o ambas de sede)
        3. Los rangos de hora se cruzan: nueva_inicio < existente_fin AND nueva_fin > existente_inicio
        
        Args:
            sede_id: ID de la sede
            cancha_id: ID de la cancha (None para tarifa de sede)
            dia_semana: Día de la semana (0-6)
            hora_inicio: Hora de inicio (HH:MM)
            hora_fin: Hora de fin (HH:MM)
            excluir_tarifa_id: ID de tarifa a excluir (para updates)
            
        Returns:
            Tupla (hay_solapamiento, tarifa_solapada)
        """
        query = self.db.query(Tarifario).filter(
            Tarifario.sede_id == sede_id,
            Tarifario.dia_semana == dia_semana,
            Tarifario.activo == 1
        )
        
        # Mismo nivel de especificidad
        if cancha_id:
            # Buscar solapamientos en la misma cancha
            query = query.filter(Tarifario.cancha_id == cancha_id)
        else:
            # Buscar solapamientos en tarifas generales de sede
            query = query.filter(Tarifario.cancha_id.is_(None))
        
        # Excluir la tarifa actual si es un update
        if excluir_tarifa_id:
            query = query.filter(Tarifario.id != excluir_tarifa_id)
        
        # Validar solapamiento de rangos de hora
        # Dos rangos se solapan si: nueva_inicio < existente_fin AND nueva_fin > existente_inicio
        # Pero NO se solapan si son contiguos exactos (18:00-20:00 y 20:00-22:00 NO solapan)
        query = query.filter(
            and_(
                Tarifario.hora_inicio < hora_fin,    # inicio_existente < fin_nueva
                Tarifario.hora_fin > hora_inicio      # fin_existente > inicio_nueva
            )
        )
        
        tarifa_solapada = query.first()
        
        if tarifa_solapada:
            logger.warning(
                f"Solapamiento detectado: Nueva tarifa ({hora_inicio}-{hora_fin}) "
                f"se cruza con tarifa existente {tarifa_solapada.id} "
                f"({tarifa_solapada.hora_inicio}-{tarifa_solapada.hora_fin})"
            )
            return True, tarifa_solapada
        
        return False, None
    
    def listar(
        self,
        sede_id: Optional[str] = None,
        cancha_id: Optional[str] = None,
        dia_semana: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Tarifario], int]:
        """
        Listar tarifas con filtros
        
        Returns:
            Tupla (lista de tarifas, total de registros)
        """
        query = self.db.query(Tarifario).filter(Tarifario.activo == 1)
        
        # Aplicar filtros
        if sede_id:
            query = query.filter(Tarifario.sede_id == sede_id)
        
        if cancha_id:
            query = query.filter(Tarifario.cancha_id == cancha_id)
        
        if dia_semana is not None:
            query = query.filter(Tarifario.dia_semana == dia_semana)
        
        # Ordenar por prioridad: cancha específica primero, luego sede general
        query = query.order_by(
            Tarifario.cancha_id.isnot(None).desc(),  # Canchas primero
            Tarifario.dia_semana,
            Tarifario.hora_inicio
        )
        
        # Contar total
        total = query.count()
        
        # Aplicar paginación
        tarifas = query.offset(skip).limit(limit).all()
        
        return tarifas, total
    
    def obtener_tarifa_aplicable(
        self,
        sede_id: str,
        cancha_id: Optional[str],
        dia_semana: int,
        hora: str
    ) -> Optional[Tarifario]:
        """
        Obtener la tarifa aplicable según prioridad cancha > sede
        """
        tarifa_cancha = None
        if cancha_id:
            tarifa_cancha = self.db.query(Tarifario).filter(
                Tarifario.cancha_id == cancha_id,
                Tarifario.dia_semana == dia_semana,
                Tarifario.hora_inicio <= hora,
                Tarifario.hora_fin > hora,
                Tarifario.activo == 1
            ).first()
        
        if tarifa_cancha:
            logger.info(f"Tarifa específica de cancha encontrada: {tarifa_cancha.id}")
            return tarifa_cancha
        
        tarifa_sede = self.db.query(Tarifario).filter(
            Tarifario.sede_id == sede_id,
            Tarifario.cancha_id.is_(None),
            Tarifario.dia_semana == dia_semana,
            Tarifario.hora_inicio <= hora,
            Tarifario.hora_fin > hora,
            Tarifario.activo == 1
        ).first()
        
        if tarifa_sede:
            logger.info(f"Tarifa general de sede encontrada: {tarifa_sede.id}")
            return tarifa_sede
        
        logger.warning(
            f"No se encontró tarifa aplicable para sede {sede_id}, cancha {cancha_id}, día {dia_semana}, hora {hora}"
        )
        return None
    
    def actualizar(self, tarifa_id: str, tarifa_data: TarifarioUpdate) -> Optional[Tarifario]:
        """Actualizar tarifa existente"""
        tarifa = self.obtener_por_id(tarifa_id)
        
        if not tarifa:
            return None
        
        # Actualizar solo campos proporcionados
        update_data = tarifa_data.model_dump(exclude_unset=True)
        
        for campo, valor in update_data.items():
            if campo == 'activo':
                setattr(tarifa, campo, 1 if valor else 0)
            else:
                setattr(tarifa, campo, valor)
        
        # Actualizar timestamp
        tarifa.updated_at = datetime.utcnow().isoformat()
        
        try:
            self.db.commit()
            self.db.refresh(tarifa)
            logger.info(f"Tarifa actualizada: {tarifa.id}")
            return tarifa
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error al actualizar tarifa: {e}")
            raise
    
    def eliminar(self, tarifa_id: str) -> bool:
        """Eliminar tarifa (soft delete)"""
        tarifa = self.obtener_por_id(tarifa_id)
        
        if not tarifa:
            return False
        
        try:
            tarifa.activo = 0
            self.db.commit()
            logger.info(f"Tarifa eliminada (soft delete): {tarifa.id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error al eliminar tarifa: {e}")
            raise
    
    def verificar_sede_existe(self, sede_id: str) -> bool:
        """Verificar que la sede existe"""
        from app.models.sede import Sede
        
        sede = self.db.query(Sede).filter(
            Sede.id == sede_id,
            Sede.activo == 1
        ).first()
        
        return sede is not None
    
    def verificar_cancha_existe(self, cancha_id: str) -> bool:
        """Verificar que la cancha existe"""
        from app.models.cancha import Cancha
        
        cancha = self.db.query(Cancha).filter(
            Cancha.id == cancha_id,
            Cancha.activo == 1
        ).first()
        
        return cancha is not None
    
    def verificar_cancha_pertenece_sede(self, cancha_id: str, sede_id: str) -> bool:
        """Verificar que la cancha pertenece a la sede indicada"""
        from app.models.cancha import Cancha
        
        cancha = self.db.query(Cancha).filter(
            Cancha.id == cancha_id,
            Cancha.sede_id == sede_id,
            Cancha.activo == 1
        ).first()
        
        return cancha is not None


def seed_tarifas_demo(db: Session, sede_id: str, cancha_id: Optional[str]) -> None:
    """Crear una tarifa de sede y una específica de cancha si no existen registros."""
    if db.query(Tarifario).count() > 0:
        return

    tarifa_sede = Tarifario(
        sede_id=sede_id,
        cancha_id=None,
        dia_semana=3,
        hora_inicio="18:00",
        hora_fin="22:00",
        precio_por_bloque=120000,
        moneda="COP",
    )
    db.add(tarifa_sede)

    if cancha_id:
        tarifa_cancha = Tarifario(
            sede_id=sede_id,
            cancha_id=cancha_id,
            dia_semana=3,
            hora_inicio="18:00",
            hora_fin="20:00",
            precio_por_bloque=150000,
            moneda="COP",
        )
        db.add(tarifa_cancha)

    db.commit()
    logging.getLogger(__name__).info("Tarifas demo sembradas para sede %s", sede_id)
