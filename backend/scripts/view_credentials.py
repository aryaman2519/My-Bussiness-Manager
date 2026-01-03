"""
View credentials database - See all stored credentials with passwords.

Usage:
    python scripts/view_credentials.py
"""
import sqlite3
from pathlib import Path

db_path = Path(__file__).parent.parent / "credentials.db"

if not db_path.exists():
    print("[ERROR] credentials.db not found!")
    exit(1)

try:
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, username, email, password, full_name, business_name, 
               role, is_active, is_auto_generated, created_at 
        FROM user_credentials
        ORDER BY id
    """)
    
    rows = cursor.fetchall()
    
    if not rows:
        print("No credentials found in database.")
    else:
        print("=" * 80)
        print("CREDENTIALS DATABASE - ALL PASSWORDS")
        print("=" * 80)
        print()
        
        for row in rows:
            (id_val, username, email, password, full_name, business_name, 
             role, is_active, is_auto_generated, created_at) = row
            
            role_label = "[OWNER]" if role == "owner" else "[STAFF]"
            status = "[ACTIVE]" if is_active else "[INACTIVE]"
            auto_gen = "[AUTO-GENERATED]" if is_auto_generated else "[USER-SET]"
            
            print(f"{role_label} ID: {id_val}")
            print(f"   Name: {full_name}")
            print(f"   Username: {username}")
            print(f"   Email: {email or 'N/A'}")
            print(f"   Business: {business_name or 'N/A'}")
            print(f"   Role: {role.upper()}")
            print(f"   Status: {status}")
            print(f"   Password Type: {auto_gen}")
            print(f"   PASSWORD: {password}")
            print(f"   Created: {created_at}")
            print("-" * 80)
            print()
        
        print(f"Total: {len(rows)} credentials")
    
    conn.close()
    
except sqlite3.Error as e:
    print(f"[ERROR] Database error: {e}")
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
