from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.repository.user_repository import seed_users
from app.schemas.auth import LoginRequest, ApiResponse, TokensData
from app.services import auth_service
from app.domain.user_model import Usuario


router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.on_event("startup")
def on_startup_seed():
    # Seed demo users at startup
    from app.database import SessionLocal, init_db
    init_db(create_all=True)
    with SessionLocal() as db:
        seed_users(db)


@router.post("/login", response_model=ApiResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = auth_service.authenticate_user(db, payload.correo, payload.telefono, payload.contrasena)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Credentials")

    if user.estado == "bloqueado":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="USUARIO_BLOQUEADO")

    access_token, refresh_token, exp_s = auth_service.issue_tokens_for_user(user)
    return ApiResponse(
        mensaje="Login exitoso",
        data=TokensData(access_token=access_token, refresh_token=refresh_token, expira_en_seg=exp_s),
        success=True,
    )


@router.post("/refresh", response_model=ApiResponse)
def refresh(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Refresh Token")

    refresh_token = credentials.credentials
    payload = auth_service.decode_and_validate(refresh_token, expected_type="refresh")

    # Invalidate the used refresh token
    auth_service.blacklist_token(refresh_token)

    subject = payload.get("sub")
    role = payload.get("role")
    if not subject:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Refresh Token")

    # Re-issue new tokens
    from app.auth.jwt_utils import create_token
    access_token, exp_s = create_token(subject=subject, token_type="access", extra_claims={"role": role})
    new_refresh, _ = create_token(subject=subject, token_type="refresh", extra_claims={"role": role})

    return ApiResponse(
        mensaje="Tokens renovados",
        data=TokensData(access_token=access_token, refresh_token=new_refresh, expira_en_seg=exp_s),
        success=True,
    )


@router.post("/logout", response_model=ApiResponse)
def logout(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token")

    token = credentials.credentials
    # Blacklist whatever token is presented (typically refresh token per spec)
    auth_service.blacklist_token(token)
    return ApiResponse(mensaje="Logout exitoso", data=None, success=True)
