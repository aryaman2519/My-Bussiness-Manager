from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Text, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.models.database import Base


class PurchaseOrderStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING = "pending"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String, unique=True, index=True, nullable=False)
    
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False, index=True)
    supplier = relationship("Supplier", back_populates="purchase_orders")
    
    # Order details
    total_amount = Column(Float, nullable=False)
    tax_amount = Column(Float, default=0.0, nullable=False)
    discount_amount = Column(Float, default=0.0, nullable=False)
    final_amount = Column(Float, nullable=False)
    
    # Status
    status = Column(SQLEnum(PurchaseOrderStatus), default=PurchaseOrderStatus.DRAFT, nullable=False)
    
    # Dates
    order_date = Column(DateTime, server_default=func.now(), nullable=False)
    expected_delivery_date = Column(DateTime, nullable=True)
    received_date = Column(DateTime, nullable=True)
    
    # Created by (Owner only)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Notes
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    items = relationship("PurchaseOrderItem", back_populates="purchase_order", cascade="all, delete-orphan")
    # Note: StockMovement relationship is one-way (foreign key only) to avoid circular imports


class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"

    id = Column(Integer, primary_key=True, index=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False, index=True)
    purchase_order = relationship("PurchaseOrder", back_populates="items")
    
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    
    quantity_ordered = Column(Integer, nullable=False)
    quantity_received = Column(Integer, default=0, nullable=False)
    unit_cost = Column(Float, nullable=False)  # Cost per unit
    total_cost = Column(Float, nullable=False)  # quantity_ordered * unit_cost
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    product = relationship("Product", back_populates="price_history")
    
    # Price changes
    old_landing_cost = Column(Float, nullable=True)
    new_landing_cost = Column(Float, nullable=True)
    old_selling_price = Column(Float, nullable=True)
    new_selling_price = Column(Float, nullable=True)
    
    # Changed by
    changed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reason = Column(Text, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)

