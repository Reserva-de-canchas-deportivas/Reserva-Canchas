from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class PerfilData(BaseModel):
    idioma: str = "es"
    notificaciones_correo: bool = True
    mfa_habilitado: bool = False

    model_config = ConfigDict(from_attributes=True)


class PerfilResponse(BaseModel):
    mensaje: str
    data: PerfilData
    success: bool = True

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "mensaje": "Perfil actualizado correctamente",
                "data": {
                    "idioma": "es",
                    "notificaciones_correo": True,
                    "mfa_habilitado": True,
                },
                "success": True,
            }
        }
    )


class PerfilUpdate(BaseModel):
    idioma: Optional[str] = None
    notificaciones_correo: Optional[bool] = None

    @field_validator("idioma")
    @classmethod
    def validate_idioma(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        if value not in {"es", "en"}:
            raise ValueError("Idioma no soportado. Use 'es' o 'en'.")
        return value


class MFAActivateResponse(BaseModel):
    mensaje: str
    data: PerfilData
    success: bool = True


class MFAVerifyRequest(BaseModel):
    codigo: str


class MFAVerifyResponse(BaseModel):
    mensaje: str
    data: PerfilData
    success: bool = True

