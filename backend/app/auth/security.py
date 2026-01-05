from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.config import get_settings
from app.models.database import get_db
from app.models.user import User, UserRole

settings = get_settings()

# We keep this for hashing passwords into the main DB
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def verify_password(plain_password: str, stored_password: str) -> bool:
    """
    Verify a stored password against the provided plain password.
    """
    # Truncate to 72 bytes strictly to match hashing behavior
    b_plain = plain_password.encode("utf-8")
    if len(b_plain) > 72:
        b_plain = b_plain[:72]
    
    # DECISION: Passlib/Bcrypt can be finicky with bytes on some platforms
    # Decode back to utf-8 string, ignoring errors (lossy is fine for truncation)
    valid_str = b_plain.decode("utf-8", errors="ignore")
    
    return pwd_context.verify(valid_str, stored_password)

def get_password_hash(password: str) -> str:
    """Hash a password for the main application database."""
    print(f"DEBUG: Input PW Len: {len(password)}")
    
    # Ensure strict 72-byte limit
    b = password.encode("utf-8")
    if len(b) > 72:
        print("DEBUG: Truncating password bytes")
        b = b[:72]
        
    # DECISION: Decode back to utf-8 string for maximum compatibility
    valid_str = b.decode("utf-8", errors="ignore")
    print(f"DEBUG: Hashing final string of len: {len(valid_str)}")
    
    return pwd_context.hash(valid_str)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    # Ensure settings.secret_key is used
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm="HS256")
    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """Get the current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get the current active user."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def require_owner(current_user: User = Depends(get_current_active_user)) -> User:
    """Require the current user to be an owner."""
    if current_user.role != UserRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can perform this action",
        )
    return current_user