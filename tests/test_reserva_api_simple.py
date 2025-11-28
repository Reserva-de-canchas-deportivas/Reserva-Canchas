import pytest
import sys
import os
from datetime import datetime
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Agregar el directorio raíz al path de Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

from app.api.reserva_api import router as reserva_router
from app.services.order_service import ReservaService
from app.domain.order_model import EstadoReserva

# Crear app de prueba específica para las reservas
app_test = FastAPI()
app_test.include_router(reserva_router, prefix="/api/v1", tags=["Reservas"])

client = TestClient(app_test)

class TestReservaAPISimple:
    
    def setup_method(self):
        """Limpiar datos antes de cada test"""
        from app.services.order_service import reservas_db, historial_db
        reservas_db.clear()
        historial_db.clear()
    
    def test_transicionar_estado_valido_hold_to_pending(self):
        """Test API: Transición válida HOLD → PENDING (Caso HU)"""
        # Crear reserva primero
        reserva = ReservaService.crear_reserva("cancha1", "user1", datetime.now())
        
        response = client.post(
            f"/api/v1/reservas/{reserva.id}/transicionar",
            json={
                "estado_nuevo": "pending",
                "usuario_id": "admin1"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["mensaje"] == "Estado actualizado correctamente"
        assert data["data"]["reserva_id"] == reserva.id
        assert data["data"]["estado_anterior"] == "hold"
        assert data["data"]["estado_actual"] == "pending"
    
    def test_transicionar_estado_valido_pending_to_confirmed(self):
        """Test API: Transición válida PENDING → CONFIRMED (Caso 1 de HU)"""
        # Crear reserva y llevarla a PENDING primero
        reserva = ReservaService.crear_reserva("cancha1", "user1", datetime.now())
        ReservaService.transicionar_estado(reserva.id, EstadoReserva.PENDING, "admin1")
        
        response = client.post(
            f"/api/v1/reservas/{reserva.id}/transicionar",
            json={
                "estado_nuevo": "confirmed",
                "usuario_id": "admin1"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["mensaje"] == "Estado actualizado correctamente"
        assert data["data"]["reserva_id"] == reserva.id
        assert data["data"]["estado_anterior"] == "pending"
        assert data["data"]["estado_actual"] == "confirmed"
    
    def test_transicionar_estado_valido_hold_to_expirada(self):
        """Test API: Transición válida HOLD → EXPIRADA (Caso 2 de HU)"""
        reserva = ReservaService.crear_reserva("cancha1", "user1", datetime.now())
        
        response = client.post(
            f"/api/v1/reservas/{reserva.id}/transicionar",
            json={
                "estado_nuevo": "expirada",
                "usuario_id": "admin1"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["data"]["estado_anterior"] == "hold"
        assert data["data"]["estado_actual"] == "expirada"
    
    def test_transicionar_estado_valido_confirmed_to_cancelled(self):
        """Test API: Transición válida CONFIRMED → CANCELLED (Caso 3 de HU)"""
        reserva = ReservaService.crear_reserva("cancha1", "user1", datetime.now())
        # Workflow completo: HOLD → PENDING → CONFIRMED → CANCELLED
        ReservaService.transicionar_estado(reserva.id, EstadoReserva.PENDING, "admin1")
        ReservaService.transicionar_estado(reserva.id, EstadoReserva.CONFIRMED, "admin1")
        
        response = client.post(
            f"/api/v1/reservas/{reserva.id}/transicionar",
            json={
                "estado_nuevo": "cancelled",
                "usuario_id": "user1"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["data"]["estado_anterior"] == "confirmed"
        assert data["data"]["estado_actual"] == "cancelled"
    
    def test_transicionar_estado_invalido(self):
        """Test API: Transición inválida CANCELLED → CONFIRMED (Caso 4 de HU)"""
        reserva = ReservaService.crear_reserva("cancha1", "user1", datetime.now())
        
        # Llevar a CANCELLED vía workflow válido
        ReservaService.transicionar_estado(reserva.id, EstadoReserva.PENDING, "admin1")
        ReservaService.transicionar_estado(reserva.id, EstadoReserva.CONFIRMED, "admin1")
        ReservaService.transicionar_estado(reserva.id, EstadoReserva.CANCELLED, "admin1")
        
        # Intentar transición inválida: CANCELLED -> CONFIRMED
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
        ReservaService.transicionar_estado(reserva.id, EstadoReserva.PENDING, "admin1")
        
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