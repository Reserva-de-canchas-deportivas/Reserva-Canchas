"""
Configuración de logging para servicios SOAP
"""

import logging
import sys
from typing import Any, Dict
import json
from datetime import datetime


class SoapJsonFormatter(logging.Formatter):
    """Formateador JSON para logs SOAP"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


def configure_soap_logging(level: str = "INFO") -> None:
    """
    Configura el sistema de logging para servicios SOAP.
    
    Args:
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Configurar handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(SoapJsonFormatter())
    
    # Configurar logger para el módulo SOAP
    soap_logger = logging.getLogger("app.soap")
    soap_logger.setLevel(getattr(logging, level.upper()))
    soap_logger.addHandler(console_handler)
    soap_logger.propagate = False