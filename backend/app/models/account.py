from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.models.database import Base

class AccountType(str, enum.Enum):
    BANK = "bank"
    CASH = "cash"
    UPI = "upi"
    OTHER = "other"

class TransactionType(str, enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"

class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True) # e.g., "HDFC Bank", "Petty Cash"
    type = Column(SQLEnum(AccountType), default=AccountType.CASH, nullable=False)
    account_number = Column(String, nullable=True) # Optional, mainly for banks
    
    balance = Column(Float, default=0.0, nullable=False)
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    transactions_from = relationship("Transaction", foreign_keys="Transaction.from_account_id", back_populates="from_account", cascade="all, delete-orphan")
    transactions_to = relationship("Transaction", foreign_keys="Transaction.to_account_id", back_populates="to_account", cascade="all, delete-orphan")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    type = Column(SQLEnum(TransactionType), nullable=False)
    
    # For Income/Expense: use from_account_id (Expense comes FROM account, Income goes TO account? 
    # Let's standardize: 
    # Expense: from_account_id is SET, to_account_id is NULL
    # Income: from_account_id is NULL, to_account_id is SET
    # Transfer: both SET
    
    # Actually, simpler model:
    # Account ID involved. But transfer needs two.
    # Let's stick to source/destination.
    
    from_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    to_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    
    from_account = relationship("Account", foreign_keys=[from_account_id], back_populates="transactions_from")
    to_account = relationship("Account", foreign_keys=[to_account_id], back_populates="transactions_to")
    
    date = Column(DateTime, server_default=func.now(), nullable=False)
    category = Column(String, nullable=True) # e.g., "Food", "Rent", "Sales"
    
    reference_id = Column(String, nullable=True) # To link with Sale ID or Purchase ID if needed later
    
    # Day Book Fields
    customer_name = Column(String, nullable=True) # From Whom
    handler_name = Column(String, nullable=True) # To Whom (Staff Name)
    payment_method = Column(String, default="cash", nullable=True) # Cash, UPI
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=True) # Link to Invoice
    
    notes = Column(Text, nullable=True)
    
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
