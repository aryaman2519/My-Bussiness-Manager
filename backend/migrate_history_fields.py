
import sqlite3
import os

# Database file path
DB_FILE = "smartstock.db"

def migrate():
    print("="*60)
    print("DATABASE MIGRATION: Add Billing History Fields")
    print("="*60)

    if not os.path.exists(DB_FILE):
        print(f"❌ Database file {DB_FILE} not found!")
        return

    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        print(f"📁 Connecting to database: {DB_FILE}")

        # Check existing columns
        cursor.execute("PRAGMA table_info(sales)")
        columns = [info[1] for info in cursor.fetchall()]

        # Add pdf_file_path if missing
        if 'pdf_file_path' not in columns:
            print("➕ Adding column: pdf_file_path")
            cursor.execute("ALTER TABLE sales ADD COLUMN pdf_file_path TEXT")
        else:
            print("ℹ️ Column 'pdf_file_path' already exists")

        conn.commit()
        print("\n✅ Migration successful!")
        
        # Verify
        cursor.execute("PRAGMA table_info(sales)")
        new_columns = [info[1] for info in cursor.fetchall()]
        print(f"\n📋 Total columns in sales table: {len(new_columns)}")
        print(f"   pdf_file_path present: {'pdf_file_path' in new_columns}")

        conn.close()

    except Exception as e:
        print(f"\n❌ Migration Failed: {e}")

if __name__ == "__main__":
    migrate()
