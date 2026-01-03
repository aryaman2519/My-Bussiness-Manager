from app.models.database import engine
from sqlalchemy import text, inspect

def migrate():
    inspector = inspect(engine)
    columns = [c['name'] for c in inspector.get_columns('users')]
    
    with engine.connect() as conn:
        if 'invoice_template_html' not in columns:
            print("Adding invoice_template_html column...")
            conn.execute(text("ALTER TABLE users ADD COLUMN invoice_template_html TEXT"))
            conn.commit()
            print("invoice_template_html added successfully.")
        else:
            print("invoice_template_html already exists.")

        if 'invoice_mapping' not in columns:
            print("Adding invoice_mapping column...")
            conn.execute(text("ALTER TABLE users ADD COLUMN invoice_mapping TEXT"))
            conn.commit()
            print("invoice_mapping added successfully.")
        else:
            print("invoice_mapping already exists.")
        
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
