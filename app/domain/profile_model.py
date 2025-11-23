from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, UniqueConstraint

from app.domain.user_model import Base


class Perfil(Base):
    __tablename__ = "perfiles"
    __table_args__ = (UniqueConstraint("usuario_id", name="uq_perfil_usuario"),)

    perfil_id = Column(String(36), primary_key=True)
    usuario_id = Column(String(36), ForeignKey("usuarios.usuario_id"), nullable=False)
    idioma = Column(String(8), nullable=False, default="es")
    notificaciones_correo = Column(Boolean, nullable=False, default=True)
    mfa_habilitado = Column(Boolean, nullable=False, default=False)
    mfa_metodo = Column(String(16), nullable=True)
    mfa_secret = Column(String(64), nullable=True)
    creado_en = Column(DateTime, default=datetime.utcnow, nullable=False)
    actualizado_en = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
