from datetime import datetime, timezone
from typing import Optional, Tuple

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, ExpiredSignatureError
from sqlalchemy.orm import Session

from app.auth.jwt_utils import create_token, decode_token
from app.database import get_db
from app.repository import user_repository
from app.services.security import verify_password
from app.services.token_blacklist import blacklist


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
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token Expired")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token")

    if expected_type and payload.get("type") != expected_type:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token Type")

    # Blacklist check
    jti = payload.get("jti")
    if jti and blacklist.contains(jti):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token Revoked")

    return payload


def blacklist_token(token: str) -> None:
    payload = decode_and_validate(token, expected_type=None)
    jti = payload.get("jti")
    exp = payload.get("exp")
    if jti and exp:
        blacklist.add(jti, int(exp))


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
):
    if not credentials or not credentials.scheme.lower() == "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    token = credentials.credentials
    payload = decode_and_validate(token, expected_type="access")
    return payload  # For simplicity, return claims; could fetch user if needed

