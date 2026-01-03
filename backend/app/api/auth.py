from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel
from app.models.database import get_db
from app.models.user import User, UserRole
from app.models.credentials_db import get_credentials_db, UserCredentials, init_credentials_db
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

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

class OwnerRegister(BaseModel):
    full_name: str
    business_name: str
    business_type: str  # New field
    username: str
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str]
    full_name: str
    business_name: Optional[str]
    business_type: Optional[str] # New field
    role: str
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True

@router.post("/register", response_model=UserResponse)
async def register_owner(
    owner_data: OwnerRegister,
    db: Session = Depends(get_db),
    cred_db: Session = Depends(get_credentials_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """Register owner: plain text in credentials.db, hashed in main db. Handles errors gracefully."""
    try:
        init_credentials_db()
        
        username = owner_data.username.strip()
        email = owner_data.email.strip()
        
        # Security Code Generator
        security_code = generate_security_code()

        # 1. Check uniqueness in Credentials DB (Optimistic check, real check is try/except)
        if cred_db.query(UserCredentials).filter(UserCredentials.username == username).first():
             raise HTTPException(status_code=400, detail="Username is taken. Please choose another one.")

        # 2. Store PLAIN TEXT in credentials database
        new_credentials = UserCredentials(
            username=username,
            email=email,
            password=owner_data.password,  # SAVED AS PLAIN TEXT
            full_name=owner_data.full_name.strip(),
            business_name=owner_data.business_name.strip(),
            business_type=owner_data.business_type.strip(),
            role="owner",
            is_active=True,
            is_auto_generated=False,
            security_code=security_code,
            created_at=datetime.utcnow(),
        )
        cred_db.add(new_credentials)
        cred_db.commit()

        # 3. Store HASHED version in main application database
        hashed_password = get_password_hash(owner_data.password)
        new_owner = User(
            username=username,
            email=email,
            hashed_password=hashed_password, # SAVED AS HASH
            full_name=owner_data.full_name.strip(),
            business_name=owner_data.business_name.strip(),
            business_type=owner_data.business_type.strip(),
            role=UserRole.OWNER,
            is_active=True,
            security_code=security_code,
            created_at=datetime.utcnow(),
        )
        db.add(new_owner)
        db.commit()
        db.refresh(new_owner)

        # Send Welcome Email
        background_tasks.add_task(
            send_welcome_email, 
            to_email=new_owner.email, 
            username=new_owner.username, 
            password=owner_data.password,
            security_code=security_code
        )

        return UserResponse(
            id=new_owner.id,
            username=new_owner.username,
            email=new_owner.email,
            full_name=new_owner.full_name,
            business_name=new_owner.business_name,
            business_type=new_owner.business_type,
            role=new_owner.role.value,
            is_active=new_owner.is_active,
            created_at=new_owner.created_at.isoformat(),
        )
        
    except IntegrityError as e:
        cred_db.rollback()
        db.rollback()
        error_msg = str(e.orig).lower() if hasattr(e, 'orig') else str(e).lower()
        if "users.email" in error_msg or "email" in error_msg:
             raise HTTPException(status_code=400, detail="This email is already registered. Please log in or use a different email.")
        elif "users.username" in error_msg or "username" in error_msg:
             raise HTTPException(status_code=400, detail="This username is taken. Please choose another one.")
        else:
             raise HTTPException(status_code=400, detail="Account already exists (username or email).")
             
    except Exception as e:
        cred_db.rollback()
        db.rollback()
        # Clean up partial state if necessary
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    cred_db: Session = Depends(get_credentials_db),
):
    """Login using plain-text comparison from credentials.db."""
    print(f"LOGIN ATTEMPT: username={repr(form_data.username)}")
    print(f"LOGIN ATTEMPT: password={repr(form_data.password)}")
    
    cred_user = cred_db.query(UserCredentials).filter(UserCredentials.username == form_data.username).first()
    
    if cred_user:
        print(f"USER FOUND in DB: {repr(cred_user.username)}")
        print(f"STORED PASSWORD: {repr(cred_user.password)}")
        print(f"MATCH RESULT: {verify_password(form_data.password, cred_user.password)}")
    else:
        print("USER NOT FOUND in DB")

    # Using the verify_password logic (which we updated to plain-text comparison)
    if not cred_user or not verify_password(form_data.password, cred_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    user = db.query(User).filter(User.username == form_data.username).first()
    
    # Sync main DB if user only exists in Cred DB
    if not user:
        user = User(
            username=cred_user.username,
            email=cred_user.email,
            hashed_password=get_password_hash(cred_user.password),
            full_name=cred_user.full_name,
            business_name=cred_user.business_name,
            role=UserRole.OWNER if cred_user.role == "owner" else UserRole.STAFF,
            is_active=True,
            created_at=cred_user.created_at,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    access_token = create_access_token(data={"sub": user.username, "role": user.role.value})

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
    cred_db: Session = Depends(get_credentials_db),
    current_user: User = Depends(get_current_active_user),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """
    Reset password using the Verified Security Code.
    Updates both Credentials DB (plain text) and Main DB (hashed).
    """
    # 1. Verify Code Again (Security Best Practice)
    if not current_user.security_code or current_user.security_code != reset_data.security_code.strip():
        raise HTTPException(status_code=400, detail="Invalid Security Code")
    
    try:
        # 2. Update Credentials DB (Plain Text)
        cred_user = cred_db.query(UserCredentials).filter(UserCredentials.username == current_user.username).first()
        if cred_user:
            cred_user.password = reset_data.new_password
            cred_db.commit()
            
        # 3. Update Main DB (Hashed)
        hashed_password = get_password_hash(reset_data.new_password)
        current_user.hashed_password = hashed_password
        db.commit()
        
        # 4. Send Confirmation Email (TODO: Implement proper email function if needed, reusing welcome for now or generic)
        # Request says: "automatically send a confirmation email... containing Username and New Updated Password"
        # We can reuse send_welcome_email or create a new one. Let's create a quick one or adapt.
        # For this turn, I will just return success, but task says "Success Notification... via email"
        # I'll add a simple email function task or reuse existing if possible.
        # Let's add send_password_change_email to email.py quickly.
        
        # 4. Send Confirmation Email
        if current_user.email:
            background_tasks.add_task(
                send_password_change_email,
                to_email=current_user.email,
                username=current_user.username,
                new_password=reset_data.new_password
            )
        
        return {"message": "Password updated successfully"}
        
    except Exception as e:
        cred_db.rollback()
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
        
        # 1. Identify all users in this business (Owner + Staff)
        team_ids = [uid[0] for uid in db.query(User.id).filter(
            (User.id == owner_id) | (User.owner_id == owner_id)
        ).all()]
        
        # 2. Get all Sales by these users
        sales = db.query(Sale).filter(Sale.created_by_id.in_(team_ids)).all()
        sale_ids = [s.id for s in sales]

        if sale_ids:
            # A. Delete Warranty Claims
            # Find warranties related to these sales
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
        # Note: Delete users with owner_id = current_user.id
        db.query(User).filter(User.owner_id == owner_id).delete(synchronize_session=False)
        
        # 6. Delete User Credentials (Owner + Staff)
        cred_db.query(UserCredentials).filter(
            (UserCredentials.username == current_user.username) | 
            (UserCredentials.owner_id == owner_id)
        ).delete(synchronize_session=False)
        cred_db.commit()

        # 7. Delete the Owner User
        db.delete(current_user)
        db.commit()
        
    except Exception as e:
        db.rollback()
        cred_db.rollback()
        print(f"Delete Error: {e}") # Log to console
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete account: {str(e)}"
        )