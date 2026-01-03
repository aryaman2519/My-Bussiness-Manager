"""
Separate database for storing user credentials.
This keeps credentials isolated from business data.
"""
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.sql import func
from app.config import get_settings

settings = get_settings()

# Credentials database URL from config
CREDENTIALS_DB_URL = settings.credentials_db_url

# Create engine for credentials database
credentials_engine = create_engine(
    CREDENTIALS_DB_URL,
    connect_args={"check_same_thread": False}
)

CredentialsSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=credentials_engine)

# Base for credentials models
CredentialsBase = declarative_base()


class UserCredentials(CredentialsBase):
    """Stores user credentials separately from business data."""
    __tablename__ = "user_credentials"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    password = Column(String, nullable=False)  # Plain text password
    full_name = Column(String, nullable=False)
    business_name = Column(String, nullable=True)
    role = Column(String, nullable=False)  # 'owner' or 'staff'
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    is_auto_generated = Column(Boolean, default=False, nullable=False)  # True for staff, False for owners
    
    # New Fields matching main User model
    security_code = Column(String, nullable=True)
    business_type = Column(String, nullable=True)
    owner_id = Column(Integer, nullable=True) # Reference to owner's ID in MAIN DB (conceptually) or just plain int


def get_credentials_db():
    """Dependency for getting credentials database session."""
    db = CredentialsSessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_credentials_db():
    """Initialize credentials database tables."""
    CredentialsBase.metadata.create_all(bind=credentials_engine)

