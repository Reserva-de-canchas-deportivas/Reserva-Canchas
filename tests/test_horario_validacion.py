import os

os.environ.setdefault("DISABLE_TRACING", "1")

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def _admin_headers():
    resp = client.post(
        "/api/v1/auth/login",
        json={"correo": "admin@example.com", "contrasena": "admin123"},
    )
    assert resp.status_code == 200
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_validar_horario_valido():
    headers = _admin_headers()
    payload = {
        "zona_horaria": "America/Bogota",
        "horario_apertura_json": {"lunes": ["08:00-12:00", "13:00-18:00"]},
    }
    response = client.post(
        "/api/v1/sedes/validar-horario", json=payload, headers=headers
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["errores"] == []


def test_validar_horario_con_solape():
    headers = _admin_headers()
    payload = {
        "zona_horaria": "America/Bogota",
        "horario_apertura_json": {"lunes": ["08:00-10:00", "09:30-11:00"]},
    }
    response = client.post(
        "/api/v1/sedes/validar-horario", json=payload, headers=headers
    )
    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert any(err["code"] == "SOLAPE_HORARIO" for err in body["data"]["errores"])


def test_validar_zona_horaria_invalida():
    headers = _admin_headers()
    payload = {
        "zona_horaria": "America/NoExiste",
        "horario_apertura_json": {"lunes": ["08:00-10:00"]},
    }
    response = client.post(
        "/api/v1/sedes/validar-horario", json=payload, headers=headers
    )
    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert body["data"]["errores"][0]["code"] == "ZONA_HORARIA_INVALIDA"


def test_validar_rango_invertido():
    headers = _admin_headers()
    payload = {
        "zona_horaria": "America/Bogota",
        "horario_apertura_json": {"martes": ["18:00-08:00"]},
    }
    response = client.post(
        "/api/v1/sedes/validar-horario", json=payload, headers=headers
    )
    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert any(err["code"] == "RANGO_INVALIDO" for err in body["data"]["errores"])


def test_formato_incorrecto():
    headers = _admin_headers()
    payload = {
        "zona_horaria": "America/Bogota",
        "horario_apertura_json": {"miercoles": ["8:00-10:00"]},
    }
    response = client.post(
        "/api/v1/sedes/validar-horario", json=payload, headers=headers
    )
    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert any(
        err["code"] == "FORMATO_HORARIO_INVALIDO" for err in body["data"]["errores"]
    )
