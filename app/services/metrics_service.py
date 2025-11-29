from prometheus_client import Counter, Gauge, Histogram
import time

# Métricas personalizadas para reservas y pagos
RESERVAS_ACTIVAS = Gauge(
    'reservas_activas_total', 
    'Total de reservas confirmadas'
)

PAGOS_PENDIENTES = Gauge(
    'pagos_pendientes_total', 
    'Total de pagos pendientes'
)

# Métricas de negocio adicionales
RESERVAS_CREADAS = Counter(
    'reservas_creadas_total',
    'Total de reservas creadas',
    ['estado']
)

PAGOS_PROCESADOS = Counter(
    'pagos_procesados_total',
    'Total de pagos procesados',
    ['estado']
)

# Histograma para tiempos de procesamiento de reservas
TIEMPO_PROCESAMIENTO_RESERVA = Histogram(
    'reserva_procesamiento_segundos',
    'Tiempo de procesamiento de reservas',
    ['operacion']
)

class MetricsService:
    @staticmethod
    def incrementar_reservas_activas():
        """Incrementa el contador de reservas activas"""
        RESERVAS_ACTIVAS.inc()
    
    @staticmethod
    def decrementar_reservas_activas():
        """Decrementa el contador de reservas activas"""
        RESERVAS_ACTIVAS.dec()
    
    @staticmethod
    def establecer_reservas_activas(valor: int):
        """Establece el valor directo de reservas activas"""
        RESERVAS_ACTIVAS.set(valor)
    
    @staticmethod
    def incrementar_pagos_pendientes():
        """Incrementa el contador de pagos pendientes"""
        PAGOS_PENDIENTES.inc()
    
    @staticmethod
    def decrementar_pagos_pendientes():
        """Decrementa el contador de pagos pendientes"""
        PAGOS_PENDIENTES.dec()
    
    @staticmethod
    def establecer_pagos_pendientes(valor: int):
        """Establece el valor directo de pagos pendientes"""
        PAGOS_PENDIENTES.set(valor)
    
    @staticmethod
    def contar_reserva_creada(estado: str):
        """Cuenta una reserva creada con su estado"""
        RESERVAS_CREADAS.labels(estado=estado).inc()
    
    @staticmethod
    def contar_pago_procesado(estado: str):
        """Cuenta un pago procesado con su estado"""
        PAGOS_PROCESADOS.labels(estado=estado).inc()
    
    @staticmethod
    def medir_tiempo_reserva(operacion: str):
        """Decorador para medir tiempo de operaciones de reserva"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start_time
                    TIEMPO_PROCESAMIENTO_RESERVA.labels(operacion=operacion).observe(duration)
            return wrapper
        return decorator

# Instancia global del servicio de métricas
metrics_service = MetricsService()