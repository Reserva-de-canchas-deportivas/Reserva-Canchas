from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class UserProfileData(BaseModel):
    usuario_id: str
    usuario: str
    correo: Optional[EmailStr] = None
    rol: str

    model_config = ConfigDict(from_attributes=True)


class UserProfileResponse(BaseModel):
    mensaje: str
    data: UserProfileData
    success: bool = True

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "mensaje": "Acceso permitido",
                "data": {"usuario": "juanperez", "rol": "admin"},
                "success": True,
            }
        }
    )


class UserAdminData(BaseModel):
    usuario_id: str
    nombre: str
    correo: Optional[EmailStr] = None
    rol: str
    estado: str
    ultimo_login: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserListData(BaseModel):
    items: List[UserAdminData]
    total: int
    page: int
    page_size: int


class UserListResponse(BaseModel):
    mensaje: str
    data: UserListData
    success: bool = True


class UserEstadoUpdate(BaseModel):
    estado: str


class UserRolUpdate(BaseModel):
    rol: str


class UserUpdateResponse(BaseModel):
    mensaje: str
    data: UserAdminData
    success: bool = True


class UserResetPasswordRequest(BaseModel):
    correo: EmailStr


class UserResetPasswordData(BaseModel):
    usuario_id: str
    reset_token: str
    expira_en_seg: int


class UserResetPasswordResponse(BaseModel):
    mensaje: str
    data: UserResetPasswordData
    success: bool = True
