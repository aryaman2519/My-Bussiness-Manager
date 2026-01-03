import sqlite3
import os

DB_FILE = "./smartstock.db"

def migrate():
    if not os.path.exists(DB_FILE):
        print(f"Database file {DB_FILE} not found. Skipping migration.")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Get columns
    cursor.execute("PRAGMA table_info(stock)")
    columns = [info[1] for info in cursor.fetchall()]
    
    if 'threshold_quantity' not in columns:
        print("Adding threshold_quantity column...")
        try:
            cursor.execute("ALTER TABLE stock ADD COLUMN threshold_quantity INTEGER DEFAULT 5 NOT NULL")
        except Exception as e:
            print(f"Error adding threshold_quantity: {e}")
    else:
        print("threshold_quantity already exists.")

    if 'last_alert_sent' not in columns:
        print("Adding last_alert_sent column...")
        try:
             cursor.execute("ALTER TABLE stock ADD COLUMN last_alert_sent DATETIME")
        except Exception as e:
            print(f"Error adding last_alert_sent: {e}")
    else:
        print("last_alert_sent already exists.")
        
    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
