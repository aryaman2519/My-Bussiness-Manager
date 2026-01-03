"""
PDF Invoice Generator Service

This module handles generating PDF invoices by overlaying business data
onto a user-provided PDF template.
"""

import io
import fitz  # PyMuPDF
from PIL import Image
import base64
import json
from datetime import datetime
from typing import List, Dict, Optional, BinaryIO


class PDFInvoiceGenerator:
    """Generate invoices by overlaying data on PDF templates."""
    
    def __init__(self, template_pdf_bytes: bytes):
        """
        Initialize the PDF generator with a template.
        
        Args:
            template_pdf_bytes: The PDF template as bytes
        """
        self.template_pdf = fitz.open(stream=template_pdf_bytes, filetype="pdf")
        self.page = self.template_pdf[0]  # Assume single-page invoice
        self.page_width = self.page.rect.width
        self.page_height = self.page.rect.height
    
    def add_logo(self, logo_base64: str, coordinates: Dict[str, float]):
        """
        Add business logo to the invoice.
        
        Args:
            logo_base64: Base64-encoded image data (with or without data URI prefix)
            coordinates: Dict with 'x', 'y', 'width', 'height' in points
        """
        try:
            # Remove data URI prefix if present
            if ',' in logo_base64:
                logo_base64 = logo_base64.split(',', 1)[1]
            
            # Decode base64 image
            img_data = base64.b64decode(logo_base64)
            
            # Create rectangle for logo placement
            rect = fitz.Rect(
                coordinates.get('x', 50),
                coordinates.get('y', 50),
                coordinates.get('x', 50) + coordinates.get('width', 100),
                coordinates.get('y', 50) + coordinates.get('height', 50)
            )
            
            # Insert image
            self.page.insert_image(rect, stream=img_data)
        except Exception as e:
            print(f"Error adding logo: {e}")
    
    def add_signature(self, signature_base64: str, coordinates: Dict[str, float]):
        """
        Add signature to the invoice.
        
        Args:
            signature_base64: Base64-encoded signature image
            coordinates: Dict with 'x', 'y', 'width', 'height' in points
        """
        try:
            # Remove data URI prefix if present
            if ',' in signature_base64:
                signature_base64 = signature_base64.split(',', 1)[1]
            
            # Decode base64 image
            img_data = base64.b64decode(signature_base64)
            
            # Create rectangle for signature placement
            rect = fitz.Rect(
                coordinates.get('x', 400),
                coordinates.get('y', 700),
                coordinates.get('x', 400) + coordinates.get('width', 100),
                coordinates.get('y', 700) + coordinates.get('height', 30)
            )
            
            # Insert image
            self.page.insert_image(rect, stream=img_data)
        except Exception as e:
            print(f"Error adding signature: {e}")
    
    def add_text(self, text: str, x: float, y: float, fontsize: int = 10, 
                 fontname: str = "helv", color: tuple = (0, 0, 0), bold: bool = False):
        """
        Add text at specific coordinates.
        
        Args:
            text: Text to add
            x, y: Coordinates in points
            fontsize: Font size
            fontname: Font name (helv, cour, symb, zadb)
            color: RGB color tuple (0-1 range)
            bold: Use bold variant if available
        """
        try:
            # Use Helvetica-Bold for bold text
            if bold and fontname == "helv":
                fontname = "hebo"  # Helvetica-Bold
            
            # Convert RGB from 0-255 to 0-1 if needed
            if all(c <= 1 for c in color):
                text_color = color
            else:
                text_color = tuple(c/255 for c in color)
            
            # Insert text using Base14 fonts (no external font file needed)
            self.page.insert_text(
                (x, y),
                str(text),  # Ensure text is string
                fontsize=fontsize,
                fontname=fontname,  # Use Base14 font names
                color=text_color
            )
            return True
        except Exception as e:
            print(f"❌ Error adding text '{text}' at ({x},{y}): {e}")
            return False
    
    def add_business_header(self, business_name: str, address: str, phone: str,
                           coordinates: Dict[str, Dict[str, float]]):
        """
        Add business header information.
        
        Args:
            business_name: Name of the business
            address: Business address
            phone: Phone number(s)
            coordinates: Dict mapping field names to {x, y, fontsize} dicts
        """
        if 'business_name' in coordinates:
            coords = coordinates['business_name']
            self.add_text(
                business_name,
                coords.get('x', 50),
                coords.get('y', 100),
                fontsize=coords.get('fontsize', 16)
            )
        
        if 'address' in coordinates:
            coords = coordinates['address']
            # Handle multiline address
            lines = address.split('\n')
            for i, line in enumerate(lines):
                self.add_text(
                    line,
                    coords.get('x', 50),
                    coords.get('y', 120) + (i * 12),
                    fontsize=coords.get('fontsize', 10)
                )
        
        if 'phone' in coordinates:
            coords = coordinates['phone']
            self.add_text(
                phone,
                coords.get('x', 50),
                coords.get('y', 160),
                fontsize=coords.get('fontsize', 10)
            )
    
    def add_invoice_metadata(self, invoice_number: str, date: str,
                            coordinates: Dict[str, Dict[str, float]]):
        """
        Add invoice number and date.
        
        Args:
            invoice_number: Unique invoice number
            date: Invoice date
            coordinates: Dict mapping 'invoice_number' and 'date' to {x, y, fontsize}
        """
        if 'invoice_number' in coordinates:
            coords = coordinates['invoice_number']
            self.add_text(
                invoice_number,
                coords.get('x', 400),
                coords.get('y', 100),
                fontsize=coords.get('fontsize', 10)
            )
        
        if 'date' in coordinates:
            coords = coordinates['date']
            self.add_text(
                date,
                coords.get('x', 400),
                coords.get('y', 120),
                fontsize=coords.get('fontsize', 10)
            )
    
    def add_customer_info(self, customer_name: str, customer_phone: str,
                         coordinates: Dict[str, Dict[str, float]]):
        """
        Add customer information.
        
        Args:
            customer_name: Customer name
            customer_phone: Customer phone
            coordinates: Dict mapping field names to {x, y, fontsize}
        """
        if 'customer_name' in coordinates:
            coords = coordinates['customer_name']
            self.add_text(
                customer_name,
                coords.get('x', 50),
                coords.get('y', 200),
                fontsize=coords.get('fontsize', 10)
            )
        
        if 'customer_phone' in coordinates:
            coords = coordinates['customer_phone']
            self.add_text(
                customer_phone,
                coords.get('x', 50),
                coords.get('y', 220),
                fontsize=coords.get('fontsize', 10)
            )
    
    def add_items_table(self, items: List[Dict], 
                       table_coordinates: Dict[str, float],
                       column_positions: Dict[str, float]):
        """
        Add items to the invoice table.
        
        Args:
            items: List of dicts with 'product_name', 'quantity', 'unit_price', 'total_price'
            table_coordinates: Dict with 'start_y', 'row_height'
            column_positions: Dict mapping column names to x positions
        """
        start_y = table_coordinates.get('start_y', 300)
        row_height = table_coordinates.get('row_height', 20)
        
        for i, item in enumerate(items):
            y_pos = start_y + (i * row_height)
            
            # Item Number / S.No (if column exists)
            if 'items' in column_positions:
                self.add_text(
                    str(i + 1),  # Serial number
                    column_positions['items'],
                    y_pos,
                    fontsize=9
                )
            
            # Description/Product Name
            if 'description' in column_positions:
                self.add_text(
                    item['product_name'],
                    column_positions['description'],
                    y_pos,
                    fontsize=9
                )
            
            # Quantity
            if 'quantity' in column_positions:
                self.add_text(
                    str(item['quantity']),
                    column_positions['quantity'],
                    y_pos,
                    fontsize=9
                )
            
            # Amount (Total Price for this item)
            if 'amount' in column_positions:
                self.add_text(
                    f"{item['total_price']:.2f}",  # No rupee symbol in table
                    column_positions['amount'],
                    y_pos,
                    fontsize=9
                )
    
    def add_total(self, total_amount: float, coordinates: Dict[str, float]):
        """
        Add total amount.
        
        Args:
            total_amount: Total invoice amount
            coordinates: Dict with 'x', 'y', 'fontsize'
        """
        self.add_text(
            f"{total_amount:.2f}",  # No rupee symbol - template has "Rs. P." label
            coordinates.get('x', 450),
            coordinates.get('y', 650),
            fontsize=coordinates.get('fontsize', 12),
            bold=True  # Make total bold
        )
    
    def add_footer_messages(self, coordinates: Dict[str, Dict[str, float]]):
        """
        Add footer messages like 'THANK YOU FOR YOUR VISIT'.
        
        Args:
            coordinates: Dict mapping message names to {x, y, fontsize, text}
        """
        for msg_key, coords in coordinates.items():
            text = coords.get('text', '')
            if text:
                self.add_text(
                    text,
                    coords.get('x', 200),
                    coords.get('y', 750),
                    fontsize=coords.get('fontsize', 12)
                )
    
    def generate(self) -> bytes:
        """
        Generate the final PDF and return as bytes.
        
        Returns:
            PDF file as bytes
        """
        pdf_bytes = self.template_pdf.write()
        self.template_pdf.close()
        return pdf_bytes


