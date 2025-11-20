from fastapi import APIRouter, Depends

from app.domain.user_model import Usuario
from app.schemas.user import UserProfileData, UserProfileResponse
from app.services.rbac import require_role_dependency

router = APIRouter(prefix="/api/v1/usuarios", tags=["Usuarios"])


@router.get(
    "/perfil",
    response_model=UserProfileResponse,
    summary="Consultar perfil autenticado",
    description="Endpoint protegido con JWT y RBAC que retorna información del usuario autenticado.",
)
async def obtener_perfil(
    current_user: Usuario = Depends(require_role_dependency("admin")),
) -> UserProfileResponse:
    profile = UserProfileData(
        usuario_id=current_user.usuario_id,
        usuario=current_user.nombre,
        correo=current_user.correo,
        rol=current_user.rol,
    )
    return UserProfileResponse(mensaje="Acceso permitido", data=profile, success=True)
