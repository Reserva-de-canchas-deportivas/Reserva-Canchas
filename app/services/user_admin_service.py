from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from jose import jwt
from sqlalchemy.orm import Session

from app.auth.jwt_utils import KeyProvider
from app.config.settings import settings
from app.domain.user_model import Usuario
from app.repository import audit_repository, user_repository


ALLOWED_ROLES = {"admin", "personal", "cliente"}
ALLOWED_ESTADOS = {"activo", "bloqueado"}


class UserAdminService:
    def __init__(self, db: Session):
        self.db = db

    def list_users(
        self, *, rol: str | None, estado: str | None, page: int, page_size: int
    ) -> dict:
        query = self.db.query(Usuario)
        if rol:
            self._validate_role_value(rol)
            query = query.filter(Usuario.rol == rol)
        if estado:
            self._validate_estado_value(estado)
            query = query.filter(Usuario.estado == estado)

        total = query.count()
        items = (
            query.order_by(Usuario.creado_en.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def cambiar_estado(self, *, user_id: str, estado: str, actor: Usuario) -> Usuario:
        self._validate_estado_value(estado)
        user = user_repository.get_by_id(self.db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "USER_NOT_FOUND", "message": "Usuario no encontrado"}},
            )

        user.estado = estado
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        self._log_event(
            event_type="USER_STATUS_CHANGE",
            message=f"Estado cambiado a {estado}",
            user=user,
            actor=actor,
            details={"estado": estado},
        )
        return user

    def cambiar_rol(self, *, user_id: str, rol: str, actor: Usuario) -> Usuario:
        self._validate_role_value(rol)
        user = user_repository.get_by_id(self.db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "USER_NOT_FOUND", "message": "Usuario no encontrado"}},
            )

        previo = user.rol
        user.rol = rol
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        self._log_event(
            event_type="USER_ROLE_CHANGE",
            message=f"Rol {previo} -> {rol}",
            user=user,
            actor=actor,
            details={"rol_anterior": previo, "rol_nuevo": rol},
        )
        return user

    def generar_reset_password(
        self, *, correo: str, actor: Usuario
    ) -> tuple[Usuario, str, int]:
        user = user_repository.get_by_correo(self.db, correo)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "USER_NOT_FOUND", "message": "Usuario no encontrado"}},
            )

        token, expira_en = self._create_reset_token(user.usuario_id)
        self._log_event(
            event_type="RESET_PASSWORD_TOKEN",
            message="Token de reset generado",
            user=user,
            actor=actor,
            details={"reset_token": token, "expira_en_seg": expira_en},
        )
        return user, token, expira_en

    def _create_reset_token(self, user_id: str) -> tuple[str, int]:
        private_key, _ = KeyProvider.load_keys()
        ttl_seconds = settings.reset_token_expire_seconds
        ahora = datetime.now(tz=timezone.utc)
        payload = {
            "sub": user_id,
            "type": "reset",
            "jti": str(uuid.uuid4()),
            "iat": int(ahora.timestamp()),
            "exp": int((ahora + timedelta(seconds=ttl_seconds)).timestamp()),
            "purpose": "reset_password",
        }
        token = jwt.encode(payload, private_key, algorithm=settings.jwt_algorithm)
        return token, ttl_seconds

    def _validate_role_value(self, rol: str) -> None:
        if rol not in ALLOWED_ROLES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "ROL_INVALIDO", "message": "Rol no permitido"}},
            )

    def _validate_estado_value(self, estado: str) -> None:
        if estado not in ALLOWED_ESTADOS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "ESTADO_INVALIDO", "message": "Estado no permitido"}},
            )

    def _log_event(
        self,
        *,
        event_type: str,
        message: str,
        user: Usuario,
        actor: Usuario,
        details: dict | None = None,
    ) -> None:
        # Guardamos auditoria en tabla centralizada
        audit_repository.log_event(
            self.db,
            event_type=event_type,
            status="SUCCESS",
            message=message,
            user_id=user.usuario_id,
            role=user.rol,
            details=json.dumps(
                {
                    "actor_id": actor.usuario_id,
                    "actor_role": actor.rol,
                    **(details or {}),
                }
            ),
        )
