import logging
import logging.config
import sys

def setup_logging() -> None:
    """Configura el logging estructurado para la aplicación"""
    
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "fmt": "%(timestamp)s %(levelname)s %(name)s %(message)s %(request_id)s %(usuario)s %(endpoint)s",
                "timestamp": True
            },
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s [request_id=%(request_id)s]"
            }
        },
        "handlers": {
            "default": {
                "level": "INFO",
                "formatter": "json",
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
            },
            "error": {
                "level": "ERROR",
                "formatter": "json",
                "class": "logging.StreamHandler",
                "stream": sys.stderr,
            }
        },
        "loggers": {
            "app": {
                "handlers": ["default", "error"],
                "level": "INFO",
                "propagate": False
            },
            "uvicorn": {
                "handlers": ["default"],
                "level": "INFO",
                "propagate": False
            },
            "fastapi": {
                "handlers": ["default"],
                "level": "INFO",
                "propagate": False
            }
        },
        "root": {
            "handlers": ["default"],
            "level": "INFO"
        }
    }
    
    logging.config.dictConfig(logging_config)
