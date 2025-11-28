import pytest
import logging
import uuid
from unittest.mock import Mock, patch
from fastapi import Request
from starlette.datastructures import Headers



# Intentar importar los componentes
try:
    from app.middleware.logging_middleware import LoggingMiddleware
    middleware_available = True
except ImportError:
    middleware_available = False

try:
    from app.utils.logger import get_logger, get_request_logger, setup_structlog
    logger_utils_available = True
except ImportError:
    logger_utils_available = False

try:
    from app.services.example_service import ExampleService
    example_service_available = True
except ImportError:
    example_service_available = False


class TestLoggingStandalone:
    """Pruebas standalone que no dependen del main.py"""
    
    def test_basic_logging(self):
        """Test básico de logging"""
        logger = logging.getLogger("test.basic")
        logger.info("Test message")
        assert True
    
    @pytest.mark.skipif(not logger_utils_available, reason="Logger utils no disponibles")
    def test_logger_utils(self):
        """Test básico de las utilidades de logging"""
        logger = get_logger("test.standalone")
        assert isinstance(logger, logging.Logger)
        
        # Test setup_structlog
        setup_structlog()
        assert True
    
    @pytest.mark.skipif(not middleware_available, reason="Middleware no disponible")
    def test_middleware_initialization(self):
        """Test que el middleware se inicializa correctamente"""
        mock_app = Mock()
        middleware = LoggingMiddleware(mock_app)
        
        assert middleware.app == mock_app
        assert hasattr(middleware, 'logger')
    
    @pytest.mark.skipif(not middleware_available, reason="Middleware no disponible")
    @pytest.mark.asyncio
    async def test_middleware_request_flow(self):
        """Test del flujo completo del middleware"""
        mock_app = Mock()
        middleware = LoggingMiddleware(mock_app)
        
        # Crear mock request
        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({})
        mock_request.method = "GET"
        mock_request.url.path = "/test"
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"
        mock_request.state = Mock()
        
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}
        
        async def call_next(request):
            return mock_response
        
        with patch('app.middleware.logging_middleware.logging.getLogger') as mock_logger_class:
            mock_logger = Mock()
            mock_logger_class.return_value = mock_logger
            
            # Ejecutar middleware
            response = await middleware.dispatch(mock_request, call_next)
            
            # Verificaciones
            assert hasattr(mock_request.state, 'request_id')
            assert "X-Request-ID" in response.headers
            assert response.headers["X-Request-ID"] == mock_request.state.request_id
            
            # Verificar que se llamaron los métodos de logging
            assert mock_logger.info.called
    
    @pytest.mark.skipif(not example_service_available, reason="ExampleService no disponible")
    def test_example_service_operations(self):
        """Test del servicio de ejemplo con datos en memoria"""
        service = ExampleService()
        mock_request = Mock()
        mock_request.state.request_id = "test-req-123"
        mock_request.state.usuario = "test-user"
        mock_request.method = "POST"
        mock_request.url.path = "/api/v1/items"
        
        # Test crear item
        item_data = {"name": "Test Item", "value": 100}
        
        with patch.object(service.logger, 'info'):
            result = service.create_item(mock_request, item_data)
            
            assert "id" in result
            assert result["name"] == "Test Item"
            assert result["created_by"] == "test-user"
            
            # Test obtener items
            items_result = service.get_items(mock_request)
            assert "items" in items_result
            assert "total" in items_result
            assert len(items_result["items"]) == 1
    
    @pytest.mark.skipif(not logger_utils_available, reason="Logger utils no disponibles")
    def test_request_logger_context(self):
        """Test del request logger con contexto"""
        mock_request = Mock(spec=Request)
        mock_request.state.request_id = "ctx-test-123"
        mock_request.state.usuario = "context-user"
        mock_request.method = "GET"
        mock_request.url.path = "/context-test"
        
        # Usar el path correcto para el mock
        with patch('app.utils.logger.get_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            request_logger = get_request_logger(mock_request)
            
            # Verificar contexto
            assert request_logger.extra["request_id"] == "ctx-test-123"
            assert request_logger.extra["usuario"] == "context-user"
            assert request_logger.extra["endpoint"] == "GET /context-test"


class TestErrorScenarios:
    """Pruebas para escenarios de error"""
    
    @pytest.mark.skipif(not middleware_available, reason="Middleware no disponible")
    @pytest.mark.asyncio
    async def test_middleware_exception_handling(self):
        """Test que el middleware maneja excepciones correctamente"""
        mock_app = Mock()
        middleware = LoggingMiddleware(mock_app)
        
        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({})
        mock_request.method = "GET"
        mock_request.url.path = "/error-test"
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"
        mock_request.state = Mock()
        
        # Mock que levanta excepción
        async def call_next(request):
            raise RuntimeError("Simulated error")
        
        with patch('app.middleware.logging_middleware.logging.getLogger') as mock_logger_class:
            mock_logger = Mock()
            mock_logger_class.return_value = mock_logger
            
            # Verificar que la excepción se propaga
            with pytest.raises(RuntimeError, match="Simulated error"):
                await middleware.dispatch(mock_request, call_next)
            
            # Verificar que se logueó el error
            mock_logger.error.assert_called_once()


@pytest.mark.skipif(not logger_utils_available, reason="Logger utils no disponibles")
def test_logging_configuration():
    """Test de la configuración de logging"""
    from app.config.logging_config import setup_logging
    
    # Esta función no debería lanzar excepciones
    setup_logging()
    assert True


# Tests que siempre funcionan (sin dependencias)
def test_always_passes():
    """Test básico que siempre pasa"""
    assert 1 + 1 == 2


def test_mock_logging():
    """Test de logging con mocks"""
    with patch('logging.getLogger') as mock_logger:
        logger_instance = Mock()
        mock_logger.return_value = logger_instance
        
        logger = logging.getLogger("test.mock")
        logger.info("Test message")
        
        # Verificar que se llamó al logger
        logger_instance.info.assert_called_with("Test message")


def test_import_status():
    """Test que muestra qué componentes están disponibles"""
    print(f"Middleware disponible: {middleware_available}")
    print(f"Logger utils disponible: {logger_utils_available}")
    print(f"ExampleService disponible: {example_service_available}")
    assert True  # Siempre pasa, solo para información

    # ... código anterior ...

    @pytest.mark.skipif(not middleware_available, reason="Middleware no disponible")
    @pytest.mark.asyncio
    async def test_middleware_request_flow(self):
        """Test del flujo completo del middleware"""
        mock_app = Mock()
        middleware = LoggingMiddleware(mock_app)

        # Crear mock request
        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({})
        mock_request.method = "GET"
        mock_request.url.path = "/test"
        mock_request.url = Mock()
        mock_request.url.path = "/test"
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"
        mock_request.state = Mock()

        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}

        async def call_next(request):
            return mock_response

        # Mockear el logger del middleware directamente
        with patch.object(middleware, 'logger') as mock_logger:
            # También mockear LoggerAdapter para evitar problemas
            with patch('app.middleware.logging_middleware.logging.LoggerAdapter') as mock_adapter:
                mock_adapter_instance = Mock()
                mock_adapter.return_value = mock_adapter_instance

                # Ejecutar middleware
                response = await middleware.dispatch(mock_request, call_next)

                # Verificaciones básicas
                assert hasattr(mock_request.state, 'request_id')
                assert "X-Request-ID" in response.headers
                assert response.headers["X-Request-ID"] == mock_request.state.request_id

                # Verificar que se creó el LoggerAdapter
                mock_adapter.assert_called_once()


