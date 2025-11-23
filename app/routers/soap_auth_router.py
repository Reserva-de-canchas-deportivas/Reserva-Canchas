"""
Router SOAP Manual para Autenticacion
Sin dependencia de fastapi-soap (tiene bugs)
"""

from datetime import datetime, timedelta
import logging
import xml.etree.ElementTree as ET

from fastapi import APIRouter, Depends, Request, Response, status

from app.services.api_key_guard import require_api_key

logger = logging.getLogger(__name__)

auth_soap_router = APIRouter(prefix="/soap/auth", tags=["SOAP - Auth"])


@auth_soap_router.get("")
async def get_auth_wsdl() -> Response:
    """Retorna WSDL para AuthService (publico para consulta de contrato)."""
    wsdl = """<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://schemas.xmlsoap.org/wsdl/"
             xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
             xmlns:tns="http://miempresa.com/soap/v1/auth"
             xmlns:xsd="http://www.w3.org/2001/XMLSchema"
             targetNamespace="http://miempresa.com/soap/v1/auth">
    
    <types>
        <xsd:schema targetNamespace="http://miempresa.com/soap/v1/auth">
            <xsd:element name="LoginRequest">
                <xsd:complexType>
                    <xsd:sequence>
                        <xsd:element name="Username" type="xsd:string"/>
                        <xsd:element name="Password" type="xsd:string"/>
                    </xsd:sequence>
                </xsd:complexType>
            </xsd:element>
            <xsd:element name="LoginResponse">
                <xsd:complexType>
                    <xsd:sequence>
                        <xsd:element name="Token" type="xsd:string"/>
                        <xsd:element name="ExpiresAt" type="xsd:dateTime"/>
                        <xsd:element name="Success" type="xsd:boolean"/>
                        <xsd:element name="Message" type="xsd:string"/>
                    </xsd:sequence>
                </xsd:complexType>
            </xsd:element>
        </xsd:schema>
    </types>
    
    <message name="LoginRequestMsg">
        <part name="parameters" element="tns:LoginRequest"/>
    </message>
    <message name="LoginResponseMsg">
        <part name="parameters" element="tns:LoginResponse"/>
    </message>
    
    <portType name="AuthServicePortType">
        <operation name="Login">
            <input message="tns:LoginRequestMsg"/>
            <output message="tns:LoginResponseMsg"/>
        </operation>
    </portType>
    
    <binding name="AuthServiceBinding" type="tns:AuthServicePortType">
        <soap:binding transport="http://schemas.xmlsoap.org/soap/http"/>
        <operation name="Login">
            <soap:operation soapAction="Login"/>
            <input><soap:body use="literal"/></input>
            <output><soap:body use="literal"/></output>
        </operation>
    </binding>
    
    <service name="AuthService">
        <port name="AuthServicePort" binding="tns:AuthServiceBinding">
            <soap:address location="http://localhost:8000/soap/auth"/>
        </port>
    </service>
</definitions>"""
    return Response(content=wsdl, media_type="application/xml")


@auth_soap_router.post("")
async def handle_auth_soap(
    request: Request, api_key=Depends(require_api_key)
) -> Response:
    """Procesa solicitudes SOAP de login."""
    try:
        body_str = (await request.body()).decode("utf-8")
        logger.info("SOAP Auth request received")

        root = ET.fromstring(body_str)
        username = None
        password = None

        for elem in root.iter():
            if "Username" in elem.tag:
                username = elem.text
            elif "Password" in elem.tag:
                password = elem.text

        logger.info("Login attempt for user: %s", username)

        if username and password:
            token = f"soap_token_{username}_{datetime.utcnow().timestamp()}"
            expires = (datetime.utcnow() + timedelta(hours=24)).isoformat()
            success = "true"
            message = "Autenticacion exitosa"
        else:
            token = ""
            expires = datetime.utcnow().isoformat()
            success = "false"
            message = "Credenciales invalidas"

        response_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:tns="http://miempresa.com/soap/v1/auth">
    <soap:Body>
        <tns:LoginResponse>
            <tns:Token>{token}</tns:Token>
            <tns:ExpiresAt>{expires}</tns:ExpiresAt>
            <tns:Success>{success}</tns:Success>
            <tns:Message>{message}</tns:Message>
        </tns:LoginResponse>
    </soap:Body>
</soap:Envelope>"""

        return Response(content=response_xml, media_type="text/xml")

    except Exception as exc:  # noqa: BLE001
        logger.error("Error processing SOAP request: %s", exc, exc_info=True)

        fault_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        <soap:Fault>
            <faultcode>soap:Server</faultcode>
            <faultstring>Error interno: {str(exc)}</faultstring>
        </soap:Fault>
    </soap:Body>
</soap:Envelope>"""

        return Response(
            content=fault_xml,
            media_type="text/xml",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
