import pytest
import sys
import os

def test_diagnostic_imports():
    """Test de diagnóstico para verificar imports"""
    print("\n=== DIAGNÓSTICO DE IMPORTS ===")
    
    # Verificar app.utils.logger
    try:
        from app.utils.logger import get_logger, get_request_logger, setup_structlog
        print("✅ app.utils.logger - OK")
        logger_ok = True
    except ImportError as e:
        print(f"❌ app.utils.logger - ERROR: {e}")
        logger_ok = False
    
    # Verificar app.middleware.logging_middleware
    try:
        from app.middleware.logging_middleware import LoggingMiddleware
        print("✅ app.middleware.logging_middleware - OK")
        middleware_ok = True
    except ImportError as e:
        print(f"❌ app.middleware.logging_middleware - ERROR: {e}")
        middleware_ok = False
    
    # Verificar app.config.logging_config
    try:
        from app.config.logging_config import setup_logging
        print("✅ app.config.logging_config - OK")
        config_ok = True
    except ImportError as e:
        print(f"❌ app.config.logging_config - ERROR: {e}")
        config_ok = False
    
    # Verificar app.services.example_service
    try:
        from app.services.example_service import ExampleService
        print("✅ app.services.example_service - OK")
        service_ok = True
    except ImportError as e:
        print(f"❌ app.services.example_service - ERROR: {e}")
        service_ok = False
    
    print(f"\nRESUMEN:")
    print(f"Logger: {'✅' if logger_ok else '❌'}")
    print(f"Middleware: {'✅' if middleware_ok else '❌'}")
    print(f"Config: {'✅' if config_ok else '❌'}")
    print(f"Service: {'✅' if service_ok else '❌'}")
    
    # Este test siempre pasa, es solo para diagnóstico
    assert True

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])