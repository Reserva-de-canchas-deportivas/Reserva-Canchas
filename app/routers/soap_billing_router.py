"""
Router SOAP Manual para Facturación
"""

from fastapi import APIRouter, Response, Request
import logging

logger = logging.getLogger(__name__)

billing_soap_router = APIRouter(prefix="/soap/billing", tags=["SOAP - Billing"])


@billing_soap_router.get("")
async def get_billing_wsdl():
    """Retornar WSDL para BillingService"""
    wsdl = """<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://schemas.xmlsoap.org/wsdl/"
             xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
             targetNamespace="http://miempresa.com/soap/v1/billing">
    <service name="BillingService">
        <port name="BillingServicePort" binding="tns:BillingServiceBinding">
            <soap:address location="http://localhost:8000/soap/billing"/>
        </port>
    </service>
</definitions>"""
    
    return Response(content=wsdl, media_type="application/xml")


@billing_soap_router.post("")
async def handle_billing_soap(request: Request):
    """Manejar requests SOAP de facturación"""
    response_xml = """<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        <Response>
            <mensaje>Servicio de facturación disponible</mensaje>
        </Response>
    </soap:Body>
</soap:Envelope>"""
    
    return Response(content=response_xml, media_type="text/xml")