"""
Módulo SOAP para servicios legados
Compatible con Python 3.13
"""

__version__ = "1.0.0"

from .soap_config import setup_soap_services, get_soap_info

__all__ = [
    "setup_soap_services",
    "get_soap_info",
]
