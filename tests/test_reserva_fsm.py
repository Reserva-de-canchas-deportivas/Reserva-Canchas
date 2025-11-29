import pytest
from app.domain.order_model import EstadoReserva
from app.services.reserva_fsm import ReservaFSM

class TestReservaFSM:
    
    def test_transiciones_validas_hold(self):
        """Test transiciones válidas desde HOLD"""
        assert ReservaFSM.es_transicion_valida(EstadoReserva.HOLD, EstadoReserva.PENDING)
        assert ReservaFSM.es_transicion_valida(EstadoReserva.HOLD, EstadoReserva.EXPIRADA)
        
    def test_transiciones_invalidas_hold(self):
        """Test transiciones inválidas desde HOLD"""
        assert not ReservaFSM.es_transicion_valida(EstadoReserva.HOLD, EstadoReserva.CONFIRMED)
        assert not ReservaFSM.es_transicion_valida(EstadoReserva.HOLD, EstadoReserva.CANCELLED)
        assert not ReservaFSM.es_transicion_valida(EstadoReserva.HOLD, EstadoReserva.NO_SHOW)
        
    def test_transiciones_validas_pending(self):
        """Test transiciones válidas desde PENDING"""
        assert ReservaFSM.es_transicion_valida(EstadoReserva.PENDING, EstadoReserva.CONFIRMED)
        
    def test_transiciones_invalidas_pending(self):
        """Test transiciones inválidas desde PENDING"""
        assert not ReservaFSM.es_transicion_valida(EstadoReserva.PENDING, EstadoReserva.HOLD)
        assert not ReservaFSM.es_transicion_valida(EstadoReserva.PENDING, EstadoReserva.CANCELLED)
        assert not ReservaFSM.es_transicion_valida(EstadoReserva.PENDING, EstadoReserva.NO_SHOW)
        assert not ReservaFSM.es_transicion_valida(EstadoReserva.PENDING, EstadoReserva.EXPIRADA)
        
    def test_transiciones_validas_confirmed(self):
        """Test transiciones válidas desde CONFIRMED"""
        assert ReservaFSM.es_transicion_valida(EstadoReserva.CONFIRMED, EstadoReserva.CANCELLED)
        assert ReservaFSM.es_transicion_valida(EstadoReserva.CONFIRMED, EstadoReserva.NO_SHOW)
        
    def test_transiciones_invalidas_confirmed(self):
        """Test transiciones inválidas desde CONFIRMED"""
        assert not ReservaFSM.es_transicion_valida(EstadoReserva.CONFIRMED, EstadoReserva.HOLD)
        assert not ReservaFSM.es_transicion_valida(EstadoReserva.CONFIRMED, EstadoReserva.PENDING)
        assert not ReservaFSM.es_transicion_valida(EstadoReserva.CONFIRMED, EstadoReserva.EXPIRADA)
        
    def test_estados_finales(self):
        """Test que estados finales no permiten transiciones"""
        estados_finales = [EstadoReserva.CANCELLED, EstadoReserva.NO_SHOW, EstadoReserva.EXPIRADA]
        for estado_final in estados_finales:
            for estado in EstadoReserva:
                assert not ReservaFSM.es_transicion_valida(estado_final, estado)
                
    def test_validar_transicion_valida(self):
        """Test que validar_transicion no lanza excepción para transición válida"""
        # Esto no debería lanzar excepción
        ReservaFSM.validar_transicion(EstadoReserva.HOLD, EstadoReserva.PENDING)
        
    def test_validar_transicion_invalida(self):
        """Test que validar_transicion lanza excepción para transición inválida"""
        with pytest.raises(ValueError, match="TRANSICION_INVALIDA"):
            ReservaFSM.validar_transicion(EstadoReserva.CANCELLED, EstadoReserva.CONFIRMED)
