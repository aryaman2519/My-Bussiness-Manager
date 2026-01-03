"""
Create database tables - Creates database.db file with all tables.

Usage:
    python scripts/create_tables.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.database import engine, Base
from app.models import *  # Import all models
from app.models.credentials_db import init_credentials_db


def create_tables():
    """Create all database tables for both databases."""
    print("=" * 60)
    print("Creating Database Tables for SmartStock 360")
    print("=" * 60)
    print()
    
    try:
        from app.models.user import User
        
        # Create main database tables
        print("Creating main database (database.db)...")
        Base.metadata.create_all(bind=engine)
        print("✅ database.db created")
        print()
        
        # Create credentials database tables
        print("Creating credentials database (credentials.db)...")
        init_credentials_db()
        print("✅ credentials.db created")
        print()
        
        # Verify files exist
        import os
        db_files = []
        if os.path.exists("database.db"):
            db_files.append("✓ database.db")
        if os.path.exists("credentials.db"):
            db_files.append("✓ credentials.db")
        
        print("✅ All databases created successfully!")
        print()
        print("Database files created:")
        for db_file in db_files:
            print(f"  {db_file}")
        print()
        print("Main database (database.db):")
        print("  - Stores: Products, Sales, Inventory, etc.")
        for table_name in sorted(Base.metadata.tables.keys()):
            print(f"    ✓ {table_name}")
        print()
        print("Credentials database (credentials.db):")
        print("  - Stores: User credentials (owners & staff)")
        print("    ✓ user_credentials")
        print()
        print("Next steps:")
        print("  1. Start backend: uvicorn app.main:app --reload")
        print("  2. Start frontend: cd frontend && npm run dev")
        print("  3. Register at: http://localhost:5173/register")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    create_tables()

