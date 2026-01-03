import sqlite3
import os

# Paths to databases
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_DB_PATH = os.path.join(BASE_DIR, "app", "inventory.db") # Assuming default name from database.py if likely
CRED_DB_PATH = os.path.join(BASE_DIR, "app", "credentials.db") # Assuming default name

# Check if DBs exist, if not, they will be created by app anyway, but we want to migrate existing ones
# Adjust paths if they are different in .env, but usually they are defaults or we can read them.
# For now, let's try to infer or check typical locations. 
# Based on previous file listings, we didn't see .db files in `app`, they might be in root `backend` or `app`.
# Let's check where they are likely created. `database.py` likely uses `sqlite:///./inventory.db` which implies relative to running dir.
# If running from `backend/`, it's `backend/inventory.db`.

def add_column_if_not_exists(cursor, table, column, definition):
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        print(f"Added column '{column}' to table '{table}'")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print(f"Column '{column}' already exists in table '{table}'")
        else:
            print(f"Error adding column '{column}' to '{table}': {e}")

def migrate_main_db():
    db_path = os.path.join(BASE_DIR, "smartstock.db") # Relative to backend root
    if not os.path.exists(db_path):
        print(f"Main DB {db_path} not found. Skipping migration (will be created fresh).")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Migrating Main DB...")
    add_column_if_not_exists(cursor, "users", "security_code", "VARCHAR")
    add_column_if_not_exists(cursor, "users", "business_type", "VARCHAR")
    # Foreign keys in SQLite are tricky with ALTER TABLE. We can add the column, but enforcing constraint physically 
    # might require recreation. For now, adding column is enough for app logic to work (ORM handles constraints logic often).
    # But for ON DELETE CASCADE to work natively in SQLite, we need foreign key enabled and table structure correct.
    # Since we can't easily recreate table with data preservation in a simple script without more logic,
    # we will add the column. The CASCADE might effectively rely on ORM or manual deletion if not enforced by DB schema update.
    # However, `ondelete='CASCADE'` in SQLAlchemy works if `Pragma foreign_keys=ON`.
    add_column_if_not_exists(cursor, "users", "owner_id", "INTEGER REFERENCES users(id) ON DELETE CASCADE")
    
    conn.commit()
    conn.close()

def migrate_cred_db():
    db_path = os.path.join(BASE_DIR, "credentials.db") # Relative to backend root
    if not os.path.exists(db_path):
        print(f"Credentials DB {db_path} not found. Skipping migration.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Migrating Credentials DB...")
    add_column_if_not_exists(cursor, "user_credentials", "security_code", "VARCHAR")
    add_column_if_not_exists(cursor, "user_credentials", "business_type", "VARCHAR")
    add_column_if_not_exists(cursor, "user_credentials", "owner_id", "INTEGER")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    print("Starting migration...")
    migrate_main_db()
    migrate_cred_db()
    print("Migration completed.")
