"""
Staff Management API - Auto-generated credentials for staff accounts.
"""
from sqlalchemy.sql import func
import secrets
import string
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.models.database import get_db
from app.models.user import User, UserRole
from app.models.credentials_db import get_credentials_db, UserCredentials
from app.auth.security import get_password_hash, require_owner
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/staff", tags=["staff"])


from app.utils.security_utils import generate_security_code

class StaffCreateRequest(BaseModel):
    staff_name: str
    email: str # Mandatory email field


class StaffCreateResponse(BaseModel):
    id: int
    full_name: str
    username: str
    password: str
    security_code: str # New field
    business_name: str
    message: str = "Staff account created successfully. Save these credentials now."


class StaffResponse(BaseModel):
    id: int
    username: str
    full_name: str
    business_name: Optional[str]
    role: str
    is_active: bool
    created_at: str
    owner_name: Optional[str] = None # For "Reporting to"

    class Config:
        from_attributes = True


def generate_username(first_name: str, cred_db: Session) -> str:
    """Generate a unique username from first name."""
    base_username = first_name.lower().strip().replace(" ", "_")
    
    # Try base username first (check credentials DB)
    existing = cred_db.query(UserCredentials).filter(UserCredentials.username == base_username).first()
    if not existing:
        return base_username
    
    # If exists, append random digits
    max_attempts = 100
    for _ in range(max_attempts):
        random_digits = ''.join(secrets.choice(string.digits) for _ in range(3))
        username = f"{base_username}_{random_digits}"
        
        existing = cred_db.query(UserCredentials).filter(UserCredentials.username == username).first()
        if not existing:
            return username
    
    # Fallback: use timestamp
    import time
    return f"{base_username}_{int(time.time()) % 10000}"


