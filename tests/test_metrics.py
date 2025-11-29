import pytest
from fastapi.testclient import TestClient

from main import app
from app.services.metrics_service import metrics_service

client = TestClient(app)


class TestMetricsIntegration:
    """Pruebas de integración para métricas Prometheus."""

    def test_metrics_endpoint_accessible(self):
        """Caso 1: GET /metrics debe retornar texto Prometheus válido."""
        response = client.get("/metrics")

        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]
        assert "http_requests_total" in response.text

    def test_health_endpoint_accessible(self):
        """Health check accesible sin autenticación."""
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json().get("status") in {"healthy", "degraded"}

    def test_reserva_incrementa_metricas(self):
        """Caso 2: Incremento de reservas activas."""
        metrics_service.incrementar_reservas_activas()

        metrics_after = client.get("/metrics").text
        assert "reservas_activas_total" in metrics_after

    def test_error_incrementa_metricas(self):
        """Caso 3: Error 404/500 incrementa http_requests_total."""
        client.get("/endpoint-inexistente")

        metrics = client.get("/metrics").text
        assert 'method="GET"' in metrics
        assert 'endpoint="/endpoint-inexistente"' in metrics

    def test_metricas_personalizadas_funcionan(self):
        response = client.get("/metrics")

        assert "reservas_activas_total" in response.text
        assert "pagos_pendientes_total" in response.text
        assert "reservas_creadas_total" in response.text
        assert "pagos_procesados_total" in response.text


class TestMetricsService:
    """Pruebas unitarias para el servicio de métricas."""

    def setup_method(self):
        metrics_service.establecer_reservas_activas(0)
        metrics_service.establecer_pagos_pendientes(0)

    def test_incrementar_reservas_activas(self):
        metrics_service.incrementar_reservas_activas()
        metrics_service.incrementar_reservas_activas()

        metrics = client.get("/metrics").text
        lines = [
            line
            for line in metrics.split("\n")
            if "reservas_activas_total" in line and not line.startswith("#")
        ]
        assert len(lines) > 0

    def test_contar_reserva_creada(self):
        metrics_service.contar_reserva_creada("confirmada")
        metrics_service.contar_reserva_creada("confirmada")
        metrics_service.contar_reserva_creada("cancelada")

        metrics = client.get("/metrics").text
        assert "reservas_creadas_total" in metrics

    def test_medir_tiempo_reserva(self):
        @metrics_service.medir_tiempo_reserva("test_operation")
        def dummy_operation():
            import time

            time.sleep(0.1)
            return "done"

        result = dummy_operation()
        assert result == "done"

        metrics = client.get("/metrics").text
        assert "reserva_procesamiento_segundos" in metrics


if __name__ == "__main__":
    pytest.main([__file__, "-v"])







