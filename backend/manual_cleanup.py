import sys
import os
from sqlalchemy import text

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from app.models.database import SessionLocal
from app.models.credentials_db import CredentialsSessionLocal # Assuming this works, if not we'll use raw generic

def wipe_all_data_raw():
    db = SessionLocal()
    cred_db = CredentialsSessionLocal()
    
    try:
        print("Starting Full Database Wipe (RAW SQL)...")
        
        # 1. Main DB Tables
        # Order matters for FKs
        tables_to_wipe = [
            "sale_items",
            "sales",
            "stock", # stock might depend on products
            "products",
            "categories",
            "business_settings", # Assuming table name
            "inventory_items", # Just in case
            "users"
        ]
        
        for table in tables_to_wipe:
            try:
                print(f"Deleting table: {table}")
                db.execute(text(f"DELETE FROM {table}"))
                # If table doesn't exist, it might throw error, catch it
            except Exception as e:
                print(f"Skipping {table} (maybe not exists or error): {e}")

        db.commit()
        print("Main Database Wiped.")

        # 2. Credentials DB
        try:
            print("Deleting user_credentials...")
            cred_db.execute(text("DELETE FROM user_credentials"))
            cred_db.commit()
            print("Credentials Database Wiped.")
        except Exception as e:
             print(f"Error wiping creds: {e}")
        
    except Exception as e:
        print(f"Error during wipe: {e}")
        db.rollback()
        cred_db.rollback()
    finally:
        db.close()
        cred_db.close()

if __name__ == "__main__":
    wipe_all_data_raw()
