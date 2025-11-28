import logging
from typing import Dict, Any
from fastapi import Request

class ExampleService:
    def __init__(self):
        self.logger = logging.getLogger("app.services.example")
        self.data = {}  # Datos temporales en memoria

    def create_item(self, request: Request, item_data: Dict[str, Any]) -> Dict[str, Any]:
        # Obtener logger con contexto de request
        request_id = getattr(request.state, "request_id", "unknown")
        usuario = getattr(request.state, "usuario", "anonimo")
        
        logger = logging.LoggerAdapter(
            self.logger,
            extra={
                "request_id": request_id,
                "usuario": usuario,
                "endpoint": "POST /items"
            }
        )
        
        logger.info("Creando nuevo item", extra={"item_data": item_data})
        
        try:
            item_id = str(len(self.data) + 1)
            self.data[item_id] = {
                "id": item_id,
                **item_data,
                "created_by": usuario
            }
            
            logger.info("Item creado exitosamente", extra={"item_id": item_id})
            
            return self.data[item_id]
            
        except Exception as e:
            logger.error(
                "Error al crear item",
                extra={"error_type": type(e).__name__, "error_message": str(e)},
                exc_info=True
            )
            raise

    def get_items(self, request: Request) -> Dict[str, Any]:
        request_id = getattr(request.state, "request_id", "unknown")
        
        logger = logging.LoggerAdapter(
            self.logger,
            extra={
                "request_id": request_id,
                "usuario": getattr(request.state, "usuario", "anonimo"),
                "endpoint": "GET /items"
            }
        )
        
        logger.info("Obteniendo lista de items", extra={"total_items": len(self.data)})
        
        return {
            "items": list(self.data.values()),
            "total": len(self.data),
            "request_id": request_id
        }