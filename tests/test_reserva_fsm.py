import pytest
from app.domain.reserva_fsm import ReservaFSM, EstadoReserva, TransicionInvalidaError

def test_transiciones_validas():
    assert ReservaFSM.validar_transicion(EstadoReserva.HOLD, EstadoReserva.PENDING) == True
    assert ReservaFSM.validar_transicion(EstadoReserva.PENDING, EstadoReserva.CONFIRMED) == True
    assert ReservaFSM.validar_transicion(EstadoReserva.CONFIRMED, EstadoReserva.CANCELLED) == True
    assert ReservaFSM.validar_transicion(EstadoReserva.HOLD, EstadoReserva.EXPIRADA) == True

def test_transiciones_invalidas():
    assert ReservaFSM.validar_transicion(EstadoReserva.CANCELLED, EstadoReserva.CONFIRMED) == False
    assert ReservaFSM.validar_transicion(EstadoReserva.HOLD, EstadoReserva.CONFIRMED) == False

def test_transicionar_exitoso():
    nuevo_estado = ReservaFSM.transicionar(EstadoReserva.HOLD, EstadoReserva.PENDING)
    assert nuevo_estado == EstadoReserva.PENDING

def test_transicionar_fallido():
    with pytest.raises(TransicionInvalidaError):
        ReservaFSM.transicionar(EstadoReserva.CANCELLED, EstadoReserva.CONFIRMED)