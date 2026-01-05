from app.models.database import engine as main_engine, Base as MainBase
from app.models.credentials_db import credentials_engine, CredentialsBase
from sqlalchemy import text

print("💥 Nuking All Database Tables...")

def nuke_db(engine, base_name):
    try:
        with engine.connect() as connection:
            # Disable foreign key checks to allow dropping tables in any order
            connection.execute(text("PRAGMA foreign_keys = OFF;"))
            
            # Get table names
            result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
            tables = [row[0] for row in result if row[0] != 'sqlite_sequence']
            
            for table in tables:
                connection.execute(text(f"DROP TABLE IF EXISTS {table};"))
                print(f"   - Dropped table: {table}")
            
            connection.execute(text("PRAGMA foreign_keys = ON;"))
            connection.commit()
            print(f"✅ {base_name} Cleared.")
    except Exception as e:
        print(f"❌ Error clearing {base_name}: {e}")

# Nuke Main DB
nuke_db(main_engine, "Main Database")

# Nuke Credentials DB
nuke_db(credentials_engine, "Credentials Database")

print("✨ Cleanup Complete. Please Restart Server.")
