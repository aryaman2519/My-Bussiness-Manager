from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import pytz
from sqlalchemy import func

from app.models.database import get_db
from app.models.user import User, UserRole
from app.models.stock import Stock
from app.models.account import Transaction, TransactionType
from app.auth.security import get_current_active_user, require_owner
from app.utils.email import send_low_stock_alert

router = APIRouter(prefix="/stock", tags=["stock"])

# Helper to get the effective owner_id
def get_owner_id(user: User) -> int:
    if user.role == UserRole.OWNER:
        return user.id
    if user.role == UserRole.STAFF:
        # Check if owner_id is set (it should be)
        if hasattr(user, "owner_id") and user.owner_id:
             return user.owner_id
        # Fallback if owner_id is missing (should not happen with new schema)
        return -1 
    return -1

# --- Domain Knowledge Data ---
# In a real app, this could be in a DB or separate JSON file
DOMAIN_KNOWLEDGE = {
    "pharmacy": [
        {"product_name": "Paracetamol", "company_name": "GSK", "category": "Medicine"},
        {"product_name": "Panadol", "company_name": "GSK", "category": "Medicine"},
        {"product_name": "Ibuprofen", "company_name": "Abbott", "category": "Medicine"},
        {"product_name": "Cough Syrup", "company_name": "Benadryl", "category": "Medicine"},
        {"product_name": "Vitamin C", "company_name": "Nature's Way", "category": "Supplement"},
        {"product_name": "Bandages", "company_name": "Johnson & Johnson", "category": "First Aid"},
    ],
    "grocery": [
        {"product_name": "Rice", "company_name": "Daawat", "category": "Grains"},
        {"product_name": "Wheat Flour", "company_name": "Aashirvaad", "category": "Flour"},
        {"product_name": "Sugar", "company_name": "Madhur", "category": "Sweets"},
        {"product_name": "Salt", "company_name": "Tata", "category": "Spices"},
        {"product_name": "Milk", "company_name": "Amul", "category": "Dairy"},
        {"product_name": "Butter", "company_name": "Amul", "category": "Dairy"},
    ],
    "electronics": [
        {"product_name": "Smartphone", "company_name": "Samsung", "category": "Mobile"},
        {"product_name": "Laptop", "company_name": "Dell", "category": "Computer"},
        {"product_name": "Headphones", "company_name": "Sony", "category": "Audio"},
        {"product_name": "Charger", "company_name": "Apple", "category": "Accessories"},
        {"product_name": "Smart Watch", "company_name": "Fitbit", "category": "Wearable"},
    ],
    "default": [
        {"product_name": "Pen", "company_name": "Reynolds", "category": "Stationery"},
        {"product_name": "Notebook", "company_name": "Classmate", "category": "Stationery"},
    ]
}

# --- Pydantic Models ---

class StockSuggestion(BaseModel):
    product_name: str
    company_name: str
    category: str

class StockCreateRequest(BaseModel):
    product_name: str
    company_name: str
    category: str
    quantity: int
    selling_price: Optional[float] = 0.0
    cost_price: Optional[float] = 0.0
    threshold_quantity: Optional[int] = None # Change Default to None (To detecting missing vs 5)

class StockResponse(BaseModel):
    id: int
    product_name: str
    company_name: str
    category: str
    quantity: int
    selling_price: float
    threshold_quantity: int
    last_updated_by: str
    last_updated_at: str  # Send as formatted string

    class Config:
        from_attributes = True

# --- Endpoints ---

