from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional


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
