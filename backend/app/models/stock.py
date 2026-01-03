from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.database import Base

class Stock(Base):
    __tablename__ = "stock"

    id = Column(Integer, primary_key=True, index=True)
    # business_name kept for legacy/display if needed, but owner_id is the source of truth for isolation
    business_name = Column(String, index=True, nullable=True) 
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    product_name = Column(String, nullable=False)
    company_name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    quantity = Column(Integer, default=0, nullable=False)
    selling_price = Column(Float, default=0.0, nullable=False)
    threshold_quantity = Column(Integer, default=5, nullable=False)
    last_alert_sent = Column(DateTime, nullable=True)
    last_updated_by = Column(String, nullable=False)
    last_updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<Stock {self.product_name} - {self.company_name} ({self.quantity})>"
