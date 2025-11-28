from fastapi import APIRouter, Request, HTTPException
from app.services.example_service import ExampleService
from app.utils.logger import get_request_logger

router = APIRouter(prefix="/api/v1", tags=["example"])
service = ExampleService()

@router.post("/items")
async def create_item(request: Request, item_data: dict):
    request_logger = get_request_logger(request)
    
    request_logger.info("Solicitud para crear item")
    
    try:
        result = service.create_item(request, item_data)
        return result
    except Exception as e:
        request_logger.error(
            "Error en creación de item",
            extra={"error_type": type(e).__name__, "error_message": str(e)},
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Error al crear item")

@router.get("/items")
async def get_items(request: Request):
    request_logger = get_request_logger(request)
    
    request_logger.info("Solicitud para obtener items")
    
    try:
        result = service.get_items(request)
        return result
    except Exception as e:
        request_logger.error(
            "Error al obtener items",
            extra={"error_type": type(e).__name__, "error_message": str(e)},
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Error al obtener items")