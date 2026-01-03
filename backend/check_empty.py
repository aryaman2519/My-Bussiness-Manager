
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User

SQLALCHEMY_DATABASE_URL = "sqlite:///./smartstock.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def check_db():
    try:
        db = SessionLocal()
        count = db.query(User).count()
        print(f"User count in 'smartstock.db': {count}")
        if count == 0:
            print("✅ Database is empty.")
        else:
            print(f"⚠️ Database NOT empty. Found {count} users.")
        db.close()
    except Exception as e:
        print(f"Error checking DB: {e}")

if __name__ == "__main__":
    check_db()
