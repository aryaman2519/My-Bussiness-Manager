"""
Database Migration - Update SaleItem Foreign Key

Changes sale_items.product_id to reference stock table instead of products table.
This fixes the FOREIGN KEY constraint error during billing.
"""

import sqlite3
import os

def migrate_fix_sale_items_fk():
    """Update sale_items table to reference stock instead of products."""
    
    db_path = os.path.join(os.path.dirname(__file__), 'smartstock.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return False
    
    print(f"📁 Connecting to database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Since SQLite doesn't support modifying foreign keys directly,
        # we need to recreate the table
        
        print("🔍 Checking sale_items table...")
        
        # Check if sale_items table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sale_items'")
        if not cursor.fetchone():
            print("✅ sale_items table doesn't exist yet - will be created with correct schema")
            conn.close()
            return True
        
        # Backup existing data
        print("💾 Backing up existing sale_items data...")
        cursor.execute("SELECT * FROM sale_items")
        existing_data = cursor.fetchall()
        
        print(f"   Found {len(existing_data)} existing sale items")
        
        # Drop the old table
        print("🗑️  Dropping old sale_items table...")
        cursor.execute("DROP TABLE IF EXISTS sale_items")
        
        # Create new table with updated foreign key
        print("🔨 Creating new sale_items table with stock reference...")
        cursor.execute("""
            CREATE TABLE sale_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                total_price REAL NOT NULL,
                unit_cost REAL,
                profit REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sale_id) REFERENCES sales(id),
                FOREIGN KEY (product_id) REFERENCES stock(id)
            )
        """)
        
        cursor.execute("CREATE INDEX ix_sale_items_sale_id ON sale_items(sale_id)")
        cursor.execute("CREATE INDEX ix_sale_items_product_id ON sale_items(product_id)")
        
        # Restore data if any existed
        if existing_data:
            print(f"📥 Restoring {len(existing_data)} sale items...")
            for row in existing_data:
                cursor.execute("""
                    INSERT INTO sale_items 
                    (id, sale_id, product_id, quantity, unit_price, total_price, unit_cost, profit, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, row)
        
        conn.commit()
        
        print("\n✅ Migration successful!")
        print("   sale_items.product_id now references stock.id")
        
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
    print("DATABASE MIGRATION: Fix SaleItem Foreign Key")
    print("=" * 60)
    print()
    
    success = migrate_fix_sale_items_fk()
    
    print()
    print("=" * 60)
    if success:
        print("Migration completed successfully!")
        print("You can now restart the server and generate bills.")
    else:
        print("Migration failed. Please check errors above.")
    print("=" * 60)
