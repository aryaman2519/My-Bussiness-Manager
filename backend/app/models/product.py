from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String, unique=True, index=True, nullable=False)  # Stock Keeping Unit
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=False, index=True)  # phone, case, charger, tempered_glass
    brand = Column(String, nullable=True, index=True)
    model = Column(String, nullable=True)  # e.g., "iPhone 15 Pro", "Galaxy S24"
    
    # Ownership
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Pricing (Owner only - hidden from staff)
    landing_cost = Column(Float, nullable=False)  # Cost price
    selling_price = Column(Float, nullable=False)  # Selling price
    profit_margin = Column(Float, nullable=True)  # Calculated: (selling_price - landing_cost) / landing_cost * 100
    
    # Barcode & IMEI
    barcode = Column(String, unique=True, index=True, nullable=True)
    requires_imei = Column(Boolean, default=False, nullable=False)  # For phones
    
    # Supplier info
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    supplier = relationship("Supplier", back_populates="products")
    
    # Metadata
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    inventory_items = relationship("InventoryItem", back_populates="product", cascade="all, delete-orphan")
    # sale_items = relationship("SaleItem", back_populates="product")  # Commented out - SaleItem now references Stock
    price_history = relationship("PriceHistory", back_populates="product", cascade="all, delete-orphan")


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True) # Optional for now
    name = Column(String, nullable=False, index=True)
    contact_person = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    gst_number = Column(String, nullable=True)
    
    # Payment terms
    payment_terms = Column(String, nullable=True)  # e.g., "Net 30", "COD"
    
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    products = relationship("Product", back_populates="supplier")
    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    product = relationship("Product", back_populates="inventory_items")
    
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Stock details
    quantity = Column(Integer, default=0, nullable=False)
    reserved_quantity = Column(Integer, default=0, nullable=False)  # Reserved for pending sales
    # available_quantity is calculated in application logic: quantity - reserved_quantity
    
    # Location (if multiple warehouses/stores)
    location = Column(String, nullable=True, default="main_store")
    
    # Reorder settings (Owner only)
    min_stock_level = Column(Integer, nullable=True)  # Minimum stock before alert
    reorder_quantity = Column(Integer, nullable=True)  # Quantity to order when restocking
    
    # Velocity tracking
    daily_velocity = Column(Float, default=0.0, nullable=False)  # Units sold per day (calculated)
    days_of_inventory_remaining = Column(Float, nullable=True)  # Calculated: quantity / daily_velocity
    
    # Last updated
    last_restocked_at = Column(DateTime, nullable=True)
    last_sold_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    stock_movements = relationship("StockMovement", back_populates="inventory_item", cascade="all, delete-orphan")


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(Integer, primary_key=True, index=True)
    inventory_item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=False, index=True)
    inventory_item = relationship("InventoryItem", back_populates="stock_movements")
    
    movement_type = Column(String, nullable=False, index=True)  # 'purchase', 'sale', 'adjustment', 'return'
    quantity_change = Column(Integer, nullable=False)  # Positive for additions, negative for deductions
    previous_quantity = Column(Integer, nullable=False)
    new_quantity = Column(Integer, nullable=False)
    
    # Reference to related transaction
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    
    # Note: Relationships to Sale and PurchaseOrder are defined in those models to avoid circular imports

