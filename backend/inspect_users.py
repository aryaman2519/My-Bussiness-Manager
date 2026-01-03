
import sqlite3
import os
import sys

def check_db(db_name):
    with open("db_dump.txt", "a") as f:
        f.write(f"\n--- Inspecting {db_name} ---\n")
        if not os.path.exists(db_name):
            f.write(f"File {db_name} not found!\n")
            return

        try:
            conn = sqlite3.connect(db_name)
            cursor = conn.cursor()
            
            # Check tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            f.write(f"Tables: {[t[0] for t in tables]}\n")
            
            # Check users if exists
            if ('users',) in tables:
                f.write("\nUsers table content:\n")
                cursor.execute("SELECT id, username, business_name, role FROM users")
                rows = cursor.fetchall()
                for row in rows:
                    f.write(f"{row}\n")
            
            # Check user_credentials if exists
            if ('user_credentials',) in tables:
                f.write("\nUserCredentials table content:\n")
                cursor.execute("SELECT id, username, business_name, role FROM user_credentials")
                rows = cursor.fetchall()
                for row in rows:
                    f.write(f"{row}\n")
                    
            conn.close()
        except Exception as e:
            f.write(f"Error reading {db_name}: {e}\n")

if __name__ == "__main__":
    if os.path.exists("db_dump.txt"):
        os.remove("db_dump.txt")
    check_db("smartstock.db")
    check_db("credentials.db")
    check_db("database.db")
