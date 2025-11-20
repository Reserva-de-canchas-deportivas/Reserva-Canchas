from datetime import datetime, timezone
from typing import Optional, Tuple

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, ExpiredSignatureError
from sqlalchemy.orm import Session

from app.auth.jwt_utils import create_token, decode_token
from app.database import get_db
from app.repository import user_repository
from app.services.security import verify_password
from app.services.token_blacklist import blacklist
from app.services.audit_service import record_security_event
from app.services.security_responses import forbidden_error, unauthorized_error


http_bearer = HTTPBearer(auto_error=False)


def authenticate_user(db: Session, correo: Optional[str], telefono: Optional[str], contrasena: str):
    user = None
    if correo:
        user = user_repository.get_by_correo(db, correo)
    if not user and telefono:
        user = user_repository.get_by_telefono(db, telefono)
    if not user:
        return None
    if not verify_password(contrasena, user.hash_contrasena):
        return None
    return user


def issue_tokens_for_user(user) -> Tuple[str, str, int]:
    extra = {"role": user.rol}
    access_token, exp_s = create_token(subject=user.usuario_id, token_type="access", extra_claims=extra)
    refresh_token, _ = create_token(subject=user.usuario_id, token_type="refresh", extra_claims=extra)
    return access_token, refresh_token, exp_s


def decode_and_validate(token: str, expected_type: Optional[str] = None) -> dict:
    try:
        payload = decode_token(token)
    except ExpiredSignatureError:
        raise unauthorized_error("Token Expired", code="TOKEN_EXPIRED")
    except JWTError:
        raise unauthorized_error("Signature Invalid", code="SIGNATURE_INVALID")

    if expected_type and payload.get("type") != expected_type:
        raise unauthorized_error("Token inválido o ausente", code="INVALID_TOKEN_TYPE")

    # Blacklist check
    jti = payload.get("jti")
    if jti and blacklist.contains(jti):
        raise unauthorized_error("Token revocado", code="TOKEN_REVOKED")

    return payload


def blacklist_token(token: str) -> None:
    payload = decode_and_validate(token, expected_type=None)
    jti = payload.get("jti")
    exp = payload.get("exp")
    if jti and exp:
        blacklist.add(jti, int(exp))


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
    db: Session = Depends(get_db),
):
    if not credentials or not credentials.scheme.lower() == "bearer":
        record_security_event(
            db,
            event_type="TOKEN_MISSING",
            status="FAILURE",
            message="Token ausente en cabecera Authorization",
            request=request,
        )
        raise unauthorized_error("Token inválido o ausente")

    token = credentials.credentials
    try:
        payload = decode_and_validate(token, expected_type="access")
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, dict) else {}
        code = detail.get("error", {}).get("code") if isinstance(detail, dict) else None
        record_security_event(
            db,
            event_type=code or "TOKEN_INVALID",
            status="FAILURE",
            message=detail.get("error", {}).get("message") if isinstance(detail, dict) else "Token inválido",
            request=request,
        )
        raise

    user_id = payload.get("sub")
    if not user_id:
        record_security_event(
            db,
            event_type="TOKEN_WITHOUT_SUB",
            status="FAILURE",
            message="Token sin subject",
            request=request,
        )
        raise unauthorized_error("Token inválido o ausente")

    user = user_repository.get_by_id(db, user_id)
    if not user:
        record_security_event(
            db,
            event_type="USER_NOT_FOUND",
            status="FAILURE",
            message="Usuario no existe",
            request=request,
        )
        raise unauthorized_error("Token inválido o ausente")

    if user.estado != "activo":
        record_security_event(
            db,
            event_type="USER_INACTIVE",
            status="FAILURE",
            message=f"Usuario {user.usuario_id} con estado {user.estado}",
            user_id=user.usuario_id,
            role=user.rol,
            request=request,
        )
        raise forbidden_error("Usuario inactivo o bloqueado", code="USER_DISABLED")

    record_security_event(
        db,
        event_type="TOKEN_OK",
        status="SUCCESS",
        message="Token validado correctamente",
        user_id=user.usuario_id,
        role=user.rol,
        request=request,
    )
    return user

