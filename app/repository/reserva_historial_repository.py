from sqlalchemy.orm import Session
from typing import List
from app.models.reserva_historial import ReservaHistorial
from app.schemas.reserva_historial import ReservaHistorialCreate

class ReservaHistorialRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def crear(self, historial: ReservaHistorialCreate, reserva_id: str) -> ReservaHistorial:
        db_historial = ReservaHistorial(
            reserva_id=reserva_id,
            estado_anterior=historial.estado_anterior,
            estado_nuevo=historial.estado_nuevo,
            usuario_id=historial.usuario_id,
            comentario=historial.comentario
        )
        self.db.add(db_historial)
        self.db.commit()
        self.db.refresh(db_historial)
        return db_historial
    
    def obtener_por_reserva(self, reserva_id: str) -> List[ReservaHistorial]:
        return self.db.query(ReservaHistorial)\
            .filter(ReservaHistorial.reserva_id == reserva_id)\
            .order_by(ReservaHistorial.fecha.desc())\
            .all()