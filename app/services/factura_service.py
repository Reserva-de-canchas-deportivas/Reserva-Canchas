from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import uuid4
import os
from app.models.factura import Factura, EstadoFactura
from app.schemas.facturas import FacturaCreate
from app.invoices.invoice_service import InvoiceService

class NumeracionService:
    def __init__(self, db: Session):
        self.db = db
    
    def obtener_siguiente_numero(self, serie: str) -> int:
        """Obtiene el siguiente número secuencial para una serie"""
        ultimo_numero = self.db.query(func.max(Factura.numero)).filter(
            Factura.serie == serie
        ).scalar()
        
        return (ultimo_numero or 0) + 1

class FacturaService:
    def __init__(self, db: Session):
        self.db = db
        self.numeracion_service = NumeracionService(db)
        self.invoice_service = InvoiceService()
    
    def crear_factura(self, factura_data: FacturaCreate, pago_total: float) -> Factura:
        """Crea una nueva factura con numeración secuencial (idempotente)"""
        
        # Verificar si ya existe factura para esta reserva
        factura_existente = self.db.query(Factura).filter(
            Factura.reserva_id == str(factura_data.reserva_id)
        ).first()
        
        if factura_existente:
            return factura_existente
        
        # 🆕 VALIDACIÓN DE SERIE CORREGIDA
        self._validar_serie(factura_data.serie)
        
        # Obtener siguiente número
        siguiente_numero = self.numeracion_service.obtener_siguiente_numero(
            factura_data.serie
        )
        
        # Crear factura
        factura = Factura(
            id=str(uuid4()),
            reserva_id=str(factura_data.reserva_id),
            pago_id=str(factura_data.pago_id),
            serie=factura_data.serie,
            numero=siguiente_numero,
            total=pago_total,
            moneda="COP",
            estado=EstadoFactura.PENDIENTE
        )
        
        self.db.add(factura)
        self.db.commit()
        self.db.refresh(factura)
        
        return factura
    
    def _validar_serie(self, serie: str):
        """Valida que la serie sea válida"""
        if not serie:
            raise ValueError("SERIE_INVALIDA - La serie no puede estar vacía")
        
        if len(serie) > 10:
            raise ValueError("SERIE_INVALIDA - La serie no puede tener más de 10 caracteres")
        
        # Validar que la serie solo contenga letras, números y guiones
        if not all(c.isalnum() or c in ['-', '_'] for c in serie):
            raise ValueError("SERIE_INVALIDA - La serie solo puede contener letras, números, guiones y underscores")
        
        # Validar que la serie empiece con una letra
        if not serie[0].isalpha():
            raise ValueError("SERIE_INVALIDA - La serie debe empezar con una letra")
    
    def emitir_factura(self, factura_id: str) -> Factura:
        """Proceso completo de emisión de factura con generación de documentos"""
        factura = self.db.query(Factura).filter(Factura.id == factura_id).first()
        
        if not factura:
            raise ValueError("Factura no encontrada")
        
        try:
            # Generar PDF
            pdf_url = self._generar_pdf_factura(factura)
            
            # Generar XML
            xml_url = self._generar_xml_factura(factura)
            
            # Actualizar factura
            factura.url_pdf = pdf_url
            factura.url_xml = xml_url
            factura.estado = EstadoFactura.EMITIDA
            
            self.db.commit()
            self.db.refresh(factura)
            
            return factura
            
        except Exception as e:
            # Marcar como error para reintento
            factura.estado = EstadoFactura.ERROR
            self.db.commit()
            raise e
    
    def _generar_pdf_factura(self, factura: Factura) -> str:
        """Genera PDF de factura - versión simulada"""
        nombre_archivo = f"{factura.serie}-{factura.numero:06d}.pdf"
        url_simulada = f"/facturas/pdf/{nombre_archivo}"
        
        # Generar contenido HTML usando el servicio existente
        invoice_data = {
            "transaction_id": f"FACT-{factura.serie}-{factura.numero}",
            "amount": factura.total,
            "description": f"Factura {factura.serie}-{factura.numero}",
            "currency": factura.moneda
        }
        
        customer_data = {
            "name": "Cliente",  # En producción obtener de la reserva
            "email": "cliente@example.com"
        }
        
        invoice = self.invoice_service.generate_invoice(invoice_data, customer_data)
        html_content = self.invoice_service.generate_invoice_html(invoice)
        
        # Guardar HTML temporal (en producción convertir a PDF)
        os.makedirs("facturas_temp", exist_ok=True)
        with open(f"facturas_temp/{nombre_archivo.replace('.pdf', '.html')}", "w", encoding="utf-8") as f:
            f.write(html_content)
        
        return url_simulada
    
    def _generar_xml_factura(self, factura: Factura) -> str:
        """Genera XML de factura - versión simulada"""
        nombre_archivo = f"{factura.serie}-{factura.numero:06d}.xml"
        url_simulada = f"/facturas/xml/{nombre_archivo}"
        
        # XML simulado básico (en producción integrar con DIAN)
        xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<FacturaElectronica>
    <Serie>{factura.serie}</Serie>
    <Numero>{factura.numero}</Numero>
    <Total>{factura.total}</Total>
    <Moneda>{factura.moneda}</Moneda>
    <FechaEmision>{factura.fecha_emision.isoformat() if factura.fecha_emision else ""}</FechaEmision>
</FacturaElectronica>"""
        
        # Guardar XML temporal
        os.makedirs("facturas_temp", exist_ok=True)
        with open(f"facturas_temp/{nombre_archivo}", "w", encoding="utf-8") as f:
            f.write(xml_content)
        
        return url_simulada
    
    def obtener_factura_por_reserva(self, reserva_id: str) -> Factura:
        """Obtiene factura por ID de reserva"""
        return self.db.query(Factura).filter(Factura.reserva_id == reserva_id).first()
    
    def validar_pago_para_factura(self, pago_id: str) -> bool:
        """Valida que el pago esté en estado capturado para facturar"""
        # Esta función debería integrarse con tu PagoService existente
        # Por ahora retornamos True para simular validación
        return True