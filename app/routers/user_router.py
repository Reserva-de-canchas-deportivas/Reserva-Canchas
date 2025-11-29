from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.domain.user_model import Usuario
from app.schemas.user import (
    UserAdminData,
    UserEstadoUpdate,
    UserListData,
    UserListResponse,
    UserProfileData,
    UserProfileResponse,
    UserResetPasswordData,
    UserResetPasswordRequest,
    UserResetPasswordResponse,
    UserRolUpdate,
    UserUpdateResponse,
)
from app.services.rbac import require_role_dependency
from app.services.user_admin_service import UserAdminService

router = APIRouter(prefix="/api/v1/users", tags=["Usuarios"])

ADMIN_DEP = require_role_dependency("admin")
ANY_ROLE_DEP = require_role_dependency("admin", "personal", "cliente")


def get_user_admin_service(db: Session = Depends(get_db)) -> UserAdminService:
    return UserAdminService(db)


@router.get(
    "/perfil",
    response_model=UserProfileResponse,
    summary="Consultar perfil autenticado",
    description="Endpoint protegido con JWT y RBAC que retorna informacion del usuario autenticado.",
)
async def obtener_perfil(
    current_user: Usuario = Depends(ANY_ROLE_DEP),
) -> UserProfileResponse:
    profile = UserProfileData(
        usuario_id=current_user.usuario_id,
        usuario=current_user.nombre,
        correo=current_user.correo,
        rol=current_user.rol,
    )
    return UserProfileResponse(mensaje="Acceso permitido", data=profile, success=True)


@router.get(
    "/",
    response_model=UserListResponse,
    summary="Listar usuarios (solo admin)",
)
async def listar_usuarios(
    rol: str | None = Query(None, description="Filtrar por rol"),
    estado: str | None = Query(None, description="Filtrar por estado"),
    page: int = Query(1, ge=1, description="Numero de pagina"),
    page_size: int = Query(20, ge=1, le=100, description="Cantidad por pagina"),
    service: UserAdminService = Depends(get_user_admin_service),
    _admin: Usuario = Depends(ADMIN_DEP),
) -> UserListResponse:
    resultado = service.list_users(
        rol=rol, estado=estado, page=page, page_size=page_size
    )
    data = UserListData(
        items=[UserAdminData.model_validate(u) for u in resultado["items"]],
        total=resultado["total"],
        page=resultado["page"],
        page_size=resultado["page_size"],
    )
    return UserListResponse(
        mensaje="Lista de usuarios recuperada correctamente",
        data=data,
        success=True,
    )


@router.patch(
    "/{user_id}/estado",
    response_model=UserUpdateResponse,
    summary="Cambiar estado de usuario",
)
async def cambiar_estado_usuario(
    payload: UserEstadoUpdate,
    user_id: str = Path(..., description="ID del usuario a modificar"),
    service: UserAdminService = Depends(get_user_admin_service),
    admin: Usuario = Depends(ADMIN_DEP),
) -> UserUpdateResponse:
    user = service.cambiar_estado(user_id=user_id, estado=payload.estado, actor=admin)
    return UserUpdateResponse(
        mensaje="Usuario actualizado correctamente",
        data=UserAdminData.model_validate(user),
        success=True,
    )


@router.patch(
    "/{user_id}/rol",
    response_model=UserUpdateResponse,
    summary="Cambiar rol de usuario",
)
async def cambiar_rol_usuario(
    payload: UserRolUpdate,
    user_id: str = Path(..., description="ID del usuario a modificar"),
    service: UserAdminService = Depends(get_user_admin_service),
    admin: Usuario = Depends(ADMIN_DEP),
) -> UserUpdateResponse:
    user = service.cambiar_rol(user_id=user_id, rol=payload.rol, actor=admin)
    return UserUpdateResponse(
        mensaje="Usuario actualizado correctamente",
        data=UserAdminData.model_validate(user),
        success=True,
    )


@router.post(
    "/reset-password",
    response_model=UserResetPasswordResponse,
    summary="Generar token de restablecimiento de contrasena",
)
async def generar_reset_password(
    payload: UserResetPasswordRequest,
    service: UserAdminService = Depends(get_user_admin_service),
    admin: Usuario = Depends(ADMIN_DEP),
) -> UserResetPasswordResponse:
    user, token, expira_en = service.generar_reset_password(
        correo=payload.correo, actor=admin
    )
    return UserResetPasswordResponse(
        mensaje="Token de restablecimiento generado y enviado",
        data=UserResetPasswordData(
            usuario_id=user.usuario_id,
            reset_token=token,
            expira_en_seg=expira_en,
        ),
        success=True,
    )
