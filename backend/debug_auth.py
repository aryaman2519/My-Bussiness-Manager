import sys
import os

# Ensure backend dir is in path
sys.path.append(os.getcwd())

from app.models.credentials_db import get_credentials_db, UserCredentials
from app.auth.security import verify_password

def debug_login():
    db = next(get_credentials_db())
    try:
        user = db.query(UserCredentials).filter(UserCredentials.username == "arya").first()
        if not user:
            print("User 'arya' NOT FOUND in credentials db.")
        else:
            print(f"User Found: ID={user.id}")
            print(f"Stored Username: {repr(user.username)}")
            print(f"Stored Password: {repr(user.password)}")
            
            input_pass = "123456"
            print(f"Testing against input: {repr(input_pass)}")
            
            is_match = verify_password(input_pass, user.password)
            print(f"Match Result: {is_match}")
            
            if not is_match:
                print("MISMATCH DETECTED!")
                print(f"Lengths: Stored={len(user.password)}, Input={len(input_pass)}")
                
    finally:
        db.close()

if __name__ == "__main__":
    debug_login()
