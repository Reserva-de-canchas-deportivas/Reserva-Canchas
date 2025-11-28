import pytest
from app.domain.order_model import EstadoReserva
from app.services.reserva_fsm import ReservaFSM

class TestReservaFSM:
    
    def test_transiciones_validas_hold(self):
        """Test transiciones válidas desde HOLD"""
        assert ReservaFSM.es_transicion_valida(EstadoReserva.HOLD, EstadoReserva.PENDING) == True
        assert ReservaFSM.es_transicion_valida(EstadoReserva.HOLD, EstadoReserva.EXPIRADA) == True
        
    def test_transiciones_invalidas_hold(self):
        """Test transiciones inválidas desde HOLD"""
        assert ReservaFSM.es_transicion_valida(EstadoReserva.HOLD, EstadoReserva.CONFIRMED) == False
        assert ReservaFSM.es_transicion_valida(EstadoReserva.HOLD, EstadoReserva.CANCELLED) == False
        assert ReservaFSM.es_transicion_valida(EstadoReserva.HOLD, EstadoReserva.NO_SHOW) == False
        
    def test_transiciones_validas_pending(self):
        """Test transiciones válidas desde PENDING"""
        assert ReservaFSM.es_transicion_valida(EstadoReserva.PENDING, EstadoReserva.CONFIRMED) == True
        
    def test_transiciones_invalidas_pending(self):
        """Test transiciones inválidas desde PENDING"""
        assert ReservaFSM.es_transicion_valida(EstadoReserva.PENDING, EstadoReserva.HOLD) == False
        assert ReservaFSM.es_transicion_valida(EstadoReserva.PENDING, EstadoReserva.CANCELLED) == False
        assert ReservaFSM.es_transicion_valida(EstadoReserva.PENDING, EstadoReserva.NO_SHOW) == False
        assert ReservaFSM.es_transicion_valida(EstadoReserva.PENDING, EstadoReserva.EXPIRADA) == False
        
    def test_transiciones_validas_confirmed(self):
        """Test transiciones válidas desde CONFIRMED"""
        assert ReservaFSM.es_transicion_valida(EstadoReserva.CONFIRMED, EstadoReserva.CANCELLED) == True
        assert ReservaFSM.es_transicion_valida(EstadoReserva.CONFIRMED, EstadoReserva.NO_SHOW) == True
        
    def test_transiciones_invalidas_confirmed(self):
        """Test transiciones inválidas desde CONFIRMED"""
        assert ReservaFSM.es_transicion_valida(EstadoReserva.CONFIRMED, EstadoReserva.HOLD) == False
        assert ReservaFSM.es_transicion_valida(EstadoReserva.CONFIRMED, EstadoReserva.PENDING) == False
        assert ReservaFSM.es_transicion_valida(EstadoReserva.CONFIRMED, EstadoReserva.EXPIRADA) == False
        
    def test_estados_finales(self):
        """Test que estados finales no permiten transiciones"""
        estados_finales = [EstadoReserva.CANCELLED, EstadoReserva.NO_SHOW, EstadoReserva.EXPIRADA]
        for estado_final in estados_finales:
            for estado in EstadoReserva:
                assert ReservaFSM.es_transicion_valida(estado_final, estado) == False
                
    def test_validar_transicion_valida(self):
        """Test que validar_transicion no lanza excepción para transición válida"""
        # Esto no debería lanzar excepción
        ReservaFSM.validar_transicion(EstadoReserva.HOLD, EstadoReserva.PENDING)
        
    def test_validar_transicion_invalida(self):
        """Test que validar_transicion lanza excepción para transición inválida"""
        with pytest.raises(ValueError, match="TRANSICION_INVALIDA"):
            ReservaFSM.validar_transicion(EstadoReserva.CANCELLED, EstadoReserva.CONFIRMED)