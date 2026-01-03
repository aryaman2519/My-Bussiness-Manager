import os
import io
from typing import List, Dict, Optional
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib.units import cm, inch
from reportlab.pdfgen import canvas

class PDFInvoiceGenerator:
    # Colors
    TEAL_COLOR = colors.HexColor("#2091A2")
    LIGHT_GRAY = colors.HexColor("#F2F2F2")
    
    def __init__(self, buffer):
        self.buffer = buffer
        self.doc = SimpleDocTemplate(
            self.buffer,
            pagesize=A4,
            rightMargin=1.5*cm,
            leftMargin=1.5*cm,
            topMargin=1.5*cm,
            bottomMargin=1.5*cm
        )
        self.styles = getSampleStyleSheet()
        self.elements = []

    def _get_image_path(self, image_input: Optional[str]) -> Optional[str]:
        """Resolves image path from input (file path or base64 - though we prefer file path now)."""
        if not image_input:
            return None
        
        # If it's a valid path on disk, return it
        if os.path.exists(image_input):
            return image_input
            
        return None

    def generate(self, business_settings: Dict, customer_data: Dict, items: List[Dict], 
                 invoice_number: str, invoice_date: str, total_amount: float):
        
        # --- Top Teal Border ---
        # Note: SimpleDocTemplate doesn't easily support absolute positioning for a top bar 
        # without using a custom page template or canvas drawing. 
        # We will use a drawing function for the header/footer graphics.
        
        # --- Header Section ---
        # Logo (Right aligned)
        logo_path = self._get_image_path(business_settings.get('logo'))
        logo_img = None
        if logo_path:
            try:
                # Aspect ratio preservation could be added here, currently fixed width
                logo_img = RLImage(logo_path, width=4*cm, height=2.5*cm)
                logo_img.hAlign = 'RIGHT'
            except Exception as e:
                print(f"Error loading logo: {e}")

        # Business Info (Center aligned)
        biz_name = business_settings.get('business_name', 'MY STORE')
        biz_addr = business_settings.get('address', '')
        biz_phone = business_settings.get('phone', '')

        header_style = ParagraphStyle(
            'Header',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=18,
            alignment=1, # Center
            spaceAfter=6
        )
        sub_header_style = ParagraphStyle(
            'SubHeader',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10,
            alignment=1, # Center
            leading=12
        )

        # Create a table for Header: Text on Left/Center, Logo on Right?
        # Actually, user template had centered text and logic. 
        # Let's stack them: Logo might push text if flowable.
        # Better: Table with [Text, Logo] or just Text and Logo below?
        # User template: Logo at D2 (Right), Text Centered.
        
        # We will use a Table for the header layout to put Logo on right and Text in center
        header_data = [
            [
                Paragraph(f"{biz_name}<br/><font size=10>{biz_addr}<br/>{biz_phone}</font>", header_style),
                logo_img if logo_img else ""
            ]
        ]
        
        header_table = Table(header_data, colWidths=[12*cm, 5*cm])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (0,0), 'CENTER'),
            ('ALIGN', (1,0), (1,0), 'RIGHT'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        
        self.elements.append(header_table)
        self.elements.append(Spacer(1, 1*cm))

        # --- Metadata (Invoice No, Date) ---
        meta_style = ParagraphStyle(
            'Meta',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10
        )
        
        meta_data = [
            [f"Date: {invoice_date}", f"S. No: {invoice_number}"]
        ]
        meta_table = Table(meta_data, colWidths=[9*cm, 9*cm])
        meta_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (0,0), 'LEFT'),  # Date Left
            ('ALIGN', (1,0), (1,0), 'RIGHT'), # Invoice No Right
        ]))
        self.elements.append(meta_table)
        self.elements.append(Spacer(1, 0.5*cm))

        # --- Bill To Section ---
        # Box styled like the Excel tempalte
        # Header "BILL TO" gray background
        # Customer Name below
        
        bill_to_style = ParagraphStyle(
            'BillToHeader',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10,
            alignment=1, # Center
            textColor=colors.black
        )
        cust_style = ParagraphStyle(
            'CustomerName',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=12,
            alignment=1, # Center
            leading=14
        )
        
        # We start indentation for Bill To box (Center roughly)
        # Excel: Col B-C. 
        # We'll make a table width 50% centered.
        
        cust_name = customer_data.get('customer_name', '')
        cust_phone = customer_data.get('customer_phone', '')
        bill_data = [
            [Paragraph("BILL TO", bill_to_style)],
            [Paragraph(f"Name: {cust_name}<br/>Mobile No: {cust_phone}", cust_style)]
        ]
        
        bill_table = Table(bill_data, colWidths=[10*cm])
        bill_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,0), self.LIGHT_GRAY),
            ('BOX', (0,0), (-1,-1), 1, colors.black),
            ('INNERGRID', (0,0), (-1,-1), 1, colors.black),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        
        # Center the table within document
        # SimpleDocTemplate flows elements. To center a table, we can just append it, 
        # but alignment works better if we wrap it or use hAlign
        bill_table.hAlign = 'CENTER'
        
        self.elements.append(bill_table)
        self.elements.append(Spacer(1, 1*cm))
        
        # --- Items Table ---
        # Headers
        table_headers = ["ITEMS", "DESCRIPTION", "QUANTITY", "AMOUNT"]
        
        # Data
        data = [table_headers]
        for idx, item in enumerate(items):
            data.append([
                str(idx + 1),
                item.get('product_name', ''),
                str(item.get('quantity', 0)),
                f"{item.get('total_price', 0.0):.2f}"
            ])
            
        # Add Rows to fill page? (Optional) - Excel didn't strictly enforce empty rows but looked like it
        # We will just list items for now.
        
        # Column widths roughly matching Excel
        # A=18, B=35, C=18, D=20 -> approx ratios
        col_widths = [2*cm, 8*cm, 3*cm, 4*cm]
        
        items_table = Table(data, colWidths=col_widths)
        
        # Styling
        ts = TableStyle([
            ('BACKGROUND', (0,0), (-1,0), self.LIGHT_GRAY), # Header bg
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 10),
            ('ALIGN', (0,0), (-1,0), 'CENTER'),
            ('ALIGN', (0,1), (0,-1), 'CENTER'), # S.No
            ('ALIGN', (1,1), (1,-1), 'LEFT'),   # Desc
            ('ALIGN', (2,1), (2,-1), 'CENTER'), # Qty
            ('ALIGN', (3,1), (3,-1), 'RIGHT'),  # Amount
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,1), (-1,-1), 10),
            ('LINEOBELOW', (0,0), (-1,0), 1, colors.black), # Header bottom line
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),     # Full grid (can be removed if minimal style preferred)
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ])
        
        # Clean look: Top and Bottom line for header, maybe just row lines
        # User template had borders on header cells.
        
        items_table.setStyle(ts)
        self.elements.append(items_table)
        self.elements.append(Spacer(1, 1*cm))
        
        # --- Totals ---
        # Aligned to right
        total_data = [
            ["TOTAL", f"{total_amount:.2f}"]
        ]
        
        total_table = Table(total_data, colWidths=[13*cm, 4*cm])
        total_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (0,0), 'RIGHT'),
            ('ALIGN', (1,0), (1,0), 'RIGHT'),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
            ('LINEABOVE', (0,0), (-1,-1), 1.5, colors.black) # Thick line top
        ]))
        self.elements.append(total_table)
        self.elements.append(Spacer(1, 2*cm))
        
        # --- Signature ---
        sig_path = self._get_image_path(business_settings.get('signature'))
        sig_img = None
        if sig_path:
            try:
                sig_img = RLImage(sig_path, width=3*cm, height=1.5*cm)
                sig_img.hAlign = 'LEFT'
            except Exception as e:
                print(f"Error loading signature: {e}")
                
        if sig_img:
            self.elements.append(sig_img)
            self.elements.append(Spacer(1, 0.2*cm))
            
        self.elements.append(Paragraph("SIGNATURE", ParagraphStyle('SigLabel', parent=self.styles['Normal'], fontName='Helvetica-Bold')))
        
        # --- Footer ---
        # Will be drawn by page template or we append at end
        # "THANK YOU FOR YOUR VISIT" with Teal background
        # Since flowable is hard to push to exact bottom, we can just append.
        
        self.elements.append(Spacer(1, 1*cm))
        footer_style = ParagraphStyle(
            'Footer',
            parent=self.styles['Normal'],
            textColor=colors.white,
            backColor=self.TEAL_COLOR,
            alignment=1, # Center
            fontName='Helvetica-Bold',
            fontSize=10,
            leading=14,
            borderPadding=5
        )
        
        self.elements.append(Paragraph("THANK YOU FOR YOUR VISIT<br/>VISIT AGAIN", footer_style))

        # Build Document
        def on_page(canvas, doc):
            canvas.saveState()
            # Draw Top Teal Border
            canvas.setFillColor(self.TEAL_COLOR)
            canvas.rect(0, A4[1] - 1.5*cm, A4[0], 0.5*cm, fill=True, stroke=False)
            canvas.restoreState()

        self.doc.build(self.elements, onFirstPage=on_page, onLaterPages=on_page)

def generate_invoice_pdf(business_settings, customer_data, items, invoice_number, invoice_date, total_amount):
    """Wrapper to generate PDF bytes"""
    buffer = io.BytesIO()
    generator = PDFInvoiceGenerator(buffer)
    generator.generate(business_settings, customer_data, items, invoice_number, invoice_date, total_amount)
    buffer.seek(0)
    return buffer.getvalue()
