from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.domain.profile_model import Perfil


def get_by_user_id(db: Session, usuario_id: str) -> Optional[Perfil]:
    return db.query(Perfil).filter(Perfil.usuario_id == usuario_id).first()


def create_default(db: Session, usuario_id: str) -> Perfil:
    perfil = Perfil(
        perfil_id=str(uuid.uuid4()),
        usuario_id=usuario_id,
        idioma="es",
        notificaciones_correo=True,
        mfa_habilitado=False,
        mfa_metodo=None,
        mfa_secret=None,
    )
    db.add(perfil)
    db.commit()
    db.refresh(perfil)
    return perfil


def update_preferences(
    db: Session, perfil: Perfil, idioma: Optional[str], notificaciones_correo: Optional[bool]
) -> Perfil:
    if idioma is not None:
        perfil.idioma = idioma
    if notificaciones_correo is not None:
        perfil.notificaciones_correo = notificaciones_correo
    db.add(perfil)
    db.commit()
    db.refresh(perfil)
    return perfil


def set_mfa(
    db: Session,
    perfil: Perfil,
    secret: str,
    metodo: str,
    habilitado: bool,
) -> Perfil:
    perfil.mfa_secret = secret
    perfil.mfa_metodo = metodo
    perfil.mfa_habilitado = habilitado
    db.add(perfil)
    db.commit()
    db.refresh(perfil)
    return perfil
