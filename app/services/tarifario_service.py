"""
Servicio de Tarifario - Lógica de Negocio
Maneja validaciones y reglas de negocio complejas
"""

from sqlalchemy.orm import Session
from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
import logging
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.repository.tarifario_repository import TarifarioRepository
from app.schemas.tarifario import (
    TarifarioCreate,
    TarifarioUpdate,
    TarifarioResponse,
    TarifaResolverData,
)
from app.models.tarifario import Tarifario
from app.models.sede import Sede
from app.models.cancha import Cancha
from app.services.cache import TTLCache

logger = logging.getLogger(__name__)
resolver_cache = TTLCache(ttl_seconds=300)


class TarifarioService:
    """Servicio para gestión de tarifario"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = TarifarioRepository(db)
    
    def crear_tarifa(self, tarifa_data: TarifarioCreate) -> Tarifario:
        """
        Crear una nueva tarifa con validaciones completas
        
        Validaciones:
        1. La sede debe existir
        2. Si cancha_id está presente:
           - La cancha debe existir
           - La cancha debe pertenecer a la sede
        3. No debe haber solapamiento de franjas en el mismo nivel
        
        Args:
            tarifa_data: Datos de la tarifa a crear
            
        Returns:
            Tarifa creada
            
        Raises:
            HTTPException: Si hay errores de validación
        """
        # Validar que la sede existe
        if not self.repository.verificar_sede_existe(tarifa_data.sede_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "SEDE_NO_ENCONTRADA",
                        "message": f"No se encontró la sede con ID {tarifa_data.sede_id}",
                        "details": {"sede_id": tarifa_data.sede_id}
                    }
                }
            )
        
        # Si se especifica cancha, validar
        if tarifa_data.cancha_id:
            # Validar que la cancha existe
            if not self.repository.verificar_cancha_existe(tarifa_data.cancha_id):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "error": {
                            "code": "CANCHA_NO_ENCONTRADA",
                            "message": f"No se encontró la cancha con ID {tarifa_data.cancha_id}",
                            "details": {"cancha_id": tarifa_data.cancha_id}
                        }
                    }
                )
            
            # Validar que la cancha pertenece a la sede
            if not self.repository.verificar_cancha_pertenece_sede(
                tarifa_data.cancha_id, tarifa_data.sede_id
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": {
                            "code": "CANCHA_SEDE_MISMATCH",
                            "message": "La cancha no pertenece a la sede especificada",
                            "details": {
                                "cancha_id": tarifa_data.cancha_id,
                                "sede_id": tarifa_data.sede_id
                            }
                        }
                    }
                )
        
        # Validar solapamiento de franjas
        hay_solapamiento, tarifa_solapada = self.repository.verificar_solapamiento(
            sede_id=tarifa_data.sede_id,
            cancha_id=tarifa_data.cancha_id,
            dia_semana=tarifa_data.dia_semana,
            hora_inicio=tarifa_data.hora_inicio,
            hora_fin=tarifa_data.hora_fin
        )
        
        if hay_solapamiento:
            nivel = "cancha" if tarifa_data.cancha_id else "sede"
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": {
                        "code": "FRANJA_SOLAPADA",
                        "message": f"Existe una tarifa de {nivel} que se cruza con la franja horaria especificada",
                        "details": {
                            "tarifa_existente": tarifa_solapada.id,
                            "franja_existente": f"{tarifa_solapada.hora_inicio}-{tarifa_solapada.hora_fin}",
                            "franja_nueva": f"{tarifa_data.hora_inicio}-{tarifa_data.hora_fin}"
                        }
                    }
                }
            )
        
        try:
            tarifa = self.repository.crear(tarifa_data)
            logger.info(f"Tarifa creada exitosamente: {tarifa.id}")
            return tarifa
            
        except IntegrityError as e:
            logger.error(f"Error de integridad al crear tarifa: {e}")
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
            logger.error(f"Error inesperado al crear tarifa: {e}")
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
    
    def obtener_tarifa(self, tarifa_id: str) -> Tarifario:
        """Obtener tarifa por ID"""
        tarifa = self.repository.obtener_por_id(tarifa_id)
        
        if not tarifa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "TARIFA_NO_ENCONTRADA",
                        "message": f"No se encontró la tarifa con ID {tarifa_id}",
                        "details": {"tarifa_id": tarifa_id}
                    }
                }
            )
        
        return tarifa
    
    def listar_tarifas(
        self,
        sede_id: Optional[str] = None,
        cancha_id: Optional[str] = None,
        dia_semana: Optional[int] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Tarifario], int]:
        """Listar tarifas con filtros y paginación"""
        
        # Validar paginación
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 20
        
        skip = (page - 1) * page_size
        
        tarifas, total = self.repository.listar(
            sede_id=sede_id,
            cancha_id=cancha_id,
            dia_semana=dia_semana,
            skip=skip,
            limit=page_size
        )
        
        return tarifas, total
    
    def obtener_tarifa_aplicable(
        self,
        sede_id: str,
        cancha_id: str,
        dia_semana: int,
        hora: str
    ) -> Tarifario:
        """
        Obtener la tarifa aplicable según prioridad cancha > sede
        
        Args:
            sede_id: ID de la sede
            cancha_id: ID de la cancha
            dia_semana: Día de la semana (0-6)
            hora: Hora a consultar (HH:MM)
            
        Returns:
            Tarifa aplicable
            
        Raises:
            HTTPException: Si no se encuentra tarifa aplicable
        """
        tarifa = self.repository.obtener_tarifa_aplicable(
            sede_id, cancha_id, dia_semana, hora
        )
        
        if not tarifa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "TARIFA_NO_DISPONIBLE",
                        "message": "No se encontró tarifa aplicable para los parámetros especificados",
                        "details": {
                            "sede_id": sede_id,
                            "cancha_id": cancha_id,
                            "dia_semana": dia_semana,
                            "hora": hora
                        }
                    }
                }
            )
        
        return tarifa
    
    def actualizar_tarifa(self, tarifa_id: str, tarifa_data: TarifarioUpdate) -> Tarifario:
        """
        Actualizar tarifa existente
        
        Si se actualizan las franjas horarias, valida solapamiento
        """
        # Verificar que la tarifa existe
        tarifa_actual = self.obtener_tarifa(tarifa_id)
        
        # Si se están actualizando las franjas horarias, validar solapamiento
        if any([
            tarifa_data.dia_semana is not None,
            tarifa_data.hora_inicio is not None,
            tarifa_data.hora_fin is not None
        ]):
            # Usar valores actuales si no se proveen nuevos
            nuevo_dia = tarifa_data.dia_semana if tarifa_data.dia_semana is not None else tarifa_actual.dia_semana
            nueva_hora_inicio = tarifa_data.hora_inicio if tarifa_data.hora_inicio else tarifa_actual.hora_inicio
            nueva_hora_fin = tarifa_data.hora_fin if tarifa_data.hora_fin else tarifa_actual.hora_fin
            
            # Validar que hora_inicio < hora_fin
            if nueva_hora_inicio >= nueva_hora_fin:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": {
                            "code": "RANGO_HORARIO_INVALIDO",
                            "message": "La hora de inicio debe ser menor que la hora de fin",
                            "details": {
                                "hora_inicio": nueva_hora_inicio,
                                "hora_fin": nueva_hora_fin
                            }
                        }
                    }
                )
            
            # Validar solapamiento (excluyendo la tarifa actual)
            hay_solapamiento, tarifa_solapada = self.repository.verificar_solapamiento(
                sede_id=tarifa_actual.sede_id,
                cancha_id=tarifa_actual.cancha_id,
                dia_semana=nuevo_dia,
                hora_inicio=nueva_hora_inicio,
                hora_fin=nueva_hora_fin,
                excluir_tarifa_id=tarifa_id
            )
            
            if hay_solapamiento:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "error": {
                            "code": "FRANJA_SOLAPADA",
                            "message": "La actualización causaría solapamiento con otra tarifa",
                            "details": {
                                "tarifa_solapada": tarifa_solapada.id,
                                "franja_solapada": f"{tarifa_solapada.hora_inicio}-{tarifa_solapada.hora_fin}"
                            }
                        }
                    }
                )
        
        try:
            tarifa_actualizada = self.repository.actualizar(tarifa_id, tarifa_data)
            logger.info(f"Tarifa actualizada: {tarifa_id}")
            return tarifa_actualizada
            
        except Exception as e:
            logger.error(f"Error al actualizar tarifa: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": {
                        "code": "ERROR_ACTUALIZACION",
                        "message": "Error al actualizar la tarifa",
                        "details": str(e)
                    }
                }
            )
    
    def eliminar_tarifa(self, tarifa_id: str) -> bool:
        """Eliminar tarifa"""
        
        # Verificar que la tarifa existe
        self.obtener_tarifa(tarifa_id)
        
        # TODO: Validar que no esté en uso en reservas confirmadas
        # if self.repository.tarifa_en_uso(tarifa_id):
        #     raise HTTPException(
        #         status_code=status.HTTP_409_CONFLICT,
        #         detail={
        #             "error": {
        #                 "code": "TARIFA_EN_USO",
        #                 "message": "La tarifa está siendo usada en reservas confirmadas",
        #                 "details": {"tarifa_id": tarifa_id}
        #             }
        #         }
        #     )
        
        try:
            resultado = self.repository.eliminar(tarifa_id)
            logger.info(f"Tarifa eliminada: {tarifa_id}")
            return resultado
            
        except Exception as e:
            logger.error(f"Error al eliminar tarifa: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": {
                        "code": "ERROR_ELIMINACION",
                        "message": "Error al eliminar la tarifa",
                        "details": str(e)
                    }
                }
            )

    def resolver_precio(
        self,
        *,
        fecha: str,
        hora_inicio: str,
        hora_fin: str,
        sede_id: str,
        cancha_id: Optional[str] = None,
    ) -> TarifaResolverData:
        cache_key = self._build_cache_key(fecha, hora_inicio, hora_fin, sede_id, cancha_id)
        cached = resolver_cache.get(cache_key)
        if cached:
            return TarifaResolverData(**cached)

        sede = self._obtener_sede(sede_id)
        if cancha_id:
            cancha = self._obtener_cancha(cancha_id)
            if cancha.sede_id != sede.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": {
                            "code": "CANCHA_SEDE_MISMATCH",
                            "message": "La cancha no pertenece a la sede indicada",
                            "details": {"cancha_id": cancha_id, "sede_id": sede_id},
                        }
                    },
                )

        tz = self._get_timezone(sede)
        inicio_dt = self._parse_fecha_hora(fecha, hora_inicio, tz)
        fin_dt = self._parse_fecha_hora(fecha, hora_fin, tz)

        if fin_dt <= inicio_dt:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "HORARIO_INVALIDO", "message": "hora_fin debe ser mayor que hora_inicio"}},
            )

        dia_semana = inicio_dt.weekday()
        tarifa = self.repository.obtener_tarifa_aplicable(sede_id, cancha_id, dia_semana, hora_inicio)

        if not tarifa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "SIN_TARIFA",
                        "message": "No existe tarifa para la franja solicitada",
                        "details": {
                            "dia_semana": dia_semana,
                            "hora_inicio": hora_inicio,
                            "hora_fin": hora_fin,
                        },
                    }
                },
            )

        data = TarifaResolverData(
            origen="cancha" if tarifa.cancha_id else "sede",
            tarifa_id=tarifa.id,
            moneda=tarifa.moneda,
            precio_por_bloque=float(tarifa.precio_por_bloque),
        )
        resolver_cache.set(cache_key, data.model_dump())
        return data

    def _obtener_sede(self, sede_id: str) -> Sede:
        sede = self.db.query(Sede).filter(Sede.id == sede_id, Sede.activo == 1).first()
        if not sede:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "SEDE_NO_ENCONTRADA", "message": "Sede no encontrada"}},
            )
        return sede

    def _obtener_cancha(self, cancha_id: str) -> Cancha:
        cancha = self.db.query(Cancha).filter(Cancha.id == cancha_id, Cancha.activo == 1).first()
        if not cancha:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "CANCHA_NO_ENCONTRADA", "message": "Cancha no encontrada"}},
            )
        return cancha

    def _parse_fecha_hora(self, fecha: str, hora: str, tz: ZoneInfo) -> datetime:
        try:
            dt = datetime.strptime(f"{fecha} {hora}", "%Y-%m-%d %H:%M")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": {"code": "VALIDATION_ERROR", "message": "Formato de fecha u hora inválido"}},
            )
        return dt.replace(tzinfo=tz)

    def _get_timezone(self, sede: Sede) -> ZoneInfo:
        try:
            return ZoneInfo(sede.zona_horaria)
        except ZoneInfoNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": {"code": "ZONA_HORARIA_INVALIDA", "message": str(exc)}}
            )

    def _build_cache_key(
        self,
        fecha: str,
        hora_inicio: str,
        hora_fin: str,
        sede_id: str,
        cancha_id: Optional[str],
    ) -> str:
        return f"{sede_id}:{cancha_id or 'general'}:{fecha}:{hora_inicio}:{hora_fin}"

