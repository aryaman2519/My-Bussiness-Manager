from app.models.database import engine
from sqlalchemy import text, inspect, Float

def migrate():
    inspector = inspect(engine)
    columns = [c['name'] for c in inspector.get_columns('stock')]
    
    with engine.connect() as conn:
        if 'selling_price' not in columns:
            print("Adding selling_price column...")
            # SQLite doesn't strictly enforce types like Postgres, but we declare it for clarity
            conn.execute(text("ALTER TABLE stock ADD COLUMN selling_price FLOAT DEFAULT 0.0 NOT NULL"))
            conn.commit()
            print("selling_price added successfully.")
        else:
            print("selling_price already exists.")
        
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
