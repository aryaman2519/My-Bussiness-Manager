from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Text, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.models.database import Base


class PaymentMethod(str, enum.Enum):
    CASH = "cash"
    CARD = "card"
    UPI = "upi"
    BANK_TRANSFER = "bank_transfer"
    CREDIT = "credit"


class SaleStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String, unique=True, index=True, nullable=False)
    
    # Customer info
    customer_name = Column(String, nullable=True)
    customer_phone = Column(String, nullable=True, index=True)
    customer_email = Column(String, nullable=True)
    pdf_file_path = Column(String, nullable=True)
    
    # Sale details
    total_amount = Column(Float, nullable=False)
    discount_amount = Column(Float, default=0.0, nullable=False)
    final_amount = Column(Float, nullable=False)  # total_amount - discount_amount
    tax_amount = Column(Float, default=0.0, nullable=False)
    
    # Payment
    payment_method = Column(SQLEnum(PaymentMethod), nullable=False)
    payment_status = Column(String, default="paid", nullable=False)  # 'paid', 'pending', 'partial'
    amount_paid = Column(Float, nullable=False)
    amount_due = Column(Float, default=0.0, nullable=False)
    
    # Status
    status = Column(SQLEnum(SaleStatus), default=SaleStatus.COMPLETED, nullable=False)
    
    # Staff who created the sale
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_by = relationship("User", foreign_keys=[created_by_id])
    
    # Metadata
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")
    warranties = relationship("Warranty", back_populates="sale", cascade="all, delete-orphan")
    # Note: StockMovement relationship will be added in product.py


class SaleItem(Base):
    __tablename__ = "sale_items"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False, index=True)
    sale = relationship("Sale", back_populates="items")
    
    # Changed to reference stock table instead of products
    product_id = Column(Integer, ForeignKey("stock.id"), nullable=False, index=True)
    product = relationship("Stock") # Linked to Stock model
    
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)  # Selling price at time of sale
    total_price = Column(Float, nullable=False)  # quantity * unit_price
    
    # Profit tracking (Owner only)
    unit_cost = Column(Float, nullable=True)  # Landing cost at time of sale
    profit = Column(Float, nullable=True)  # (unit_price - unit_cost) * quantity
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class Warranty(Base):
    __tablename__ = "warranties"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False, index=True)
    sale = relationship("Sale", back_populates="warranties")
    
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    
    # IMEI tracking (for phones)
    imei = Column(String, unique=True, index=True, nullable=True)  # Unique IMEI number
    imei2 = Column(String, nullable=True)  # For dual SIM phones
    
    # Warranty details
    warranty_period_months = Column(Integer, nullable=False, default=12)
    warranty_start_date = Column(DateTime, nullable=False)
    warranty_end_date = Column(DateTime, nullable=False)
    
    # Warranty claims
    is_active = Column(Boolean, default=True, nullable=False)
    claims_count = Column(Integer, default=0, nullable=False)
    
    # Customer info (duplicated for quick lookup)
    customer_name = Column(String, nullable=True)
    customer_phone = Column(String, nullable=True, index=True)
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    warranty_claims = relationship("WarrantyClaim", back_populates="warranty", cascade="all, delete-orphan")


class WarrantyClaim(Base):
    __tablename__ = "warranty_claims"

    id = Column(Integer, primary_key=True, index=True)
    warranty_id = Column(Integer, ForeignKey("warranties.id"), nullable=False, index=True)
    warranty = relationship("Warranty", back_populates="warranty_claims")
    
    claim_type = Column(String, nullable=False)  # 'repair', 'replacement', 'refund'
    description = Column(Text, nullable=False)
    status = Column(String, default="pending", nullable=False)  # 'pending', 'approved', 'rejected', 'completed'
    
    # Resolution
    resolution_notes = Column(Text, nullable=True)
    resolved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

