"""
Configuracion de servicios SOAP manuales.
"""

import logging

from fastapi import FastAPI

logger = logging.getLogger(__name__)


def setup_soap_services(app: FastAPI) -> None:
    """Registrar routers SOAP en la aplicacion."""
    try:
        from app.routers.soap_auth_router import auth_soap_router
        from app.routers.soap_booking_router import booking_soap_router
        from app.routers.soap_billing_router import billing_soap_router

        app.include_router(auth_soap_router)
        app.include_router(booking_soap_router)
        app.include_router(billing_soap_router)

        logger.info("Servicios SOAP configurados")

        print("\n" + "=" * 60)
        print("SERVICIOS SOAP DISPONIBLES (Implementacion Manual)")
        print("=" * 60)
        print("Auth:    http://localhost:8000/soap/auth?wsdl")
        print("Booking: http://localhost:8000/soap/booking?wsdl")
        print("Billing: http://localhost:8000/soap/billing?wsdl")
        print("=" * 60 + "\n")

    except Exception as exc:
        logger.error("Error configurando servicios SOAP: %s", exc)
        raise


def get_soap_info() -> dict:
    """Informacion sobre los servicios SOAP disponibles."""
    return {
        "services": ["AuthService", "BookingService", "BillingService"],
        "implementation": "Manual (FastAPI nativo)",
    }
