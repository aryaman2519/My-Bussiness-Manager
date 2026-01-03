"""
Create credentials.db file - Standalone script to create credentials database.

Usage:
    python scripts/create_credentials_db_only.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base

# Create credentials database
CREDENTIALS_DB_URL = "sqlite:///./credentials.db"
credentials_engine = create_engine(
    CREDENTIALS_DB_URL,
    connect_args={"check_same_thread": False}
)

CredentialsBase = declarative_base()

# Define the table
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func

class UserCredentials(CredentialsBase):
    __tablename__ = "user_credentials"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    business_name = Column(String, nullable=True)
    role = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    is_auto_generated = Column(Boolean, default=False, nullable=False)

def create_credentials_db():
    """Create credentials.db file."""
    print("Creating credentials.db file...")
    try:
        CredentialsBase.metadata.create_all(bind=credentials_engine)
        print("✅ credentials.db file created successfully!")
        print("Location: backend/credentials.db")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_credentials_db()



