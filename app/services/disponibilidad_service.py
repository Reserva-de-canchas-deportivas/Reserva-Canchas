"""
Servicio de Disponibilidad - Lógica de Negocio
Calcula disponibilidad considerando TZ, horarios y buffer
"""

from sqlalchemy.orm import Session
from typing import List, Tuple, Optional
from datetime import datetime
from fastapi import HTTPException, status
import pytz
import json
import logging

from app.models.sede import Sede
from app.models.cancha import Cancha
from app.models.reserva import Reserva
from app.schemas.disponibilidad import (
    DisponibilidadQuery,
    DisponibilidadResponse,
    SlotDisponibilidad,
)

logger = logging.getLogger(__name__)


class DisponibilidadService:
    """Servicio para cálculo de disponibilidad"""

    # Mapeo de día de semana Python a nombres en español
    DIAS_SEMANA = {
        0: "lunes",
        1: "martes",
        2: "miercoles",
        3: "jueves",
        4: "viernes",
        5: "sabado",
        6: "domingo",
    }

    def __init__(self, db: Session):
        self.db = db

    def calcular_disponibilidad(
        self, query: DisponibilidadQuery
    ) -> DisponibilidadResponse:
        """
        Calcular disponibilidad de una cancha en una fecha

        Args:
            query: Parámetros de consulta validados

        Returns:
            DisponibilidadResponse con slots calculados
        """
        # 1. Validar y obtener cancha
        cancha = self._obtener_cancha(query.cancha_id)

        # 2. Validar y obtener sede
        sede = self._obtener_sede(query.sede_id)

        # 3. Validar que la cancha pertenece a la sede
        if cancha.sede_id != sede.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "CANCHA_SEDE_MISMATCH",
                        "message": "La cancha no pertenece a la sede especificada",
                        "details": {
                            "cancha_id": cancha.id,
                            "cancha_sede_id": cancha.sede_id,
                            "sede_id_solicitada": sede.id,
                        },
                    }
                },
            )

        # 4. Convertir fecha a timezone de la sede
        fecha_obj, dia_semana = self._parsear_fecha_con_timezone(
            query.fecha, sede.zona_horaria
        )

        # 5. Obtener horario de apertura para ese día
        horario_apertura = self._obtener_horario_apertura(
            sede.horario_apertura_json, dia_semana
        )

        # Si no hay horario (día cerrado)
        if not horario_apertura:
            return DisponibilidadResponse(
                fecha=query.fecha,
                sede_id=sede.id,
                cancha_id=cancha.id,
                sede_nombre=sede.nombre,
                cancha_nombre=cancha.nombre,
                zona_horaria=sede.zona_horaria,
                horario_apertura=None,
                minutos_buffer=sede.minutos_buffer,
                slots=[],
                total_slots=0,
                slots_disponibles=0,
                slots_ocupados=0,
                dia_cerrado=True,
            )

        # 6. Obtener reservas existentes para esa cancha y fecha
        reservas = self._obtener_reservas_activas(cancha.id, query.fecha)

        # 7. Generar slots de tiempo
        slots = self._generar_slots(
            horario_apertura, reservas, sede.minutos_buffer, query.duracion_slot
        )

        # 8. Calcular estadísticas
        total_slots = len(slots)
        slots_disponibles = sum(1 for s in slots if s.reservable)
        slots_ocupados = total_slots - slots_disponibles

        logger.info(
            f"Disponibilidad calculada: {slots_disponibles}/{total_slots} slots "
            f"disponibles para cancha {cancha.id} el {query.fecha}"
        )

        return DisponibilidadResponse(
            fecha=query.fecha,
            sede_id=sede.id,
            cancha_id=cancha.id,
            sede_nombre=sede.nombre,
            cancha_nombre=cancha.nombre,
            zona_horaria=sede.zona_horaria,
            horario_apertura=horario_apertura,
            minutos_buffer=sede.minutos_buffer,
            slots=slots,
            total_slots=total_slots,
            slots_disponibles=slots_disponibles,
            slots_ocupados=slots_ocupados,
            dia_cerrado=False,
        )

    def _obtener_cancha(self, cancha_id: str) -> Cancha:
        """Obtener cancha y validar existencia"""
        cancha = (
            self.db.query(Cancha)
            .filter(Cancha.id == cancha_id, Cancha.activo == 1)
            .first()
        )

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

    def _obtener_sede(self, sede_id: str) -> Sede:
        """Obtener sede y validar existencia"""
        sede = self.db.query(Sede).filter(Sede.id == sede_id, Sede.activo == 1).first()

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

    def _parsear_fecha_con_timezone(
        self, fecha_str: str, zona_horaria_str: str
    ) -> Tuple[datetime, int]:
        """
        Convertir fecha string a datetime en timezone de la sede

        Returns:
            Tupla (datetime_local, dia_semana)
        """
        try:
            # Parsear fecha
            fecha_naive = datetime.strptime(fecha_str, "%Y-%m-%d")

            # Convertir a timezone de la sede
            tz = pytz.timezone(zona_horaria_str)
            fecha_local = tz.localize(fecha_naive)

            # Obtener día de semana (0=Monday, 6=Sunday)
            dia_semana = fecha_local.weekday()

            logger.info(
                f"Fecha parseada: {fecha_str} → {fecha_local} "
                f"(TZ: {zona_horaria_str}, Día: {self.DIAS_SEMANA[dia_semana]})"
            )

            return fecha_local, dia_semana

        except pytz.exceptions.UnknownTimeZoneError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": {
                        "code": "ZONA_HORARIA_INVALIDA",
                        "message": f"Zona horaria inválida en la sede: {zona_horaria_str}",
                        "details": {"zona_horaria": zona_horaria_str},
                    }
                },
            )

    def _obtener_horario_apertura(
        self, horario_json_str: str, dia_semana: int
    ) -> Optional[str]:
        """
        Obtener horario de apertura para un día específico

        Returns:
            String "HH:MM-HH:MM" o None si está cerrado
        """
        try:
            # Parsear JSON
            horario_dict = json.loads(horario_json_str)

            # Obtener nombre del día
            nombre_dia = self.DIAS_SEMANA[dia_semana]

            # Buscar horario para ese día
            horarios = horario_dict.get(nombre_dia, [])

            if not horarios or len(horarios) == 0:
                logger.info(f"Sede cerrada el {nombre_dia}")
                return None

            # Tomar el primer rango horario
            # Formato esperado: ["08:00-22:00"]
            horario = horarios[0]

            logger.info(f"Horario de apertura {nombre_dia}: {horario}")
            return horario

        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error parseando horario de apertura: {e}")
            return None

    def _obtener_reservas_activas(self, cancha_id: str, fecha: str) -> List[Reserva]:
        """
        Obtener reservas activas para una cancha en una fecha

        Estados activos: hold, pending, confirmed
        """
        reservas = (
            self.db.query(Reserva)
            .filter(
                Reserva.cancha_id == cancha_id,
                Reserva.fecha == fecha,
                Reserva.estado.in_(["hold", "pending", "confirmed"]),
                Reserva.activo == 1,
            )
            .order_by(Reserva.hora_inicio)
            .all()
        )

        logger.info(
            f"Reservas activas encontradas: {len(reservas)} "
            f"para cancha {cancha_id} el {fecha}"
        )

        return reservas

    def _generar_slots(
        self,
        horario_apertura: str,
        reservas: List[Reserva],
        minutos_buffer: int,
        duracion_slot: int,
    ) -> List[SlotDisponibilidad]:
        """
        Generar slots de tiempo considerando reservas y buffer

        Args:
            horario_apertura: "HH:MM-HH:MM"
            reservas: Lista de reservas activas
            minutos_buffer: Minutos de buffer entre reservas
            duracion_slot: Duración de cada slot en minutos

        Returns:
            Lista de SlotDisponibilidad
        """
        # Parsear horario de apertura
        hora_apertura, hora_cierre = horario_apertura.split("-")

        # Convertir a minutos desde medianoche
        apertura_mins = self._hora_a_minutos(hora_apertura)
        cierre_mins = self._hora_a_minutos(hora_cierre)

        # Crear timeline de rangos ocupados (reserva + buffer)
        rangos_ocupados = []
        for reserva in reservas:
            inicio_mins = self._hora_a_minutos(reserva.hora_inicio)
            fin_mins = self._hora_a_minutos(reserva.hora_fin)

            # Aplicar buffer antes y después
            inicio_con_buffer = max(apertura_mins, inicio_mins - minutos_buffer)
            fin_con_buffer = min(cierre_mins, fin_mins + minutos_buffer)

            rangos_ocupados.append(
                {
                    "inicio": inicio_con_buffer,
                    "fin": fin_con_buffer,
                    "motivo": (
                        "Reservado"
                        if inicio_mins <= inicio_mins < fin_mins
                        else "Buffer"
                    ),
                }
            )

        # Generar slots
        slots = []
        minuto_actual = apertura_mins

        while minuto_actual + duracion_slot <= cierre_mins:
            slot_inicio = minuto_actual
            slot_fin = minuto_actual + duracion_slot

            # Verificar si el slot está ocupado
            ocupado, motivo = self._slot_esta_ocupado(
                slot_inicio, slot_fin, rangos_ocupados
            )

            slots.append(
                SlotDisponibilidad(
                    hora_inicio=self._minutos_a_hora(slot_inicio),
                    hora_fin=self._minutos_a_hora(slot_fin),
                    reservable=not ocupado,
                    motivo=motivo if ocupado else None,
                )
            )

            minuto_actual += duracion_slot

        return slots

    def _hora_a_minutos(self, hora: str) -> int:
        """Convertir HH:MM a minutos desde medianoche"""
        h, m = map(int, hora.split(":"))
        return h * 60 + m

    def _minutos_a_hora(self, minutos: int) -> str:
        """Convertir minutos desde medianoche a HH:MM"""
        h = minutos // 60
        m = minutos % 60
        return f"{h:02d}:{m:02d}"

    def _slot_esta_ocupado(
        self, slot_inicio: int, slot_fin: int, rangos_ocupados: List[dict]
    ) -> Tuple[bool, Optional[str]]:
        """
        Verificar si un slot se solapa con algún rango ocupado

        Returns:
            Tupla (esta_ocupado, motivo)
        """
        for rango in rangos_ocupados:
            # Verificar solapamiento
            # Slot se solapa si: slot_inicio < rango_fin AND slot_fin > rango_inicio
            if slot_inicio < rango["fin"] and slot_fin > rango["inicio"]:
                return True, rango.get("motivo", "No disponible")

        return False, None
