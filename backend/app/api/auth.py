from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel
from app.models.database import get_db
from app.models.user import User, UserRole
from app.models.credentials_db import get_credentials_db, UserCredentials
from app.auth.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_active_user,
    require_owner,
)
from app.utils.email import send_welcome_email, send_password_change_email
from app.utils.security_utils import generate_security_code

router = APIRouter(prefix="/auth", tags=["authentication"])

def validate_password(password: str):
    """Ensure password fits within bcrypt's 72-byte limit."""
    if len(password.encode("utf-8")) > 72:
        raise HTTPException(
            status_code=400,
            detail="Password must be 72 characters or fewer"
        )

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

class OwnerRegister(BaseModel):
    full_name: str
    business_name: str
    business_type: str
    username: str
    email: str
    phone_number: str # e.g. 919876543210
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str]
    phone_number: Optional[str]
    full_name: str
    business_name: Optional[str]
    business_type: Optional[str]
    role: str
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True

@router.options("/register")
async def options_register():
    return {}

@router.post("/register", response_model=UserResponse)
async def register_owner(
    owner_data: OwnerRegister,
    db: Session = Depends(get_db),
    cred_db: Session = Depends(get_credentials_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    username = owner_data.username.strip()
    email = owner_data.email.strip()
    phone_number = owner_data.phone_number.strip()

    # 1️⃣ Check username in credentials DB
    if cred_db.query(UserCredentials).filter_by(username=username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    # 1.5 Check if phone number is already registered (Optional, but good practice)
    if cred_db.query(UserCredentials).filter_by(phone_number=phone_number).first():
        raise HTTPException(status_code=400, detail="Phone number already registered")

    # 2️⃣ Check username in main DB
    if db.query(User).filter_by(username=username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    security_code = generate_security_code()

    try:
        # 3️⃣ Create credential user
        # User requested to store HASHED password in credentials DB to avoid plaintext storage
        hashed_password = get_password_hash(owner_data.password)
        
        cred_user = UserCredentials(
            username=username,
            email=email,
            phone_number=phone_number,
            password=hashed_password,  # Storing HASHED password
            full_name=owner_data.full_name.strip(),
            business_name=owner_data.business_name.strip(),
            business_type=owner_data.business_type.strip(),
            role="owner",
            is_active=True,
            security_code=security_code,
            created_at=datetime.utcnow(),
        )
        cred_db.add(cred_user)

        # 4️⃣ Create main user
        user = User(
            username=username,
            email=email,
            phone_number=phone_number,
            hashed_password=hashed_password, # Use SAME hash
            full_name=owner_data.full_name.strip(),
            business_name=owner_data.business_name.strip(),
            business_type=owner_data.business_type.strip(),
            role=UserRole.OWNER,
            is_active=True,
            security_code=security_code,
            created_at=datetime.utcnow(),
        )
        db.add(user)

        # 5️⃣ Commit both
        cred_db.commit()
        db.commit()
        db.refresh(user)

        # Send Welcome WhatsApp
        from app.utils.whatsapp import send_welcome_whatsapp
        background_tasks.add_task(
            send_welcome_whatsapp, 
            to_number=user.phone_number, 
            business_name=user.business_name, 
            username=user.username
        )

        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            phone_number=user.phone_number,
            full_name=user.full_name,
            business_name=user.business_name,
            business_type=user.business_type,
            role=user.role.value,
            is_active=user.is_active,
            created_at=user.created_at.isoformat(),
        )

    except Exception as e:
        cred_db.rollback()
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    cred_db: Session = Depends(get_credentials_db),
):
    # 1. Login using ONLY main DB hash (Single Source of Truth)
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    # 2. Verify password (hash-check)
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "business_name": user.business_name,
            "role": user.role.value,
        },
    }

class SecurityCodeVerify(BaseModel):
    security_code: str

class PasswordReset(BaseModel):
    security_code: str
    new_password: str

@router.post("/verify-security-code")
async def verify_security_code(
    verify_data: SecurityCodeVerify,
    current_user: User = Depends(get_current_active_user),
):
    """Verify the 8-digit security code for the current user."""
    # Compare strings strictly
    if not current_user.security_code or current_user.security_code != verify_data.security_code.strip():
        raise HTTPException(status_code=400, detail="Invalid Security Code")
    return {"message": "Security code verified"}

@router.get("/verify-token", response_model=UserResponse)
async def verify_token(current_user: User = Depends(get_current_active_user)):
    """
    Verify the current token and user existence.
    If the user has been deleted or token is invalid, the dependency raises 401.
    """
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        business_name=current_user.business_name,
        business_type=current_user.business_type,
        role=current_user.role.value,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat(),
    )

