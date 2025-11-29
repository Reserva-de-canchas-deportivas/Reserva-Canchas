#!/usr/bin/env python3
"""
Pruebas unitarias DIRECTAS del servicio de métricas - Sin dependencias externas
"""
import pytest
import time
from prometheus_client import generate_latest, REGISTRY, CollectorRegistry

# Importar servicios simulados (sin dependencias)
from app.services.metrics_service import metrics_service
from app.services.simulated_services import simulated_reserva_service, simulated_pago_service

# Crear un registry limpio para pruebas
TEST_REGISTRY = CollectorRegistry()

class TestMetricsServiceUnit:
    """Pruebas unitarias del servicio de métricas"""
    
    def setup_method(self):
        """Resetear métricas antes de cada test"""
        # Limpiar registros de métricas usando el registry de prueba
        metrics_service.establecer_reservas_activas(0)
        metrics_service.establecer_pagos_pendientes(0)
        
        # Limpiar datos temporales
        simulated_reserva_service.reservas.clear()
        simulated_pago_service.pagos.clear()
    
    def test_incrementar_reservas_activas(self):
        """Test: Incrementar reservas activas afecta la métrica"""
        # Acción: incrementar
        metrics_service.incrementar_reservas_activas()
        metrics_service.incrementar_reservas_activas()
        
        # Verificación
        metrics_after = generate_latest(REGISTRY).decode('utf-8')
        # Buscar la línea específica de reservas_activas_total
        reservas_lines = [line for line in metrics_after.split('\n') 
                         if 'reservas_activas_total' in line and not line.startswith('#')]
        assert len(reservas_lines) > 0
        assert '2.0' in reservas_lines[0]
    
    def test_decrementar_reservas_activas(self):
        """Test: Decrementar reservas activas"""
        # Configurar valor inicial
        metrics_service.establecer_reservas_activas(5)
        
        # Acción: decrementar
        metrics_service.decrementar_reservas_activas()
        metrics_service.decrementar_reservas_activas()
        
        # Verificación
        metrics_after = generate_latest(REGISTRY).decode('utf-8')
        reservas_lines = [line for line in metrics_after.split('\n') 
                         if 'reservas_activas_total' in line and not line.startswith('#')]
        assert len(reservas_lines) > 0
        assert '3.0' in reservas_lines[0]
    
    def test_establecer_reservas_activas(self):
        """Test: Establecer valor directo de reservas activas"""
        # Acción
        metrics_service.establecer_reservas_activas(42)
        
        # Verificación
        metrics = generate_latest(REGISTRY).decode('utf-8')
        reservas_lines = [line for line in metrics.split('\n') 
                         if 'reservas_activas_total' in line and not line.startswith('#')]
        assert len(reservas_lines) > 0
        assert '42.0' in reservas_lines[0]
    
    def test_contar_reserva_creada(self):
        """Test: Contador de reservas creadas por estado"""
        # Acción
        metrics_service.contar_reserva_creada("confirmada")
        metrics_service.contar_reserva_creada("confirmada")
        metrics_service.contar_reserva_creada("cancelada")
        metrics_service.contar_reserva_creada("pendiente")
        
        # Verificación
        metrics = generate_latest(REGISTRY).decode('utf-8')
        assert 'reservas_creadas_total' in metrics
        # Verificar que existen las métricas con los estados
        confirmada_lines = [line for line in metrics.split('\n') 
                           if 'reservas_creadas_total' in line and 'confirmada' in line]
        cancelada_lines = [line for line in metrics.split('\n') 
                          if 'reservas_creadas_total' in line and 'cancelada' in line]
        assert len(confirmada_lines) > 0
        assert len(cancelada_lines) > 0
    
    def test_contar_pago_procesado(self):
        """Test: Contador de pagos procesados por estado"""
        # Acción
        metrics_service.contar_pago_procesado("completado")
        metrics_service.contar_pago_procesado("completado")
        metrics_service.contar_pago_procesado("fallido")
        metrics_service.contar_pago_procesado("pendiente")
        
        # Verificación
        metrics = generate_latest(REGISTRY).decode('utf-8')
        assert 'pagos_procesados_total' in metrics
        # Verificar que existen las métricas con los estados
        completado_lines = [line for line in metrics.split('\n') 
                           if 'pagos_procesados_total' in line and 'completado' in line]
        fallido_lines = [line for line in metrics.split('\n') 
                        if 'pagos_procesados_total' in line and 'fallido' in line]
        assert len(completado_lines) > 0
        assert len(fallido_lines) > 0
    
    def test_decorador_tiempo_reserva(self):
        """Test: Decorador de medición de tiempo"""
        
        # Función de prueba
        @metrics_service.medir_tiempo_reserva("test_operation")
        def operacion_lenta():
            time.sleep(0.01)  # 10ms
            return "éxito"
        
        # Ejecutar
        resultado = operacion_lenta()
        
        # Verificar
        assert resultado == "éxito"
        
        metrics = generate_latest(REGISTRY).decode('utf-8')
        assert 'reserva_procesamiento_segundos' in metrics
        assert 'operacion="test_operation"' in metrics

