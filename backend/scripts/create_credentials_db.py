"""
Create credentials database - Creates credentials.db file for storing user credentials.

Usage:
    python scripts/create_credentials_db.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.credentials_db import CredentialsBase, credentials_engine, init_credentials_db


def create_credentials_db():
    """Create credentials database tables."""
    print("=" * 60)
    print("Creating Credentials Database")
    print("=" * 60)
    print()
    
    try:
        # Initialize credentials database
        init_credentials_db()
        
        print("✅ Credentials database created successfully!")
        print()
        print("Database file: credentials.db")
        print()
        print("Created tables:")
        for table_name in sorted(CredentialsBase.metadata.tables.keys()):
            print(f"  ✓ {table_name}")
        print()
        print("This database stores:")
        print("  - Owner registration credentials")
        print("  - Staff auto-generated credentials")
        print("  - All user authentication data")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    create_credentials_db()



