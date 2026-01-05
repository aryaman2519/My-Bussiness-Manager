from app.models.database import engine as main_engine, Base as MainBase, SessionLocal
from app.models.credentials_db import credentials_engine, CredentialsBase, CredentialsSessionLocal
from app.models.user import User
from app.models.stock import Stock
from app.models.account import Transaction
# Import credentials model to ensure it's registered
from app.models.credentials_db import UserCredentials

print("🔄 Resetting Database State...")

# 1. Recreate Tables (if they were dropped)
print("   - Creating Main DB tables...")
MainBase.metadata.create_all(bind=main_engine)

print("   - Creating Credentials DB tables...")
CredentialsBase.metadata.create_all(bind=credentials_engine)

# 2. Clear All Data (Truncate) -> Just in case tables existed with data
print("   - Clearing all user data...")

db = SessionLocal()
cred_db = CredentialsSessionLocal()

try:
    # Delete from Child tables first to avoid FK constraints (if cascading fails)
    db.query(Stock).delete()
    db.query(Transaction).delete()
    db.query(User).delete()
    db.commit()
    print("     ✅ Main DB users & data cleared.")
except Exception as e:
    db.rollback()
    print(f"     ❌ Error clearing Main DB: {e}")

try:
    cred_db.query(UserCredentials).delete()
    cred_db.commit()
    print("     ✅ Credentials DB users cleared.")
except Exception as e:
    cred_db.rollback()
    print(f"     ❌ Error clearing Credentials DB: {e}")

db.close()
cred_db.close()

print("✨ Database reset complete. Zero users. Ready for registration.")
