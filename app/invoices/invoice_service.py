from datetime import datetime
import uuid
from pydantic import BaseModel
from typing import List, Dict, Any

class InvoiceData(BaseModel):
    invoice_number: str
    transaction_id: str
    customer_name: str
    customer_email: str
    amount: float
    currency: str
    issue_date: datetime
    items: List[Dict[str, Any]]

class InvoiceService:
    """
    Servicio para generación de facturas y comprobantes
    """
    
    def generate_invoice(self, payment_data: dict, customer_data: dict) -> InvoiceData:
        """Genera datos de factura simulada"""
        
        invoice = InvoiceData(
            invoice_number=f"INV-{uuid.uuid4().hex[:8].upper()}",
            transaction_id=payment_data['transaction_id'],
            customer_name=customer_data.get('name', 'Cliente'),
            customer_email=customer_data.get('email', ''),
            amount=payment_data['amount'],
            currency=payment_data.get('currency', 'COP'),
            issue_date=datetime.now(),
            items=[
                {
                    "description": payment_data.get('description', 'Reserva de cancha deportiva'),
                    "quantity": 1,
                    "unit_price": payment_data['amount'],
                    "total": payment_data['amount']
                }
            ]
        )
        
        return invoice
    
    def generate_invoice_html(self, invoice: InvoiceData) -> str:
        """Genera HTML de factura (puede convertirse a PDF después)"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Factura {invoice.invoice_number}</title>
            <style>
                body {{ 
                    font-family: 'Arial', sans-serif; 
                    margin: 0;
                    padding: 20px;
                    color: #333;
                }}
                .container {{
                    max-width: 800px;
                    margin: 0 auto;
                    border: 2px solid #2c3e50;
                    border-radius: 10px;
                    padding: 30px;
                    background: #f8f9fa;
                }}
                .header {{
                    border-bottom: 3px solid #2c3e50;
                    padding-bottom: 20px;
                    margin-bottom: 30px;
                    text-align: center;
                }}
                .header h1 {{
                    color: #2c3e50;
                    margin: 0;
                    font-size: 28px;
                }}
                .details {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 20px;
                    margin-bottom: 30px;
                }}
                .detail-section {{
                    background: white;
                    padding: 15px;
                    border-radius: 5px;
                    border-left: 4px solid #3498db;
                }}
                .detail-section h3 {{
                    margin-top: 0;
                    color: #2c3e50;
                    border-bottom: 1px solid #eee;
                    padding-bottom: 5px;
                }}
                .items-table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                    background: white;
                    border-radius: 5px;
                    overflow: hidden;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }}
                .items-table th {{
                    background: #2c3e50;
                    color: white;
                    padding: 12px;
                    text-align: left;
                }}
                .items-table td {{
                    padding: 12px;
                    border-bottom: 1px solid #eee;
                }}
                .items-table tr:hover {{
                    background: #f5f5f5;
                }}
                .total-section {{
                    text-align: right;
                    margin-top: 20px;
                    padding: 20px;
                    background: #2c3e50;
                    color: white;
                    border-radius: 5px;
                }}
                .total-amount {{
                    font-size: 24px;
                    font-weight: bold;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    color: #7f8c8d;
                    font-style: italic;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>FACTURA {invoice.invoice_number}</h1>
                    <p><strong>Fecha de emisión:</strong> {invoice.issue_date.strftime('%d/%m/%Y %H:%M')}</p>
                </div>
                
                <div class="details">
                    <div class="detail-section">
                        <h3>📋 Información del Cliente</h3>
                        <p><strong>Nombre:</strong> {invoice.customer_name}</p>
                        <p><strong>Email:</strong> {invoice.customer_email}</p>
                    </div>
                    
                    <div class="detail-section">
                        <h3>🔗 Detalles de Transacción</h3>
                        <p><strong>ID Transacción:</strong> {invoice.transaction_id}</p>
                        <p><strong>N° Factura:</strong> {invoice.invoice_number}</p>
                    </div>
                </div>
                
                <h3>📦 Detalles del Servicio</h3>
                <table class="items-table">
                    <thead>
                        <tr>
                            <th>Descripción</th>
                            <th>Cantidad</th>
                            <th>Precio Unitario</th>
                            <th>Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        {"".join([f'''
                        <tr>
                            <td>{item['description']}</td>
                            <td>{item['quantity']}</td>
                            <td>${item['unit_price']:,.2f} {invoice.currency}</td>
                            <td>${item['total']:,.2f} {invoice.currency}</td>
                        </tr>
                        ''' for item in invoice.items])}
                    </tbody>
                </table>
                
                <div class="total-section">
                    <div class="total-amount">
                        TOTAL: ${invoice.amount:,.2f} {invoice.currency}
                    </div>
                    <p><small>IVA incluido donde aplique</small></p>
                </div>
                
                <div class="footer">
                    <p>🏢 <strong>Sistema de Reservas Deportivas</strong></p>
                    <p><em>Factura generada automáticamente - Este es un comprobante simulado para fines de desarrollo</em></p>
                </div>
            </div>
        </body>
        </html>
        """