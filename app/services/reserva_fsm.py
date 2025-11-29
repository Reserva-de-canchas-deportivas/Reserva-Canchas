from app.domain.order_model import EstadoReserva

class ReservaFSM:
    """Máquina de estados finita para controlar transiciones de reservas"""
    
    TRANSICIONES_VALIDAS = {
        EstadoReserva.HOLD: [EstadoReserva.PENDING, EstadoReserva.EXPIRADA],
        EstadoReserva.PENDING: [EstadoReserva.CONFIRMED],
        EstadoReserva.CONFIRMED: [EstadoReserva.CANCELLED, EstadoReserva.NO_SHOW],
        # Estados finales - no permiten más transiciones
        EstadoReserva.CANCELLED: [],
        EstadoReserva.NO_SHOW: [],
        EstadoReserva.EXPIRADA: []
    }
    
    @classmethod
    def es_transicion_valida(cls, estado_actual: EstadoReserva, estado_nuevo: EstadoReserva) -> bool:
        """Verifica si la transición entre estados es válida"""
        return estado_nuevo in cls.TRANSICIONES_VALIDAS.get(estado_actual, [])
    
    @classmethod
    def validar_transicion(cls, estado_actual: EstadoReserva, estado_nuevo: EstadoReserva):
        """Valida la transición y lanza excepción si no es válida"""
        if not cls.es_transicion_valida(estado_actual, estado_nuevo):
            raise ValueError(f"TRANSICION_INVALIDA: No se puede cambiar de {estado_actual} a {estado_nuevo}")