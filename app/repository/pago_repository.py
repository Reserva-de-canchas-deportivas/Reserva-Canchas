from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.pago import Pago, EstadoPago
from sqlalchemy.exc import IntegrityError

class PagoRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def crear(self, pago_data: dict) -> Pago:
        pago = Pago(**pago_data)
        self.db.add(pago)
        self.db.commit()
        self.db.refresh(pago)
        return pago
    
    def obtener_por_id(self, pago_id: str) -> Optional[Pago]:
        return self.db.query(Pago).filter(Pago.id == pago_id).first()
    
    def obtener_por_reserva(self, reserva_id: str) -> Optional[Pago]:
        return self.db.query(Pago).filter(Pago.reserva_id == reserva_id).first()
    
    def actualizar_estado(self, pago_id: str, nuevo_estado: EstadoPago, referencia_proveedor: str = None) -> Optional[Pago]:
        pago = self.obtener_por_id(pago_id)
        if pago:
            pago.estado = nuevo_estado
            if referencia_proveedor:
                pago.referencia_proveedor = referencia_proveedor
            self.db.commit()
            self.db.refresh(pago)
        return pago
    
    def listar_por_usuario(self, usuario_id: str) -> List[Pago]:
        # Esto requiere join con reservas, se implementará después
        return self.db.query(Pago).all()  # Placeholder
    
    def existe_pago_para_reserva(self, reserva_id: str) -> bool:
        return self.db.query(Pago).filter(Pago.reserva_id == reserva_id).first() is not None