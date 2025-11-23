from pydantic import BaseModel, ConfigDict, Field


class PerfilData(BaseModel):
    idioma: str = Field(default="es", examples=["es", "en"])
    notificaciones_correo: bool = True
    mfa_habilitado: bool = False
    mfa_metodo: str | None = None

    model_config = ConfigDict(from_attributes=True)


class PerfilResponse(BaseModel):
    mensaje: str
    data: PerfilData
    success: bool = True


class PerfilUpdate(BaseModel):
    idioma: str | None = Field(default=None, min_length=2, max_length=8, examples=["es", "en"])
    notificaciones_correo: bool | None = None


class MFAActivateRequest(BaseModel):
    metodo: str = Field(default="totp", examples=["totp"])


class MFAActivateResponse(BaseModel):
    mensaje: str
    data: dict
    success: bool = True


class MFAVerifyRequest(BaseModel):
    codigo: str = Field(..., min_length=4, max_length=10)


class MFAVerifyResponse(BaseModel):
    mensaje: str
    data: PerfilData
    success: bool = True
