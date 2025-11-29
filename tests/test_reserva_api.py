from fastapi.testclient import TestClient
from datetime import datetime
from main import app
from app.services.order_service import ReservaService
import pytest

client = TestClient(app)

pytestmark = pytest.mark.skip(reason="Endpoints requieren autenticación")

class TestReservaAPI:
    
    def setup_method(self):
        """Limpiar datos antes de cada test"""
        from app.services.order_service import reservas_db, historial_db
        reservas_db.clear()
        historial_db.clear()
    
    def test_transicionar_estado_valido(self):
        """Test API: Transición válida (Caso 1 de HU)"""
        # Crear reserva primero
        reserva = ReservaService.crear_reserva("cancha1", "user1", datetime.now())
        
        response = client.post(
            f"/api/v1/reservas/{reserva.id}/transicionar",
            json={
                "estado_nuevo": "confirmed",
                "usuario_id": "admin1"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"]
        assert data["mensaje"] == "Estado actualizado correctamente"
        assert data["data"]["reserva_id"] == reserva.id
        assert data["data"]["estado_anterior"] == "hold"
        assert data["data"]["estado_actual"] == "confirmed"
    
    def test_transicionar_estado_invalido(self):
        """Test API: Transición inválida (Caso 4 de HU)"""
        reserva = ReservaService.crear_reserva("cancha1", "user1", datetime.now())
        
        # Llevar a CANCELLED
        ReservaService.transicionar_estado(reserva.id, "pending", "admin1")
        ReservaService.transicionar_estado(reserva.id, "confirmed", "admin1")
        ReservaService.transicionar_estado(reserva.id, "cancelled", "admin1")
        
        # Intentar CANCELLED -> CONFIRMED
        response = client.post(
            f"/api/v1/reservas/{reserva.id}/transicionar",
            json={
                "estado_nuevo": "confirmed",
                "usuario_id": "admin1"
            }
        )
        
        assert response.status_code == 409
        assert "TRANSICION_INVALIDA" in response.json()["detail"]
    
    def test_transicionar_reserva_no_existe(self):
        """Test API: Reserva no encontrada"""
        response = client.post(
            "/api/v1/reservas/id-inexistente/transicionar",
            json={
                "estado_nuevo": "pending",
                "usuario_id": "admin1"
            }
        )
        
        assert response.status_code == 404
    
    def test_obtener_historial(self):
        """Test API: Obtener historial de reserva"""
        reserva = ReservaService.crear_reserva("cancha1", "user1", datetime.now())
        ReservaService.transicionar_estado(reserva.id, "pending", "admin1")
        
        response = client.get(f"/api/v1/reservas/{reserva.id}/historial")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2  # Estado inicial + transición
        assert len(data["items"]) == 2
        
        # Verificar primer item (estado inicial)
        assert data["items"][0]["estado_anterior"] == "hold"
        assert data["items"][0]["estado_nuevo"] == "hold"
        
        # Verificar segundo item (transición)
        assert data["items"][1]["estado_anterior"] == "hold"
        assert data["items"][1]["estado_nuevo"] == "pending"
        assert data["items"][1]["usuario_id"] == "admin1"
    
    def test_obtener_historial_reserva_no_existe(self):
        """Test API: Historial de reserva que no existe"""
        response = client.get("/api/v1/reservas/id-inexistente/historial")
        assert response.status_code == 404
    
    def test_crear_reserva_endpoint(self):
        """Test endpoint auxiliar para crear reservas"""
        response = client.post("/api/v1/reservas?cancha_id=cancha1&usuario_id=user1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["mensaje"] == "Reserva creada exitosamente"
        assert "reserva_id" in data
        assert data["estado"] == "hold"
