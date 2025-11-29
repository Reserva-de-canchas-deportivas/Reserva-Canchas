from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from app.repository.pago_repository import PagoRepository
from app.models.pago import EstadoPago
from app.models.reserva import Reserva

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
    
    



