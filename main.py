from fastapi import FastAPI
from fastapi.responses import JSONResponse
from app.config.routers import include_routers
from app.soap.soap_config import setup_soap_services, get_soap_info

# Crear la instancia de FastAPI
app = FastAPI(
    title="Mi API con FastAPI",
    description="API RESTful profesional",
    version="1.0.0"
)

# Configurar SOAP primero
setup_soap_services(app)

# Incluir routers REST
include_routers(app)

# Ruta raíz
@app.get("/")
async def root():
    """Endpoint de bienvenida"""
    return {
        "message": "¡Bienvenido a mi API con FastAPI!",
        "status": "online",
        "version": "1.0.0"
    }

# Endpoint con parámetros
@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str = None):
    """Ejemplo con parámetros de ruta y query"""
    return {
        "item_id": item_id,
        "query": q
    }

# Health check (SOLO UNA VEZ)
@app.get("/health")
async def health_check():
    """Verifica el estado del servidor"""
    return {
        "status": "healthy",
        "rest_enabled": True,
        "soap_enabled": True
    }

# Información SOAP
@app.get("/soap/info")
async def soap_info():
    """Información sobre servicios SOAP disponibles"""
    return JSONResponse(content=get_soap_info())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)