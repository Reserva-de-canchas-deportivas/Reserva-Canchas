import os
import uuid

os.environ.setdefault("DISABLE_TRACING", "1")

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.domain.user_model import Usuario
from app.services.security import get_password_hash
from main import app

client = TestClient(app)


def _create_user(
    *,
    nombre: str,
    correo: str,
    rol: str = "cliente",
    estado: str = "activo",
    contrasena: str = "secret123",
) -> Usuario:
    with SessionLocal() as db:
        user = Usuario(
            nombre=nombre,
            correo=correo,
            telefono=None,
            hash_contrasena=get_password_hash(contrasena),
            rol=rol,
            estado=estado,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user


def _admin_token() -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"correo": "admin@example.com", "contrasena": "admin123"},
    )
    assert response.status_code == 200
    return response.json()["data"]["access_token"]


def _user_token(correo: str, contrasena: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"correo": correo, "contrasena": contrasena},
    )
    assert response.status_code == 200
    return response.json()["data"]["access_token"]


def _unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"


def test_admin_can_list_users():
    _create_user(nombre="Usuario Demo", correo=_unique_email("demo"))
    token = _admin_token()

    response = client.get(
        "/api/v1/users", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["total"] >= 1
    assert isinstance(payload["data"]["items"], list)


def test_bloquear_usuario_actualiza_estado():
    user = _create_user(nombre="Para Bloquear", correo=_unique_email("block"))
    token = _admin_token()

    response = client.patch(
        f"/api/v1/users/{user.usuario_id}/estado",
        json={"estado": "bloqueado"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["estado"] == "bloqueado"
    assert payload["mensaje"].startswith("Usuario actualizado")


def test_cambiar_rol_usuario():
    user = _create_user(nombre="Para Rol", correo=_unique_email("rol"), rol="cliente")
    token = _admin_token()

    response = client.patch(
        f"/api/v1/users/{user.usuario_id}/rol",
        json={"rol": "personal"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["rol"] == "personal"


def test_no_admin_no_puede_acceder():
    correo = _unique_email("cliente")
    contrasena = "mipass123"
    _create_user(
        nombre="Cliente",
        correo=correo,
        rol="cliente",
        estado="activo",
        contrasena=contrasena,
    )
    token = _user_token(correo, contrasena)

    response = client.get(
        "/api/v1/users", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 403


def test_usuario_inexistente_retorna_404():
    token = _admin_token()
    response = client.patch(
        "/api/v1/users/no-such-user/estado",
        json={"estado": "activo"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


def test_reset_password_devuelve_token():
    correo = _unique_email("reset")
    _create_user(nombre="Reset", correo=correo, contrasena="reset123")
    token = _admin_token()

    response = client.post(
        "/api/v1/users/reset-password",
        json={"correo": correo},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["usuario_id"]
    assert payload["data"]["reset_token"]
    assert payload["data"]["expira_en_seg"] > 0
