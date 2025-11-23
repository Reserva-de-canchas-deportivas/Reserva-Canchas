import pyotp
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.jwt_utils import create_token
from app.database import SessionLocal, init_db
from app.domain.user_model import Usuario
from main import app


client = TestClient(app)


def _crear_usuario(db: Session) -> Usuario:
    user = db.query(Usuario).filter(Usuario.correo == "perfil@example.com").first()
    if user:
        return user
    user = Usuario(
        nombre="Perfil Usuario",
        correo="perfil@example.com",
        telefono=None,
        hash_contrasena="hash",
        rol="cliente",
        estado="activo",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _auth_headers(user: Usuario) -> dict[str, str]:
    token, _ = create_token(subject=user.usuario_id, token_type="access", extra_claims={"role": user.rol})
    return {"Authorization": f"Bearer {token}"}


def test_get_perfil_autenticado():
    init_db(create_all=True)
    with SessionLocal() as db:
        user = _crear_usuario(db)
    headers = _auth_headers(user)

    res = client.get("/api/v1/perfil", headers=headers)
    assert res.status_code == 200
    payload = res.json()
    assert payload["success"] is True
    assert payload["data"]["idioma"] == "es"


def test_patch_perfil_actualiza_idioma_y_notificaciones():
    with SessionLocal() as db:
        user = _crear_usuario(db)
    headers = _auth_headers(user)
    res = client.patch(
        "/api/v1/perfil",
        headers=headers,
        json={"idioma": "es", "notificaciones_correo": True},
    )
    assert res.status_code == 200
    payload = res.json()
    assert payload["data"]["idioma"] == "es"
    assert payload["data"]["notificaciones_correo"] is True


def test_mfa_activar_y_verificar_correcto():
    with SessionLocal() as db:
        user = _crear_usuario(db)
    headers = _auth_headers(user)
    res = client.post("/api/v1/perfil/mfa/activar", headers=headers, json={"metodo": "totp"})
    assert res.status_code == 200
    payload = res.json()
    secret = payload["data"]["secret"]
    assert payload["data"]["perfil"]["mfa_habilitado"] is True

    code = pyotp.TOTP(secret, interval=60).now()
    res_verify = client.post("/api/v1/perfil/mfa/verificar", headers=headers, json={"codigo": code})
    assert res_verify.status_code == 200
    assert res_verify.json()["data"]["mfa_habilitado"] is True


def test_mfa_codigo_invalido():
    with SessionLocal() as db:
        user = _crear_usuario(db)
    headers = _auth_headers(user)
    client.post("/api/v1/perfil/mfa/activar", headers=headers, json={"metodo": "totp"})
    bad = client.post("/api/v1/perfil/mfa/verificar", headers=headers, json={"codigo": "000000"})
    assert bad.status_code == 400


def test_perfil_sin_token():
    res = client.get("/api/v1/perfil")
    assert res.status_code == 401
