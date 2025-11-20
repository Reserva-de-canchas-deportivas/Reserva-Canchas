from __future__ import annotations

from fastapi import Depends

from app.domain.user_model import Usuario
from app.services.auth_service import get_current_user
from app.services.security_responses import forbidden_error


def _validate_role(user: Usuario, roles: tuple[str, ...]) -> Usuario:
    if roles and user.rol not in roles:
        raise forbidden_error("No tienes permisos para esta operación", code="FORBIDDEN")
    return user


def require_role_dependency(*roles: str):
    async def dependency(current_user: Usuario = Depends(get_current_user)):
        return _validate_role(current_user, roles)

    return dependency
