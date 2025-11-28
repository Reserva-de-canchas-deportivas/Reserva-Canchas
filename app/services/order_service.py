from datetime import datetime
from app.domain.order_model import Reserva, ReservaHistorial, EstadoReserva
from app.services.reserva_fsm import ReservaFSM
from typing import Optional
# Datos temporales en memoria
reservas_db = {}
historial_db = []

class ReservaService:
    
    @staticmethod
    def crear_reserva(cancha_id: str, usuario_id: str, fecha_reserva: datetime) -> Reserva:
        """Crea una nueva reserva en estado HOLD"""
        reserva = Reserva(cancha_id, usuario_id, fecha_reserva)
        reservas_db[reserva.id] = reserva
        
        # Registrar estado inicial en historial
        historial = ReservaHistorial(
            reserva_id=reserva.id,
            estado_anterior=EstadoReserva.HOLD,
            estado_nuevo=EstadoReserva.HOLD,
            usuario_id=usuario_id
        )
        historial_db.append(historial)
        
        return reserva
    
    @staticmethod
    def transicionar_estado(reserva_id: str, estado_nuevo: EstadoReserva, usuario_id: str) -> dict:
        """Realiza la transición de estado con validación FSM"""
        # Verificar que la reserva existe
        reserva = reservas_db.get(reserva_id)
        if not reserva:
            raise ValueError("RESERVA_NO_ENCONTRADA")
        
        estado_anterior = reserva.estado
        
        # Validar transición usando FSM
        ReservaFSM.validar_transicion(estado_anterior, estado_nuevo)
        
        # Actualizar estado
        reserva.estado = estado_nuevo
        reserva.fecha_actualizacion = datetime.now()
        
        # Registrar en historial
        historial = ReservaHistorial(
            reserva_id=reserva_id,
            estado_anterior=estado_anterior,
            estado_nuevo=estado_nuevo,
            usuario_id=usuario_id
        )
        historial_db.append(historial)
        
        # Emitir evento (simulado)
        ReservaService._emitir_evento_estado_cambiado(reserva_id, estado_anterior, estado_nuevo)
        
        return {
            "reserva_id": reserva_id,
            "estado_anterior": estado_anterior,
            "estado_actual": estado_nuevo,
            "fecha": datetime.now()
        }
    
    @staticmethod
    def obtener_historial(reserva_id: str) -> list[ReservaHistorial]:
        """Obtiene el historial de cambios de estado de una reserva"""
        return [h for h in historial_db if h.reserva_id == reserva_id]
    
    @staticmethod
    def obtener_reserva(reserva_id: str) -> Optional[Reserva]:
        """Obtiene una reserva por ID"""
        return reservas_db.get(reserva_id)
    
    @staticmethod
    def _emitir_evento_estado_cambiado(reserva_id: str, estado_anterior: EstadoReserva, estado_nuevo: EstadoReserva):
        """Simula la emisión de un evento cuando cambia el estado"""
        print(f"EVENTO: reserva.estado_cambiado - Reserva {reserva_id}: {estado_anterior} -> {estado_nuevo}")