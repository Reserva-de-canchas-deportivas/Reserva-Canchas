"""
Router SOAP Manual para Reservas
"""

from fastapi import APIRouter, Response, Request
import logging
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

booking_soap_router = APIRouter(prefix="/soap/booking", tags=["SOAP - Booking"])


@booking_soap_router.get("")
async def get_booking_wsdl():
    """Retornar WSDL para BookingService"""
    wsdl = """<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://schemas.xmlsoap.org/wsdl/"
             xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
             xmlns:tns="http://miempresa.com/soap/v1/booking"
             xmlns:xsd="http://www.w3.org/2001/XMLSchema"
             targetNamespace="http://miempresa.com/soap/v1/booking">
    
    <types>
        <xsd:schema targetNamespace="http://miempresa.com/soap/v1/booking">
            <xsd:element name="ConsultarDisponibilidadRequest">
                <xsd:complexType>
                    <xsd:sequence>
                        <xsd:element name="idSede" type="xsd:int"/>
                        <xsd:element name="idCancha" type="xsd:int"/>
                        <xsd:element name="fecha" type="xsd:date"/>
                    </xsd:sequence>
                </xsd:complexType>
            </xsd:element>
            <xsd:element name="ConsultarDisponibilidadResponse">
                <xsd:complexType>
                    <xsd:sequence>
                        <xsd:element name="mensaje" type="xsd:string"/>
                    </xsd:sequence>
                </xsd:complexType>
            </xsd:element>
        </xsd:schema>
    </types>
    
    <message name="ConsultarDisponibilidadRequestMsg">
        <part name="parameters" element="tns:ConsultarDisponibilidadRequest"/>
    </message>
    <message name="ConsultarDisponibilidadResponseMsg">
        <part name="parameters" element="tns:ConsultarDisponibilidadResponse"/>
    </message>
    
    <portType name="BookingServicePortType">
        <operation name="ConsultarDisponibilidad">
            <input message="tns:ConsultarDisponibilidadRequestMsg"/>
            <output message="tns:ConsultarDisponibilidadResponseMsg"/>
        </operation>
    </portType>
    
    <binding name="BookingServiceBinding" type="tns:BookingServicePortType">
        <soap:binding transport="http://schemas.xmlsoap.org/soap/http"/>
        <operation name="ConsultarDisponibilidad">
            <soap:operation soapAction="ConsultarDisponibilidad"/>
            <input><soap:body use="literal"/></input>
            <output><soap:body use="literal"/></output>
        </operation>
    </binding>
    
    <service name="BookingService">
        <port name="BookingServicePort" binding="tns:BookingServiceBinding">
            <soap:address location="http://localhost:8000/soap/booking"/>
        </port>
    </service>
</definitions>"""
    
    return Response(content=wsdl, media_type="application/xml")


@booking_soap_router.post("")
async def handle_booking_soap(request: Request):
    """Manejar requests SOAP de reservas"""
    try:
        body = await request.body()
        logger.info("SOAP Booking request received")
        
        response_xml = """<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:tns="http://miempresa.com/soap/v1/booking">
    <soap:Body>
        <tns:ConsultarDisponibilidadResponse>
            <tns:mensaje>Horarios disponibles: 08:00-09:00, 09:00-10:00</tns:mensaje>
        </tns:ConsultarDisponibilidadResponse>
    </soap:Body>
</soap:Envelope>"""
        
        return Response(content=response_xml, media_type="text/xml")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return Response(content="<error/>", media_type="text/xml", status_code=500)