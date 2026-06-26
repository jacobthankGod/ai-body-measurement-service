"""
Invoice Generator Service
====================
Generates professional PDF invoices for billing events.
"""
import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger("KORRA_INVOICE")

# Try to import PDF library, fallback to HTML-based generation
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logger.warning("reportlab not available, using HTML-based invoice generation")

# Supabase storage for PDF storage
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://blsettabymllulsxtziw.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', '')


async def generate_invoice_pdf(invoice: Dict[str, Any], db_client) -> str:
    """
    Generate and upload a PDF invoice.
    
    Args:
        invoice: Invoice data from database
        db_client: Supabase client
        
    Returns:
        Public URL of the generated PDF
    """
    invoice_id = invoice.get('id')
    user_id = invoice.get('user_id')
    
    logger.info(f"Generating invoice PDF for {invoice_id}")
    
    if PDF_AVAILABLE:
        pdf_path = await _generate_pdf_reportlab(invoice)
    else:
        pdf_path = await _generate_pdf_html(invoice)
    
    # Upload to Supabase Storage
    pdf_url = await _upload_pdf(pdf_path, invoice_id, db_client)
    
    # Update invoice with PDF URL
    try:
        db_client.table("invoices").update({
            "invoice_pdf_url": pdf_url,
            "receipt_generated_at": datetime.now().isoformat()
        }).eq("id", invoice_id).execute()
    except Exception as e:
        logger.warning(f"Could not update invoice PDF URL: {e}")
    
    return pdf_url


async def _generate_pdf_reportlab(invoice: Dict[str, Any]) -> str:
    """Generate PDF using ReportLab."""
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
    
    invoice_id = invoice.get('id')
    temp_dir = os.getenv('TMPDIR', '/tmp')
    pdf_path = os.path.join(temp_dir, f"invoice_{invoice_id}.pdf")
    
    # Create PDF document
    doc = SimpleDocTemplate(pdf_path, pagesize=letter, rightMargin=72, leftMargin=72, 
                       topMargin=72, bottomMargin=72)
    
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    normal_style = styles['Normal']
    
    # Build content
    story = []
    
    # Header
    story.append(Paragraph("KORRA", title_style))
    story.append(Paragraph("AI Body Scanning Platform", normal_style))
    story.append(Spacer(1, 0.5*inch))
    
    # Invoice details
    amount_paid = invoice.get('amount_paid', 0)
    currency = invoice.get('currency', 'NGN')
    paid_at = invoice.get('paid_at', '')
    
    if isinstance(paid_at, str) and paid_at:
        try:
            paid_at = datetime.fromisoformat(paid_at.replace('Z', '+00:00'))
            paid_at_str = paid_at.strftime('%B %d, %Y')
        except:
            paid_at_str = str(paid_at)
    else:
        paid_at_str = 'N/A'
    
    # Invoice info table
    invoice_data = [
        ['Invoice ID:', str(invoice_id)[:8]],
        ['Date:', paid_at_str],
        ['Amount:', f"{currency} {amount_paid / 100:.2f}"],
    ]
    
    if invoice.get('credits_purchased'):
        invoice_data.append(['Credits:', str(invoice.get('credits_purchased'))])
    
    t = Table(invoice_data, colWidths=[2*inch, 3*inch])
    t.setStyle(TableStyle([
        ('ALIGN', (0, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (1, -1), 8),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.5*inch))
    
    # Tax breakdown if available
    if invoice.get('tax_amount') and invoice.get('tax_amount') > 0:
        tax_data = [
            ['Subtotal:', f"{currency} {invoice.get('subtotal', 0) / 100:.2f}"],
            [f"Tax ({invoice.get('tax_rate', 0) * 100}%):", f"{currency} {invoice.get('tax_amount', 0) / 100:.2f}"],
            ['Total:', f"{currency} {amount_paid / 100:.2f}"]]
        
        tax_table = Table(tax_data, colWidths=[2*inch, 3*inch])
        tax_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (1, -1), 10),
        ]))
        story.append(tax_table)
    
    story.append(Spacer(1, 1*inch))
    
    # Footer
    story.append(Paragraph("Thank you for your business!", normal_style))
    story.append(Paragraph("KORRA - AI Body Scanning", normal_style))
    
    # Build PDF
    doc.build(story)
    
    return pdf_path