@router.get("/companies", response_model=List[str])
async def get_companies(
    business_type: str = "default",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Returns unique company names based on business type + existing stock.
    Scoped to Owner ID.
    """
    b_type = business_type.lower().strip()
    
    # 1. Get suggestions from Domain Knowledge
    suggestions = DOMAIN_KNOWLEDGE.get("default", [])
    for key, items in DOMAIN_KNOWLEDGE.items():
        if key in b_type or b_type in key:
            suggestions = items
            break
            
    domain_companies = set([item["company_name"] for item in suggestions])

    # 2. Get companies from User's existing stock (Scoped by Owner ID)
    owner_id = get_owner_id(current_user)
    
    if owner_id != -1:
        db_companies_query = db.query(Stock.company_name).filter(
            Stock.owner_id == owner_id
        ).distinct().all()
        db_companies = set([row[0] for row in db_companies_query])
    else:
        db_companies = set()

    # 3. Merge & Sort
    all_companies = list(domain_companies.union(db_companies))
    all_companies.sort()
    
    return all_companies


@router.get("/suggestions", response_model=List[StockSuggestion])
async def get_suggestions(
    business_type: str = "default",
    company_name: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Returns suggested products. 
    Scoped to Owner ID.
    Merges Domain Knowledge + Existing Stock.
    """
    b_type = business_type.lower().strip()
    
    # 1. Domain Knowledge
    suggestions_list = DOMAIN_KNOWLEDGE.get("default", [])
    for key, items in DOMAIN_KNOWLEDGE.items():
        if key in b_type or b_type in key:
            suggestions_list = items
            break
            
    # Convert to objects for consistency
    domain_suggestions = [StockSuggestion(**s) for s in suggestions_list]

    # 2. DB Stock (Scoped by Owner ID)
    owner_id = get_owner_id(current_user)
    db_suggestions = []

    if owner_id != -1:
        db_stock = db.query(Stock).filter(
            Stock.owner_id == owner_id
        ).all()
        
        db_suggestions = [
            StockSuggestion(
                product_name=s.product_name,
                company_name=s.company_name,
                category=s.category
            )
            for s in db_stock
        ]

    all_suggestions = domain_suggestions + db_suggestions

    # 3. Filter by company if provided
    if company_name:
        c_name = company_name.lower().strip()
        all_suggestions = [s for s in all_suggestions if s.company_name.lower().strip() == c_name]
        
    # 4. Deduplicate by product name
    unique_map = {s.product_name.lower(): s for s in all_suggestions}
    return list(unique_map.values())

@router.post("/add-or-update", response_model=StockResponse)
async def add_or_update_stock(
    stock_data: StockCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """
    Add new stock or update quantity if it exists.
    Scoped to Owner ID.
    """
    owner_id = get_owner_id(current_user)
    if owner_id == -1:
         raise HTTPException(status_code=400, detail="Unable to determine Business Owner ID.")

    try:
        # Check if stock exists for this business (Using owner_id)
        existing_stock = db.query(Stock).filter(
            Stock.owner_id == owner_id,
            func.lower(Stock.product_name) == stock_data.product_name.lower().strip(),
            func.lower(Stock.company_name) == stock_data.company_name.lower().strip()
        ).first()

        if existing_stock:
            # Update existing
            existing_stock.quantity += stock_data.quantity
            existing_stock.last_updated_by = current_user.full_name
            existing_stock.category = stock_data.category # Update category if changed
            if stock_data.threshold_quantity is not None:
                existing_stock.threshold_quantity = stock_data.threshold_quantity
            
            # Update Price if provided (allow 0.0)
            if stock_data.selling_price is not None:
                existing_stock.selling_price = stock_data.selling_price
            
            # Ensure quantity doesn't go negative if bad input
            if existing_stock.quantity < 0:
                 existing_stock.quantity = 0
            
            # Check Low Stock Alert
            # Condition: Quantity <= Threshold AND (No previous alert OR > 24h since last alert)
            if existing_stock.quantity <= existing_stock.threshold_quantity:
                should_alert = False
                if not existing_stock.last_alert_sent:
                    should_alert = True
                else:
                    # Check if 24 hours passed
                    # Use Naive IST for comparison (since DB stores naive)
                    now_ist_naive = datetime.now(pytz.timezone('Asia/Kolkata')).replace(tzinfo=None)
                    if existing_stock.last_alert_sent:
                         # Ensure database value is treated as naive (it usually is)
                         last_sent = existing_stock.last_alert_sent
                         # DEV MODE: Cooldown reduced to 1 minute for easier testing
                         if now_ist_naive - last_sent > timedelta(minutes=1):
                             should_alert = True
                
                if should_alert:
                    # Fetch recipients: Owner + ALL Staff members (Phone Numbers)
                    phone_numbers = set()
                    
                    # 1. Get Owner Phone
                    # If owner_id is set, get that owner.
                    if owner_id != -1:
                        owner = db.query(User).filter(User.id == owner_id).first()
                        if owner and owner.phone_number:
                            phone_numbers.add(owner.phone_number)
                    
                    # 2. Get All Staff for this Owner
                    if owner_id != -1:
                         staff_members = db.query(User).filter(User.owner_id == owner_id).all()
                         for staff in staff_members:
                             if staff.phone_number:
                                 phone_numbers.add(staff.phone_number)
                    
                    # Call WhatsApp for each number
                    from app.utils.whatsapp import send_low_stock_whatsapp
                    
                    if phone_numbers:
                        for phone in phone_numbers:
                            background_tasks.add_task(
                                send_low_stock_whatsapp,
                                to_number=phone,
                                product_name=existing_stock.product_name,
                                current_quantity=existing_stock.quantity
                            )
                        
                        # Store as Naive IST
                        existing_stock.last_alert_sent = datetime.now(pytz.timezone('Asia/Kolkata')).replace(tzinfo=None)
            
            # Auto-Log Expense if Cost Price & Quantity provided (and positive)

            if stock_data.quantity > 0 and stock_data.cost_price and stock_data.cost_price > 0:
                print("DEBUG: Condition Met. Creating Transaction...")
                total_cost = stock_data.quantity * stock_data.cost_price
                expense_txn = Transaction(
                    description=f"Stock Purchase: {existing_stock.product_name} x {stock_data.quantity}",
                    amount=total_cost,
                    type=TransactionType.EXPENSE,
                    category="Stock",
                    # Store as Naive IST
                    date=datetime.now(pytz.timezone('Asia/Kolkata')).replace(tzinfo=None),
                    created_by_id=current_user.id,
                    payment_method="cash", # Default to cash
                    handler_name=current_user.full_name # Mark who added it
                )
                db.add(expense_txn)

            db.commit()
            db.refresh(existing_stock)
            return StockResponse(
                id=existing_stock.id,
                product_name=existing_stock.product_name,
                company_name=existing_stock.company_name,
                category=existing_stock.category,
                quantity=existing_stock.quantity,
                selling_price=existing_stock.selling_price,
                threshold_quantity=existing_stock.threshold_quantity,
                last_updated_by=existing_stock.last_updated_by,
                last_updated_at=existing_stock.last_updated_at.isoformat()
            )
        else:
            # Create new
            new_stock = Stock(
                business_name=current_user.business_name,
                owner_id=owner_id,
                product_name=stock_data.product_name.strip(),
                company_name=stock_data.company_name.strip(),
                category=stock_data.category.strip(),
                quantity=stock_data.quantity,

                selling_price=stock_data.selling_price if stock_data.selling_price is not None else 0.0,
                threshold_quantity=stock_data.threshold_quantity if stock_data.threshold_quantity is not None else 5,
                last_updated_by=current_user.full_name
            )
            # Ensure non-negative initial quantity
            if new_stock.quantity < 0:
                new_stock.quantity = 0
            
            # Initial Check for Low Stock (Unlikely unless initial qty is low)
            if new_stock.quantity <= new_stock.threshold_quantity:
                 # Fetch recipients: Owner + ALL Staff members
                 phone_numbers = set()
                 
                 if owner_id != -1:
                    owner = db.query(User).filter(User.id == owner_id).first()
                    if owner and owner.phone_number:
                        phone_numbers.add(owner.phone_number)
                 
                 if owner_id != -1:
                     staff_members = db.query(User).filter(User.owner_id == owner_id).all()
                     for staff in staff_members:
                         if staff.phone_number:
                             phone_numbers.add(staff.phone_number)
                 
                 if phone_numbers:
                    from app.utils.whatsapp import send_low_stock_whatsapp
                    for phone in phone_numbers:
                        background_tasks.add_task(
                            send_low_stock_whatsapp,
                            to_number=phone,
                            product_name=new_stock.product_name,
                            current_quantity=new_stock.quantity
                        )
                 
                 new_stock.last_alert_sent = datetime.now(pytz.timezone('Asia/Kolkata'))

            # Auto-Log Expense
            if stock_data.quantity > 0 and stock_data.cost_price and stock_data.cost_price > 0:
                total_cost = stock_data.quantity * stock_data.cost_price
                expense_txn = Transaction(
                    description=f"Stock Purchase: {new_stock.product_name} x {stock_data.quantity}",
                    amount=total_cost,
                    type=TransactionType.EXPENSE,
                    category="Stock",
                    date=datetime.now(pytz.timezone('Asia/Kolkata')),
                    created_by_id=current_user.id,
                    payment_method="cash",
                    handler_name=current_user.full_name
                )
                db.add(expense_txn)

            db.add(new_stock)
            db.commit()
            db.refresh(new_stock)
            
            return StockResponse(
                id=new_stock.id,
                product_name=new_stock.product_name,
                company_name=new_stock.company_name,
                category=new_stock.category,
                quantity=new_stock.quantity,
                selling_price=new_stock.selling_price,
                threshold_quantity=new_stock.threshold_quantity,
                last_updated_by=new_stock.last_updated_by,
                last_updated_at=new_stock.last_updated_at.isoformat()
            )

    except Exception as e:
        db.rollback()
        print(f"Error adding/updating stock: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update stock inventory. Please try again."
        )

@router.get("/list", response_model=List[StockResponse])
async def list_stock(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    List stock Scoped to Owner ID.
    """
    owner_id = get_owner_id(current_user)
    if owner_id == -1:
        return []

    try:
        stocks = db.query(Stock).filter(
            Stock.owner_id == owner_id
        ).order_by(Stock.last_updated_at.desc()).all()

        return [
            StockResponse(
                id=s.id,
                product_name=s.product_name,
                company_name=s.company_name,
                category=s.category,
                quantity=s.quantity,
                selling_price=s.selling_price,
                threshold_quantity=s.threshold_quantity,
                last_updated_by=s.last_updated_by,
                last_updated_at=s.last_updated_at.isoformat()
            )
            for s in stocks
        ]
    except Exception as e:
        print(f"Error listing stock: {e}")
        # Return empty list on error for list endpoint, or raise? 
        # User asked for "Graceful Error Handling... display: 'This username...'"
        # For list endpoints, empty list or 500 is debatable. 
        # Let's clean fail to 500 with message, so frontend handles it (or shows nothing)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve inventory list. Please try again."
        )


@router.delete("/{stock_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_stock(
    stock_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner), # Enforce Owner Role
):
    """
    Delete a stock item. Only Owners can perform this action.
    """
    owner_id = get_owner_id(current_user)
    
    # Verify owner_id (should be self for owner, but good to check)
    if owner_id == -1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Could not determine business owner."
        )

    # Find stock item belonging to this owner
    stock_item = db.query(Stock).filter(
        Stock.id == stock_id,
        Stock.owner_id == owner_id
    ).first()

    if not stock_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock item not found"
        )

    try:
        db.delete(stock_item)
        db.commit()
    except Exception as e:
        db.rollback()
        # Check for IntegrityError (Foreign Key Violation)
        if "FOREIGN KEY constraint failed" in str(e):
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete this item because it is part of existing sales records."
            )
            
        print(f"Error deleting stock: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete stock item."
        )
