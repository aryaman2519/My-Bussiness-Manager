from app.models.database import engine
from sqlalchemy import text, inspect

def migrate():
    inspector = inspect(engine)
    columns = [c['name'] for c in inspector.get_columns('stock')]
    
    with engine.connect() as conn:
        if 'threshold_quantity' not in columns:
            print("Adding threshold_quantity column...")
            conn.execute(text("ALTER TABLE stock ADD COLUMN threshold_quantity INTEGER DEFAULT 5 NOT NULL"))
        else:
            print("threshold_quantity already exists.")

        if 'last_alert_sent' not in columns:
            print("Adding last_alert_sent column...")
            conn.execute(text("ALTER TABLE stock ADD COLUMN last_alert_sent DATETIME"))
        else:
            print("last_alert_sent already exists.")
        
        conn.commit()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
