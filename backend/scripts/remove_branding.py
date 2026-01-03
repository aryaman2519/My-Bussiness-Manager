import sys
import os

# Add the parent directory to sys.path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.database import SessionLocal
from app.models.user import User

def remove_branding():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        count = 0
        for user in users:
            if user.business_logo or user.signature_image:
                user.business_logo = None
                user.signature_image = None
                count += 1
        
        db.commit()
        print(f"Successfully removed branding from {count} users.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    remove_branding()
