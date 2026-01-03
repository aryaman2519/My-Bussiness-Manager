from app.models.database import engine, Base
from sqlalchemy import text

def migrate():
    with engine.connect() as conn:
        try:
            # Check if column exists
            columns = conn.execute(text("PRAGMA table_info(sales)")).fetchall()
            column_names = [col[1] for col in columns]
            
            if 'pdf_file_path' not in column_names:
                print("Adding pdf_file_path column to sales table...")
                conn.execute(text("ALTER TABLE sales ADD COLUMN pdf_file_path VARCHAR"))
                conn.commit()
                print("Migration successful: pdf_file_path column added.")
            else:
                print("Migration skipped: pdf_file_path column already exists.")
                
        except Exception as e:
            print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate()
