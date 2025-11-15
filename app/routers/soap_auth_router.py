"""
Router SOAP Manual para Autenticación
Sin dependencia de fastapi-soap (tiene bugs)
"""

from fastapi import APIRouter, Response, Request
from datetime import datetime, timedelta
import logging
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

auth_soap_router = APIRouter(prefix="/soap/auth", tags=["SOAP - Auth"])


@auth_soap_router.get("")
async def get_auth_wsdl():
    """Retornar WSDL para AuthService"""
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
async def handle_auth_soap(request: Request):
    """Manejar requests SOAP de autenticación"""
    try:
        body = await request.body()
        body_str = body.decode('utf-8')
        
        logger.info(f"SOAP Auth request received")
        
        # Parsear XML
        root = ET.fromstring(body_str)
        
        # Buscar Username y Password
        username = None
        password = None
        
        for elem in root.iter():
            if 'Username' in elem.tag:
                username = elem.text
            elif 'Password' in elem.tag:
                password = elem.text
        
        logger.info(f"Login attempt for user: {username}")
        
        # Generar respuesta
        if username and password:
            token = f"soap_token_{username}_{datetime.utcnow().timestamp()}"
            expires = (datetime.utcnow() + timedelta(hours=24)).isoformat()
            success = "true"
            message = "Autenticación exitosa"
        else:
            token = ""
            expires = datetime.utcnow().isoformat()
            success = "false"
            message = "Credenciales inválidas"
        
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
        
    except Exception as e:
        logger.error(f"Error processing SOAP request: {e}", exc_info=True)
        
        fault_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        <soap:Fault>
            <faultcode>soap:Server</faultcode>
            <faultstring>Error interno: {str(e)}</faultstring>
        </soap:Fault>
    </soap:Body>
</soap:Envelope>"""
        
        return Response(content=fault_xml, media_type="text/xml", status_code=500)