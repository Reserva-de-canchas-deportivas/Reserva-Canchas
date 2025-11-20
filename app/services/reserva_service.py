from __future__ import annotations

import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Tuple
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.domain.user_model import Usuario
from app.models.cancha import Cancha
from app.models.reserva import Reserva
from app.models.sede import Sede
from app.schemas.reserva import (
    ReservaHoldData,
    ReservaHoldRequest,
    ReservaConfirmRequest,
    ReservaConfirmData,
)
from app.services.tarifario_service import TarifarioService


class ReservaService:
    ESTADOS_ACTIVOS = ("hold", "pending", "confirmed")

    def __init__(self, db: Session):
        self.db = db
        self.tarifario_service = TarifarioService(db)

    def crear_hold(self, payload: ReservaHoldRequest, usuario: Usuario) -> Tuple[ReservaHoldData, bool]:
        existente = self._buscar_por_clave(payload.clave_idempotencia)
        if existente:
            return self._respuesta(existente), False

        sede = self._obtener_sede(payload.sede_id)
        cancha = self._obtener_cancha(payload.cancha_id)

        self._validar_cancha_en_sede(cancha, sede)
        self._validar_cancha_reservable(cancha)

        tz = self._obtener_timezone(sede)
        inicio_dt = self._parse_fecha_hora(payload.fecha.isoformat(), payload.hora_inicio, tz)
        fin_dt = self._parse_fecha_hora(payload.fecha.isoformat(), payload.hora_fin, tz)
        if fin_dt <= inicio_dt:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "HORARIO_INVALIDO", "message": "hora_fin debe ser mayor a hora_inicio"}},
            )

        self._validar_en_horario(sede, payload.hora_inicio, payload.hora_fin, inicio_dt.weekday())
        self._validar_solape(
            cancha.id,
            payload.fecha.isoformat(),
            payload.hora_inicio,
            payload.hora_fin,
            sede.minutos_buffer,
            exclude_reserva_id=None,
        )

        tarifa = self.tarifario_service.resolver_precio(
            fecha=payload.fecha.isoformat(),
            hora_inicio=payload.hora_inicio,
            hora_fin=payload.hora_fin,
            sede_id=sede.id,
            cancha_id=cancha.id,
        )
        total = tarifa.precio_por_bloque

        reserva = Reserva(
            sede_id=sede.id,
            cancha_id=cancha.id,
            usuario_id=usuario.usuario_id,
            fecha=payload.fecha.isoformat(),
            hora_inicio=payload.hora_inicio,
            hora_fin=payload.hora_fin,
            estado="hold",
            vence_hold=self._calcular_vence_hold(tz),
            clave_idempotencia=payload.clave_idempotencia,
            total=Decimal(total),
            moneda=tarifa.moneda,
        )

        try:
            self.db.add(reserva)
            self.db.commit()
            self.db.refresh(reserva)
        except IntegrityError:
            self.db.rollback()
            existente = self._buscar_por_clave(payload.clave_idempotencia)
            if existente:
                return self._respuesta(existente), False
            raise

        return self._respuesta(reserva), True

    def confirmar_reserva(
        self,
        *,
        reserva_id: str,
        payload: ReservaConfirmRequest,
        usuario: Usuario,
    ) -> ReservaConfirmData:
        reserva = self._obtener_reserva(reserva_id)

        if reserva.estado == "confirmed":
            return self._respuesta_confirm(reserva)

        if reserva.estado not in {"hold", "pending"}:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": {"code": "RESERVA_INVALIDA", "message": "La reserva no se puede confirmar"}},
            )

        if reserva.usuario_id and usuario.rol == "cliente" and reserva.usuario_id != usuario.usuario_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": {"code": "FORBIDDEN", "message": "No puedes confirmar esta reserva"}},
            )

        sede = self._obtener_sede(reserva.sede_id)
        tz = self._obtener_timezone(sede)
        if reserva.vence_hold:
            vence = self._parse_iso(reserva.vence_hold)
            if vence < datetime.now(tz):
                raise HTTPException(
                    status_code=status.HTTP_410_GONE,
                    detail={"error": {"code": "HOLD_EXPIRADO", "message": "La pre-reserva ha expirado"}},
                )

        if settings.require_payment_capture and not reserva.pago_capturado:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={"error": {"code": "PAGO_REQUERIDO", "message": "Se requiere pago capturado"}},
            )

        self._validar_solape(
            cancha_id=reserva.cancha_id,
            fecha=reserva.fecha,
            hora_inicio=reserva.hora_inicio,
            hora_fin=reserva.hora_fin,
            buffer_minutos=sede.minutos_buffer,
            exclude_reserva_id=reserva.id,
        )

        reserva.estado = "confirmed"
        if payload.clave_idempotencia:
            reserva.confirm_idempotencia = payload.clave_idempotencia
        self.db.add(reserva)
        self.db.commit()
        self.db.refresh(reserva)
        return self._respuesta_confirm(reserva)

    def _respuesta(self, reserva: Reserva) -> ReservaHoldData:
        sede = self._obtener_sede(reserva.sede_id)
        tz = self._obtener_timezone(sede)
        inicio = datetime.strptime(f"{reserva.fecha} {reserva.hora_inicio}", "%Y-%m-%d %H:%M").replace(tzinfo=tz)
        fin = datetime.strptime(f"{reserva.fecha} {reserva.hora_fin}", "%Y-%m-%d %H:%M").replace(tzinfo=tz)
        return ReservaHoldData(
            reserva_id=reserva.id,
            estado=reserva.estado,
            sede_id=reserva.sede_id,
            cancha_id=reserva.cancha_id,
            inicio=inicio.isoformat(),
            fin=fin.isoformat(),
            vence_hold=reserva.vence_hold or "",
            total=float(reserva.total) if reserva.total is not None else 0.0,
            moneda=reserva.moneda or "COP",
        )

    def _respuesta_confirm(self, reserva: Reserva) -> ReservaConfirmData:
        return ReservaConfirmData(
            reserva_id=reserva.id,
            estado=reserva.estado,
            total=float(reserva.total) if reserva.total is not None else 0.0,
            moneda=reserva.moneda or "COP",
        )

    def _buscar_por_clave(self, clave: str) -> Optional[Reserva]:
        if not clave:
            return None
        return (
            self.db.query(Reserva)
            .filter(Reserva.clave_idempotencia == clave)
            .first()
        )

    def _obtener_reserva(self, reserva_id: str) -> Reserva:
        reserva = self.db.query(Reserva).filter(Reserva.id == reserva_id).first()
        if not reserva:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "RESERVA_NO_ENCONTRADA", "message": "Reserva no encontrada"}},
            )
        return reserva

    def _obtener_sede(self, sede_id: str) -> Sede:
        sede = self.db.query(Sede).filter(Sede.id == sede_id).first()
        if not sede:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "SEDE_NO_ENCONTRADA", "message": "Sede no encontrada"}},
            )
        return sede

    def _obtener_cancha(self, cancha_id: str) -> Cancha:
        cancha = self.db.query(Cancha).filter(Cancha.id == cancha_id).first()
        if not cancha:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "CANCHA_NO_ENCONTRADA", "message": "Cancha no encontrada"}},
            )
        return cancha

    def _validar_cancha_en_sede(self, cancha: Cancha, sede: Sede) -> None:
        if cancha.sede_id != sede.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "CANCHA_SEDE_MISMATCH", "message": "La cancha no pertenece a la sede"}},
            )

    def _validar_cancha_reservable(self, cancha: Cancha) -> None:
        if cancha.estado != "activo" or cancha.activo != 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": {"code": "CANCHA_NO_RESERVABLE", "message": "La cancha no se encuentra disponible"}},
            )

    def _obtener_timezone(self, sede: Sede) -> ZoneInfo:
        try:
            return ZoneInfo(sede.zona_horaria)
        except ZoneInfoNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": {"code": "ZONA_HORARIA_INVALIDA", "message": str(exc)}},
            )

    def _parse_fecha_hora(self, fecha: str, hora: str, tz: ZoneInfo) -> datetime:
        return datetime.strptime(f"{fecha} {hora}", "%Y-%m-%d %H:%M").replace(tzinfo=tz)

    def _parse_iso(self, value: str) -> datetime:
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")

    def _validar_en_horario(self, sede: Sede, hora_inicio: str, hora_fin: str, dia_semana: int) -> None:
        try:
            horarios = json.loads(sede.horario_apertura_json)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "HORARIO_INVALIDO", "message": "Horarios de sede inválidos"}},
            )

        mapa = {
            0: "lunes",
            1: "martes",
            2: "miercoles",
            3: "jueves",
            4: "viernes",
            5: "sabado",
            6: "domingo",
        }
        franjas = horarios.get(mapa[dia_semana], [])
        if not franjas:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "FUERA_DE_APERTURA", "message": "La sede está cerrada en esa fecha"}},
            )

        inicio_min = self._hora_a_minutos(hora_inicio)
        fin_min = self._hora_a_minutos(hora_fin)
        for franja in franjas:
            rango_inicio, rango_fin = franja.split("-")
            if inicio_min >= self._hora_a_minutos(rango_inicio) and fin_min <= self._hora_a_minutos(rango_fin):
                return

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "FUERA_DE_APERTURA", "message": "Horario fuera de apertura"}},
        )

    def _validar_solape(
        self,
        cancha_id: str,
        fecha: str,
        hora_inicio: str,
        hora_fin: str,
        buffer_minutos: int,
        exclude_reserva_id: Optional[str] = None,
    ) -> None:
        reservas = (
            self.db.query(Reserva)
            .filter(
                Reserva.cancha_id == cancha_id,
                Reserva.fecha == fecha,
                Reserva.estado.in_(self.ESTADOS_ACTIVOS),
                Reserva.activo == 1,
            )
            .all()
        )
        solicitud_inicio = self._hora_a_minutos(hora_inicio)
        solicitud_fin = self._hora_a_minutos(hora_fin)
        for reserva in reservas:
            if exclude_reserva_id and reserva.id == exclude_reserva_id:
                continue
            inicio = self._hora_a_minutos(reserva.hora_inicio) - buffer_minutos
            fin = self._hora_a_minutos(reserva.hora_fin) + buffer_minutos
            if solicitud_inicio < fin and solicitud_fin > inicio:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "error": {
                            "code": "RESERVA_SOLAPADA",
                            "message": "La franja solicitada se encuentra ocupada",
                            "details": {"cancha_id": cancha_id},
                        }
                    },
                )

    def _hora_a_minutos(self, hora: str) -> int:
        h, m = map(int, hora.split(":"))
        return h * 60 + m

    def _calcular_vence_hold(self, tz: ZoneInfo) -> str:
        ahora = datetime.now(tz)
        return (ahora + timedelta(minutes=settings.hold_ttl_minutes)).isoformat()