@router.post("/reset-password")
async def reset_password_with_code(
    reset_data: PasswordReset,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """
    Reset password using the Verified Security Code.
    Updates Main DB (hashed).
    """
    # 1. Verify Code Again
    if not current_user.security_code or current_user.security_code != reset_data.security_code.strip():
        raise HTTPException(status_code=400, detail="Invalid Security Code")
    
    try:
        validate_password(reset_data.new_password)

        # 2. Update Main DB (Hashed)
        hashed_password = get_password_hash(reset_data.new_password)
        current_user.hashed_password = hashed_password
        db.commit()
        
        # 3. Send Confirmation Email
        if current_user.email:
            background_tasks.add_task(
                send_password_change_email,
                to_email=current_user.email,
                username=current_user.username,
                new_password=reset_data.new_password
            )
        
        return {"message": "Password updated successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    cred_db: Session = Depends(get_credentials_db),
):
    """
    Delete the current user's account.
    Only Owners can perform this action.
    Removes data from BOTH Main DB and Credentials DB.
    """
    if current_user.role != UserRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff members cannot delete their own account. Please contact the Business Owner."
        )

    try:
        # Import all necessary models
        from app.models.sale import Sale, SaleItem, Warranty, WarrantyClaim
        from app.models.stock import Stock
        from app.models.account import Transaction
        
        owner_id = current_user.id
        username = current_user.username # Store username before delete
        
        # 1. Identify all users in this business (Owner + Staff)
        team_ids = [uid[0] for uid in db.query(User.id).filter(
            (User.id == owner_id) | (User.owner_id == owner_id)
        ).all()]
        
        # 2. Get all Sales by these users
        sales = db.query(Sale).filter(Sale.created_by_id.in_(team_ids)).all()
        sale_ids = [s.id for s in sales]

        if sale_ids:
            # A. Delete Warranty Claims
            warranties = db.query(Warranty).filter(Warranty.sale_id.in_(sale_ids)).all()
            warranty_ids = [w.id for w in warranties]
            if warranty_ids:
                db.query(WarrantyClaim).filter(WarrantyClaim.warranty_id.in_(warranty_ids)).delete(synchronize_session=False)
                # B. Delete Warranties
                db.query(Warranty).filter(Warranty.sale_id.in_(sale_ids)).delete(synchronize_session=False)

            # C. Delete Sale Items
            db.query(SaleItem).filter(SaleItem.sale_id.in_(sale_ids)).delete(synchronize_session=False)
            
            # D. Delete Transactions linked to Sales (Income)
            db.query(Transaction).filter(Transaction.sale_id.in_(sale_ids)).delete(synchronize_session=False)
            
            # Delete Sales
            db.query(Sale).filter(Sale.id.in_(sale_ids)).delete(synchronize_session=False)

        # 3. Delete Remaining Transactions (Expenses, Manual logs) by this team
        db.query(Transaction).filter(Transaction.created_by_id.in_(team_ids)).delete(synchronize_session=False)
        
        # 4. Delete Stock (Owned by owner)
        db.query(Stock).filter(Stock.owner_id == owner_id).delete(synchronize_session=False)
        
        # 5. Delete Staff Members (Main DB)
        # Also need to delete Staff from Credentials DB? 
        # Yes, find staff usernames first if we want strict cleanup, 
        # OR just delete based on pattern/logic if possible.
        # But UserCredentials doesn't always have owner_id populated in old records.
        # However, improved 'create_staff' populates 'owner_id' in UserCredentials.
        # Let's try to delete by username for consistency or owner_id if available.
        
        # 5a. Get staff usernames
        staff_usernames = [u.username for u in db.query(User).filter(User.owner_id == owner_id).all()]
        
        db.query(User).filter(User.owner_id == owner_id).delete(synchronize_session=False)
        
        # 6. Delete the Owner User (Main DB)
        db.delete(current_user)
        
        # 7. SYNC DELETE: Remove from Credentials DB
        # Remove Owner
        cred_db.query(UserCredentials).filter(UserCredentials.username == username).delete(synchronize_session=False)
        
        # Remove Staff (using usernames collected from Main DB)
        if staff_usernames:
            cred_db.query(UserCredentials).filter(UserCredentials.username.in_(staff_usernames)).delete(synchronize_session=False)

        db.commit()
        cred_db.commit()
        
    except Exception as e:
        db.rollback()
        cred_db.rollback()
        print(f"Delete Error: {e}") # Log to console
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete account: {str(e)}"
        )