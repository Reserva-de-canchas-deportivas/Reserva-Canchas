from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.domain.user_model import Usuario
from app.schemas.profile import (
    MFAActivateResponse,
    MFAVerifyRequest,
    MFAVerifyResponse,
    PerfilData,
    PerfilResponse,
    PerfilUpdate,
)
from app.services.profile_service import PerfilService
from app.services.rbac import require_role_dependency

router = APIRouter(prefix="/api/v1/perfil", tags=["Perfil"])

ANY_ROLE_DEP = require_role_dependency("admin", "personal", "cliente")


def get_perfil_service(db: Session = Depends(get_db)) -> PerfilService:
    return PerfilService(db)


@router.get(
    "",
    response_model=PerfilResponse,
    summary="Obtener perfil del usuario autenticado",
    status_code=status.HTTP_200_OK,
)
async def obtener_perfil(
    current_user: Usuario = Depends(ANY_ROLE_DEP),
    service: PerfilService = Depends(get_perfil_service),
) -> PerfilResponse:
    perfil = service.get_profile(current_user)
    data = PerfilData.model_validate(perfil)
    return PerfilResponse(
        mensaje="Perfil recuperado correctamente",
        data=data,
        success=True,
    )


@router.patch(
    "",
    response_model=PerfilResponse,
    summary="Actualizar preferencias del perfil",
    status_code=status.HTTP_200_OK,
)
async def actualizar_perfil(
    payload: PerfilUpdate,
    current_user: Usuario = Depends(ANY_ROLE_DEP),
    service: PerfilService = Depends(get_perfil_service),
) -> PerfilResponse:
    perfil = service.update_profile(current_user, payload)
    data = PerfilData.model_validate(perfil)
    return PerfilResponse(
        mensaje="Perfil actualizado correctamente",
        data=data,
        success=True,
    )


@router.post(
    "/mfa/activar",
    response_model=MFAActivateResponse,
    summary="Activar autenticacion MFA para el usuario",
    status_code=status.HTTP_200_OK,
)
async def activar_mfa(
    current_user: Usuario = Depends(ANY_ROLE_DEP),
    service: PerfilService = Depends(get_perfil_service),
) -> MFAActivateResponse:
    perfil, _secret = service.activar_mfa(current_user)
    data = PerfilData.model_validate(perfil)
    return MFAActivateResponse(
        mensaje="MFA activada correctamente",
        data=data,
        success=True,
    )


@router.post(
    "/mfa/verificar",
    response_model=MFAVerifyResponse,
    summary="Verificar codigo MFA",
    status_code=status.HTTP_200_OK,
)
async def verificar_mfa(
    payload: MFAVerifyRequest,
    current_user: Usuario = Depends(ANY_ROLE_DEP),
    service: PerfilService = Depends(get_perfil_service),
) -> MFAVerifyResponse:
    perfil = service.verificar_mfa(current_user, payload.codigo)
    data = PerfilData.model_validate(perfil)
    return MFAVerifyResponse(
        mensaje="Codigo MFA verificado correctamente",
        data=data,
        success=True,
    )