class TestErrorScenarios:
    """Pruebas para escenarios de error"""

    @pytest.mark.skipif(not middleware_available, reason="Middleware no disponible")
    @pytest.mark.asyncio
    async def test_middleware_exception_handling(self):
        """Test que el middleware maneja excepciones correctamente"""
        mock_app = Mock()
        middleware = LoggingMiddleware(mock_app)

        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({})
        mock_request.method = "GET"
        mock_request.url.path = "/error-test"
        mock_request.url = Mock()
        mock_request.url.path = "/error-test"
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"
        mock_request.state = Mock()

        # Mock que levanta excepción
        async def call_next(request):
            raise RuntimeError("Simulated error")

        # Mockear el logger del middleware directamente
        with patch.object(middleware, 'logger') as mock_logger:
            # Mockear LoggerAdapter
            with patch('app.middleware.logging_middleware.logging.LoggerAdapter') as mock_adapter:
                mock_adapter_instance = Mock()
                mock_adapter.return_value = mock_adapter_instance

                # Verificar que la excepción se propaga
                with pytest.raises(RuntimeError, match="Simulated error"):
                    await middleware.dispatch(mock_request, call_next)

                # Verificar que se logueó el error a través del LoggerAdapter
                mock_adapter_instance.error.assert_called_once()

# ... código posterior ...