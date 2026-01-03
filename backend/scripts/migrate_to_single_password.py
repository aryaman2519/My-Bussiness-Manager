"""
Migration script to convert credentials.db to single password column.

This script:
1. Creates a new table with password column
2. Migrates data from hashed_password/plain_password to password
3. Drops old columns
4. Renames table

Usage:
    python scripts/migrate_to_single_password.py
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
    
    print("Starting migration to single password column...")
    print()
    
    # Step 1: Get all existing data
    cursor.execute("SELECT * FROM user_credentials")
    rows = cursor.fetchall()
    
    # Get column names
    cursor.execute("PRAGMA table_info(user_credentials)")
    columns = [col[1] for col in cursor.fetchall()]
    
    print(f"Found {len(rows)} records to migrate")
    print(f"Current columns: {', '.join(columns)}")
    print()
    
    # Step 2: Create backup table
    print("Creating backup table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_credentials_backup AS 
        SELECT * FROM user_credentials
    """)
    print("[OK] Backup created")
    print()
    
    # Step 3: Drop old table and create new one with password column
    print("Creating new table structure...")
    cursor.execute("DROP TABLE IF EXISTS user_credentials_new")
    cursor.execute("""
        CREATE TABLE user_credentials_new (
            id INTEGER PRIMARY KEY,
            username VARCHAR UNIQUE NOT NULL,
            email VARCHAR,
            password VARCHAR NOT NULL,
            full_name VARCHAR NOT NULL,
            business_name VARCHAR,
            role VARCHAR NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT 1,
            created_at DATETIME NOT NULL,
            is_auto_generated BOOLEAN NOT NULL DEFAULT 0
        )
    """)
    print("[OK] New table created")
    print()
    
    # Step 4: Migrate data
    print("Migrating data...")
    migrated = 0
    
    for row in rows:
        row_dict = dict(zip(columns, row))
        
        # Determine password to use
        password = None
        
        # Try plain_password first (for staff)
        if 'plain_password' in row_dict and row_dict['plain_password']:
            password = row_dict['plain_password']
        # Otherwise use hashed_password (we'll store it as-is, but it's actually hashed)
        elif 'hashed_password' in row_dict and row_dict['hashed_password']:
            # For existing records, we'll keep the hash but note it needs to be updated
            # Actually, let's extract plain password if possible, or use a placeholder
            password = row_dict['hashed_password']  # Temporary - user will need to reset
        
        if not password:
            print(f"[WARNING] No password found for user {row_dict.get('username', 'unknown')}")
            continue
        
        # Insert into new table
        cursor.execute("""
            INSERT INTO user_credentials_new 
            (id, username, email, password, full_name, business_name, 
             role, is_active, created_at, is_auto_generated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row_dict.get('id'),
            row_dict.get('username'),
            row_dict.get('email'),
            password,
            row_dict.get('full_name'),
            row_dict.get('business_name'),
            row_dict.get('role'),
            row_dict.get('is_active', True),
            row_dict.get('created_at'),
            row_dict.get('is_auto_generated', False)
        ))
        migrated += 1
    
    print(f"[OK] Migrated {migrated} records")
    print()
    
    # Step 5: Replace old table with new one
    print("Replacing table...")
    cursor.execute("DROP TABLE user_credentials")
    cursor.execute("ALTER TABLE user_credentials_new RENAME TO user_credentials")
    print("[OK] Table replaced")
    print()
    
    # Step 6: Verify
    cursor.execute("SELECT COUNT(*) FROM user_credentials")
    count = cursor.fetchone()[0]
    print(f"[OK] Verification: {count} records in new table")
    print()
    
    # Show sample data
    cursor.execute("SELECT id, username, password FROM user_credentials LIMIT 3")
    samples = cursor.fetchall()
    print("Sample data:")
    for sample in samples:
        print(f"  ID {sample[0]}: {sample[1]} - Password: {sample[2][:20]}...")
    print()
    
    conn.commit()
    conn.close()
    
    print("=" * 60)
    print("Migration completed successfully!")
    print("=" * 60)
    print()
    print("NOTE: Existing passwords were migrated from hashed_password.")
    print("      For security, users should reset their passwords.")
    print("      New registrations will store plain passwords.")
    
except sqlite3.Error as e:
    print(f"[ERROR] Database error: {e}")
    conn.rollback()
    conn.close()
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
    if conn:
        conn.close()



