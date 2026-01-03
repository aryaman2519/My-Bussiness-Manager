from sqlalchemy import Column, Integer, String, Boolean, Enum as SQLEnum, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.models.database import Base


class UserRole(str, enum.Enum):
    OWNER = "owner"
    STAFF = "staff"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)  # Optional - staff might not have email
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    business_name = Column(String, nullable=True)  # Required for owners, inherited for staff
    role = Column(SQLEnum(UserRole), default=UserRole.STAFF, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # New Fields
    security_code = Column(String, nullable=True) # 8-digit code
    business_type = Column(String, nullable=True)
    
    # Smart Billing Fields
    invoice_template_html = Column(String, nullable=True) # Stores the raw HTML for the bill
    invoice_mapping = Column(String, nullable=True) # JSON string for mapping coordinates (optional for now)
    
    # Business Setup Fields for PDF Template System
    business_logo = Column(String, nullable=True)  # Base64-encoded logo image
    business_address = Column(String, nullable=True)  # Business address for header
    business_phone = Column(String, nullable=True)  # Phone number(s) for header
    signature_image = Column(String, nullable=True)  # Base64-encoded signature
    template_pdf_path = Column(String, nullable=True)  # Path to stored PDF template
    template_coordinates = Column(String, nullable=True)  # JSON: coordinate mappings for all fields
    
    # Owner-Staff Relationship
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    
    # Relationships
    sales_created = relationship("Sale", foreign_keys="Sale.created_by_id", back_populates="created_by")
    
    # Self-referential relationship to access owner details from staff
    owner = relationship("User", remote_side=[id], backref="staff_members")

