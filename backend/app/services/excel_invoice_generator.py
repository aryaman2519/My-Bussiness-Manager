import io
import base64
import xlsxwriter
import tempfile
import os
from datetime import datetime
from typing import Dict, List, Optional
from PIL import Image as PILImage

def generate_invoice_excel(
    business_settings: Dict,
    customer_data: Dict,
    items: List[Dict],
    total_amount: float,
    invoice_number: Optional[str] = None,
    invoice_date: Optional[str] = None
) -> bytes:
    """Generate Excel invoice using xlsxwriter using physical temp files for images."""
    
    # Auto-generate meta if missing
    if not invoice_number:
        invoice_number = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    if not invoice_date:
        invoice_date = datetime.now().strftime('%d-%m-%Y')
    
    # Create in-memory Excel file
    output = io.BytesIO()
    # vital: 'in_memory': True is good, but we will use real files for insert_image
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet('Invoice')
    
    # --- Page Setup (A4) ---
    worksheet.set_paper(9)  # A4
    worksheet.set_margins(left=0.5, right=0.5, top=0.5, bottom=0.5)
    worksheet.fit_to_pages(1, 1)
    
    # --- Styles ---
    teal_bar = workbook.add_format({'bg_color': '#2091A2'})
    name_style = workbook.add_format({'bold': True, 'align': 'center', 'font_size': 22, 'font_name': 'Arial'})
    info_style = workbook.add_format({'bold': True, 'align': 'center', 'font_size': 12, 'font_name': 'Arial'})
    label_style = workbook.add_format({'font_name': 'Arial', 'font_size': 10, 'bold': True})
    
    # Footer with wrap
    footer_f = workbook.add_format({
        'bg_color': '#2091A2', 'font_color': 'white', 'bold': True, 
        'align': 'center', 'valign': 'vcenter', 'text_wrap': True
    })
    
    # Bill To styles (Borders visible)
    bill_header = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#F2F2F2', 'border': 1})
    cust_box = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'font_size': 14})
    
    table_h = workbook.add_format({'bold': True, 'top': 2, 'bottom': 2, 'align': 'center'})
    total_s = workbook.add_format({'bold': True, 'top': 2, 'num_format': '#,##0.00', 'align': 'right'})
    
    # --- Columns ---
    worksheet.set_column('A:A', 18)
    worksheet.set_column('B:B', 35)
    worksheet.set_column('C:C', 18)
    worksheet.set_column('D:D', 20)
    worksheet.set_row(0, 20, teal_bar)
    
    # --- Header Text ---
    business_name = business_settings.get('business_name', 'MY STORE')
    business_address = business_settings.get('address', '')
    phone_numbers = business_settings.get('phone', '')
    
    worksheet.merge_range('A2:D2', business_name, name_style)
    worksheet.merge_range('A3:D3', business_address, info_style)
    worksheet.merge_range('A4:D4', phone_numbers, info_style)
    
    worksheet.write('B6', f"Date: {invoice_date}", label_style)
    worksheet.write('C6', f"S. No: {invoice_number}", label_style)
    
    # --- Helper to save base64 to temp file ---
    temp_files = []
    
    def get_image_path(image_input: Optional[str], prefix: str) -> Optional[str]:
        """
        Resolves image path from input which could be:
        1. An existing file path (absolute or relative)
        2. A base64 string (data URI or raw)
        """
        if not image_input:
            return None
            
        # Case 1: Input is a valid file path
        if os.path.exists(image_input):
            return image_input
            
        # Case 2: Input is Base64 - save to temp file
        try:
            b64_str = image_input
            if ',' in b64_str:
                b64_str = b64_str.split(',', 1)[1]
            
            data = base64.b64decode(b64_str)
            
            # Create a temp file
            fd, path = tempfile.mkstemp(suffix='.png', prefix=prefix)
            with os.fdopen(fd, 'wb') as f:
                f.write(data)
            temp_files.append(path)
            return path
        except Exception as e:
            print(f"Error processing image {prefix}: {e}")
            return None

    # --- Logo Placement ---
    logo_path = get_image_path(business_settings.get('logo'), 'logo_')
    
    # Fallback to local default file
    if not logo_path and os.path.exists('logo.png'):
        logo_path = 'logo.png'

    if logo_path:
        try:
            worksheet.insert_image('D2', logo_path, {'x_scale': 0.3, 'y_scale': 0.3, 'x_offset': 15})
        except Exception as e:
            print(f"Failed to insert logo: {e}")
    
    # --- Bill To ---
    customer_name = customer_data.get('customer_name', '')
    customer_mobile = customer_data.get('customer_phone', '')
    worksheet.merge_range('B8:C8', "BILL TO", bill_header)
    worksheet.merge_range('B9:C10', f"Name: {customer_name}\nMobile No: {customer_mobile}", cust_box)
    
    # --- Table ---
    worksheet.write('A12', 'ITEMS', table_h)
    worksheet.write('B12', 'DESCRIPTION', table_h)
    worksheet.write('C12', 'QUANTITY', table_h)
    worksheet.write('D12', 'AMOUNT', table_h)
    
    row = 13
    for idx, item in enumerate(items):
        worksheet.write(row, 0, idx + 1, workbook.add_format({'align': 'center'}))
        worksheet.write(row, 1, item.get('product_name', ''))
        worksheet.write(row, 2, item.get('quantity', 0), workbook.add_format({'align': 'center'}))
        worksheet.write_number(row, 3, item.get('total_price', 0.0), workbook.add_format({'num_format': '#,##0.00', 'align': 'right'}))
        row += 1
    
    # --- Totals ---
    worksheet.write('C35', 'TOTAL', workbook.add_format({'bold': True, 'top': 2, 'align': 'right'}))
    worksheet.write_formula('D35', f'=SUM(D13:D{row})', total_s)
    
    # --- Signature ---
    sig_path = get_image_path(business_settings.get('signature'), 'sig_')
    
    # Fallback
    if not sig_path and os.path.exists('signature.png'):
        sig_path = 'signature.png'

    if sig_path:
        try:
            worksheet.insert_image('A33', sig_path, {'x_scale': 0.2, 'y_scale': 0.2})
        except Exception as e:
             print(f"Failed to insert signature: {e}")
        
    worksheet.write('A37', 'SIGNATURE', label_style)
    
    # --- Footer ---
    worksheet.merge_range('A40:D41', 'THANK YOU FOR YOUR VISIT\nVISIT AGAIN', footer_f)
    
    workbook.close()
    
    # Cleanup temp files
    for path in temp_files:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception as e:
            print(f"Error removing temp file {path}: {e}")
            
    output.seek(0)
    return output.getvalue()