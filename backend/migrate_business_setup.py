"""
Database Migration Script - Add Business Setup Fields

Adds new columns to the users table for the invoice template PDF system:
- business_logo
- business_address
- business_phone
- signature_image
- template_pdf_path
- template_coordinates

Run this script to update the database schema without losing existing data.
"""

import sqlite3
import os

def migrate_add_business_fields():
    """Add business setup fields to users table."""
    
    # Database path
    db_path = os.path.join(os.path.dirname(__file__), 'smartstock.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return False
    
    print(f"📁 Connecting to database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(users)")
        existing_columns = [col[1] for col in cursor.fetchall()]
        
        new_columns = {
            'business_logo': 'TEXT',
            'business_address': 'TEXT',
            'business_phone': 'TEXT',
            'signature_image': 'TEXT',
            'template_pdf_path': 'TEXT',
            'template_coordinates': 'TEXT'
        }
        
        added_count = 0
        
        for column_name, column_type in new_columns.items():
            if column_name not in existing_columns:
                print(f"➕ Adding column: {column_name}")
                cursor.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}")
                added_count += 1
            else:
                print(f"✓ Column already exists: {column_name}")
        
        conn.commit()
        
        if added_count > 0:
            print(f"\n✅ Migration successful! Added {added_count} new column(s)")
        else:
            print(f"\n✅ All columns already exist. No migration needed.")
        
        # Verify the changes
        cursor.execute("PRAGMA table_info(users)")
        all_columns = [col[1] for col in cursor.fetchall()]
        print(f"\n📋 Total columns in users table: {len(all_columns)}")
        print(f"   New business fields present: {all(col in all_columns for col in new_columns.keys())}")
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("DATABASE MIGRATION: Add Business Setup Fields")
    print("=" * 60)
    print()
    
    success = migrate_add_business_fields()
    
    print()
    print("=" * 60)
    if success:
        print("Migration completed successfully!")
    else:
        print("Migration failed. Please check errors above.")
    print("=" * 60)
