"""
Quick script to create user_credentials table in credentials.db

Usage:
    python scripts/create_credentials_table.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from app.models.credentials_db import init_credentials_db
    
    print("Creating user_credentials table in credentials.db...")
    init_credentials_db()
    print("✅ user_credentials table created successfully!")
    print("Location: backend/credentials.db")
    print()
    print("You can now register owners and create staff accounts.")
    
except ImportError as e:
    print(f"❌ Error: Missing dependencies. Please install requirements:")
    print("   pip install -r requirements.txt")
    print(f"   Original error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()



