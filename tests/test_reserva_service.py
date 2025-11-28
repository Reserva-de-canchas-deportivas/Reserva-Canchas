import pytest
from datetime import datetime
from app.domain.order_model import EstadoReserva
from app.services.order_service import ReservaService

class TestReservaService:
    
    def setup_method(self):
        """Limpiar datos antes de cada test"""
        from app.services.order_service import reservas_db, historial_db
        reservas_db.clear()
        historial_db.clear()
    
    def test_crear_reserva(self):
        """Test creación de reserva"""
        reserva = ReservaService.crear_reserva(
            cancha_id="cancha1",
            usuario_id="user1",
            fecha_reserva=datetime.now()
        )
        
        assert reserva.id is not None
        assert reserva.estado == EstadoReserva.HOLD
        assert reserva.cancha_id == "cancha1"
        assert reserva.usuario_id == "user1"
        
        # Verificar que se guardó en la "base de datos"
        from app.services.order_service import reservas_db
        assert reserva.id in reservas_db
        
        # Verificar que se creó historial inicial
        from app.services.order_service import historial_db
        historial_reserva = [h for h in historial_db if h.reserva_id == reserva.id]
        assert len(historial_reserva) == 1
        assert historial_reserva[0].estado_anterior == EstadoReserva.HOLD
        assert historial_reserva[0].estado_nuevo == EstadoReserva.HOLD
    
    def test_transicionar_estado_valido(self):
        """Test transición de estado válida"""
        # Crear reserva
        reserva = ReservaService.crear_reserva("cancha1", "user1", datetime.now())
        
        # Transicionar de HOLD a PENDING
        resultado = ReservaService.transicionar_estado(
            reserva_id=reserva.id,
            estado_nuevo=EstadoReserva.PENDING,
            usuario_id="admin1"
        )
        
        assert resultado["reserva_id"] == reserva.id
        assert resultado["estado_anterior"] == EstadoReserva.HOLD
        assert resultado["estado_actual"] == EstadoReserva.PENDING
        
        # Verificar que la reserva se actualizó
        reserva_actualizada = ReservaService.obtener_reserva(reserva.id)
        assert reserva_actualizada.estado == EstadoReserva.PENDING
        
        # Verificar historial
        historial = ReservaService.obtener_historial(reserva.id)
        assert len(historial) == 2  # Estado inicial + transición
        
        ultimo_cambio = historial[-1]
        assert ultimo_cambio.estado_anterior == EstadoReserva.HOLD
        assert ultimo_cambio.estado_nuevo == EstadoReserva.PENDING
        assert ultimo_cambio.usuario_id == "admin1"
    
    def test_transicionar_estado_invalido(self):
        """Test transición de estado inválida"""
        reserva = ReservaService.crear_reserva("cancha1", "user1", datetime.now())
        
        # Intentar transición inválida: HOLD -> CANCELLED
        with pytest.raises(ValueError, match="TRANSICION_INVALIDA"):
            ReservaService.transicionar_estado(
                reserva_id=reserva.id,
                estado_nuevo=EstadoReserva.CANCELLED,
                usuario_id="admin1"
            )
    
    def test_transicionar_reserva_no_existe(self):
        """Test transición en reserva que no existe"""
        with pytest.raises(ValueError, match="RESERVA_NO_ENCONTRADA"):
            ReservaService.transicionar_estado(
                reserva_id="id-inexistente",
                estado_nuevo=EstadoReserva.PENDING,
                usuario_id="admin1"
            )
    
    def test_workflow_completo_valido(self):
        """Test workflow completo válido: HOLD -> PENDING -> CONFIRMED -> CANCELLED"""
        reserva = ReservaService.crear_reserva("cancha1", "user1", datetime.now())
        
        # HOLD -> PENDING
        ReservaService.transicionar_estado(reserva.id, EstadoReserva.PENDING, "admin1")
        assert ReservaService.obtener_reserva(reserva.id).estado == EstadoReserva.PENDING
        
        # PENDING -> CONFIRMED
        ReservaService.transicionar_estado(reserva.id, EstadoReserva.CONFIRMED, "admin2")
        assert ReservaService.obtener_reserva(reserva.id).estado == EstadoReserva.CONFIRMED
        
        # CONFIRMED -> CANCELLED
        ReservaService.transicionar_estado(reserva.id, EstadoReserva.CANCELLED, "user1")
        assert ReservaService.obtener_reserva(reserva.id).estado == EstadoReserva.CANCELLED
        
        # Verificar historial completo
        historial = ReservaService.obtener_historial(reserva.id)
        assert len(historial) == 4  # Estado inicial + 3 transiciones
        
        estados = [h.estado_nuevo for h in historial]
        assert estados == [EstadoReserva.HOLD, EstadoReserva.PENDING, EstadoReserva.CONFIRMED, EstadoReserva.CANCELLED]
    
    def test_workflow_invalido_cancelled_to_confirmed(self):
        """Test workflow inválido: CANCELLED -> CONFIRMED (Caso 4 de HU)"""
        reserva = ReservaService.crear_reserva("cancha1", "user1", datetime.now())
        
        # Llevar a CANCELLED vía workflow válido
        ReservaService.transicionar_estado(reserva.id, EstadoReserva.PENDING, "admin1")
        ReservaService.transicionar_estado(reserva.id, EstadoReserva.CONFIRMED, "admin2")
        ReservaService.transicionar_estado(reserva.id, EstadoReserva.CANCELLED, "user1")
        
        # Intentar transición inválida: CANCELLED -> CONFIRMED
        with pytest.raises(ValueError, match="TRANSICION_INVALIDA"):
            ReservaService.transicionar_estado(
                reserva_id=reserva.id,
                estado_nuevo=EstadoReserva.CONFIRMED,
                usuario_id="admin1"
            )