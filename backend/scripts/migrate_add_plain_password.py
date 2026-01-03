"""
Migration script to add plain_password column to existing credentials.db

Usage:
    python scripts/migrate_add_plain_password.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import sqlite3
    
    db_path = Path(__file__).parent.parent / "credentials.db"
    
    if not db_path.exists():
        print("[ERROR] credentials.db not found. Run create_tables.py first.")
        sys.exit(1)
    
    print("Adding plain_password column to user_credentials table...")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(user_credentials)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'plain_password' in columns:
            print("[OK] plain_password column already exists!")
        else:
            # Add the column
            cursor.execute("""
                ALTER TABLE user_credentials 
                ADD COLUMN plain_password TEXT NULL
            """)
            conn.commit()
            print("[OK] plain_password column added successfully!")
        
        # Show table structure
        cursor.execute("PRAGMA table_info(user_credentials)")
        print("\nTable structure:")
        for col in cursor.fetchall():
            print(f"  - {col[1]} ({col[2]})")
        
    except sqlite3.OperationalError as e:
        print(f"[ERROR] {e}")
        print("Make sure the user_credentials table exists.")
    finally:
        conn.close()
        
except ImportError:
    print("[ERROR] sqlite3 not available. This script requires Python's built-in sqlite3.")
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()

