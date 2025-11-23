import os

os.environ.setdefault("DISABLE_TRACING", "1")

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_root_ok():
    response = client.get("/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "online"
    assert payload["version"] == "1.0.0"


def test_health_ok():
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["db"] in {"up", "down"}


def test_soap_info():
    response = client.get("/soap/info")
    assert response.status_code == 200
    payload = response.json()
    assert "services" in payload
    assert payload["implementation"].startswith("Manual")
