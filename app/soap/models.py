"""
Modelos SOAP usando pydantic-xml
Compatible con Python 3.13
"""

from datetime import date, datetime
from typing import Optional, List
from pydantic import Field
from pydantic_xml import BaseXmlModel, element
from fastapi_soap.models import BodyContent


# ==================== MODELOS DE AUTENTICACIÓN ====================

class AuthRequest(BodyContent, tag="AuthRequest"):
    """Solicitud de autenticación SOAP"""
    username: str = element(tag="Username")
    password: str = element(tag="Password")


class AuthResponse(BodyContent, tag="AuthResponse"):
    """Respuesta de autenticación SOAP"""
    token: str = element(tag="Token")
    expires_at: datetime = element(tag="ExpiresAt")
    success: bool = element(tag="Success")
    message: str = element(tag="Message", default="")


class ValidateTokenRequest(BodyContent, tag="ValidateTokenRequest"):
    """Solicitud de validación de token"""
    token: str = element(tag="Token")


class ValidateTokenResponse(BodyContent, tag="ValidateTokenResponse"):
    """Respuesta de validación de token"""
    valid: bool = element(tag="Valid")
    username: Optional[str] = element(tag="Username", default=None)
    message: str = element(tag="Message", default="")


# ==================== MODELOS DE RESERVAS ====================

class DisponibilidadRequest(BodyContent, tag="ConsultarDisponibilidadRequest"):
    """Solicitud para consultar disponibilidad de canchas"""
    id_sede: int = element(tag="idSede")
    id_cancha: int = element(tag="idCancha")
    fecha: date = element(tag="fecha")


class HorarioDisponible(BaseXmlModel, tag="HorarioDisponible"):
    """Horario disponible"""
    hora_inicio: str = element(tag="HoraInicio")
    hora_fin: str = element(tag="HoraFin")
    disponible: bool = element(tag="Disponible")
    precio: float = element(tag="Precio")


class DisponibilidadResponse(BodyContent, tag="ConsultarDisponibilidadResponse"):
    """Respuesta con horarios disponibles"""
    horarios: List[HorarioDisponible] = element(tag="Horario", default_factory=list)
    mensaje: str = element(tag="Mensaje", default="")


class CrearReservaRequest(BodyContent, tag="CrearReservaRequest"):
    """Solicitud para crear una reserva"""
    id_sede: int = element(tag="idSede")
    id_cancha: int = element(tag="idCancha")
    fecha: date = element(tag="fecha")
    hora_inicio: str = element(tag="horaInicio")
    hora_fin: str = element(tag="horaFin")
    id_usuario: int = element(tag="idUsuario")
    nombre_cliente: str = element(tag="nombreCliente")
    telefono: str = element(tag="telefono")


class CrearReservaResponse(BodyContent, tag="CrearReservaResponse"):
    """Respuesta de creación de reserva"""
    id_reserva: int = element(tag="idReserva")
    codigo_reserva: str = element(tag="codigoReserva")
    estado: str = element(tag="estado")
    monto_total: float = element(tag="montoTotal")
    mensaje: str = element(tag="mensaje", default="")
    exito: bool = element(tag="exito")


class CancelarReservaRequest(BodyContent, tag="CancelarReservaRequest"):
    """Solicitud para cancelar una reserva"""
    id_reserva: int = element(tag="idReserva")
    motivo: str = element(tag="motivo", default="")


class CancelarReservaResponse(BodyContent, tag="CancelarReservaResponse"):
    """Respuesta de cancelación de reserva"""
    exito: bool = element(tag="exito")
    mensaje: str = element(tag="mensaje")
    monto_reembolso: Optional[float] = element(tag="montoReembolso", default=None)


# ==================== MODELOS DE FACTURACIÓN ====================

class ConsultarFacturaRequest(BodyContent, tag="ConsultarFacturaRequest"):
    """Solicitud para consultar una factura"""
    id_reserva: int = element(tag="idReserva")


class ItemFactura(BaseXmlModel, tag="ItemFactura"):
    """Item de factura"""
    descripcion: str = element(tag="Descripcion")
    cantidad: int = element(tag="Cantidad")
    precio_unitario: float = element(tag="PrecioUnitario")
    subtotal: float = element(tag="Subtotal")


class ConsultarFacturaResponse(BodyContent, tag="ConsultarFacturaResponse"):
    """Respuesta con datos de factura"""
    numero_factura: str = element(tag="NumeroFactura")
    fecha_emision: date = element(tag="FechaEmision")
    id_reserva: int = element(tag="idReserva")
    items: List[ItemFactura] = element(tag="Item", default_factory=list)
    subtotal: float = element(tag="Subtotal")
    impuestos: float = element(tag="Impuestos")
    total: float = element(tag="Total")
    estado_pago: str = element(tag="EstadoPago")
    mensaje: str = element(tag="Mensaje", default="")


class RegistrarPagoRequest(BodyContent, tag="RegistrarPagoRequest"):
    """Solicitud para registrar un pago"""
    id_reserva: int = element(tag="idReserva")
    monto: float = element(tag="monto")
    metodo_pago: str = element(tag="metodoPago")
    referencia: str = element(tag="referencia", default="")


class RegistrarPagoResponse(BodyContent, tag="RegistrarPagoResponse"):
    """Respuesta de registro de pago"""
    id_pago: int = element(tag="idPago")
    exito: bool = element(tag="exito")
    mensaje: str = element(tag="mensaje")
    comprobante: str = element(tag="comprobante", default="")
