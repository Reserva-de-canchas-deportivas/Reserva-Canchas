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
    ReservaCancelRequest,
    ReservaCancelData,
    ReservaReprogramarRequest,
    ReservaReprogramarData,
    DiferenciaPrecio,
    ReservaCleanData,
)
from app.services.tarifario_service import TarifarioService

from app.domain.reserva_fsm import ReservaFSM, EstadoReserva, TransicionInvalidaError
from app.repository.reserva_historial_repository import ReservaHistorialRepository
from app.schemas.reserva_historial import ReservaHistorialCreate


class ReservaService:
    ESTADOS_ACTIVOS = ("hold", "pending", "confirmed")

    def __init__(self, db: Session):
        self.db = db
        self.tarifario_service = TarifarioService(db)

    def crear_hold(
        self, payload: ReservaHoldRequest, usuario: Usuario
    ) -> Tuple[ReservaHoldData, bool]:
        existente = self._buscar_por_clave(payload.clave_idempotencia)
        if existente:
            return self._respuesta(existente), False

        sede = self._obtener_sede(payload.sede_id)
        cancha = self._obtener_cancha(payload.cancha_id)

        self._validar_cancha_en_sede(cancha, sede)
        self._validar_cancha_reservable(cancha)

        tz = self._obtener_timezone(sede)
        inicio_dt = self._parse_fecha_hora(
            payload.fecha.isoformat(), payload.hora_inicio, tz
        )
        fin_dt = self._parse_fecha_hora(payload.fecha.isoformat(), payload.hora_fin, tz)
        if fin_dt <= inicio_dt:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "HORARIO_INVALIDO",
                        "message": "hora_fin debe ser mayor a hora_inicio",
                    }
                },
            )

        self._validar_en_horario(
            sede, payload.hora_inicio, payload.hora_fin, inicio_dt.weekday()
        )
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
                detail={
                    "error": {
                        "code": "RESERVA_INVALIDA",
                        "message": "La reserva no se puede confirmar",
                    }
                },
            )

        if (
            reserva.usuario_id
            and usuario.rol == "cliente"
            and reserva.usuario_id != usuario.usuario_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "FORBIDDEN",
                        "message": "No puedes confirmar esta reserva",
                    }
                },
            )

        sede = self._obtener_sede(reserva.sede_id)
        tz = self._obtener_timezone(sede)
        if reserva.vence_hold:
            vence = self._parse_iso(reserva.vence_hold)
            if vence < datetime.now(tz):
                raise HTTPException(
                    status_code=status.HTTP_410_GONE,
                    detail={
                        "error": {
                            "code": "HOLD_EXPIRADO",
                            "message": "La pre-reserva ha expirado",
                        }
                    },
                )

        if settings.require_payment_capture and not reserva.pago_capturado:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={
                    "error": {
                        "code": "PAGO_REQUERIDO",
                        "message": "Se requiere pago capturado",
                    }
                },
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

    def cancelar_reserva(
        self,
        *,
        reserva_id: str,
        payload: ReservaCancelRequest,
        usuario: Usuario,
    ) -> ReservaCancelData:
        reserva = self._obtener_reserva(reserva_id)
        if reserva.estado == "cancelled":
            return self._respuesta_cancel(reserva, 0.0, "sin_reembolso")
        if reserva.estado not in {"confirmed", "hold", "pending"}:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": {
                        "code": "NO_CANCELABLE",
                        "message": "La reserva no puede cancelarse",
                    }
                },
            )

        sede = self._obtener_sede(reserva.sede_id)
        tz = self._obtener_timezone(sede)
        inicio_dt = datetime.strptime(
            f"{reserva.fecha} {reserva.hora_inicio}", "%Y-%m-%d %H:%M"
        ).replace(tzinfo=tz)
        if inicio_dt <= datetime.now(tz):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": {
                        "code": "NO_CANCELABLE",
                        "message": "La reserva ya inició o finalizó",
                    }
                },
            )

        horas_restantes = (inicio_dt - datetime.now(tz)).total_seconds() / 3600
        if horas_restantes >= settings.cancel_full_refund_hours:
            monto = float(reserva.total or 0.0)
            tipo = "total"
        else:
            porcentaje = settings.cancel_partial_percentage / 100
            monto = float(reserva.total or 0.0) * porcentaje
            tipo = "parcial" if monto > 0 else "sin_reembolso"

        reserva.estado = "cancelled"
        if payload.clave_idempotencia:
            reserva.cancel_idempotencia = payload.clave_idempotencia
        self.db.add(reserva)
        self.db.commit()
        self.db.refresh(reserva)
        return self._respuesta_cancel(reserva, monto, tipo)

    def expirar_holds_vencidos(self) -> ReservaCleanData:
        """Marca como expirada cualquier reserva en HOLD cuyo vence_hold ya pasó."""
        expiradas = 0
        holds = (
            self.db.query(Reserva)
            .filter(Reserva.estado == "hold", Reserva.vence_hold.isnot(None), Reserva.activo == 1)
            .all()
        )
        for hold in holds:
            try:
                vence = datetime.fromisoformat(hold.vence_hold)
            except ValueError:
                continue
            ahora_ref = datetime.now(vence.tzinfo) if vence.tzinfo else datetime.utcnow()
            if vence < ahora_ref:
                hold.estado = "expired"
                hold.activo = 0
                expiradas += 1
                self.db.add(hold)

        if expiradas:
            self.db.commit()
        else:
            self.db.rollback()

        return ReservaCleanData(expiradas=expiradas, ejecutado_en=datetime.utcnow().isoformat())

    def reprogramar_reserva(
        self,
        *,
        reserva_id: str,
        payload: ReservaReprogramarRequest,
        usuario: Usuario,
    ) -> ReservaReprogramarData:
        original = self._obtener_reserva(reserva_id)
        if original.estado != "confirmed":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": {
                        "code": "RESERVA_INVALIDA",
                        "message": "Solo puedes reprogramar reservas confirmadas",
                    }
                },
            )
        if (
            original.usuario_id
            and usuario.rol == "cliente"
            and original.usuario_id != usuario.usuario_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "FORBIDDEN",
                        "message": "No puedes reprogramar esta reserva",
                    }
                },
            )

        sede = self._obtener_sede(original.sede_id)
        tz = self._obtener_timezone(sede)
        inicio_original = datetime.strptime(
            f"{original.fecha} {original.hora_inicio}", "%Y-%m-%d %H:%M"
        ).replace(tzinfo=tz)
        if inicio_original <= datetime.now(tz):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": {
                        "code": "NO_REPROGRAMABLE",
                        "message": "La reserva ya inici�� o finaliz��",
                    }
                },
            )

        nueva_cancha_id = payload.cancha_id or original.cancha_id
        cancha = self._obtener_cancha(nueva_cancha_id)
        self._validar_cancha_en_sede(cancha, sede)
        self._validar_cancha_reservable(cancha)

        nueva_fecha = payload.fecha.isoformat()
        self._validar_en_horario(
            sede, payload.hora_inicio, payload.hora_fin, payload.fecha.weekday()
        )
        self._validar_solape(
            cancha_id=cancha.id,
            fecha=nueva_fecha,
            hora_inicio=payload.hora_inicio,
            hora_fin=payload.hora_fin,
            buffer_minutos=sede.minutos_buffer,
            exclude_reserva_id=original.id,
        )

        tarifa_nueva = self.tarifario_service.resolver_precio(
            fecha=nueva_fecha,
            hora_inicio=payload.hora_inicio,
            hora_fin=payload.hora_fin,
            sede_id=sede.id,
            cancha_id=cancha.id,
        )
        total_nuevo = Decimal(tarifa_nueva.precio_por_bloque)
        total_anterior = Decimal(original.total or 0)
        diferencia = total_nuevo - total_anterior
        if diferencia > 0:
            tipo_diferencia = "cargo_adicional"
        elif diferencia < 0:
            tipo_diferencia = "reembolso_parcial"
        else:
            tipo_diferencia = "sin_cambio"

        try:
            tx = self.db.begin_nested() if self.db.in_transaction() else self.db.begin()
            with tx:
                original.estado = "reprogrammed"
                original.activo = 0

                nueva_reserva = Reserva(
                    sede_id=sede.id,
                    cancha_id=cancha.id,
                    usuario_id=original.usuario_id,
                    fecha=nueva_fecha,
                    hora_inicio=payload.hora_inicio,
                    hora_fin=payload.hora_fin,
                    estado="confirmed",
                    clave_idempotencia=None,
                    confirm_idempotencia=None,
                    total=total_nuevo,
                    moneda=tarifa_nueva.moneda,
                    pago_capturado=original.pago_capturado,
                    reprogramada_desde=original.id,
                )

                self.db.add(nueva_reserva)
                self.db.flush()

                original.reprogramada_a = nueva_reserva.id
                self.db.add(original)
        except Exception:
            self.db.rollback()
            raise

        self.db.refresh(original)
        self.db.refresh(nueva_reserva)

        diff_data = DiferenciaPrecio(
            monto=float(abs(diferencia)),
            moneda=tarifa_nueva.moneda or "COP",
            tipo=tipo_diferencia,
        )
        return ReservaReprogramarData(
            reserva_original=original.id,
            reserva_nueva=nueva_reserva.id,
            diferencia=diff_data,
        )

    def _respuesta(self, reserva: Reserva) -> ReservaHoldData:
        sede = self._obtener_sede(reserva.sede_id)
        tz = self._obtener_timezone(sede)
        inicio = datetime.strptime(
            f"{reserva.fecha} {reserva.hora_inicio}", "%Y-%m-%d %H:%M"
        ).replace(tzinfo=tz)
        fin = datetime.strptime(
            f"{reserva.fecha} {reserva.hora_fin}", "%Y-%m-%d %H:%M"
        ).replace(tzinfo=tz)
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

    def _respuesta_cancel(
        self, reserva: Reserva, monto: float, tipo: str
    ) -> ReservaCancelData:
        return ReservaCancelData(
            reserva_id=reserva.id,
            estado=reserva.estado,
            reembolso={"monto": monto, "moneda": reserva.moneda or "COP", "tipo": tipo},
        )

    def _buscar_por_clave(self, clave: str) -> Optional[Reserva]:
        if not clave:
            return None
        return (
            self.db.query(Reserva).filter(Reserva.clave_idempotencia == clave).first()
        )

    def _obtener_reserva(self, reserva_id: str) -> Reserva:
        reserva = self.db.query(Reserva).filter(Reserva.id == reserva_id).first()
        if not reserva:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "RESERVA_NO_ENCONTRADA",
                        "message": "Reserva no encontrada",
                    }
                },
            )
        return reserva

    def _obtener_sede(self, sede_id: str) -> Sede:
        sede = self.db.query(Sede).filter(Sede.id == sede_id).first()
        if not sede:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "SEDE_NO_ENCONTRADA",
                        "message": "Sede no encontrada",
                    }
                },
            )
        return sede

    def _obtener_cancha(self, cancha_id: str) -> Cancha:
        cancha = self.db.query(Cancha).filter(Cancha.id == cancha_id).first()
        if not cancha:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "CANCHA_NO_ENCONTRADA",
                        "message": "Cancha no encontrada",
                    }
                },
            )
        return cancha

    def _validar_cancha_en_sede(self, cancha: Cancha, sede: Sede) -> None:
        if cancha.sede_id != sede.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "CANCHA_SEDE_MISMATCH",
                        "message": "La cancha no pertenece a la sede",
                    }
                },
            )

    def _validar_cancha_reservable(self, cancha: Cancha) -> None:
        if cancha.estado != "activo" or cancha.activo != 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": {
                        "code": "CANCHA_NO_RESERVABLE",
                        "message": "La cancha no se encuentra disponible",
                    }
                },
            )

    def _obtener_timezone(self, sede: Sede) -> ZoneInfo:
        try:
            return ZoneInfo(sede.zona_horaria)
        except ZoneInfoNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": {"code": "ZONA_HORARIA_INVALIDA", "message": str(exc)}
                },
            )

    def _parse_fecha_hora(self, fecha: str, hora: str, tz: ZoneInfo) -> datetime:
        return datetime.strptime(f"{fecha} {hora}", "%Y-%m-%d %H:%M").replace(tzinfo=tz)

    def _parse_iso(self, value: str) -> datetime:
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")

    def _validar_en_horario(
        self, sede: Sede, hora_inicio: str, hora_fin: str, dia_semana: int
    ) -> None:
        try:
            horarios = json.loads(sede.horario_apertura_json)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "HORARIO_INVALIDO",
                        "message": "Horarios de sede inválidos",
                    }
                },
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
                detail={
                    "error": {
                        "code": "FUERA_DE_APERTURA",
                        "message": "La sede está cerrada en esa fecha",
                    }
                },
            )

        inicio_min = self._hora_a_minutos(hora_inicio)
        fin_min = self._hora_a_minutos(hora_fin)
        for franja in franjas:
            rango_inicio, rango_fin = franja.split("-")
            if inicio_min >= self._hora_a_minutos(
                rango_inicio
            ) and fin_min <= self._hora_a_minutos(rango_fin):
                return

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "FUERA_DE_APERTURA",
                    "message": "Horario fuera de apertura",
                }
            },
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
        delta = timedelta(minutes=settings.hold_ttl_minutes)
        return (ahora + delta).isoformat()



