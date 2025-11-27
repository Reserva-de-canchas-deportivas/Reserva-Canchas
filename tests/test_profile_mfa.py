import os

os.environ.setdefault("DISABLE_TRACING", "1")

import pyotp  # type: ignore
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.domain.profile_model import PerfilUsuario
from main import app

client = TestClient(app)


def _admin_token() -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"correo": "admin@example.com", "contrasena": "admin123"},
    )
    assert response.status_code == 200
    return response.json()["data"]["access_token"]


def test_get_perfil_requires_auth():
    response = client.get("/api/v1/perfil")
    assert response.status_code == 401


def test_get_and_update_perfil():
    token = _admin_token()

    # GET inicial crea perfil con valores por defecto
    response = client.get(
        "/api/v1/perfil", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["idioma"] == "es"
    assert payload["data"]["notificaciones_correo"] is True
    assert payload["data"]["mfa_habilitado"] is False

    # PATCH para actualizar idioma y notificaciones
    response = client.patch(
        "/api/v1/perfil",
        headers={"Authorization": f"Bearer {token}"},
        json={"idioma": "es", "notificaciones_correo": False},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["idioma"] == "es"
    assert payload["data"]["notificaciones_correo"] is False


def test_mfa_activation_and_verification_flow():
    token = _admin_token()

    # Asegurar que existe perfil
    response = client.get(
        "/api/v1/perfil", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

    # Activar MFA
    response = client.post(
        "/api/v1/perfil/mfa/activar",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["mfa_habilitado"] is True

    # Intento con codigo invalido
    response_invalid = client.post(
        "/api/v1/perfil/mfa/verificar",
        headers={"Authorization": f"Bearer {token}"},
        json={"codigo": "000000"},
    )
    assert response_invalid.status_code == 400

    # Obtener secret real desde la base de datos
    with SessionLocal() as db:
        perfil = db.query(PerfilUsuario).first()
        assert perfil is not None
        secret = perfil.mfa_secret
        assert secret

    totp = pyotp.TOTP(secret, interval=60)
    codigo_valido = totp.now()

    response_valid = client.post(
        "/api/v1/perfil/mfa/verificar",
        headers={"Authorization": f"Bearer {token}"},
        json={"codigo": codigo_valido},
    )
    assert response_valid.status_code == 200
    payload_valid = response_valid.json()
    assert payload_valid["data"]["mfa_habilitado"] is True