async def _generate_pdf_html(invoice: Dict[str, Any]) -> str:
    """
    Generate PDF using HTML template (fallback when reportlab unavailable).
    Uses browser print-to-PDF as a workaround.
    """
    import json
    
    invoice_id = invoice.get('id')
    amount_paid = invoice.get('amount_paid', 0)
    currency = invoice.get('currency', 'NGN')
    paid_at = invoice.get('paid_at', '')
    
    # Format date
    if isinstance(paid_at, str) and paid_at:
        try:
            paid_dt = datetime.fromisoformat(paid_at.replace('Z', '+00:00'))
            paid_at_str = paid_dt.strftime('%B %d, %Y')
        except:
            paid_at_str = str(paid_at)
    else:
        paid_at_str = 'N/A'
    
    # Build HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Invoice {invoice_id}</title>
        <style>
            body {{ font-family: Helvetica, Arial, sans-serif; padding: 40px; }}
            .header {{ margin-bottom: 40px; }}
            .title {{ font-size: 32px; font-weight: bold; color: #C6FF00; }}
            .subtitle {{ font-size: 14px; color: #666; }}
            .details {{ margin: 20px 0; }}
            .row {{ display: flex; justify-content: space-between; margin: 8px 0; }}
            .label {{ font-weight: bold; }}
            .total {{ font-size: 24px; font-weight: bold; margin-top: 20px; }}
            .footer {{ margin-top: 60px; font-size: 12px; color: #999; }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="title">KORRA</div>
            <div class="subtitle">AI Body Scanning Platform</div>
        </div>
        
        <div class="details">
            <div class="row"><span class="label">Invoice ID:</span><span>{invoice_id}</span></div>
            <div class="row"><span class="label">Date:</span><span>{paid_at_str}</span></div>
            <div class="row"><span class="label">Reference:</span><span>{invoice.get('paystack_reference', 'N/A')}</span></div>
        </div>
        
        <div class="total">
            Total Paid: {currency} {amount_paid / 100:.2f}
        </div>
        
        <div class="footer">
            Thank you for your business!<br>
            KORRA - AI Body Scanning
        </div>
    </body>
    </html>
    """
    
    # Save HTML as fallback
    temp_dir = os.getenv('TMPDIR', '/tmp')
    html_path = os.path.join(temp_dir, f"invoice_{invoice_id}.html")
    
    with open(html_path, 'w') as f:
        f.write(html)
    
    # Note: In production, you'd use a headless browser to convert HTML to PDF
    # For now, return the HTML path
    return html_path


async def _upload_pdf(pdf_path: str, invoice_id: str, db_client) -> str:
    """
    Upload PDF to Supabase Storage.
    
    Args:
        pdf_path: Local path to PDF file
        invoice_id: Invoice ID for filename
        db_client: Supabase client
        
    Returns:
        Public URL of uploaded PDF
    """
    import base64
    
    try:
        # Read PDF file
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()
        
        # Encode as base64 for storage upload
        file_name = f"invoices/{invoice_id}.pdf"
        
        # Try uploading to Supabase Storage
        try:
            result = db_client.storage.from_('invoices').upload(
                file_name,
                pdf_data,
                {"content-type": "application/pdf", "upsert": True}
            )
            
            # Get public URL
            public_url = db_client.storage.from_('invoices').get_public_url(file_name)
            
            logger.info(f"PDF uploaded: {public_url}")
            return public_url
            
        except Exception as e:
            logger.warning(f"Supabase storage upload failed: {e}")
            # Fallback: Return data URL for inline viewing
            b64_pdf = base64.b64encode(pdf_data).decode('utf-8')
            return f"data:application/pdf;base64,{b64_pdf}"
            
    except Exception as e:
        logger.error(f"PDF upload failed: {e}")
        # Return empty string on failure
        return ""


def format_invoice_for_display(invoice: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format invoice data for UI display.
    
    Args:
        invoice: Raw invoice from database
        
    Returns:
        Formatted invoice for frontend
    """
    amount_paid = invoice.get('amount_paid', 0)
    currency = invoice.get('currency', 'NGN')
    
    # Get values
    subtotal = invoice.get('subtotal', amount_paid)
    tax_amount = invoice.get('tax_amount', 0)
    
    # Format amounts
    display_amount = f"{currency} {amount_paid / 100:.2f}"
    display_subtotal = f"{currency} {subtotal / 100:.2f}"
    display_tax = f"{currency} {tax_amount / 100:.2f}" if tax_amount > 0 else None
    
    # Format date
    paid_at = invoice.get('paid_at', '')
    if isinstance(paid_at, str) and paid_at:
        try:
            paid_dt = datetime.fromisoformat(paid_at.replace('Z', '+00:00'))
            display_date = paid_dt.strftime('%b %d, %Y')
        except:
            display_date = str(paid_at)[:10]
    else:
        display_date = 'N/A'
    
    return {
        'id': invoice.get('id'),
        'date': display_date,
        'amount': display_amount,
        'subtotal': display_subtotal,
        'tax': display_tax,
        'tax_rate': f"{invoice.get('tax_rate', 0) * 100}%" if invoice.get('tax_rate') else None,
        'credits': invoice.get('credits_purchased'),
        'reference': invoice.get('paystack_reference'),
        'status': 'Paid',
        'has_pdf': bool(invoice.get('invoice_pdf_url'))
    }