def generate_invoice_number() -> str:
    """
    Generate a unique invoice number.
    
    Returns:
        Invoice number string (e.g., 'INV-20231229135532')
    """
    return f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"


def generate_invoice_pdf(
    template_pdf_bytes: bytes,
    business_settings: Dict,
    customer_data: Dict,
    items: List[Dict],
    total_amount: float,
    invoice_number: Optional[str] = None,
    invoice_date: Optional[str] = None
) -> bytes:
    """
    Main function to generate a complete invoice PDF.
    
    Args:
        template_pdf_bytes: The PDF template as bytes
        business_settings: Dict with logo, signature, name, address, phone, coordinates
        customer_data: Dict with customer_name, customer_phone
        items: List of item dicts
        total_amount: Total invoice amount
        invoice_number: Optional invoice number (auto-generated if not provided)
        invoice_date: Optional date string (uses current date if not provided)
    
    Returns:
        Complete PDF as bytes
    """
    print("=" * 60)
    print("🚀 Starting PDF Generation")
    print("=" * 60)
    
    # Create generator
    print(f"📄 Loading template PDF ({len(template_pdf_bytes)} bytes)...")
    generator = PDFInvoiceGenerator(template_pdf_bytes)
    print(f"✅ Template loaded. Page size: {generator.page_width}x{generator.page_height}")
    
    # Parse coordinates from JSON if needed
    coordinates = business_settings.get('coordinates', {})
    if isinstance(coordinates, str):
        coordinates = json.loads(coordinates)
    
    print(f"📍 Coordinates loaded: {len(coordinates)} sections")
    print(f"   Sections: {list(coordinates.keys())}")
    
    # Auto-generate invoice number if not provided
    if not invoice_number:
        invoice_number = generate_invoice_number()
    
    # Use current date if not provided
    if not invoice_date:
        invoice_date = datetime.now().strftime('%Y-%m-%d')
    
    print(f"📋 Invoice: {invoice_number}, Date: {invoice_date}")
    
    # Add logo
    if business_settings.get('logo') and coordinates.get('logo'):
        print(f"🖼️  Adding logo at {coordinates['logo']}...")
        generator.add_logo(business_settings['logo'], coordinates['logo'])
    
    # Add business header
    if coordinates.get('header'):
        print(f"🏢 Adding business header...")
        print(f"   Name: {business_settings.get('business_name', '')}")
        print(f"   Address: {business_settings.get('address', '')[:30]}...")
        print(f"   Phone: {business_settings.get('phone', '')}")
        generator.add_business_header(
            business_settings.get('business_name', ''),
            business_settings.get('address', ''),
            business_settings.get('phone', ''),
            coordinates['header']
        )
    
    # Add invoice metadata
    if coordinates.get('metadata'):
        print(f"📊 Adding invoice metadata (#{invoice_number}, {invoice_date})...")
        generator.add_invoice_metadata(
            invoice_number,
            invoice_date,
            coordinates['metadata']
        )
    
    # Add customer info
    if coordinates.get('customer'):
        print(f"👤 Adding customer: {customer_data.get('customer_name', '')}, {customer_data.get('customer_phone', '')}")
        generator.add_customer_info(
            customer_data.get('customer_name', ''),
            customer_data.get('customer_phone', ''),
            coordinates['customer']
        )
    
    # Add items table
    if coordinates.get('table'):
        print(f"📦 Adding {len(items)} items to table...")
        for i, item in enumerate(items):
            print(f"   Item {i+1}: {item.get('product_name')} x{item.get('quantity')} = ${item.get('total_price')}")
        generator.add_items_table(
            items,
            coordinates['table'],
            coordinates.get('columns', {})
        )
    
    # Add total
    if coordinates.get('total'):
        print(f"💰 Adding total: {total_amount}")
        generator.add_total(total_amount, coordinates['total'])
    
    # Add signature
    if business_settings.get('signature') and coordinates.get('signature'):
        print(f"✍️  Adding signature...")
        generator.add_signature(business_settings['signature'], coordinates['signature'])
    
    # Add footer messages
    if coordinates.get('footer'):
        print(f"📝 Adding footer messages...")
        generator.add_footer_messages(coordinates['footer'])
    
    # Generate and return PDF
    print(f"🎉 Finalizing PDF...")
    result = generator.generate()
    print(f"✅ PDF GENERATION COMPLETE! Size: {len(result)} bytes")
    print("=" * 60)
    return result
