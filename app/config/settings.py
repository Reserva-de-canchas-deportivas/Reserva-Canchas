from pydantic_settings import BaseSettings
from pydantic import Field
import os


class Settings(BaseSettings):
    app_name: str = "Reserva Canchas API"

    # JWT settings
    access_token_expire_seconds: int = Field(default=900)  # 15 minutes
    refresh_token_expire_seconds: int = Field(default=60 * 60 * 24 * 7)  # 7 days
    jwt_algorithm: str = "RS256"

    # Keys can be provided as PEM strings via env vars or loaded from files
    private_key: str | None = None
    public_key: str | None = None
    private_key_path: str | None = Field(default=os.getenv("PRIVATE_KEY_PATH"))
    public_key_path: str | None = Field(default=os.getenv("PUBLIC_KEY_PATH"))

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