class TestSimulatedReservaService:
    """Pruebas del servicio simulado de reservas"""
    
    def setup_method(self):
        """Resetear antes de cada test"""
        metrics_service.establecer_reservas_activas(0)
        simulated_reserva_service.reservas.clear()
    
    def test_crear_reserva_incrementa_metricas(self):
        """Test: Crear reserva incrementa métricas correctamente"""
        # Datos de prueba
        reserva_data = {
            "usuario_id": 1,
            "cancha_id": 1, 
            "fecha": "2024-01-01",
            "hora": "10:00"
        }
        
        # Crear reserva
        reserva = simulated_reserva_service.crear_reserva(reserva_data)
        
        # Verificar reserva creada
        assert reserva["id"] == 1
        assert reserva["estado"] == "confirmada"
        
        # Verificar métricas - buscar valores específicos
        metrics_after = generate_latest(REGISTRY).decode('utf-8')
        
        # Buscar línea de reservas activas
        reservas_activas_lines = [line for line in metrics_after.split('\n') 
                                 if 'reservas_activas_total' in line and not line.startswith('#')]
        assert len(reservas_activas_lines) > 0
        assert '1.0' in reservas_activas_lines[0]
        
        # Buscar línea de reservas creadas confirmadas
        reservas_creadas_lines = [line for line in metrics_after.split('\n') 
                                 if 'reservas_creadas_total' in line and 'confirmada' in line]
        assert len(reservas_creadas_lines) > 0
    
    def test_cancelar_reserva_decrementa_metricas(self):
        """Test: Cancelar reserva decrementa métricas correctamente"""
        # Primero crear una reserva
        reserva_data = {
            "usuario_id": 1,
            "cancha_id": 1,
            "fecha": "2024-01-01", 
            "hora": "10:00"
        }
        reserva = simulated_reserva_service.crear_reserva(reserva_data)
        
        # Cancelar reserva
        reserva_cancelada = simulated_reserva_service.cancelar_reserva(reserva["id"])
        
        # Verificar
        assert reserva_cancelada["estado"] == "cancelada"
        
        # Verificar métricas - buscar valores específicos
        metrics_after = generate_latest(REGISTRY).decode('utf-8')
        
        # Buscar línea de reservas activas (debe ser 0)
        reservas_activas_lines = [line for line in metrics_after.split('\n') 
                                 if 'reservas_activas_total' in line and not line.startswith('#')]
        assert len(reservas_activas_lines) > 0
        assert '0.0' in reservas_activas_lines[0]

class TestSimulatedPagoService:
    """Pruebas del servicio simulado de pagos"""
    
    def setup_method(self):
        """Resetear antes de cada test"""
        metrics_service.establecer_pagos_pendientes(0)
        simulated_pago_service.pagos.clear()
    
    def test_crear_pago_incrementa_metricas(self):
        """Test: Crear pago incrementa métricas correctamente"""
        # Datos de prueba
        pago_data = {
            "reserva_id": 1,
            "monto": 100.0,
            "metodo_pago": "tarjeta"
        }
        
        # Crear pago
        pago = simulated_pago_service.crear_pago(pago_data)
        
        # Verificar pago creado
        assert pago["id"] == 1
        assert pago["estado"] == "pendiente"
        
        # Verificar métricas - buscar valores específicos
        metrics_after = generate_latest(REGISTRY).decode('utf-8')
        
        # Buscar línea de pagos pendientes
        pagos_pendientes_lines = [line for line in metrics_after.split('\n') 
                                 if 'pagos_pendientes_total' in line and not line.startswith('#')]
        assert len(pagos_pendientes_lines) > 0
        assert '1.0' in pagos_pendientes_lines[0]
        
        # Buscar línea de pagos procesados pendientes
        pagos_procesados_lines = [line for line in metrics_after.split('\n') 
                                 if 'pagos_procesados_total' in line and 'pendiente' in line]
        assert len(pagos_procesados_lines) > 0
    
    def test_procesar_pago_actualiza_metricas(self):
        """Test: Procesar pago actualiza métricas correctamente"""
        # Primero crear un pago
        pago_data = {
            "reserva_id": 1,
            "monto": 100.0,
            "metodo_pago": "tarjeta"
        }
        pago = simulated_pago_service.crear_pago(pago_data)
        
        # Procesar pago como completado
        pago_procesado = simulated_pago_service.procesar_pago(pago["id"], "completado")
        
        # Verificar
        assert pago_procesado["estado"] == "completado"
        
        # Verificar métricas - buscar valores específicos
        metrics_after = generate_latest(REGISTRY).decode('utf-8')
        
        # Buscar línea de pagos pendientes (debe ser 0)
        pagos_pendientes_lines = [line for line in metrics_after.split('\n') 
                                 if 'pagos_pendientes_total' in line and not line.startswith('#')]
        assert len(pagos_pendientes_lines) > 0
        assert '0.0' in pagos_pendientes_lines[0]

def test_formato_prometheus_valido():
    """Test: Verificar que el formato de métricas es válido para Prometheus"""
    # Generar métricas
    metrics_data = generate_latest(REGISTRY)
    metrics_text = metrics_data.decode('utf-8')
    
    # Verificar características del formato Prometheus
    assert metrics_text is not None
    assert len(metrics_text) > 0
    
    # Verificar que tiene líneas de HELP y TYPE (formato estándar)
    lines = metrics_text.strip().split('\n')
    help_lines = [line for line in lines if line.startswith('# HELP')]
    type_lines = [line for line in lines if line.startswith('# TYPE')]
    
    assert len(help_lines) > 0, "Debe tener líneas HELP"
    assert len(type_lines) > 0, "Debe tener líneas TYPE"
    
    # Verificar métricas específicas
    required_metrics = [
        'reservas_activas_total',
        'pagos_pendientes_total', 
        'reservas_creadas_total',
        'pagos_procesados_total',
        'reserva_procesamiento_segundos'
    ]
    
    for metric in required_metrics:
        assert any(metric in line for line in lines), f"Métrica {metric} no encontrada"

if __name__ == "__main__":
    # Ejecutar pruebas manualmente
    pytest.main([__file__, "-v"])
