from __future__ import annotations

import pyotp
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.profile_model import Perfil
from app.domain.user_model import Usuario
from app.repository import profile_repository


class PerfilService:
    def __init__(self, db: Session):
        self.db = db

    def _ensure_perfil(self, user: Usuario) -> Perfil:
        perfil = profile_repository.get_by_user_id(self.db, user.usuario_id)
        if perfil is None:
            perfil = profile_repository.create_default(self.db, user.usuario_id)
        return perfil

    def obtener(self, user: Usuario) -> Perfil:
        return self._ensure_perfil(user)

    def actualizar(self, user: Usuario, idioma: str | None, notificaciones_correo: bool | None) -> Perfil:
        perfil = self._ensure_perfil(user)
        return profile_repository.update_preferences(self.db, perfil, idioma, notificaciones_correo)

    def activar_mfa(self, user: Usuario, metodo: str = "totp") -> dict:
        metodo = metodo.lower()
        if metodo not in {"totp"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "MFA_METODO_INVALIDO", "message": "Metodo MFA no soportado"}},
            )
        perfil = self._ensure_perfil(user)
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret, interval=60)
        profile_repository.set_mfa(self.db, perfil, secret=secret, metodo=metodo, habilitado=True)

        return {
            "perfil": perfil,
            "secret": secret,
            "otpauth_url": totp.provisioning_uri(name=user.correo or user.nombre, issuer_name="ReservaCanchas"),
        }

    def verificar_mfa(self, user: Usuario, codigo: str) -> Perfil:
        perfil = self._ensure_perfil(user)
        if not perfil.mfa_secret or not perfil.mfa_metodo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "MFA_NO_CONFIGURADO", "message": "MFA no ha sido configurado"}},
            )

        totp = pyotp.TOTP(perfil.mfa_secret, interval=60)
        if not totp.verify(codigo, valid_window=1):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "MFA_CODIGO_INVALIDO", "message": "Codigo MFA invalido o expirado"}},
            )

        perfil.mfa_habilitado = True
        self.db.add(perfil)
        self.db.commit()
        self.db.refresh(perfil)
        return perfil
