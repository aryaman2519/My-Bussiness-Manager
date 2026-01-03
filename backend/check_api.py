import sys
import os

# Add current directory to path so 'app' module is found
current_dir = os.getcwd()
if current_dir not in sys.path:
    sys.path.append(current_dir)

print(f"Checking environment in: {current_dir}")
print(f"Python: {sys.executable}")

try:
    import reportlab
    print(f"✅ reportlab module found: {reportlab.__file__}")
except ImportError as e:
    print(f"❌ reportlab import FAILED: {e}")

try:
    from app.services.pdf_invoice_generator import generate_invoice_pdf
    print("✅ app.services.pdf_invoice_generator imported successfully")
    
    # Test generation
    print("Testing PDF generation...")
    settings = {'business_name': 'Test', 'address': 'Addr', 'phone': '123', 'logo': None, 'signature': None}
    cust = {'customer_name': 'C', 'customer_phone': 'P'}
    items = [{'product_name': 'I', 'quantity': 1, 'unit_price': 10, 'total_price': 10}]
    pdf = generate_invoice_pdf(settings, cust, items, "INV-1", "2023-01-01", 10.0)
    print(f"✅ generate_invoice_pdf SUCCEEDED. Size: {len(pdf)}")

except Exception as e:
    print(f"❌ app.services.pdf_invoice_generator FAILED: {e}")
    import traceback
    traceback.print_exc()

try:
    from app.api import billing
    print("✅ app.api.billing imported successfully")
    if hasattr(billing, 'router'):
        print("✅ billing.router is defined")
    else:
        print("❌ billing.router is MISSING")
except Exception as e:
    print(f"❌ app.api.billing import FAILED: {e}")
    import traceback
    traceback.print_exc()
