"""
View main database contents - See all business data (NOT credentials).

Usage:
    python scripts/view_database.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.models.database import SessionLocal
from app.models.user import User, UserRole
from app.models.product import Product, InventoryItem, Supplier, StockMovement
from app.models.sale import Sale, SaleItem, Warranty
from app.models.purchase import PurchaseOrder
from datetime import datetime


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def view_users(db: Session):
    """View all users."""
    print_section("USERS")
    users = db.query(User).all()
    if not users:
        print("  No users found.")
        return
    
    for user in users:
        role_icon = "👑" if user.role == UserRole.OWNER else "👤"
        status = "✅ Active" if user.is_active else "❌ Inactive"
        print(f"\n  {role_icon} {user.full_name} ({user.username})")
        print(f"     Email: {user.email}")
        print(f"     Role: {user.role.value.upper()}")
        print(f"     Status: {status}")
        print(f"     Created: {user.created_at}")


def view_suppliers(db: Session):
    """View all suppliers."""
    print_section("SUPPLIERS")
    suppliers = db.query(Supplier).all()
    if not suppliers:
        print("  No suppliers found.")
        return
    
    for supplier in suppliers:
        status = "✅ Active" if supplier.is_active else "❌ Inactive"
        print(f"\n  🏢 {supplier.name}")
        print(f"     Contact: {supplier.contact_person or 'N/A'}")
        print(f"     Email: {supplier.email or 'N/A'}")
        print(f"     Phone: {supplier.phone or 'N/A'}")
        print(f"     Status: {status}")


def view_products(db: Session):
    """View all products."""
    print_section("PRODUCTS")
    products = db.query(Product).all()
    if not products:
        print("  No products found.")
        return
    
    for product in products:
        print(f"\n  📦 {product.name} ({product.sku})")
        print(f"     Category: {product.category}")
        print(f"     Brand: {product.brand or 'N/A'}")
        print(f"     Landing Cost: ₹{product.landing_cost:,.2f}")
        print(f"     Selling Price: ₹{product.selling_price:,.2f}")
        print(f"     Profit Margin: {product.profit_margin or 0:.2f}%")
        print(f"     Barcode: {product.barcode or 'N/A'}")
        print(f"     Requires IMEI: {'Yes' if product.requires_imei else 'No'}")


def view_inventory(db: Session):
    """View inventory levels."""
    print_section("INVENTORY")
    inventory = db.query(InventoryItem).join(Product).all()
    if not inventory:
        print("  No inventory items found.")
        return
    
    for item in inventory:
        available = item.quantity - item.reserved_quantity
        status_icon = "🔴" if available < (item.min_stock_level or 0) else "🟢"
        print(f"\n  {status_icon} {item.product.name}")
        print(f"     SKU: {item.product.sku}")
        print(f"     Quantity: {item.quantity}")
        print(f"     Reserved: {item.reserved_quantity}")
        print(f"     Available: {available}")
        print(f"     Daily Velocity: {item.daily_velocity:.2f} units/day")
        if item.days_of_inventory_remaining:
            print(f"     Days Remaining: {item.days_of_inventory_remaining:.1f} days")
        if item.min_stock_level:
            print(f"     Min Stock Level: {item.min_stock_level}")


def view_sales(db: Session):
    """View recent sales."""
    print_section("RECENT SALES (Last 10)")
    sales = db.query(Sale).order_by(Sale.created_at.desc()).limit(10).all()
    if not sales:
        print("  No sales found.")
        return
    
    for sale in sales:
        print(f"\n  🧾 Invoice: {sale.invoice_number}")
        print(f"     Customer: {sale.customer_name or 'Walk-in'}")
        print(f"     Phone: {sale.customer_phone or 'N/A'}")
        print(f"     Amount: ₹{sale.final_amount:,.2f}")
        print(f"     Payment: {sale.payment_method.value}")
        print(f"     Status: {sale.status.value}")
        print(f"     Date: {sale.created_at}")


def view_warranties(db: Session):
    """View warranties."""
    print_section("WARRANTIES")
    warranties = db.query(Warranty).all()
    if not warranties:
        print("  No warranties found.")
        return
    
    for warranty in warranties:
        product = db.query(Product).filter(Product.id == warranty.product_id).first()
        status = "✅ Active" if warranty.is_active else "❌ Expired"
        print(f"\n  📱 IMEI: {warranty.imei or 'N/A'}")
        print(f"     Product: {product.name if product else 'N/A'}")
        print(f"     Customer: {warranty.customer_name or 'N/A'}")
        print(f"     Phone: {warranty.customer_phone or 'N/A'}")
        print(f"     Warranty Period: {warranty.warranty_period_months} months")
        print(f"     Start Date: {warranty.warranty_start_date}")
        print(f"     End Date: {warranty.warranty_end_date}")
        print(f"     Status: {status}")
        print(f"     Claims: {warranty.claims_count}")


def view_statistics(db: Session):
    """View database statistics."""
    print_section("DATABASE STATISTICS")
    
    user_count = db.query(User).count()
    owner_count = db.query(User).filter(User.role == UserRole.OWNER).count()
    staff_count = db.query(User).filter(User.role == UserRole.STAFF).count()
    
    product_count = db.query(Product).count()
    inventory_count = db.query(InventoryItem).count()
    supplier_count = db.query(Supplier).count()
    sale_count = db.query(Sale).count()
    warranty_count = db.query(Warranty).count()
    
    total_inventory_value = 0
    for item in db.query(InventoryItem).join(Product).all():
        total_inventory_value += item.quantity * item.product.landing_cost
    
    total_sales_value = db.query(Sale).with_entities(
        db.func.sum(Sale.final_amount)
    ).scalar() or 0
    
    print(f"\n  👥 Users: {user_count} (👑 {owner_count} Owners, 👤 {staff_count} Staff)")
    print(f"  📦 Products: {product_count}")
    print(f"  📊 Inventory Items: {inventory_count}")
    print(f"  🏢 Suppliers: {supplier_count}")
    print(f"  🧾 Sales: {sale_count}")
    print(f"  📱 Warranties: {warranty_count}")
    print(f"  💰 Total Inventory Value: ₹{total_inventory_value:,.2f}")
    print(f"  💵 Total Sales Value: ₹{total_sales_value:,.2f}")


def main():
    """Main function to view all database data."""
    print("\n" + "=" * 60)
    print("  SmartStock 360 - Database Viewer")
    print("=" * 60)
    
    db: Session = SessionLocal()
    try:
        view_statistics(db)
        view_users(db)
        view_suppliers(db)
        view_products(db)
        view_inventory(db)
        view_sales(db)
        view_warranties(db)
        
        print("\n" + "=" * 60)
        print("  End of Report")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error viewing database: {e}")
        print("\nMake sure:")
        print("  1. Database is initialized (run: python scripts/init_database.py)")
        print("  2. DATABASE_URL in .env is correct")
        print("  3. PostgreSQL is running")
    finally:
        db.close()


if __name__ == "__main__":
    main()

