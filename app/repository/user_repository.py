from typing import Optional

from sqlalchemy.orm import Session

from app.domain.user_model import Usuario
from app.services.security import get_password_hash


def seed_users(db: Session) -> None:
    # Seed only if empty
    if db.query(Usuario).count() > 0:
        return
    demo_users = [
        {
            "nombre": "Admin",
            "correo": "admin@example.com",
            "telefono": None,
            "hash_contrasena": get_password_hash("admin123"),
            "rol": "admin",
            "estado": "activo",
        },
        {
            "nombre": "Cliente Bloqueado",
            "correo": "blocked@example.com",
            "telefono": None,
            "hash_contrasena": get_password_hash("blocked123"),
            "rol": "cliente",
            "estado": "bloqueado",
        },
    ]
    for u in demo_users:
        db.add(Usuario(**u))
    db.commit()


def get_by_correo(db: Session, correo: str) -> Optional[Usuario]:
    return db.query(Usuario).filter(Usuario.correo == correo).first()


def get_by_telefono(db: Session, telefono: str) -> Optional[Usuario]:
    return db.query(Usuario).filter(Usuario.telefono == telefono).first()
