from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from app.repository.pago_repository import PagoRepository
from app.models.pago import EstadoPago
from app.models.reserva import Reserva

from app.services.metrics_service import metrics_service, MetricsService
from typing import List, Optional

class PagoService:
    def __init__(self, db: Session):
        self.db = db
        self.pago_repo = PagoRepository(db)
    
    def crear_pago(
        self,
        reserva_id: str,
        monto: float,
        proveedor: str,
        moneda: str = "COP",
        referencia_proveedor: str = None
    ) -> Dict[str, Any]:
        # Validar que la reserva existe
        reserva = self.db.query(Reserva).filter(Reserva.id == reserva_id).first()
        if not reserva:
            raise ValueError("RESERVA_NO_ENCONTRADA")
        
        # Validar que no existe pago para esta reserva
        if self.pago_repo.existe_pago_para_reserva(reserva_id):
            raise ValueError("PAGO_DUPLICADO")
        
        # Validar monto positivo
        if monto <= 0:
            raise ValueError("MONTO_INVALIDO")
        
        # Validar moneda (formato ISO 4217)
        if len(moneda) != 3 or not moneda.isupper():
            raise ValueError("MONEDA_INVALIDA")
        
        # Crear pago
        pago_data = {
            "reserva_id": reserva_id,
            "monto": monto,
            "moneda": moneda,
            "proveedor": proveedor,
            "referencia_proveedor": referencia_proveedor,
            "estado": EstadoPago.INICIADO
        }
        
        try:
            pago = self.pago_repo.crear(pago_data)
            return {
                "pago_id": pago.id,
                "reserva_id": pago.reserva_id,
                "monto": float(pago.monto),
                "moneda": pago.moneda,
                "proveedor": pago.proveedor,
                "referencia_proveedor": pago.referencia_proveedor,
                "estado": pago.estado,
                "fecha_creacion": pago.fecha_creacion.isoformat()
            }
        except Exception as e:
            if "unique constraint" in str(e).lower():
                raise ValueError("PAGO_DUPLICADO")
            raise e
    
    def actualizar_estado_pago(
        self,
        pago_id: str,
        nuevo_estado: EstadoPago,
        referencia_proveedor: str = None
    ) -> Dict[str, Any]:
        # Validar estado
        estados_validos = [
            EstadoPago.INICIADO,
            EstadoPago.AUTORIZADO,
            EstadoPago.CAPTURADO, 
            EstadoPago.FALLIDO,
            EstadoPago.REEMBOLSADO
        ]
        
        if nuevo_estado not in estados_validos:
            raise ValueError("ESTADO_INVALIDO")
        
        # Actualizar pago
        pago = self.pago_repo.actualizar_estado(pago_id, nuevo_estado, referencia_proveedor)
        if not pago:
            raise ValueError("PAGO_NO_ENCONTRADO")
        
        return {
            "pago_id": pago.id,
            "reserva_id": pago.reserva_id,
            "monto": float(pago.monto),
            "moneda": pago.moneda,
            "proveedor": pago.proveedor,
            "referencia_proveedor": pago.referencia_proveedor,
            "estado": pago.estado,
            "fecha_actualizacion": pago.fecha_actualizacion.isoformat()
        }
    
    def obtener_pago(self, pago_id: str) -> Optional[Dict[str, Any]]:
        pago = self.pago_repo.obtener_por_id(pago_id)
        if pago:
            return {
                "pago_id": pago.id,
                "reserva_id": pago.reserva_id,
                "monto": float(pago.monto),
                "moneda": pago.moneda,
                "proveedor": pago.proveedor,
                "referencia_proveedor": pago.referencia_proveedor,
                "estado": pago.estado,
                "fecha_creacion": pago.fecha_creacion.isoformat(),
                "fecha_actualizacion": pago.fecha_actualizacion.isoformat()
            }
        return None
    
    


# Simulación de datos temporales
pagos_temp = []

class PagoService:
    
    @MetricsService.medir_tiempo_reserva("procesar_pago")
    async def crear_pago(self, pago_data: dict):
        """Crear un nuevo pago con métricas"""
        try:
            pago_id = len(pagos_temp) + 1
            pago = {**pago_data, "id": pago_id, "estado": "pendiente"}
            pagos_temp.append(pago)
            
            # Actualizar métricas
            metrics_service.incrementar_pagos_pendientes()
            metrics_service.contar_pago_procesado("pendiente")
            
            return pago
            
        except Exception as e:
            metrics_service.contar_pago_procesado("error")
            raise e
    
    async def procesar_pago(self, pago_id: int, estado: str):
        """Procesar un pago existente"""
        try:
            for pago in pagos_temp:
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
    
    async def obtener_pagos_pendientes(self) -> List[dict]:
        """Obtener pagos pendientes y actualizar métricas"""
        pendientes = [p for p in pagos_temp if p.get("estado") == "pendiente"]
        
        # Sincronizar métrica con realidad
        metrics_service.establecer_pagos_pendientes(len(pendientes))
        
        return pendientes

# Instancia global del servicio
pago_service = PagoService()