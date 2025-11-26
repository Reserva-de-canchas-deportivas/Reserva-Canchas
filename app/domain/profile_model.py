from __future__ import annotations

from datetime import datetime
import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from app.domain.user_model import Base, Usuario


class PerfilUsuario(Base):
    __tablename__ = "perfiles_usuario"

    perfil_id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
        nullable=False,
    )
    usuario_id = Column(
        String(36),
        ForeignKey("usuarios.usuario_id"),
        unique=True,
        nullable=False,
        index=True,
    )

    idioma = Column(String(8), nullable=False, default="es")
    notificaciones_correo = Column(Boolean, nullable=False, default=True)

    mfa_habilitado = Column(Boolean, nullable=False, default=False)
    mfa_metodo = Column(String(20), nullable=True)  # ej. "totp", "sms"
    mfa_secret = Column(String(64), nullable=True)

    creado_en = Column(DateTime, nullable=False, default=datetime.utcnow)
    actualizado_en = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    usuario = relationship(Usuario)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"PerfilUsuario(usuario_id={self.usuario_id}, "
            f"idioma={self.idioma}, "
            f"notificaciones_correo={self.notificaciones_correo}, "
            f"mfa_habilitado={self.mfa_habilitado})"
        )
