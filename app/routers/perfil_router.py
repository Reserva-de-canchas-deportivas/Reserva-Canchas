from fastapi import APIRouter, Depends

from app.database import get_db
from app.domain.user_model import Usuario
from app.schemas.perfil import (
    MFAActivateRequest,
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


def get_perfil_service(db=Depends(get_db)) -> PerfilService:
    return PerfilService(db)


@router.get("", response_model=PerfilResponse, summary="Obtener perfil del usuario autenticado")
async def obtener_perfil(
    current_user: Usuario = Depends(require_role_dependency()),
    service: PerfilService = Depends(get_perfil_service),
) -> PerfilResponse:
    perfil = service.obtener(current_user)
    data = PerfilData.model_validate(perfil)
    return PerfilResponse(mensaje="Perfil obtenido correctamente", data=data, success=True)


@router.patch("", response_model=PerfilResponse, summary="Actualizar preferencias de perfil")
async def actualizar_perfil(
    payload: PerfilUpdate,
    current_user: Usuario = Depends(require_role_dependency()),
    service: PerfilService = Depends(get_perfil_service),
) -> PerfilResponse:
    perfil = service.actualizar(current_user, payload.idioma, payload.notificaciones_correo)
    data = PerfilData.model_validate(perfil)
    return PerfilResponse(mensaje="Perfil actualizado correctamente", data=data, success=True)


@router.post(
    "/mfa/activar",
    response_model=MFAActivateResponse,
    summary="Activar MFA para el usuario autenticado",
)
async def activar_mfa(
    payload: MFAActivateRequest,
    current_user: Usuario = Depends(require_role_dependency()),
    service: PerfilService = Depends(get_perfil_service),
):
    result = service.activar_mfa(current_user, metodo=payload.metodo)
    perfil = PerfilData.model_validate(result["perfil"])
    data = {
        "secret": result["secret"],
        "otpauth_url": result["otpauth_url"],
        "perfil": perfil,
    }
    return MFAActivateResponse(mensaje="MFA activado", data=data, success=True)


@router.post(
    "/mfa/verificar",
    response_model=MFAVerifyResponse,
    summary="Verificar codigo MFA",
)
async def verificar_mfa(
    payload: MFAVerifyRequest,
    current_user: Usuario = Depends(require_role_dependency()),
    service: PerfilService = Depends(get_perfil_service),
):
    perfil = service.verificar_mfa(current_user, codigo=payload.codigo)
    data = PerfilData.model_validate(perfil)
    return MFAVerifyResponse(mensaje="MFA verificado correctamente", data=data, success=True)
