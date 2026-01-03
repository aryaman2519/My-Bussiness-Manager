from app.models.database import engine
from sqlalchemy import text

def fix_schema():
    print("Dropping stale transactions table...")
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS transactions"))
        conn.commit()
    print("Table dropped. Restart the backend to recreate it with new schema.")

if __name__ == "__main__":
    fix_schema()
