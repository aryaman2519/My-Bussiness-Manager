from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date, timedelta
import pytz
from app.models.database import get_db
from app.models.account import Account, Transaction, AccountType, TransactionType
from app.auth.security import get_current_active_user, require_owner
from app.models.user import User

router = APIRouter(prefix="/accounts", tags=["accounts"])

# --- Schemas ---
class AccountCreate(BaseModel):
    name: str
    type: AccountType
    account_number: Optional[str] = None
    initial_balance: float = 0.0

class AccountResponse(BaseModel):
    id: int
    name: str
    type: AccountType
    account_number: Optional[str] = None
    balance: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TransactionCreate(BaseModel):
    description: str
    amount: float
    type: TransactionType
    
    # Day Book Fields
    customer_name: Optional[str] = None
    handler_name: Optional[str] = None
    payment_method: Optional[str] = "cash"
    sale_id: Optional[int] = None
    
    category: Optional[str] = None
    notes: Optional[str] = None
    date: Optional[datetime] = None

class TransactionResponse(BaseModel):
    id: int
    description: str
    amount: float
    type: TransactionType
    
    # Day Book Fields
    customer_name: Optional[str] = None
    handler_name: Optional[str] = None
    payment_method: Optional[str] = None
    sale_id: Optional[int] = None
    
    category: Optional[str] = None
    notes: Optional[str] = None
    date: datetime
    
    class Config:
        from_attributes = True

# --- Endpoints ---

@router.get("/transactions", response_model=List[TransactionResponse])
def list_transactions(
    date_str: Optional[str] = None, # format: YYYY-MM-DD
    month_str: Optional[str] = None, # format: YYYY-MM
    limit: int = 1000, # Increased limit for monthly views
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List transactions. Filter by specific day (date_str) or entire month (month_str)."""
    
    # --- Business Isolation Logic ---
    # 1. Determine Owner ID (Business Context)
    if current_user.role == "owner":  # Or UserRole.OWNER if imported
        owner_id = current_user.id
    else:
        owner_id = current_user.owner_id
        
    # 2. Get all User IDs belonging to this Business (Owner + All Staff)
    # We filter transactions where created_by_id is in this list.
    team_ids_query = db.query(User.id).filter(
        (User.id == owner_id) | (User.owner_id == owner_id)
    )
    team_ids = [uid[0] for uid in team_ids_query.all()]
    
    # 3. Apply Filter
    query = db.query(Transaction).filter(Transaction.created_by_id.in_(team_ids))
    # -------------------------------
    
    if date_str:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            # Filter by day
            query = query.filter(func.date(Transaction.date) == target_date)
        except ValueError:
            pass
    elif month_str:
        try:
            # format YYYY-MM means we verify year and month
            year, month = map(int, month_str.split('-'))
            query = query.filter(
                func.extract('year', Transaction.date) == year,
                func.extract('month', Transaction.date) == month
            )
        except ValueError:
            pass

    txns = query.order_by(desc(Transaction.date)).limit(limit).all()
    return txns

@router.post("/transactions", response_model=TransactionResponse)
def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Record a Day Book transaction.
    """
    
    if transaction.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    # Day Book doesn't strictly require Account balances (user said "no need of bank account link")
    # BUT we should still use a default 'Cash' account or similar to keep data valid if we ever want to use it.
    # Let's check if a default account exists, if not create one.
    
    default_acc = db.query(Account).filter(Account.type == AccountType.CASH).first()
    if not default_acc:
        default_acc = Account(name="Main Cash", type=AccountType.CASH, balance=0)
        db.add(default_acc)
        db.commit()
        db.refresh(default_acc)
        
    # Logic for updating balance (Optional but good practice)
    if transaction.type == TransactionType.INCOME:
        # Incoming money -> Add to Cash
        default_acc.balance += transaction.amount
        to_acc_id = default_acc.id
        from_acc_id = None
        
    elif transaction.type == TransactionType.EXPENSE:
        # Outgoing money -> Deduct from Cash
        default_acc.balance -= transaction.amount
        from_acc_id = default_acc.id
        to_acc_id = None
        
    elif transaction.type == TransactionType.TRANSFER:
         # For simplicity in Day Book, treat Transfer as Expense? Or just record it.
         # User asked for "Daily Transactions", usually Income/Expense.
         # Let's just record it without balance impact if distinct accounts aren't used.
         from_acc_id = default_acc.id
         to_acc_id = default_acc.id # Self transfer? Placeholder.

    # Create Transaction Record
    new_txn = Transaction(
        description=transaction.description,
        amount=transaction.amount,
        type=transaction.type,
        
        # Day Book Fields
        customer_name=transaction.customer_name,
        handler_name=transaction.handler_name,
        payment_method=transaction.payment_method,
        sale_id=transaction.sale_id,
        
        # Internal Account Linking (Hidden from user mostly)
        from_account_id=from_acc_id,
        to_account_id=to_acc_id,
        
        category=transaction.category,
        notes=transaction.notes,
        date=transaction.date or datetime.now(pytz.timezone('Asia/Kolkata')).replace(tzinfo=None),
        created_by_id=current_user.id
    )
    
    db.add(new_txn)
    db.commit()
    db.refresh(new_txn)
    
    return new_txn

@router.delete("/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a transaction and reverse its balance impact.
    """
    # 1. Fetch Transaction
    txn = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
        
    # 2. Reverse Balance Impact
    # We assume 'to_account_id' was the default cash account for INCOME
    # and 'from_account_id' was the default cash account for EXPENSE
    
    if txn.type == TransactionType.INCOME and txn.to_account_id:
        acc = db.query(Account).filter(Account.id == txn.to_account_id).first()
        if acc:
            acc.balance -= txn.amount # Reverse Income
            
    elif txn.type == TransactionType.EXPENSE and txn.from_account_id:
        acc = db.query(Account).filter(Account.id == txn.from_account_id).first()
        if acc:
            acc.balance += txn.amount # Reverse Expense (Add money back)

    # 3. Delete Record
    db.delete(txn)
    db.commit()
    return None
