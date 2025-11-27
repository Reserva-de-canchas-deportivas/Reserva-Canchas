import pytest
import sys
import os
from uuid import uuid4
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.factura_service import FacturaService, NumeracionService
from app.schemas.facturas import FacturaCreate, EstadoFactura

class TestNumeracionService:
    def test_obtener_siguiente_numero_con_facturas_existentes(self):
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.scalar.return_value = 100
        numeracion_service = NumeracionService(mock_db)
        siguiente_numero = numeracion_service.obtener_siguiente_numero("FCT")
        assert siguiente_numero == 101

    def test_obtener_primer_numero_sin_facturas(self):
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.scalar.return_value = None
        numeracion_service = NumeracionService(mock_db)
        siguiente_numero = numeracion_service.obtener_siguiente_numero("FCT")
        assert siguiente_numero == 1

class TestFacturaService:
    def setup_method(self):
        self.mock_db = Mock()
        self.factura_service = FacturaService(self.mock_db)
        self.factura_data = FacturaCreate(
            reserva_id=uuid4(),
            pago_id=uuid4(),
            serie="FCT"
        )

    def test_crear_factura_nueva(self):
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        self.factura_service.numeracion_service.obtener_siguiente_numero = Mock(return_value=42)
        factura = self.factura_service.crear_factura(self.factura_data, 150000.0)
        assert factura.serie == "FCT"
        assert factura.numero == 42
        assert factura.total == 150000.0
        assert factura.estado == EstadoFactura.PENDIENTE

    def test_crear_factura_idempotente(self):
        factura_existente = Mock()
        factura_existente.id = str(uuid4())
        self.mock_db.query.return_value.filter.return_value.first.return_value = factura_existente
        factura = self.factura_service.crear_factura(self.factura_data, 150000.0)
        assert factura.id == factura_existente.id

    def test_crear_factura_serie_invalida(self):
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        invalid_data = FacturaCreate(
            reserva_id=uuid4(),
            pago_id=uuid4(),
            serie="SERIE_MUY_LARGA_INVALIDA"
        )
        with pytest.raises(ValueError, match="SERIE_INVALIDA"):
            self.factura_service.crear_factura(invalid_data, 150000.0)

def test_factura_create_schema_valido():
    factura_data = FacturaCreate(
        reserva_id=uuid4(),
        pago_id=uuid4(),
        serie="FCT"
    )
    assert factura_data.serie == "FCT"

def test_factura_create_schema_serie_por_defecto():
    factura_data = FacturaCreate(
        reserva_id=uuid4(),
        pago_id=uuid4()
    )
    assert factura_data.serie == "FCT"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])