def generate_password(length: int = 8) -> str:
    """Generate a random alphanumeric password."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


@router.post("/create", response_model=StaffCreateResponse)
async def create_staff(
    staff_data: StaffCreateRequest,
    db: Session = Depends(get_db),
    cred_db: Session = Depends(get_credentials_db),
    owner: User = Depends(require_owner),
):
    """
    Create a new staff account with auto-generated credentials.
    Only owners can create staff accounts.
    Credentials are stored in credentials.db
    """
    if not staff_data.staff_name or not staff_data.staff_name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Staff name is required",
        )

    # Validate owner business name
    if not owner.business_name or not owner.business_name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Owner does not have a business name configured. Please update your profile.",
        )
    
    business_name = owner.business_name.strip()

    try:
        # Generate username from first name
        first_name = staff_data.staff_name.strip().split()[0]  # Get first name
        generated_username = generate_username(first_name, cred_db)
        
        # Generate password and security code
        generated_password = generate_password(8)
        security_code = generate_security_code()
        
        # Calculate hash ONCE
        hashed_password = get_password_hash(generated_password)

        # Store credentials in credentials database (HASHED password now)
        new_credentials = UserCredentials(
            username=generated_username,
            email=staff_data.email,  # Staff email
            password=hashed_password,  # Store HASHED password
            full_name=staff_data.staff_name.strip(),
            business_name=business_name,
            business_type=owner.business_type, # Inherit business type
            role="staff",
            is_active=True,
            is_auto_generated=True,  # Mark as auto-generated
            security_code=security_code,
            owner_id=owner.id, # Link to owner
            created_at=datetime.utcnow(),
        )
        cred_db.add(new_credentials)
        cred_db.commit()
        cred_db.refresh(new_credentials)
        
        # Also create user in main database
        new_staff = User(
            username=generated_username,
            email=staff_data.email, # Save email in main DB too
            hashed_password=hashed_password, # Use message hash

            full_name=staff_data.staff_name.strip(),
            business_name=business_name,
            business_type=owner.business_type, # Inherit business type
            role=UserRole.STAFF,
            is_active=True,
            security_code=security_code,
            owner_id=owner.id, # Link to owner for Cascade Delete
            created_at=datetime.utcnow(),
        )
        db.add(new_staff)
        db.commit()
        
        # Refresh to get ID and other specific DB fields
        db.refresh(new_staff)

        # Send Welcome Email (Background Task ideally, but synchronous for now)
        if staff_data.email:
            from app.utils.email import send_welcome_email
            # We wrap this in a try-except block inside the function, so it won't crash the request
            send_welcome_email(staff_data.email, generated_username, generated_password, security_code)

        return StaffCreateResponse(
            id=new_staff.id,
            full_name=new_staff.full_name,
            username=generated_username,
            password=generated_password,  # Return raw password
            security_code=security_code,
            business_name=new_staff.business_name,
            message="Staff account created successfully. Save these credentials now - they will not be shown again.",
        )
    except IntegrityError as e:
        cred_db.rollback()
        db.rollback()
        error_info = str(e.orig) if hasattr(e, 'orig') else str(e)
        if "email" in error_info.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A staff member with this email address is already registered."
            )
        elif "username" in error_info.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username collision occurred. Please try again."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This staff member already exists in the system."
            )

    except Exception as e:
        cred_db.rollback()
        db.rollback()
        print(f"Staff creation error: {e}")
        import traceback
        traceback.print_exc()
        # General error fallback - hide detailed SQL info from user interface if possible
        # but keep it useful enough for debugging if it's not SQL related
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating the staff account. Please check the logs."
        )


@router.get("/list", response_model=list[StaffResponse])
async def list_staff(
    db: Session = Depends(get_db),
    owner: User = Depends(require_owner),
):
    """
    List all staff members for the owner's business.
    """
    if not owner.business_name:
        print("DEBUG: Owner has no business name!")
        return []

    # Normalize business name for filtering
    owner_business = owner.business_name.strip()
    
    print(f"DEBUG: Listing staff for Owner: '{owner.username}' Business: '{owner_business}'")
    
    # DEBUG: Check if ANY users exist
    all_users = db.query(User).all()
    print(f"DEBUG: Total users in DB: {len(all_users)}")
    for u in all_users:
        print(f"DEBUG: User: {u.username}, Role: {u.role}, Business: '{u.business_name}'")

    # Case-insensitive business name matching
    # SQLite default collation is usually case-insensitive for ASCII, but we'll be explicit
    # Using python-side filtering for robust debug comparison if needed, but SQL filter is better.
    # We will use ilike or simple comparison after strip. Since business info is critical, exact match on normalized string is best.
    
    try:
        staff_list = db.query(User).filter(
            User.role == UserRole.STAFF,
            User.owner_id == owner.id
        ).all()
        
        print(f"DEBUG: Found {len(staff_list)} staff members after filter")
        
        # Ensure response matches schema, particularly datetime
        response = []
        for staff in staff_list:
            response.append(StaffResponse(
                id=staff.id,
                username=staff.username,
                full_name=staff.full_name,
                business_name=staff.business_name,
                role=staff.role.value if hasattr(staff.role, 'value') else str(staff.role),
                is_active=staff.is_active,
                created_at=staff.created_at.isoformat() if isinstance(staff.created_at, datetime) else str(staff.created_at),
                owner_name=staff.owner.full_name if staff.owner else None # Populate reporting manager
            ))
            
        return response
    except Exception as e:
        print(f"Error listing staff: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve staff list. Please try again later."
        )


@router.delete("/{staff_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_staff(
    staff_id: int,
    db: Session = Depends(get_db),
    cred_db: Session = Depends(get_credentials_db),
    owner: User = Depends(require_owner),
):
    """
    Delete a staff member.
    Only owners can delete staff from their business.
    """
    # Find staff in main DB
    staff_member = db.query(User).filter(
        User.id == staff_id,
        User.business_name == owner.business_name,
        User.role == UserRole.STAFF
    ).first()

    if not staff_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Staff member not found"
        )

    try:
        # 1. Reassign Sales (Non-nullable created_by) to Owner
        from app.models.sale import Sale
        db.query(Sale).filter(Sale.created_by_id == staff_id).update({Sale.created_by_id: owner.id})
        
        # 2. Unlink Transactions (Nullable created_by) - Keep handler_name string for history
        from app.models.account import Transaction
        db.query(Transaction).filter(Transaction.created_by_id == staff_id).update({Transaction.created_by_id: None})

        db.commit()

        # 3. Delete from credentials DB
        cred_user = cred_db.query(UserCredentials).filter(
            UserCredentials.username == staff_member.username
        ).first()
        
        if cred_user:
            cred_db.delete(cred_user)
            cred_db.commit()

        # 4. Delete from main DB
        db.delete(staff_member)
        db.commit()
        
    except Exception as e:
        db.rollback()
        cred_db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete staff member: {str(e)}"
        )