class ReservaEstadoService:
    def __init__(self, db: Session):
        self.db = db
        self.historial_repo = ReservaHistorialRepository(db)
    
    def transicionar_estado(self, reserva_id: str, estado_nuevo: EstadoReserva, usuario_id: str, comentario: str = None) -> dict:
        reserva = self._obtener_reserva(reserva_id)
        if not reserva:
            raise ValueError("Reserva no encontrada")
        
        estado_actual = EstadoReserva(reserva.estado)
        
        if not ReservaFSM.validar_transicion(estado_actual, estado_nuevo):
            raise TransicionInvalidaError(estado_actual, estado_nuevo)
        
        estado_anterior = reserva.estado
        reserva.estado = estado_nuevo.value
        self.db.commit()
        
        historial_data = ReservaHistorialCreate(
            estado_anterior=estado_anterior,
            estado_nuevo=estado_nuevo.value,
            usuario_id=usuario_id,
            comentario=comentario
        )
        self.historial_repo.crear(historial_data, reserva_id)
        
        return {
            "reserva_id": reserva_id,
            "estado_anterior": estado_anterior,
            "estado_actual": estado_nuevo.value,
            "fecha": reserva.updated_at.isoformat() if hasattr(reserva.updated_at, 'isoformat') else None
        }
    
    def obtener_historial(self, reserva_id: str):
        return self.historial_repo.obtener_por_reserva(reserva_id)
    
    def _obtener_reserva(self, reserva_id: str):
        return self.db.query(Reserva).filter(Reserva.id == reserva_id).first()