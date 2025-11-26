from __future__ import annotations

from typing import Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import pyotp

from app.domain.profile_model import PerfilUsuario
from app.domain.user_model import Usuario
from app.schemas.profile import PerfilUpdate


class PerfilService:
    def __init__(self, db: Session):
        self.db = db

    def _get_profile(self, user: Usuario) -> PerfilUsuario | None:
        return (
            self.db.query(PerfilUsuario)
            .filter(PerfilUsuario.usuario_id == user.usuario_id)
            .first()
        )

    def get_or_create_profile(self, user: Usuario) -> PerfilUsuario:
        perfil = self._get_profile(user)
        if perfil is None:
            perfil = PerfilUsuario(usuario_id=user.usuario_id)
            self.db.add(perfil)
            self.db.commit()
            self.db.refresh(perfil)
        return perfil

    def get_profile(self, user: Usuario) -> PerfilUsuario:
        return self.get_or_create_profile(user)

    def update_profile(self, user: Usuario, payload: PerfilUpdate) -> PerfilUsuario:
        perfil = self.get_or_create_profile(user)

        if payload.idioma is not None:
            perfil.idioma = payload.idioma
        if payload.notificaciones_correo is not None:
            perfil.notificaciones_correo = payload.notificaciones_correo

        self.db.add(perfil)
        self.db.commit()
        self.db.refresh(perfil)
        return perfil

    def activar_mfa(self, user: Usuario) -> Tuple[PerfilUsuario, str]:
        perfil = self.get_or_create_profile(user)

        if perfil.mfa_metodo and perfil.mfa_metodo != "totp":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "MFA_METODO_INVALIDO",
                        "message": "Metodo MFA no soportado",
                    }
                },
            )

        if not perfil.mfa_secret:
            perfil.mfa_secret = pyotp.random_base32()

        perfil.mfa_metodo = "totp"
        perfil.mfa_habilitado = True

        self.db.add(perfil)
        self.db.commit()
        self.db.refresh(perfil)

        return perfil, perfil.mfa_secret

    def verificar_mfa(self, user: Usuario, codigo: str) -> PerfilUsuario:
        perfil = self.get_or_create_profile(user)

        if not perfil.mfa_secret or perfil.mfa_metodo != "totp":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "MFA_NO_CONFIGURADA",
                        "message": "MFA no esta configurada para este usuario",
                    }
                },
            )

        totp = pyotp.TOTP(perfil.mfa_secret, interval=60)
        if not totp.verify(codigo, valid_window=0):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "MFA_INVALID_CODE",
                        "message": "Codigo MFA invalido o expirado",
                    }
                },
            )

        return perfil

