from pydantic import BaseModel, EmailStr
from typing import Optional


class LoginRequest(BaseModel):
    correo: Optional[EmailStr] = None
    telefono: Optional[str] = None
    contrasena: str


class TokensData(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expira_en_seg: int


class ApiResponse(BaseModel):
    mensaje: str
    data: Optional[TokensData] = None
    success: bool

