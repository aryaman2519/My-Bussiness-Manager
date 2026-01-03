"""
Show all credentials with passwords from credentials.db

Usage:
    python scripts/show_all_passwords.py
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
    
    # Get all data
    cursor.execute("""
        SELECT id, username, email, full_name, business_name, role, 
               plain_password, hashed_password, is_auto_generated, 
               is_active, created_at 
        FROM user_credentials
        ORDER BY id
    """)
    
    rows = cursor.fetchall()
    
    if not rows:
        print("No credentials found in database.")
    else:
        print("=" * 80)
        print("ALL CREDENTIALS WITH PASSWORDS")
        print("=" * 80)
        print()
        
        for row in rows:
            (id_val, username, email, full_name, business_name, role, 
             plain_password, hashed_password, is_auto_generated, 
             is_active, created_at) = row
            
            role_label = "[OWNER]" if role == "owner" else "[STAFF]"
            status = "[ACTIVE]" if is_active else "[INACTIVE]"
            auto_gen = "[AUTO]" if is_auto_generated else "[MANUAL]"
            
            print(f"{role_label} ID: {id_val}")
            print(f"   Name: {full_name}")
            print(f"   Username: {username}")
            print(f"   Email: {email or 'N/A'}")
            print(f"   Business: {business_name or 'N/A'}")
            print(f"   Role: {role.upper()}")
            print(f"   Status: {status}")
            print(f"   Password Type: {auto_gen}")
            
            if plain_password:
                print(f"   PLAIN PASSWORD: {plain_password}")
            else:
                print(f"   PLAIN PASSWORD: [Not stored - Owner set their own password]")
            
            print(f"   HASHED PASSWORD: {hashed_password[:60]}...")
            print(f"   Created: {created_at}")
            print("-" * 80)
            print()
        
        print(f"Total: {len(rows)} credentials")
        print()
        print("NOTE: Plain passwords are only stored for auto-generated staff accounts.")
        print("      Owner passwords are never stored in plain text for security.")
    
    conn.close()
    
except sqlite3.Error as e:
    print(f"[ERROR] Database error: {e}")
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()



