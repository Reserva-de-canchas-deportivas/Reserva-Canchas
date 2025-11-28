"""
Servicios simulados para pruebas - Sin dependencias de FastAPI/SQLAlchemy
"""
from app.services.metrics_service import metrics_service, MetricsService

# Datos temporales en memoria
reservas_temp = []
pagos_temp = []

class SimulatedReservaService:
    """Servicio simulado de reservas"""
    
    def __init__(self):
        self.reservas = reservas_temp
    
    @MetricsService.medir_tiempo_reserva("crear_reserva")
    def crear_reserva(self, reserva_data: dict):
        """Crear una nueva reserva con métricas"""
        try:
            reserva_id = len(self.reservas) + 1
            reserva = {
                **reserva_data, 
                "id": reserva_id, 
                "estado": "confirmada"
            }
            self.reservas.append(reserva)
            
            # Actualizar métricas
            metrics_service.incrementar_reservas_activas()
            metrics_service.contar_reserva_creada("confirmada")
            
            return reserva
            
        except Exception as e:
            metrics_service.contar_reserva_creada("error")
            raise e
    
    def cancelar_reserva(self, reserva_id: int):
        """Cancelar una reserva existente"""
        try:
            for reserva in self.reservas:
                if reserva["id"] == reserva_id:
                    reserva["estado"] = "cancelada"
                    
                    # Actualizar métricas
                    metrics_service.decrementar_reservas_activas()
                    metrics_service.contar_reserva_creada("cancelada")
                    
                    return reserva
            return None
            
        except Exception as e:
            metrics_service.contar_reserva_creada("error_cancelacion")
            raise e
    
    def obtener_reservas_activas(self):
        """Obtener reservas activas y actualizar métricas"""
        activas = [r for r in self.reservas if r.get("estado") == "confirmada"]
        
        # Sincronizar métrica con realidad
        metrics_service.establecer_reservas_activas(len(activas))
        
        return activas

class SimulatedPagoService:
    """Servicio simulado de pagos"""
    
    def __init__(self):
        self.pagos = pagos_temp
    
    @MetricsService.medir_tiempo_reserva("procesar_pago")
    def crear_pago(self, pago_data: dict):
        """Crear un nuevo pago con métricas"""
        try:
            pago_id = len(self.pagos) + 1
            pago = {
                **pago_data, 
                "id": pago_id, 
                "estado": "pendiente"
            }
            self.pagos.append(pago)
            
            # Actualizar métricas
            metrics_service.incrementar_pagos_pendientes()
            metrics_service.contar_pago_procesado("pendiente")
            
            return pago
            
        except Exception as e:
            metrics_service.contar_pago_procesado("error")
            raise e
    
    def procesar_pago(self, pago_id: int, estado: str):
        """Procesar un pago existente"""
        try:
            for pago in self.pagos:
                if pago["id"] == pago_id:
                    pago_anterior = pago["estado"]
                    pago["estado"] = estado
                    
                    # Actualizar métricas
                    if estado == "completado" and pago_anterior == "pendiente":
                        metrics_service.decrementar_pagos_pendientes()
                    
                    metrics_service.contar_pago_procesado(estado)
                    return pago
            return None
            
        except Exception as e:
            metrics_service.contar_pago_procesado("error_procesamiento")
            raise e
    
    def obtener_pagos_pendientes(self):
        """Obtener pagos pendientes y actualizar métricas"""
        pendientes = [p for p in self.pagos if p.get("estado") == "pendiente"]
        
        # Sincronizar métrica con realidad
        metrics_service.establecer_pagos_pendientes(len(pendientes))
        
        return pendientes

# Instancias globales de servicios simulados
simulated_reserva_service = SimulatedReservaService()
simulated_pago_service = SimulatedPagoService()